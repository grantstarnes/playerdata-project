"""Chat endpoint — model-selectable LLM or rule-based responses."""

from __future__ import annotations

import hashlib

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.config import get_settings
from app.db.duckdb_store import get_connection
from app.deps.auth import require_user
from app.llm.dispatch import chat as llm_chat
from app.llm.ollama_client import OllamaClient

router = APIRouter(prefix="/api/chat", tags=["chat"])


class ChatMessage(BaseModel):
    role: str  # "user" | "assistant" | "tool"
    content: str


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    athlete_ctx: int | None = None
    model: str = "gemma3n:e4b"
    history: list[ChatMessage] = Field(default_factory=list, description="Prior conversation turns, oldest first")


class ChatResponse(BaseModel):
    model: str
    response: str
    tool_calls: list[dict] = Field(default_factory=list)
    fallback_reason: str | None = None
    note: str | None = None


# Curated menu exposed to the frontend dropdown.
# tools: True = supports Ollama native function calling, False = plain chat only
AVAILABLE_MODELS = [
    {"id": "gemma4:e4b",    "label": "Gemma 4 E4B (best quality, slow)",    "tier": "quality",  "tools": True},
    {"id": "gemma4:e2b",    "label": "Gemma 4 E2B (balanced Gemma 4)",      "tier": "balanced", "tools": True},
    {"id": "qwen2.5:3b",    "label": "Qwen 2.5 3B (very fast, tools)",      "tier": "fast",     "tools": True},
    {"id": "qwen2.5:1.5b",  "label": "Qwen 2.5 1.5B (tiniest LLM, tools)",  "tier": "tiny",     "tools": True},
    {"id": "gemma3n:e4b",   "label": "Gemma 3n E4B (chat only, no tools)",  "tier": "default",  "tools": False},
    {"id": "rule-based",    "label": "Rule-based (instant, deterministic)", "tier": "instant",  "tools": False},
]


@router.get("/models")
async def list_models(_user: dict = Depends(require_user)) -> dict:
    """Return the menu + which models are actually pulled on Ollama."""
    s = get_settings()
    try:
        installed = await OllamaClient().list_models()
    except Exception:
        installed = []
    installed_set = set(installed)
    models = [
        {**m, "installed": m["id"] == "rule-based" or m["id"] in installed_set}
        for m in AVAILABLE_MODELS
    ]
    return {"default": s.default_model, "models": models}


@router.get("/session")
def chat_session(user: dict = Depends(require_user)) -> dict:
    """Deterministic default athlete_ctx per Clerk user.

    Hash the Clerk `sub` to pick a stable athlete from the dataset — same user
    always gets the same athlete, different users get different ones. Demo-friendly
    stand-in for a real user→athlete mapping table.
    """
    user_id = str(user.get("sub") or "anonymous")
    seed = int(hashlib.sha256(user_id.encode()).hexdigest()[:8], 16)

    con = get_connection()
    try:
        ids = con.execute(
            "SELECT DISTINCT athlete_number FROM sessions ORDER BY athlete_number"
        ).fetchall()
    finally:
        con.close()

    if not ids:
        return {"athlete_ctx": None, "user_id": user_id}
    athlete_id = int(ids[seed % len(ids)][0])
    return {"athlete_ctx": athlete_id, "user_id": user_id}


@router.post("")
async def chat(
    body: ChatRequest,
    _user: dict = Depends(require_user),
) -> ChatResponse:
    history = [m.model_dump() for m in body.history]
    result = await llm_chat(
        body.message,
        athlete_ctx=body.athlete_ctx,
        model=body.model,
        history=history,
    )
    return ChatResponse(**result)
