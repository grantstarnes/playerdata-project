"""Clerk JWT verification via JWKS.

Frontend sends `Authorization: Bearer <clerk_session_token>`.
We fetch Clerk's JWKS once, cache, and verify each incoming token.
Set AUTH_REQUIRED=false in .env for local dev without auth.
"""

from __future__ import annotations

import logging
from functools import lru_cache
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


def require_user(
    settings: Annotated[Settings, Depends(get_settings)],
    authorization: Annotated[str | None, Header()] = None,
) -> dict:
    """Dependency: returns Clerk token claims, or raises 401."""
    if not settings.auth_required:
        return {"sub": "dev-user", "dev_mode": True}
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")
    token = authorization.split(" ", 1)[1].strip()
    return _verify_clerk_token(token, settings)
