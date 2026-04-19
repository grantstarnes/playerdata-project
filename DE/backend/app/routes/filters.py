"""Dropdown / slider option values for the frontend filter bar."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.db.duckdb_store import get_connection
from app.deps.auth import require_user

router = APIRouter(prefix="/api/filters", tags=["filters"])


@router.get("/options")
def filter_options(_user: dict = Depends(require_user)) -> dict:
    con = get_connection()
    try:
        genders = [r[0] for r in con.execute(
            "SELECT DISTINCT athlete_gender_marker FROM sessions WHERE athlete_gender_marker IS NOT NULL ORDER BY 1"
        ).fetchall()]
        sports = [r[0] for r in con.execute(
            "SELECT DISTINCT athlete_sport FROM sessions WHERE athlete_sport IS NOT NULL ORDER BY 1"
        ).fetchall()]
        divisions = [r[0] for r in con.execute(
            "SELECT DISTINCT club_division FROM sessions WHERE club_division IS NOT NULL ORDER BY 1"
        ).fetchall()]
        age_row = con.execute(
            "SELECT MIN(athlete_relative_age), MAX(athlete_relative_age) FROM sessions"
        ).fetchone()
        total = con.execute("SELECT COUNT(*) FROM sessions").fetchone()[0]
    finally:
        con.close()

    return {
        "genders": genders,
        "sports": sports,
        "divisions": divisions,
        "age_min": int(age_row[0]) if age_row[0] is not None else 0,
        "age_max": int(age_row[1]) if age_row[1] is not None else 0,
        "total_sessions": total,
    }
