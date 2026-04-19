"""Age-Group DS metrics — mirrors r_pipeline.txt's avgs summary."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.db.duckdb_store import get_connection
from app.deps.auth import require_user
from app.deps.filters import SessionFilter, session_filter
from app.pipeline.metrics import compute_age_group_summary, PERF_METRICS

router = APIRouter(prefix="/api/age-group", tags=["age-group"])


@router.get("/summary")
def summary(
    f: SessionFilter = Depends(session_filter),
    _user: dict = Depends(require_user),
) -> dict:
    where, params = f.to_sql_where()
    con = get_connection()
    try:
        df = con.execute(f"SELECT * FROM sessions WHERE {where}", params).df()
    finally:
        con.close()

    if df.empty:
        return {"metrics": PERF_METRICS, "rows": []}

    summary_df = compute_age_group_summary(df)
    rows = summary_df.astype(object).where(summary_df.notna(), None).to_dict(orient="records")
    return {"metrics": PERF_METRICS, "rows": rows}


@router.get("/scatter")
def scatter(
    metric: str = "total_distance_m",
    color_by: str = "athlete_gender_marker",
    f: SessionFilter = Depends(session_filter),
    _user: dict = Depends(require_user),
) -> list[dict]:
    if metric not in PERF_METRICS + [
        "active_minutes", "high_intensity_events", "sprint_events",
        "acceleration_events", "deceleration_events", "metres_per_minute",
    ]:
        metric = "total_distance_m"
    if color_by not in {"athlete_gender_marker", "athlete_sport", "club_division"}:
        color_by = "athlete_gender_marker"

    where, params = f.to_sql_where()
    con = get_connection()
    try:
        rows = con.execute(
            f"""
            SELECT athlete_relative_age, {metric}, {color_by}, athlete_number
            FROM sessions WHERE {where}
            """,
            params,
        ).fetchall()
    finally:
        con.close()

    return [
        {"age": int(r[0]), "value": float(r[1] or 0), "group": r[2], "athlete_id": int(r[3])}
        for r in rows if r[0] is not None and r[1] is not None
    ]
