"""Benchmarks — cross-sport / cross-division comparisons."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.db.duckdb_store import get_connection
from app.deps.auth import require_user
from app.deps.filters import SessionFilter, session_filter

router = APIRouter(prefix="/api/benchmarks", tags=["benchmarks"])

_BENCHMARK_METRICS = [
    "total_distance_m",
    "total_high_intensity_distance_m",
    "total_sprint_distance_m",
    "max_speed_kph",
    "session_load",
    "high_intensity_events",
    "sprint_events",
    "acceleration_events",
    "deceleration_events",
    "active_minutes",
]


@router.get("/heatmap")
def heatmap(
    f: SessionFilter = Depends(session_filter),
    _user: dict = Depends(require_user),
) -> dict:
    """Mean metrics per sport, also returns per-metric min/max for normalized colouring."""
    where, params = f.to_sql_where()
    con = get_connection()
    try:
        metric_cols = ", ".join([f"AVG({m}) AS {m}" for m in _BENCHMARK_METRICS])
        rows = con.execute(
            f"SELECT athlete_sport, {metric_cols} FROM sessions WHERE {where} GROUP BY athlete_sport ORDER BY athlete_sport",
            params,
        ).fetchall()
    finally:
        con.close()

    data = [
        {"sport": r[0], **{m: float(r[i + 1] or 0) for i, m in enumerate(_BENCHMARK_METRICS)}}
        for r in rows
    ]
    ranges = {
        m: {
            "min": min((d[m] for d in data), default=0.0),
            "max": max((d[m] for d in data), default=0.0),
        }
        for m in _BENCHMARK_METRICS
    }
    return {"metrics": _BENCHMARK_METRICS, "rows": data, "ranges": ranges}


@router.get("/breakdown")
def breakdown(
    by: str = "athlete_sport",
    f: SessionFilter = Depends(session_filter),
    _user: dict = Depends(require_user),
) -> list[dict]:
    allowed = {"athlete_sport", "club_division", "athlete_gender_marker", "athlete_relative_age"}
    if by not in allowed:
        by = "athlete_sport"
    where, params = f.to_sql_where()
    con = get_connection()
    try:
        rows = con.execute(
            f"""
            SELECT
                {by}                                 AS bucket,
                COUNT(*)                             AS n,
                AVG(session_load)                    AS avg_load,
                quantile_cont(session_load, 0.25)    AS q1_load,
                median(session_load)                 AS median_load,
                quantile_cont(session_load, 0.75)    AS q3_load,
                AVG(total_distance_m)                AS avg_distance,
                AVG(max_speed_kph)                   AS avg_max_speed,
                AVG(acceleration_events)             AS avg_accel,
                AVG(deceleration_events)             AS avg_decel
            FROM sessions
            WHERE {where}
            GROUP BY bucket
            ORDER BY avg_load DESC
            """,
            params,
        ).fetchall()
    finally:
        con.close()

    return [
        {
            "bucket": str(r[0]) if r[0] is not None else "—",
            "n": int(r[1]),
            "avg_load": float(r[2] or 0),
            "q1_load": float(r[3] or 0),
            "median_load": float(r[4] or 0),
            "q3_load": float(r[5] or 0),
            "avg_distance_m": float(r[6] or 0),
            "avg_max_speed_kph": float(r[7] or 0),
            "avg_accel_events": float(r[8] or 0),
            "avg_decel_events": float(r[9] or 0),
        }
        for r in rows
    ]
