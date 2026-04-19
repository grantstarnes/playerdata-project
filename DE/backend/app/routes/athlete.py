"""Per-athlete endpoints — list, drilldown, session history, percentile ranks."""

from __future__ import annotations

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException

from app.db.duckdb_store import get_connection
from app.deps.auth import require_user
from app.deps.filters import SessionFilter, session_filter
from app.pipeline.metrics import add_percent_ranks

router = APIRouter(prefix="/api/athletes", tags=["athletes"])


@router.get("")
def list_athletes(
    search: str | None = None,
    f: SessionFilter = Depends(session_filter),
    _user: dict = Depends(require_user),
) -> list[dict]:
    where, params = f.to_sql_where()
    con = get_connection()
    try:
        rows = con.execute(
            f"""
            SELECT
                athlete_number,
                FIRST(athlete_sport)             AS sport,
                FIRST(athlete_gender_marker)     AS gender,
                FIRST(athlete_relative_age)      AS age,
                FIRST(club_division)             AS division,
                COUNT(*)                         AS sessions
            FROM sessions
            WHERE {where}
            GROUP BY athlete_number
            ORDER BY sessions DESC, athlete_number
            """,
            params,
        ).fetchall()
    finally:
        con.close()

    result = [
        {
            "athlete_id": int(r[0]),
            "sport": r[1],
            "gender": r[2],
            "age": int(r[3]) if r[3] is not None else None,
            "division": r[4],
            "sessions": int(r[5]),
        }
        for r in rows
    ]
    if search:
        needle = search.lower()
        result = [
            a for a in result
            if needle in str(a["athlete_id"]) or needle in (a["sport"] or "")
        ]
    return result


@router.get("/{athlete_id}/cohort")
def athlete_cohort(
    athlete_id: int,
    f: SessionFilter = Depends(session_filter),
    _user: dict = Depends(require_user),
) -> dict:
    """Per-athlete averages for everyone in the same age cohort (respecting filters)."""
    from fastapi import HTTPException as _HTTPException
    where, params = f.to_sql_where()
    con = get_connection()
    try:
        age_row = con.execute(
            "SELECT FIRST(athlete_relative_age) FROM sessions WHERE athlete_number = ?",
            [athlete_id],
        ).fetchone()
        if not age_row or age_row[0] is None:
            raise _HTTPException(status_code=404, detail=f"Athlete {athlete_id} not found")
        age = int(age_row[0])
        rows = con.execute(
            f"""
            SELECT
                athlete_number,
                AVG(acceleration_events) AS accel,
                AVG(deceleration_events) AS decel,
                AVG(max_speed_kph)        AS max_speed,
                AVG(total_distance_m)     AS distance,
                COUNT(*)                  AS sessions
            FROM sessions
            WHERE athlete_relative_age = $age AND {where}
            GROUP BY athlete_number
            HAVING COUNT(*) >= 2
            """,
            {**params, "age": age},
        ).fetchall()
    finally:
        con.close()
    return {
        "athlete_id": athlete_id,
        "age": age,
        "peers": [
            {
                "athlete_id": int(r[0]),
                "accel":     float(r[1] or 0),
                "decel":     float(r[2] or 0),
                "max_speed": float(r[3] or 0),
                "distance":  float(r[4] or 0),
                "sessions":  int(r[5]),
            }
            for r in rows
        ],
    }


@router.get("/{athlete_id}")
def athlete_detail(
    athlete_id: int,
    f: SessionFilter = Depends(session_filter),
    _user: dict = Depends(require_user),
) -> dict:
    where, params = f.to_sql_where()
    con = get_connection()
    try:
        sessions = con.execute(
            f"""
            SELECT * FROM sessions
            WHERE athlete_number = $aid AND {where}
            ORDER BY athlete_number
            """,
            {**params, "aid": athlete_id},
        ).df()
        # Percentile ranks are computed across the filtered cohort for this athlete's age group
        cohort = con.execute(
            f"SELECT * FROM sessions WHERE {where}",
            params,
        ).df()
    finally:
        con.close()

    if sessions.empty:
        raise HTTPException(status_code=404, detail=f"Athlete {athlete_id} has no sessions matching filter")

    ranked_cohort = add_percent_ranks(cohort) if not cohort.empty else pd.DataFrame()
    athlete_ranked = ranked_cohort[ranked_cohort["athlete_number"] == athlete_id]

    first = sessions.iloc[0]
    meta = {
        "athlete_id": int(athlete_id),
        "age": int(first["athlete_relative_age"]),
        "sport": str(first["athlete_sport"]),
        "gender": str(first["athlete_gender_marker"]),
        "division": str(first["club_division"]),
        "session_count": int(len(sessions)),
    }

    stat_cols = [
        "active_minutes", "total_distance_m", "max_speed_kph", "avg_speed_kph",
        "session_load", "metres_per_minute",
        "high_intensity_events", "sprint_events",
        "acceleration_events", "deceleration_events",
    ]
    stats = {}
    for c in stat_cols:
        if c in sessions.columns:
            col = sessions[c].dropna().astype(float)
            if len(col):
                stats[c] = {
                    "avg": round(float(col.mean()), 2),
                    "max": round(float(col.max()), 2),
                    "min": round(float(col.min()), 2),
                }

    from app.pipeline.metrics import RANK_COL_MAP
    percentiles: dict[str, float] = {}
    if not athlete_ranked.empty:
        latest = athlete_ranked.iloc[-1]
        for col in RANK_COL_MAP.values():
            if col in latest and pd.notna(latest[col]):
                percentiles[col] = float(latest[col])

    # Session timeline (trim columns for payload size)
    timeline_cols = [c for c in (
        "active_minutes", "total_distance_m", "max_speed_kph",
        "session_load", "high_intensity_events", "sprint_events",
    ) if c in sessions.columns]
    timeline = sessions[timeline_cols].reset_index(drop=True).astype(object).where(
        sessions[timeline_cols].notna(), None
    ).to_dict(orient="records")

    return {
        **meta,
        "stats": stats,
        "percentiles": percentiles,
        "timeline": timeline,
    }
