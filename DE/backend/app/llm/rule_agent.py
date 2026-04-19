"""Rule-based fallback agent — no LLM, instant responses.

Parses intent + entities via regex keyword matching, then dispatches to
the same tool functions as the LLM path. Ensures the chat UI works even
when Ollama is down or the user picks 'rule-based' from the model menu.
"""

from __future__ import annotations

import re
from typing import Any

from app.llm.tools import compare_to_cohort, get_athlete_stats, get_cohort_summary

# -- Keyword maps (ordered: longest first wins) -------------------------------

_METRIC_KEYWORDS: list[tuple[str, str]] = sorted([
    ("total distance",        "total_distance_m"),
    ("high intensity events", "high_intensity_events"),
    ("high intensity",        "high_intensity_events"),
    ("acceleration events",   "acceleration_events"),
    ("deceleration events",   "deceleration_events"),
    ("sprint events",         "sprint_events"),
    ("metres per minute",     "metres_per_minute"),
    ("meters per minute",     "metres_per_minute"),
    ("work rate",             "metres_per_minute"),
    ("session load",          "session_load"),
    ("active minutes",        "active_minutes"),
    ("max speed",             "max_speed_kph"),
    ("distance",              "total_distance_m"),
    ("speed",                 "max_speed_kph"),
    ("load",                  "session_load"),
    ("intensity",             "session_load"),
    ("sprint",                "sprint_events"),
    ("accel",                 "acceleration_events"),
    ("decel",                 "deceleration_events"),
    ("pace",                  "metres_per_minute"),
], key=lambda x: -len(x[0]))

_DIVISION = {
    "division i": "di", "division 1": "di", "d1": "di", "di": "di",
    "division ii": "dii", "division 2": "dii", "d2": "dii", "dii": "dii",
    "division iii": "diii", "division 3": "diii", "d3": "diii", "diii": "diii",
}
_SPORT = {
    "soccer": "association_football", "football": "association_football",
    "association football": "association_football",
    "american football": "american_football", "nfl": "american_football",
}
_GENDER = {
    "female": "female", "women": "female", "woman": "female", "girls": "female",
    "male": "male", "men": "male", "boys": "male",
}


def _extract_metric(text: str) -> str | None:
    t = text.lower()
    for kw, m in _METRIC_KEYWORDS:
        if kw in t:
            return m
    return None


def _extract_int(text: str, pattern: str) -> int | None:
    m = re.search(pattern, text, re.IGNORECASE)
    return int(m.group(1)) if m else None


def _extract_athlete_id(text: str, default: int | None) -> int | None:
    return _extract_int(text, r"athlete\s*#?\s*(\d+)") or _extract_int(text, r"#\s*(\d+)") or default


def _match_kwmap(text: str, m: dict[str, str]) -> str | None:
    t = text.lower()
    for kw, val in sorted(m.items(), key=lambda x: -len(x[0])):
        if re.search(r"\b" + re.escape(kw) + r"\b", t):
            return val
    return None


HELP_TEXT = """I can answer questions about athlete performance. Try:
- "Show stats for athlete #42"
- "How does athlete #42 compare on session load?"
- "What's the average max speed for women's soccer?"
- "Cohort summary for D1 men"

I understand metrics like: distance, speed, load, intensity, sprint, accel/decel, pace.
"""


def _tier(pct: float) -> str:
    if pct >= 90: return "elite (top 10%)"
    if pct >= 75: return "top quartile"
    if pct >= 50: return "above average"
    if pct >= 25: return "below average"
    return "bottom quartile"


def _format_stats(d: dict[str, Any]) -> str:
    if "error" in d:
        return d["error"]
    header = (
        f"**#{d['athlete_id']}** · {d['sport'].replace('_',' ').title()} · "
        f"{d['gender'].title()} · Age {d['age']} · Div {d['division'].upper()} — "
        f"{d['session_count']} session(s)\n\n"
    )
    rows: list[str] = []
    for k, v in d.items():
        if isinstance(v, dict) and "avg" in v:
            name = k.replace("_", " ").title()
            rows.append(f"| {name} | {v['avg']:,.2f} | {v['max']:,.2f} | {v['min']:,.2f} |")
    if not rows:
        return header + "_No numeric data._"
    return header + "| Metric | Avg | Max | Min |\n|---|---|---|---|\n" + "\n".join(rows)


def _format_compare(d: dict[str, Any]) -> str:
    if "error" in d:
        return d["error"]
    return (
        f"**Athlete #{d['athlete_id']}** on **{d['metric'].replace('_',' ').title()}**\n"
        f"- Athlete avg: **{d['athlete_avg']:,.1f}**\n"
        f"- Cohort avg ({d['cohort']}, n={d['cohort_sessions']}): {d['cohort_avg']:,.1f}\n"
        f"- Difference: {d['diff_pct']:+.1f}%\n"
        f"- Percentile: **{d['percentile']:.1f}** — {_tier(d['percentile'])}"
    )


def _format_cohort(d: dict[str, Any]) -> str:
    if "error" in d:
        return d["error"]
    header = (
        f"**Cohort**: sport={d['cohort']['sport']}, gender={d['cohort']['gender']}, "
        f"division={d['cohort']['division']} — {d['session_count']} sessions, "
        f"{d['athlete_count']} athletes\n\n"
    )
    rows: list[str] = []
    for k, v in d["metrics"].items():
        name = k.replace("_", " ").title()
        rows.append(f"| {name} | {v['mean']:,.2f} | {v['median']:,.2f} | {v['p10']:,.2f} | {v['p90']:,.2f} |")
    if not rows:
        return header + "_No metrics to report._"
    return header + "| Metric | Mean | Median | p10 | p90 |\n|---|---|---|---|---|\n" + "\n".join(rows)


def dispatch(text: str, athlete_ctx: int | None = None) -> str:
    t = text.lower().strip()
    if not t:
        return HELP_TEXT
    if any(w in t for w in ("help", "what can you", "how do i use")):
        return HELP_TEXT

    athlete_id = _extract_athlete_id(text, athlete_ctx)
    metric = _extract_metric(text)
    sport = _match_kwmap(text, _SPORT)
    gender = _match_kwmap(text, _GENDER)
    division = _match_kwmap(text, _DIVISION)

    is_cohort_q = any(kw in t for kw in (
        "cohort", "average for", "benchmark", "what does a", "what do", "typical",
        "overview of", "group average", "league average",
    ))
    is_compare_q = any(kw in t for kw in (
        "compare", " vs ", "versus", "against", "better than", "worse than",
        "percentile", "rank", "how do i stack", "compared to",
    ))

    if is_cohort_q or (not athlete_id and (sport or gender or division)):
        return _format_cohort(get_cohort_summary(sport=sport, gender=gender, division=division))

    if athlete_id and is_compare_q and metric:
        return _format_compare(compare_to_cohort(athlete_id, metric))

    if athlete_id:
        return _format_stats(get_athlete_stats(athlete_id, metric))

    return HELP_TEXT
