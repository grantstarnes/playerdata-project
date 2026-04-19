"""LLM chat dispatch — Ollama-backed tool calling with model selection.

Flow:
  1. Frontend sends { message, athlete_ctx?, model } to /api/chat
  2. If model == 'rule-based', use rule_agent.dispatch
  3. Else send to Ollama with TOOL_SCHEMAS; if the model emits tool_calls,
     execute them server-side and loop back to the model with results;
     stop after MAX_TOOL_ROUNDS or when no more tool calls.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from app.llm.ollama_client import OllamaClient
from app.llm.rule_agent import HELP_TEXT, dispatch as rule_dispatch
from app.llm.tools import TOOL_REGISTRY, TOOL_SCHEMAS

log = logging.getLogger(__name__)

MAX_TOOL_ROUNDS = 4

# Models that don't expose Ollama's native function-calling. Sending a `tools`
# param to these returns 400 Bad Request, so we fall back to plain chat.
_NO_TOOLS_MODELS = {"gemma3n:e4b", "gemma3n:e2b"}

SYSTEM_PROMPT = """You are PlayerData Coach, an analyst for athlete GPS/IMU session data.

Tools:
- get_athlete_stats(athlete_id, metric?) — one athlete's stats
- compare_to_cohort(athlete_id, metric) — athlete vs their sport+gender cohort
- get_cohort_summary(sport?, gender?, division?) — aggregate stats for a group
- top_athletes_in_cohort(metric, sport?, gender?, division?, limit?, direction?) —
  ranked top-N or bottom-N athletes (use for "who is fastest/best/worst")

Rules:
- Call ONE tool to answer. After you receive the tool result, give a final
  Markdown answer immediately. Do NOT call more tools.
- If no tool fits, say so in one sentence.
- Use athlete context from the system message when user doesn't specify an ID.

Formatting (IMPORTANT — strict Markdown tables):
- When reporting an athlete's stats (from get_athlete_stats), start with a one-
  line header like "**#1042** · Soccer · Female · Age 20 · Div DI — 14 sessions"
  then a Markdown table with columns: Metric · Avg · Max · Min.
- When reporting a cohort summary, use a Markdown table with columns:
  Metric · Mean · Median · p10 · p90.
- When reporting a top-N list, use: Rank · Athlete · Value · Sessions.
- For comparisons, prefer a short table over prose.
- Always prefer tables over bullet lists for numeric data.

STRICT table rules (these matter — the renderer is simple):
- Use plain ASCII pipes: `| Col | Col |`. Include the separator row: `|---|---|`.
- NEVER write a `|` inside a cell — units go in parentheses after the metric
  name instead. Correct: `Total Distance (m)`. Wrong: `Total Distance|m`.
- DO NOT escape characters. Write `Total_Distance` is WRONG — convert
  snake_case identifiers to Title Case: `total_distance_m` → `Total Distance (m)`,
  `max_speed_kph` → `Max Speed (kph)`, `session_load` → `Session Load`,
  `active_minutes` → `Active Minutes`, `metres_per_minute` → `Metres per Minute`,
  `high_intensity_events` → `High Intensity Events`, `sprint_events` → `Sprint Events`,
  `acceleration_events` → `Acceleration Events`, `deceleration_events` → `Deceleration Events`.
- Numbers: 2 decimal places for floats (e.g. `4380.14`), integers for counts.
- Do not backslash-escape underscores, asterisks or pipes.

Reference values:
- Metric enum: total_distance_m, max_speed_kph, session_load, active_minutes,
  metres_per_minute, high_intensity_events, sprint_events,
  acceleration_events, deceleration_events.
- Sport: 'association_football' (soccer) | 'american_football'.
- Division: 'di' | 'dii' | 'diii'. Gender: 'male' | 'female'.
- Never invent numbers. Quote what the tool returned.
"""


async def chat(
    message: str,
    *,
    athlete_ctx: int | None,
    model: str,
    history: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    if model == "rule-based":
        return {"model": model, "response": rule_dispatch(message, athlete_ctx), "tool_calls": []}

    ctx_line = f"\nCurrent athlete context: #{athlete_ctx}" if athlete_ctx else ""
    messages: list[dict[str, Any]] = [
        {"role": "system", "content": SYSTEM_PROMPT + ctx_line},
    ]
    # Carry the last ~8 conversation turns (16 messages) as context so the
    # model can refer back to earlier answers. Cap keeps prompt size bounded.
    if history:
        messages.extend(history[-16:])
    messages.append({"role": "user", "content": message})

    client = OllamaClient()
    used_tools: list[dict[str, Any]] = []
    supports_tools = model not in _NO_TOOLS_MODELS

    # Models without tool support: single plain-chat call, no loop.
    if not supports_tools:
        try:
            resp = await client.chat(model=model, messages=messages, temperature=0.3)
        except Exception as exc:
            log.warning("ollama chat failed (%s) — fallback to rule-based", exc)
            return {
                "model": "rule-based",
                "response": rule_dispatch(message, athlete_ctx),
                "tool_calls": [],
                "fallback_reason": str(exc),
            }
        msg = resp.get("message", {}) or {}
        return {
            "model": model,
            "response": msg.get("content", "").strip() or HELP_TEXT,
            "tool_calls": [],
            "note": "model does not support tool calling; plain chat only",
        }

    for _ in range(MAX_TOOL_ROUNDS):
        try:
            resp = await client.chat(
                model=model,
                messages=messages,
                tools=TOOL_SCHEMAS,
                temperature=0.2,
            )
        except Exception as exc:
            log.warning("ollama chat failed (%s) — falling back to rule-based", exc)
            return {
                "model": "rule-based",
                "response": rule_dispatch(message, athlete_ctx),
                "tool_calls": used_tools,
                "fallback_reason": str(exc),
            }

        msg = resp.get("message", {}) or {}
        tool_calls = msg.get("tool_calls") or []
        if not tool_calls:
            return {
                "model": model,
                "response": msg.get("content", "").strip() or HELP_TEXT,
                "tool_calls": used_tools,
            }

        # Execute tools, append results as tool messages
        messages.append(msg)
        for tc in tool_calls:
            fn = tc.get("function", {}) or {}
            name = fn.get("name", "")
            args = fn.get("arguments") or {}
            if isinstance(args, str):
                try:
                    args = json.loads(args)
                except Exception:
                    args = {}
            impl = TOOL_REGISTRY.get(name)
            if not impl:
                result: Any = {"error": f"Unknown tool '{name}'"}
            else:
                try:
                    result = impl(**args)
                except TypeError as exc:
                    result = {"error": f"Bad args to {name}: {exc}"}
                except Exception as exc:
                    log.exception("tool %s failed", name)
                    result = {"error": str(exc)}

            used_tools.append({"name": name, "args": args, "result": result})
            messages.append({
                "role": "tool",
                "content": json.dumps(result, default=str),
            })

    # Hit tool-round ceiling — final plain call without tools
    resp = await client.chat(model=model, messages=messages, temperature=0.2)
    msg = resp.get("message", {}) or {}
    return {
        "model": model,
        "response": msg.get("content", "").strip() or "(no response)",
        "tool_calls": used_tools,
        "note": "tool loop hit max rounds",
    }
