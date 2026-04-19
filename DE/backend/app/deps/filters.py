"""Shared filter query-params used across most endpoints.

Mirrors the Streamlit sidebar: gender, sports, divisions, age range,
minimum active minutes, synthetic-data inclusion.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import Query
from pydantic import BaseModel


class SessionFilter(BaseModel):
    gender: str | None = None
    sports: list[str] | None = None
    divisions: list[str] | None = None
    age_min: int | None = None
    age_max: int | None = None
    min_minutes: int = 70
    data_source: str = "all"  # all | sample | synthetic

    def to_sql_where(self) -> tuple[str, dict]:
        clauses: list[str] = ["active_minutes >= $min_minutes"]
        params: dict = {"min_minutes": self.min_minutes}

        if self.gender and self.gender.lower() != "all":
            clauses.append("athlete_gender_marker = $gender")
            params["gender"] = self.gender.lower()

        if self.sports:
            clauses.append("athlete_sport = ANY($sports)")
            params["sports"] = [s.lower() for s in self.sports]

        if self.divisions:
            clauses.append("club_division = ANY($divisions)")
            params["divisions"] = [d.lower() for d in self.divisions]

        if self.age_min is not None:
            clauses.append("athlete_relative_age >= $age_min")
            params["age_min"] = self.age_min

        if self.age_max is not None:
            clauses.append("athlete_relative_age <= $age_max")
            params["age_max"] = self.age_max

        if self.data_source == "sample":
            clauses.append("data_source = 'sample'")
        elif self.data_source == "synthetic":
            clauses.append("data_source = 'synthetic'")

        return " AND ".join(clauses), params


def session_filter(
    gender: Annotated[str | None, Query()] = None,
    sports: Annotated[list[str] | None, Query()] = None,
    divisions: Annotated[list[str] | None, Query()] = None,
    age_min: Annotated[int | None, Query(ge=0, le=100)] = None,
    age_max: Annotated[int | None, Query(ge=0, le=100)] = None,
    min_minutes: Annotated[int, Query(ge=0, le=200)] = 70,
    data_source: Annotated[str, Query(pattern="^(all|sample|synthetic)$")] = "all",
) -> SessionFilter:
    return SessionFilter(
        gender=gender,
        sports=sports,
        divisions=divisions,
        age_min=age_min,
        age_max=age_max,
        min_minutes=min_minutes,
        data_source=data_source,
    )
