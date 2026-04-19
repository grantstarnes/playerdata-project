"""
DE/app/agent.py

PlayerData Performance Chatbot
=================================
Rule-based chatbot that answers natural language questions about athlete
performance data.  No LLM or API key needed - intent parsing + tool
dispatch in pure Python.

Can be run standalone:
    streamlit run app/agent.py

Or imported into app.py:
    from agent import _dispatch, _HELP_TEXT
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Any

import pandas as pd

_DE_ROOT = Path(__file__).resolve().parents[1]
if str(_DE_ROOT) not in sys.path:
    sys.path.insert(0, str(_DE_ROOT))

from pipeline.metrics import load_all_data, filter_sessions

# ---------------------------------------------------------------------------
# Data loading (cached once)
# ---------------------------------------------------------------------------

try:
    import streamlit as st
    @st.cache_data(show_spinner="Loading data...")
    def _load() -> pd.DataFrame:
        return load_all_data(include_synthetic=True)
except Exception:
    def _load() -> pd.DataFrame:  # type: ignore[misc]
        return load_all_data(include_synthetic=True)


# ---------------------------------------------------------------------------
# Tool functions
# ---------------------------------------------------------------------------

def _get_athlete_stats(athlete_id: int, metric: str | None = None) -> dict[str, Any]:
    """Per-session averages, max, and min for a given athlete."""
    df = _load()
    rows = df[df["athlete_number"] == athlete_id]
    if rows.empty:
        return {"error": f"No sessions found for athlete #{athlete_id}."}

    result: dict[str, Any] = {
        "athlete_id":    athlete_id,
        "age":           int(rows["athlete_relative_age"].iloc[0]),
        "sport":         rows["athlete_sport"].iloc[0].replace("_", " ").title(),
        "gender":        rows["athlete_gender_marker"].iloc[0].title(),
        "division":      rows["club_division"].iloc[0].upper(),
        "session_count": int(len(rows)),
    }

    all_metrics = [
        "total_distance_m", "max_speed_kph", "session_load",
        "active_minutes", "metres_per_minute",
        "high_intensity_events", "sprint_events",
        "acceleration_events", "deceleration_events",
    ]
    target = [m for m in all_metrics if metric and metric.lower().replace(" ", "_") in m] \
             if metric else all_metrics

    for m in target:
        if m in rows.columns:
            vals = rows[m].dropna().astype(float)
            if not vals.empty:
                result[m] = {
                    "avg": round(float(vals.mean()), 2),
                    "max": round(float(vals.max()), 2),
                    "min": round(float(vals.min()), 2),
                }
    return result


def _compare_to_benchmark(
    athlete_id: int,
    metric: str,
    group_by: str = "club_division",
    group_value: str | None = None,
) -> dict[str, Any]:
    """Athlete average vs a benchmark group average and percentile."""
    df = _load()
    athlete_rows = df[df["athlete_number"] == athlete_id]
    if athlete_rows.empty:
        return {"error": f"Athlete #{athlete_id} not found."}

    if metric not in df.columns:
        valid = ["total_distance_m", "max_speed_kph", "session_load",
                 "metres_per_minute", "high_intensity_events", "sprint_events"]
        return {"error": f"Metric '{metric}' not found. Try: {', '.join(valid)}"}

    sport  = athlete_rows["athlete_sport"].iloc[0]
    gender = athlete_rows["athlete_gender_marker"].iloc[0]

    cohort = df[(df["athlete_sport"] == sport) & (df["athlete_gender_marker"] == gender)]
    if group_by in df.columns and group_value:
        cohort = cohort[cohort[group_by] == group_value.lower()]

    cohort_vals   = cohort[metric].dropna().astype(float)
    athlete_avg   = float(athlete_rows[metric].mean())
    benchmark_avg = float(cohort_vals.mean())
    benchmark_std = float(cohort_vals.std())

    pct = float((cohort_vals < athlete_avg).sum()) / len(cohort_vals) * 100 \
          if len(cohort_vals) > 0 else 0.0

    return {
        "athlete_id":         athlete_id,
        "metric":             metric,
        "athlete_average":    round(athlete_avg, 2),
        "benchmark_group":    f"{group_by}={group_value or 'all'} | sport={sport} | gender={gender}",
        "benchmark_average":  round(benchmark_avg, 2),
        "benchmark_std":      round(benchmark_std, 2),
        "benchmark_sessions": int(len(cohort_vals)),
        "athlete_percentile": round(pct, 1),
        "difference_pct":     round((athlete_avg - benchmark_avg) / benchmark_avg * 100, 1)
                              if benchmark_avg else 0,
    }


def _rank_in_cohort(
    athlete_id: int,
    metric: str,
    sport: str | None = None,
    gender: str | None = None,
    division: str | None = None,
    min_active_minutes: int = 70,
) -> dict[str, Any]:
    """Rank among peers using per-athlete session averages."""
    df = _load()
    athlete_rows = df[df["athlete_number"] == athlete_id]
    if athlete_rows.empty:
        return {"error": f"Athlete #{athlete_id} not found."}
    if metric not in df.columns:
        return {"error": f"Metric '{metric}' not found."}

    _sport  = sport  or athlete_rows["athlete_sport"].iloc[0]
    _gender = gender or athlete_rows["athlete_gender_marker"].iloc[0]

    filtered = filter_sessions(df, sport=_sport, gender=_gender,
                               min_active_minutes=min_active_minutes)
    if division:
        filtered = filtered[filtered["club_division"] == division.lower()]
    if filtered.empty:
        return {"error": "No athletes found for the specified cohort filters."}

    averages    = filtered.groupby("athlete_number")[metric].mean()
    athlete_avg = float(athlete_rows[metric].mean())
    n           = len(averages)
    rank        = int((averages > athlete_avg).sum()) + 1
    pct         = round((n - rank + 1) / n * 100, 1)

    return {
        "athlete_id":               athlete_id,
        "metric":                   metric,
        "athlete_average":          round(athlete_avg, 2),
        "rank":                     rank,
        "total_athletes_in_cohort": n,
        "percentile":               pct,
        "cohort": {
            "sport":              _sport,
            "gender":             _gender,
            "division":           division or "all",
            "min_active_minutes": min_active_minutes,
        },
    }


def _list_cohort_summary(
    sport: str | None = None,
    gender: str | None = None,
    division: str | None = None,
    min_active_minutes: int = 70,
) -> dict[str, Any]:
    """Aggregate benchmark stats (mean, median, std, p10, p90) for a cohort."""
    df = _load()
    cohort = df.copy()
    if sport:
        cohort = cohort[cohort["athlete_sport"] == sport.lower()]
    if gender:
        cohort = cohort[cohort["athlete_gender_marker"] == gender.lower()]
    if division:
        cohort = cohort[cohort["club_division"] == division.lower()]
    cohort = cohort[cohort["active_minutes"] >= min_active_minutes]

    if cohort.empty:
        return {"error": "No data found for this cohort."}

    summary: dict[str, Any] = {}
    for m in ["total_distance_m", "max_speed_kph", "session_load",
              "metres_per_minute", "high_intensity_events", "sprint_events"]:
        if m in cohort.columns:
            vals = cohort[m].dropna().astype(float)
            summary[m] = {
                "mean":   round(float(vals.mean()),        2),
                "median": round(float(vals.median()),      2),
                "std":    round(float(vals.std()),         2),
                "p10":    round(float(vals.quantile(0.1)), 2),
                "p90":    round(float(vals.quantile(0.9)), 2),
            }

    return {
        "cohort": {
            "sport":              sport or "all",
            "gender":             gender or "all",
            "division":           division or "all",
            "min_active_minutes": min_active_minutes,
        },
        "session_count": int(len(cohort)),
        "athlete_count": int(cohort["athlete_number"].nunique()),
        "metrics":       summary,
    }


# ---------------------------------------------------------------------------
# Intent parsing
# ---------------------------------------------------------------------------

_METRIC_KEYWORDS: list[tuple[str, str]] = sorted([
    ("total distance",         "total_distance_m"),
    ("high intensity events",  "high_intensity_events"),
    ("high intensity",         "high_intensity_events"),
    ("hi events",              "high_intensity_events"),
    ("acceleration events",    "acceleration_events"),
    ("deceleration events",    "deceleration_events"),
    ("sprint events",          "sprint_events"),
    ("metres per minute",      "metres_per_minute"),
    ("meters per minute",      "metres_per_minute"),
    ("work rate",              "metres_per_minute"),
    ("session load",           "session_load"),
    ("active minutes",         "active_minutes"),
    ("max speed",              "max_speed_kph"),
    ("distance",               "total_distance_m"),
    ("metres",                 "total_distance_m"),
    ("meters",                 "total_distance_m"),
    ("speed",                  "max_speed_kph"),
    ("fast",                   "max_speed_kph"),
    ("kph",                    "max_speed_kph"),
    ("load",                   "session_load"),
    ("intensity",              "session_load"),
    ("sprint",                 "sprint_events"),
    ("accel",                  "acceleration_events"),
    ("decel",                  "deceleration_events"),
    ("pace",                   "metres_per_minute"),
    ("mpm",                    "metres_per_minute"),
    ("duration",               "active_minutes"),
    ("minutes",                "active_minutes"),
], key=lambda x: -len(x[0]))

_DIVISION_MAP: dict[str, str] = {
    "division i": "di",   "division 1": "di",   "div i": "di",   "div 1": "di",   "d1": "di",   "di": "di",
    "division ii": "dii", "division 2": "dii",  "div ii": "dii", "div 2": "dii",  "d2": "dii",  "dii": "dii",
    "division iii": "diii","division 3": "diii","div iii": "diii","div 3": "diii","d3": "diii", "diii": "diii",
}

_SPORT_MAP: dict[str, str] = {
    "association football": "association_football",
    "american football":    "american_football",
    "soccer":               "association_football",
    "football":             "association_football",
    "american":             "american_football",
    "nfl":                  "american_football",
}

_GENDER_MAP: dict[str, str] = {
    "female": "female", "women": "female", "woman": "female", "girls": "female",
    "male":   "male",   "men":   "male",   "man":   "male",   "boys":  "male",
}


def _extract_metric(text: str) -> str | None:
    t = text.lower()
    for kw, metric in _METRIC_KEYWORDS:
        if kw in t:
            return metric
    return None


def _extract_athlete_id(text: str, default: int | None) -> int | None:
    m = re.search(r"athlete\s*#?\s*(\d+)", text, re.IGNORECASE)
    if m:
        return int(m.group(1))
    m = re.search(r"#\s*(\d+)", text)
    if m:
        return int(m.group(1))
    return default


def _extract_division(text: str) -> str | None:
    t = text.lower()
    for kw, div in sorted(_DIVISION_MAP.items(), key=lambda x: -len(x[0])):
        if re.search(r"\b" + re.escape(kw) + r"\b", t):
            return div
    return None


def _extract_sport(text: str) -> str | None:
    t = text.lower()
    for kw, sport in sorted(_SPORT_MAP.items(), key=lambda x: -len(x[0])):
        if kw in t:
            return sport
    return None


def _extract_gender(text: str) -> str | None:
    t = text.lower()
    for kw, gender in sorted(_GENDER_MAP.items(), key=lambda x: -len(x[0])):
        if re.search(r"\b" + re.escape(kw) + r"\b", t):
            return gender
    return None


def _classify_intent(text: str) -> str:
    """Returns one of: stats, compare, rank, cohort, help."""
    t = text.lower()
    if any(kw in t for kw in ["help", "what can you", "how do i", "what do you"]):
        return "help"
    if any(kw in t for kw in [
        "average for", "typical", "benchmark", "what does a", "what do",
        "cohort", "league average", "group average", "what's the average",
        "what is the average", "tell me about the", "overview of",
    ]):
        return "cohort"
    if any(kw in t for kw in [
        "rank", "ranking", "where do i", "where am i", "top 10", "top 20",
        "percentile", "standing", "leaderboard", "compared to everyone",
        "vs everyone", "vs all",
    ]):
        return "rank"
    if any(kw in t for kw in [
        "compare", " vs ", "versus", "against", "better than", "worse than",
        "above average", "below average", "how do i stack", "compared to",
        "relative to",
    ]):
        return "compare"
    return "stats"


# ---------------------------------------------------------------------------
# Response formatters
# ---------------------------------------------------------------------------

def _fmt(name: str) -> str:
    return {
        "total_distance_m":      "Total Distance (m)",
        "max_speed_kph":         "Max Speed (km/h)",
        "session_load":          "Session Load",
        "metres_per_minute":     "Metres per Minute",
        "high_intensity_events": "High Intensity Events",
        "sprint_events":         "Sprint Events",
        "acceleration_events":   "Acceleration Events",
        "deceleration_events":   "Deceleration Events",
        "active_minutes":        "Active Minutes",
    }.get(name, name.replace("_", " ").title())


def _tier(pctile: float) -> str:
    if pctile >= 90: return "elite (top 10%)"
    if pctile >= 75: return "top quartile"
    if pctile >= 50: return "above average"
    if pctile >= 25: return "below average"
    return "bottom quartile"


def _format_stats(data: dict, metric: str | None) -> str:
    if "error" in data:
        return f"Sorry, {data['error']}"
    lines = [
        f"**Athlete #{data['athlete_id']}** - {data['sport']} | "
        f"{data['gender']} | Age {data['age']} | Div {data['division']}",
        f"*{data['session_count']} session(s) on record*",
        "",
    ]
    shown = 0
    for key, vals in data.items():
        if isinstance(vals, dict) and "avg" in vals:
            lines.append(
                f"- **{_fmt(key)}**: avg **{vals['avg']:,.1f}** "
                f"(max {vals['max']:,.1f} / min {vals['min']:,.1f})"
            )
            shown += 1
    if shown == 0:
        lines.append("No numeric data found.")
    return "\n".join(lines)


def _format_compare(data: dict) -> str:
    if "error" in data:
        return f"Sorry, {data['error']}"
    diff      = data["difference_pct"]
    direction = "above" if diff >= 0 else "below"
    pctile    = data["athlete_percentile"]
    return (
        f"**{_fmt(data['metric'])} - Benchmark Comparison**\n\n"
        f"- Your average: **{data['athlete_average']:,.2f}**\n"
        f"- Benchmark avg: {data['benchmark_average']:,.2f} "
        f"(+/-{data['benchmark_std']:,.2f} SD)\n"
        f"- You are **{abs(diff):.1f}% {direction}** the benchmark - "
        f"{_tier(pctile)} ({pctile:.0f}th percentile)\n"
        f"- Group: {data['benchmark_group']} "
        f"({data['benchmark_sessions']:,} sessions)"
    )


def _format_rank(data: dict) -> str:
    if "error" in data:
        return f"Sorry, {data['error']}"
    pctile = data["percentile"]
    c = data["cohort"]
    cohort_desc = (
        f"{c['sport'].replace('_', ' ').title()} | {c['gender'].title()} | "
        f"Div {c['division'].upper()} | min {c['min_active_minutes']} min"
    )
    return (
        f"**{_fmt(data['metric'])} - Ranking**\n\n"
        f"- Your average: **{data['athlete_average']:,.2f}**\n"
        f"- Rank: **#{data['rank']}** of {data['total_athletes_in_cohort']} athletes\n"
        f"- **{pctile:.0f}th percentile** - {_tier(pctile)}\n"
        f"- Cohort: {cohort_desc}"
    )


def _format_cohort(data: dict) -> str:
    if "error" in data:
        return f"Sorry, {data['error']}"
    c = data["cohort"]
    header = (
        f"**Cohort Benchmarks**\n"
        f"Sport: {c['sport']} | Gender: {c['gender']} | "
        f"Division: {c['division']} | min {c['min_active_minutes']} active min\n"
        f"*{data['athlete_count']} athletes, {data['session_count']} sessions*\n\n"
        "| Metric | Mean | Median | P10 | P90 |\n"
        "|---|---|---|---|---|"
    )
    rows = [header]
    for m, s in data.get("metrics", {}).items():
        rows.append(
            f"| {_fmt(m)} | {s['mean']:,.1f} | {s['median']:,.1f} "
            f"| {s['p10']:,.1f} | {s['p90']:,.1f} |"
        )
    return "\n".join(rows)


_HELP_TEXT = """\
**What can I help with?**

