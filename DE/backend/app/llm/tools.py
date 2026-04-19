"""LLM tool definitions + Python implementations.

Each tool is a callable + an OpenAI-style schema for Ollama/Gemma 4 tool calls.
All tools read from DuckDB directly — fast and consistent with the REST API.
"""

from __future__ import annotations

from typing import Any

from app.db.duckdb_store import get_connection


# -- Implementations -----------------------------------------------------------

def get_athlete_stats(athlete_id: int, metric: str | None = None) -> dict[str, Any]:
    """Per-session averages / max / min for one athlete."""
    con = get_connection()
    try:
        rows = con.execute(
            "SELECT * FROM sessions WHERE athlete_number = ?",
            [athlete_id],
        ).df()
    finally:
        con.close()

    if rows.empty:
        return {"error": f"No sessions for athlete #{athlete_id}."}

    out: dict[str, Any] = {
        "athlete_id": athlete_id,
        "age": int(rows["athlete_relative_age"].iloc[0]),
        "sport": str(rows["athlete_sport"].iloc[0]),
        "gender": str(rows["athlete_gender_marker"].iloc[0]),
        "division": str(rows["club_division"].iloc[0]),
        "session_count": int(len(rows)),
    }

    all_metrics = [
        "total_distance_m", "max_speed_kph", "session_load",
        "active_minutes", "metres_per_minute",
        "high_intensity_events", "sprint_events",
        "acceleration_events", "deceleration_events",
    ]
    targets = [m for m in all_metrics if metric and metric in m] if metric else all_metrics
    for m in targets:
        if m in rows.columns:
            vals = rows[m].dropna().astype(float)
            if len(vals):
                out[m] = {
                    "avg": round(float(vals.mean()), 2),
                    "max": round(float(vals.max()), 2),
                    "min": round(float(vals.min()), 2),
                }
    return out


def compare_to_cohort(athlete_id: int, metric: str) -> dict[str, Any]:
    """Athlete's average vs their sport+gender cohort average + percentile."""
    con = get_connection()
    try:
        athlete = con.execute(
            "SELECT * FROM sessions WHERE athlete_number = ?",
            [athlete_id],
        ).df()
        if athlete.empty:
            return {"error": f"Athlete #{athlete_id} not found."}
        sport = str(athlete["athlete_sport"].iloc[0])
        gender = str(athlete["athlete_gender_marker"].iloc[0])
        cohort = con.execute(
            "SELECT * FROM sessions WHERE athlete_sport = ? AND athlete_gender_marker = ?",
            [sport, gender],
        ).df()
    finally:
        con.close()

    if metric not in athlete.columns:
        return {"error": f"Metric '{metric}' not found."}
    cohort_vals = cohort[metric].dropna().astype(float)
    athlete_avg = float(athlete[metric].mean())
    bench_avg = float(cohort_vals.mean()) if len(cohort_vals) else 0.0
    pct = (float((cohort_vals < athlete_avg).sum()) / len(cohort_vals) * 100) if len(cohort_vals) else 0.0

    return {
        "athlete_id": athlete_id,
        "metric": metric,
        "athlete_avg": round(athlete_avg, 2),
        "cohort": f"sport={sport}, gender={gender}",
        "cohort_avg": round(bench_avg, 2),
        "cohort_sessions": int(len(cohort_vals)),
        "percentile": round(pct, 1),
        "diff_pct": round((athlete_avg - bench_avg) / bench_avg * 100, 1) if bench_avg else 0.0,
    }


def get_cohort_summary(
    sport: str | None = None,
    gender: str | None = None,
    division: str | None = None,
    min_active_minutes: int = 70,
) -> dict[str, Any]:
    """Summary stats for a cohort (sport/gender/division filter)."""
    clauses = ["active_minutes >= ?"]
    params: list[Any] = [min_active_minutes]
    if sport:
        clauses.append("athlete_sport = ?")
        params.append(sport.lower())
    if gender:
        clauses.append("athlete_gender_marker = ?")
        params.append(gender.lower())
    if division:
        clauses.append("club_division = ?")
        params.append(division.lower())

    con = get_connection()
    try:
        df = con.execute(f"SELECT * FROM sessions WHERE {' AND '.join(clauses)}", params).df()
    finally:
        con.close()

    if df.empty:
        return {"error": "No data for that cohort."}

    summary = {}
    for m in ["total_distance_m", "max_speed_kph", "session_load", "metres_per_minute"]:
        vals = df[m].dropna().astype(float)
        summary[m] = {
            "mean": round(float(vals.mean()), 2),
            "median": round(float(vals.median()), 2),
            "p10": round(float(vals.quantile(0.1)), 2),
            "p90": round(float(vals.quantile(0.9)), 2),
        }
    return {
        "cohort": {
            "sport": sport or "all",
            "gender": gender or "all",
            "division": division or "all",
            "min_active_minutes": min_active_minutes,
        },
        "session_count": int(len(df)),
        "athlete_count": int(df["athlete_number"].nunique()),
        "metrics": summary,
    }


