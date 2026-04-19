"""Clerk JWT verification via JWKS + email allowlist enforcement.

Frontend sends `Authorization: Bearer <clerk_session_token>`.
We fetch Clerk's JWKS once, cache, and verify each incoming token.
After verification, the user's primary email is resolved (from JWT claims if
present, otherwise via a cached Clerk Backend API lookup) and checked against
`allowlist.txt`. Missing/empty allowlist = disabled (everyone allowed).

Set AUTH_REQUIRED=false in .env for local dev without auth.
"""

from __future__ import annotations

import logging
from functools import lru_cache
from pathlib import Path
from threading import Lock
from typing import Annotated

import httpx
import jwt
from fastapi import Depends, Header, HTTPException, status
from jwt import PyJWKClient

from app.config import Settings, get_settings

log = logging.getLogger(__name__)


@lru_cache
def _jwks_client(jwks_url: str) -> PyJWKClient:
    log.info("init JWKS client: %s", jwks_url)
    return PyJWKClient(jwks_url, cache_keys=True, lifespan=3600)


def _verify_clerk_token(token: str, settings: Settings) -> dict:
    if not settings.clerk_jwks_url:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="CLERK_JWKS_URL not configured on server",
        )
    try:
        signing_key = _jwks_client(settings.clerk_jwks_url).get_signing_key_from_jwt(token)
        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            issuer=settings.clerk_issuer or None,
            audience=settings.clerk_audience,
            options={
                "verify_aud": settings.clerk_audience is not None,
                "verify_iss": bool(settings.clerk_issuer),
            },
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError as exc:
        raise HTTPException(status_code=401, detail=f"Invalid token: {exc}")
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=503, detail=f"JWKS fetch failed: {exc}")


# --- Allowlist: file-backed, hot-reloaded on mtime change -----------------

_ALLOWLIST_CACHE: dict[str, tuple[float, frozenset[str]]] = {}
_ALLOWLIST_LOCK = Lock()


def _load_allowlist(path: Path) -> frozenset[str]:
    try:
        mtime = path.stat().st_mtime
    except FileNotFoundError:
        return frozenset()
    key = str(path)
    with _ALLOWLIST_LOCK:
        cached = _ALLOWLIST_CACHE.get(key)
        if cached and cached[0] == mtime:
            return cached[1]
        emails: set[str] = set()
        for line in path.read_text(encoding="utf-8").splitlines():
            entry = line.split("#", 1)[0].strip().lower()
            if entry:
                emails.add(entry)
        result = frozenset(emails)
        _ALLOWLIST_CACHE[key] = (mtime, result)
        log.info("allowlist loaded from %s: %d entries", path, len(result))
        return result


# --- Email resolution: JWT claims first, Clerk API fallback (cached) ------

_USER_EMAIL_CACHE: dict[str, str] = {}


def _email_from_claims(payload: dict) -> str | None:
    for key in ("email", "email_address", "primary_email_address"):
        val = payload.get(key)
        if isinstance(val, str) and "@" in val:
            return val
    return None


def _email_from_clerk_api(user_id: str, settings: Settings) -> str | None:
    cached = _USER_EMAIL_CACHE.get(user_id)
    if cached is not None:
        return cached
    if not settings.clerk_secret_key:
        log.warning("CLERK_SECRET_KEY not set — cannot resolve email for %s", user_id)
        return None
    try:
        r = httpx.get(
            f"https://api.clerk.com/v1/users/{user_id}",
            headers={"Authorization": f"Bearer {settings.clerk_secret_key}"},
            timeout=10.0,
        )
        r.raise_for_status()
        data = r.json()
    except httpx.HTTPError as exc:
        log.warning("Clerk user lookup failed for %s: %s", user_id, exc)
        return None
    primary_id = data.get("primary_email_address_id")
    for addr in data.get("email_addresses", []):
        if addr.get("id") == primary_id:
            email = addr.get("email_address")
            if isinstance(email, str):
                _USER_EMAIL_CACHE[user_id] = email
                return email
    return None


def require_user(
    settings: Annotated[Settings, Depends(get_settings)],
    authorization: Annotated[str | None, Header()] = None,
) -> dict:
    """Dependency: returns Clerk token claims, or raises 401/403."""
    if not settings.auth_required:
        return {"sub": "dev-user", "dev_mode": True}
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")
    token = authorization.split(" ", 1)[1].strip()
    payload = _verify_clerk_token(token, settings)

    allowlist = _load_allowlist(settings.allowlist_path)
    if not allowlist:
        return payload  # allowlist disabled — anyone signed in is fine

    user_id = payload.get("sub", "")
    email = _email_from_claims(payload) or _email_from_clerk_api(user_id, settings)
    if not email:
        raise HTTPException(status_code=403, detail="Could not resolve account email for allowlist check")
    if email.lower() not in allowlist:
        log.info("allowlist reject: %s (user_id=%s)", email, user_id)
        raise HTTPException(status_code=403, detail="This account is not authorized for this app")
    return payload