Ask about any athlete's performance data in plain English. For example:

- *"What are my stats?"*
- *"How fast am I compared to Division I average?"*
- *"Where do I rank in total distance?"*
- *"What does a typical DI female soccer player run?"*
- *"Show me athlete #42's session load"*

**Available metrics:** total distance, max speed, session load, metres per minute,
high intensity events, sprint events, acceleration events, deceleration events, active minutes.

**Tip:** Select an athlete above so you don't need to type the ID each time.
"""


# ---------------------------------------------------------------------------
# Main dispatcher  (importable by app.py)
# ---------------------------------------------------------------------------

def _dispatch(user_input: str, default_athlete_id: int | None) -> str:
    """Parse intent and entities, call the right tool, return formatted Markdown."""
    text     = user_input.strip()
    intent   = _classify_intent(text)
    metric   = _extract_metric(text)
    ath_id   = _extract_athlete_id(text, default_athlete_id)
    division = _extract_division(text)
    sport    = _extract_sport(text)
    gender   = _extract_gender(text)

    if intent == "help":
        return _HELP_TEXT

    if intent == "cohort":
        return _format_cohort(_list_cohort_summary(
            sport=sport, gender=gender, division=division,
        ))

    if ath_id is None:
        return (
            "Please select an athlete above, "
            "or include their ID in your message "
            "(e.g. *'Show me athlete #42 stats'*)."
        )

    if intent == "rank":
        return _format_rank(_rank_in_cohort(
            athlete_id=ath_id,
            metric=metric or "total_distance_m",
            sport=sport, gender=gender, division=division,
        ))

    if intent == "compare":
        return _format_compare(_compare_to_benchmark(
            athlete_id=ath_id,
            metric=metric or "session_load",
            group_by="club_division" if division else "athlete_sport",
            group_value=division,
        ))

    return _format_stats(_get_athlete_stats(athlete_id=ath_id, metric=metric), metric)


# ---------------------------------------------------------------------------
# Standalone Streamlit app  (only runs when executed directly)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import streamlit as st  # noqa: F811

    st.set_page_config(
        page_title="PlayerData Chat",
        page_icon=None,
        layout="centered",
        initial_sidebar_state="expanded",
    )

    st.title("PlayerData Chat")
    st.caption("Ask questions about athlete performance in plain English. No API key needed.")

    with st.sidebar:
        st.subheader("Who am I?")
        df_all = _load()
        athlete_ids = sorted(df_all["athlete_number"].dropna().unique().tolist())

        sel_id = st.selectbox(
            "Select athlete",
            options=[None] + athlete_ids,
            format_func=lambda x: "Select..." if x is None else f"Athlete #{int(x)}",
        )

        display_name_input = st.text_input("Display name (optional)", placeholder="e.g. Mark")

        if sel_id is not None:
            row = df_all[df_all["athlete_number"] == sel_id].iloc[0]
            st.markdown(
                f"**Sport:** {row['athlete_sport'].replace('_', ' ').title()}  \n"
                f"**Division:** {row['club_division'].upper()}  \n"
                f"**Gender:** {row['athlete_gender_marker'].title()}  \n"
                f"**Age:** {int(row['athlete_relative_age'])}"
            )

        st.divider()
        if st.button("Clear conversation"):
            st.session_state.chat_history = []
            st.rerun()
        st.caption("Rule-based | No API key needed")

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    if not st.session_state.chat_history:
        with st.chat_message("assistant"):
            st.markdown(_HELP_TEXT)

    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if user_input := st.chat_input("Ask about performance data..."):
        with st.chat_message("user"):
            st.markdown(user_input)
        st.session_state.chat_history.append({"role": "user", "content": user_input})

        response = _dispatch(user_input, int(sel_id) if sel_id is not None else None)

        with st.chat_message("assistant"):
            st.markdown(response)
        st.session_state.chat_history.append({"role": "assistant", "content": response})
