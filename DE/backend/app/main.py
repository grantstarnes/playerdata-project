"""PlayerData FastAPI entrypoint.

Runs on the Victus Ubuntu server at 0.0.0.0:8000, behind Tailscale Funnel for
public reachability from Vercel. All data-returning endpoints require a valid
Clerk session token (except /health).
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.db.duckdb_store import seed_from_csvs
from app.llm.ollama_client import OllamaClient

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
log = logging.getLogger("playerdata")


@asynccontextmanager
async def lifespan(_: FastAPI):
    s = get_settings()
    rows = seed_from_csvs(force=False, settings=s)
    log.info("startup: DuckDB has %d session rows", rows)
    ollama_ok = await OllamaClient().health()
    log.info("startup: Ollama reachable = %s (model default=%s)", ollama_ok, s.default_model)
    yield


app = FastAPI(
    title="PlayerData API",
    version="0.1.0",
    lifespan=lifespan,
)

_settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=_settings.cors_origin_list or ["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


@app.get("/health")
async def health() -> dict:
    ollama_ok = await OllamaClient().health()
    return {
        "status": "ok",
        "env": _settings.env,
        "ollama": "up" if ollama_ok else "down",
        "default_model": _settings.default_model,
        "auth_required": _settings.auth_required,
    }


from app.routes import age_group, athlete, benchmarks, chat, filters, overview  # noqa: E402

app.include_router(filters.router)
app.include_router(overview.router)
app.include_router(age_group.router)
app.include_router(athlete.router)
app.include_router(benchmarks.router)
app.include_router(chat.router)
