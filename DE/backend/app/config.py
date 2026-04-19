"""Runtime settings loaded from environment (or .env file)."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = BACKEND_ROOT.parent
DATA_DIR = PROJECT_ROOT / "data" / "raw"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BACKEND_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- Server ---
    host: str = "0.0.0.0"
    port: int = 8000
    env: str = "development"

    # --- CORS ---
    # Comma-separated in the env var. e.g. "https://playerdata.vercel.app,http://localhost:3000"
    cors_origins: str = "http://localhost:3000"

    # --- DuckDB ---
    duckdb_path: Path = BACKEND_ROOT / "data" / "playerdata.duckdb"
    data_dir: Path = DATA_DIR

    # --- Ollama ---
    ollama_base_url: str = "http://localhost:11434"
    default_model: str = "gemma3n:e4b"
    ollama_timeout_s: int = 120

    # --- Clerk auth ---
    clerk_jwks_url: str = ""           # e.g. https://<subdomain>.clerk.accounts.dev/.well-known/jwks.json
    clerk_issuer: str = ""             # e.g. https://<subdomain>.clerk.accounts.dev
    clerk_audience: str | None = None  # optional — set if you configure audience in Clerk
    clerk_secret_key: str = ""         # needed to resolve user_id -> email for allowlist enforcement
    auth_required: bool = Field(default=True, description="Disable with AUTH_REQUIRED=false for local dev")
    allowlist_path: Path = BACKEND_ROOT / "allowlist.txt"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