# -- OpenAI / Ollama tool schemas ---------------------------------------------

def top_athletes_in_cohort(
    metric: str,
    sport: str | None = None,
    gender: str | None = None,
    division: str | None = None,
    limit: int = 5,
    direction: str = "desc",
) -> dict[str, Any]:
    """Top-N athletes in a cohort by average of a metric. Use for 'who is fastest/best'."""
    if direction not in ("asc", "desc"):
        direction = "desc"
    clauses = ["1=1"]
    params: list[Any] = []
    if sport:
        clauses.append("athlete_sport = ?")
        params.append(sport.lower())
    if gender:
        clauses.append("athlete_gender_marker = ?")
        params.append(gender.lower())
    if division:
        clauses.append("club_division = ?")
        params.append(division.lower())

    con = get_connection()
    try:
        rows = con.execute(
            f"""
            SELECT
                athlete_number,
                FIRST(athlete_sport) AS sport,
                FIRST(athlete_gender_marker) AS gender,
                FIRST(club_division) AS division,
                AVG({metric}) AS avg_metric,
                COUNT(*) AS sessions
            FROM sessions
            WHERE {' AND '.join(clauses)}
              AND {metric} IS NOT NULL
            GROUP BY athlete_number
            HAVING COUNT(*) >= 2
            ORDER BY avg_metric {direction.upper()}
            LIMIT ?
            """,
            [*params, limit],
        ).fetchall()
    finally:
        con.close()

    return {
        "metric": metric,
        "direction": direction,
        "cohort": {
            "sport": sport or "all",
            "gender": gender or "all",
            "division": division or "all",
        },
        "results": [
            {
                "athlete_id": int(r[0]),
                "sport": r[1],
                "gender": r[2],
                "division": r[3],
                "avg_metric": round(float(r[4]), 2),
                "sessions": int(r[5]),
            }
            for r in rows
        ],
    }


TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "get_athlete_stats",
            "description": "Per-session averages, max and min for one athlete. Use when the user asks about a specific athlete's performance.",
            "parameters": {
                "type": "object",
                "properties": {
                    "athlete_id": {"type": "integer", "description": "Athlete number (athlete_number column)"},
                    "metric": {"type": "string", "description": "Optional: a specific metric name substring. Omit for all metrics."},
                },
                "required": ["athlete_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "compare_to_cohort",
            "description": "Compare an athlete's average on a metric to their sport+gender cohort. Returns percentile and % difference.",
            "parameters": {
                "type": "object",
                "properties": {
                    "athlete_id": {"type": "integer"},
                    "metric": {
                        "type": "string",
                        "enum": [
                            "total_distance_m", "max_speed_kph", "session_load",
                            "active_minutes", "metres_per_minute",
                            "high_intensity_events", "sprint_events",
                            "acceleration_events", "deceleration_events",
                        ],
                    },
                },
                "required": ["athlete_id", "metric"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_cohort_summary",
            "description": "Aggregate benchmark stats (mean, median, p10, p90) for a cohort filtered by sport/gender/division.",
            "parameters": {
                "type": "object",
                "properties": {
                    "sport": {"type": "string", "description": "e.g. association_football, american_football. Omit for all sports."},
                    "gender": {"type": "string", "enum": ["male", "female"]},
                    "division": {"type": "string", "enum": ["di", "dii", "diii"]},
                    "min_active_minutes": {"type": "integer", "default": 70},
                },
            },
        },
    },
]


TOOL_SCHEMAS.append({
    "type": "function",
    "function": {
        "name": "top_athletes_in_cohort",
        "description": "Ranked top-N (or bottom-N) athletes in a sport/gender/division cohort by average of a metric. Use this for 'who is fastest/best/worst' style questions.",
        "parameters": {
            "type": "object",
            "properties": {
                "metric": {
                    "type": "string",
                    "enum": [
                        "max_speed_kph", "total_distance_m", "session_load",
                        "metres_per_minute", "high_intensity_events", "sprint_events",
                        "active_minutes",
                    ],
                },
                "sport": {"type": "string"},
                "gender": {"type": "string", "enum": ["male", "female"]},
                "division": {"type": "string", "enum": ["di", "dii", "diii"]},
                "limit": {"type": "integer", "default": 5},
                "direction": {"type": "string", "enum": ["desc", "asc"], "default": "desc"},
            },
            "required": ["metric"],
        },
    },
})


TOOL_REGISTRY = {
    "get_athlete_stats": get_athlete_stats,
    "compare_to_cohort": compare_to_cohort,
    "get_cohort_summary": get_cohort_summary,
    "top_athletes_in_cohort": top_athletes_in_cohort,
}
