"""Team Overview endpoints — cohort KPIs + chart data for 5 tiles."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.db.duckdb_store import get_connection
from app.deps.auth import require_user
from app.deps.filters import SessionFilter, session_filter

router = APIRouter(prefix="/api/overview", tags=["overview"])


@router.get("/kpis")
def overview_kpis(
    f: SessionFilter = Depends(session_filter),
    _user: dict = Depends(require_user),
) -> dict:
    where, params = f.to_sql_where()
    con = get_connection()
    try:
        row = con.execute(
            f"""
            SELECT
                COUNT(*)                            AS sessions,
                COUNT(DISTINCT athlete_number)      AS athletes,
                AVG(session_load)                   AS avg_session_load,
                AVG(total_distance_m)               AS avg_total_distance,
                AVG(max_speed_kph)                  AS avg_max_speed,
                AVG(active_minutes)                 AS avg_active_minutes
            FROM sessions
            WHERE {where}
            """,
            params,
        ).fetchone()
    finally:
        con.close()

    return {
        "sessions": int(row[0] or 0),
        "athletes": int(row[1] or 0),
        "avg_session_load": float(row[2]) if row[2] is not None else 0.0,
        "avg_total_distance_m": float(row[3]) if row[3] is not None else 0.0,
        "avg_max_speed_kph": float(row[4]) if row[4] is not None else 0.0,
        "avg_active_minutes": float(row[5]) if row[5] is not None else 0.0,
    }


@router.get("/session-load-by-sport")
def session_load_by_sport(
    f: SessionFilter = Depends(session_filter),
    _user: dict = Depends(require_user),
) -> list[dict]:
    """Box-plot inputs: per-sport percentiles of session_load."""
    where, params = f.to_sql_where()
    con = get_connection()
    try:
        rows = con.execute(
            f"""
            SELECT
                athlete_sport,
                COUNT(*)                             AS n,
                MIN(session_load)                    AS min,
                quantile_cont(session_load, 0.25)    AS q1,
                median(session_load)                 AS median,
                quantile_cont(session_load, 0.75)    AS q3,
                MAX(session_load)                    AS max,
                AVG(session_load)                    AS mean
            FROM sessions
            WHERE {where}
            GROUP BY athlete_sport
            ORDER BY median DESC
            """,
            params,
        ).fetchall()
    finally:
        con.close()

    return [
        {
            "sport": r[0],
            "n": int(r[1]),
            "min": float(r[2] or 0),
            "q1": float(r[3] or 0),
            "median": float(r[4] or 0),
            "q3": float(r[5] or 0),
            "max": float(r[6] or 0),
            "mean": float(r[7] or 0),
        }
        for r in rows
    ]


@router.get("/volume-vs-intensity")
def volume_vs_intensity(
    f: SessionFilter = Depends(session_filter),
    limit: int = 5000,
    _user: dict = Depends(require_user),
) -> list[dict]:
    """Scatter: active_minutes × session_load, sized by total distance."""
    where, params = f.to_sql_where()
    params["limit"] = limit
    con = get_connection()
    try:
        rows = con.execute(
            f"""
            SELECT active_minutes, session_load, total_distance_m,
                   athlete_sport, athlete_number
            FROM sessions
            WHERE {where}
            LIMIT $limit
            """,
            params,
        ).fetchall()
    finally:
        con.close()

    return [
        {
            "active_minutes": float(r[0] or 0),
            "session_load":   float(r[1] or 0),
            "total_distance_m": float(r[2] or 0),
            "sport":          r[3],
            "athlete_id":     int(r[4]) if r[4] is not None else None,
        }
        for r in rows
    ]


@router.get("/distance-breakdown")
def distance_breakdown(
    group_by: str = "athlete_sport",
    f: SessionFilter = Depends(session_filter),
    _user: dict = Depends(require_user),
) -> list[dict]:
    """Mean total / HI / sprint distance per group."""
    allowed = {"athlete_sport", "club_division", "athlete_gender_marker"}
    if group_by not in allowed:
        group_by = "athlete_sport"
    where, params = f.to_sql_where()
    con = get_connection()
    try:
        rows = con.execute(
            f"""
            SELECT
                {group_by}                               AS bucket,
                AVG(total_distance_m)                    AS avg_total,
                AVG(total_high_intensity_distance_m)     AS avg_hi,
                AVG(total_sprint_distance_m)             AS avg_sprint
            FROM sessions
            WHERE {where}
            GROUP BY bucket
            ORDER BY avg_total DESC
            """,
            params,
        ).fetchall()
    finally:
        con.close()
    return [
        {
            "bucket": r[0],
            "avg_total_distance_m": float(r[1] or 0),
            "avg_hi_distance_m": float(r[2] or 0),
            "avg_sprint_distance_m": float(r[3] or 0),
        }
        for r in rows
    ]


@router.get("/session-load-by-age")
def session_load_by_age(
    f: SessionFilter = Depends(session_filter),
    _user: dict = Depends(require_user),
) -> list[dict]:
    """Box plot data: per-age percentiles + whisker bounds of session_load."""
    where, params = f.to_sql_where()
    con = get_connection()
    try:
        rows = con.execute(
            f"""
            SELECT
                athlete_relative_age            AS age,
                COUNT(*)                        AS n,
                MIN(session_load)               AS lo,
                quantile_cont(session_load,0.25) AS q1,
                median(session_load)            AS median,
                quantile_cont(session_load,0.75) AS q3,
                MAX(session_load)               AS hi,
                AVG(session_load)               AS mean
            FROM sessions
            WHERE {where}
            GROUP BY athlete_relative_age
            HAVING COUNT(*) >= 5
            ORDER BY age
            """,
            params,
        ).fetchall()
    finally:
        con.close()
    return [
        {
            "age": int(r[0]),
            "n": int(r[1]),
            "min": float(r[2] or 0),
            "q1": float(r[3] or 0),
            "median": float(r[4] or 0),
            "q3": float(r[5] or 0),
            "max": float(r[6] or 0),
            "mean": float(r[7] or 0),
        }
        for r in rows
    ]


@router.get("/age-stats")
def age_stats(
    f: SessionFilter = Depends(session_filter),
    _user: dict = Depends(require_user),
) -> dict:
    """Per-age count + mean + sd + top10 (p90) + bottom10 (p10) for 4 key metrics."""
    METRICS = ["total_distance_m", "max_speed_kph", "session_load", "sprint_events"]
    where, params = f.to_sql_where()
    con = get_connection()
    try:
        select_parts: list[str] = ["athlete_relative_age AS age", "COUNT(*) AS n"]
        for m in METRICS:
            select_parts.extend([
                f"AVG({m}) AS avg_{m}",
                f"stddev_samp({m}) AS sd_{m}",
                f"quantile_cont({m}, 0.9) AS top10_{m}",
                f"quantile_cont({m}, 0.1) AS bottom10_{m}",
            ])
        sql = f"""
            SELECT {', '.join(select_parts)}
            FROM sessions
            WHERE {where}
            GROUP BY athlete_relative_age
            HAVING COUNT(*) >= 5
            ORDER BY athlete_relative_age
        """
        rows = con.execute(sql, params).fetchall()
    finally:
        con.close()

    tables: dict[str, list[dict]] = {m: [] for m in METRICS}
    for r in rows:
        age = int(r[0])
        n = int(r[1])
        for i, m in enumerate(METRICS):
            base = 2 + i * 4
            tables[m].append({
                "age":       age,
                "count":     n,
                "mean":      float(r[base] or 0),
                "sd":        float(r[base + 1] or 0),
                "top10":     float(r[base + 2] or 0),
                "bottom10":  float(r[base + 3] or 0),
            })
    return {"metrics": METRICS, "tables": tables}


@router.get("/weighted-scatter")
def weighted_scatter(
    f: SessionFilter = Depends(session_filter),
    _user: dict = Depends(require_user),
) -> list[dict]:
    """Per-athlete scatter: session_load and max_speed_kph, weighted by active_minutes."""
    where, params = f.to_sql_where()
    con = get_connection()
    try:
        rows = con.execute(
            f"""
            SELECT
                athlete_number,
                FIRST(athlete_sport)                AS sport,
                FIRST(athlete_gender_marker)        AS gender,
                FIRST(club_division)                AS division,
                FIRST(athlete_relative_age)         AS age,
                SUM(session_load * active_minutes)
                  / NULLIF(SUM(active_minutes), 0)  AS w_load,
                SUM(max_speed_kph * active_minutes)
                  / NULLIF(SUM(active_minutes), 0)  AS w_speed,
                COUNT(*)                            AS sessions
            FROM sessions
            WHERE {where}
            GROUP BY athlete_number
            HAVING COUNT(*) >= 2 AND SUM(active_minutes) > 0
            """,
            params,
        ).fetchall()
    finally:
        con.close()
    return [
        {
            "athlete_id": int(r[0]),
            "sport": r[1],
            "gender": r[2],
            "division": r[3],
            "age": int(r[4]) if r[4] is not None else None,
            "weighted_session_load": float(r[5] or 0),
            "weighted_max_speed": float(r[6] or 0),
            "sessions": int(r[7]),
        }
        for r in rows
    ]
