"""
pipeline/metrics.py

Translates the DS team's R pipeline (data/r_pipeline.txt) into Python.

The R pipeline:
  1. Filters sessions by sport, gender, and active_minutes >= 70
  2. Groups by athlete_relative_age and computes mean, sd, and 10th/90th
     percentile (bottom10 / top10) for total_distance_m, max_speed_kph,
     and session_load  →  `compute_age_group_summary()`
  3. Adds within-age-group percent rank columns (0-100) for the same three
     metrics  →  `add_percent_ranks()`
  4. Returns a tidy athlete-level frame with the columns specified in
     w_soc_select  →  `build_athlete_metrics()`

All sport / gender comparisons are case-insensitive to align with
ingest.py's _clean_strings() step.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional, Tuple

import pandas as pd

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

ROOT_DIR = Path(__file__).resolve().parents[1]
SAMPLE_PATH = ROOT_DIR / "data" / "raw" / "sample_data.csv"
MENS_SYNTHETIC = ROOT_DIR / "data" / "raw" / "synthetic" / "mens_synthetic_data.csv"
WOMENS_SYNTHETIC = ROOT_DIR / "data" / "raw" / "synthetic" / "womens_synthetic_data.csv"

# ---------------------------------------------------------------------------
# Constants (from r_pipeline.txt)
# ---------------------------------------------------------------------------

# The three performance metrics the DS team focuses on
PERF_METRICS = ["total_distance_m", "max_speed_kph", "session_load"]

# Matching percent-rank column names from r_pipeline.txt (w_soc_select)
RANK_COL_MAP = {
    "total_distance_m":    "total_dist_perc_rank",
    "max_speed_kph":       "max_speed_perc_rank",
    "session_load":        "session_load_perc_rank",
    "acceleration_events": "accel_perc_rank",
    "deceleration_events": "decel_perc_rank",
    "sprint_events":       "sprint_perc_rank",
}

# Final athlete-level columns returned by build_athlete_metrics
# (mirrors w_soc_select from r_pipeline.txt)
ATHLETE_SELECT_COLS = [
    "athlete_number",
    "athlete_relative_age",
    "athlete_gender_marker",
    "athlete_sport",
    "club_division",
    "active_minutes",
    "total_distance_m",
    "max_speed_kph",
    "session_load",
    "total_dist_perc_rank",
    "max_speed_perc_rank",
    "session_load_perc_rank",
]

# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------


def load_all_data(include_synthetic: bool = True) -> pd.DataFrame:
    """
    Load sample data plus optional synthetic datasets through the ingest
    pipeline, then concatenate into a single cleaned dataframe.
    """
    from app.pipeline.ingest import ingest_data  # local import to avoid circular deps

    frames = []

    if SAMPLE_PATH.exists():
        frames.append(ingest_data(SAMPLE_PATH))

    if include_synthetic:
        for path in [MENS_SYNTHETIC, WOMENS_SYNTHETIC]:
            if path.exists():
                frames.append(ingest_data(path))

    if not frames:
        raise FileNotFoundError("No data files found under DE/data/raw/.")

    combined = pd.concat(frames, ignore_index=True)
    combined = combined.drop_duplicates().reset_index(drop=True)
    return combined


# ---------------------------------------------------------------------------
# Step 1 – Filter  (r_pipeline.txt lines 1-4)
# ---------------------------------------------------------------------------


def filter_sessions(
    df: pd.DataFrame,
    sport: Optional[str] = None,
    gender: Optional[str] = None,
    min_active_minutes: int = 70,
) -> pd.DataFrame:
    """
    Apply the DS-specified session filter.  Defaults mirror the R script:
      active_minutes >= 70  (required)
      sport / gender are optional to allow cross-sport / cross-gender views.

    String comparisons are case-insensitive; ingest.py lowercases both fields.
    """
    mask = df["active_minutes"] >= min_active_minutes

    if sport is not None:
        mask &= df["athlete_sport"] == sport.lower()

    if gender is not None:
        mask &= df["athlete_gender_marker"] == gender.lower()

    return df[mask].copy()


# ---------------------------------------------------------------------------
# Step 2 – Age-group summary  (r_pipeline.txt lines 7-22, `avgs`)
# ---------------------------------------------------------------------------


def compute_age_group_summary(df: pd.DataFrame) -> pd.DataFrame:
    """
    Group by athlete_relative_age and compute the summary statistics
    defined in the R script's `avgs` object:
      count, mean, sd, 90th-pctile (top10), 10th-pctile (bottom10)
    for total_distance_m, max_speed_kph, and session_load.
    """

    def q90(s: pd.Series) -> float:
        return float(s.quantile(0.9))

    def q10(s: pd.Series) -> float:
        return float(s.quantile(0.1))

    agg: dict = {"count": ("athlete_number", "count")}

    for metric in PERF_METRICS:
        prefix = metric  # keep full name for clarity
        agg[f"avg_{prefix}"]    = (metric, "mean")
        agg[f"sd_{prefix}"]     = (metric, "std")
        agg[f"top10_{prefix}"]  = (metric, q90)
        agg[f"bottom10_{prefix}"] = (metric, q10)

    summary = (
        df.groupby("athlete_relative_age")
        .agg(**agg)
        .reset_index()
        .round(3)
    )
    return summary


# ---------------------------------------------------------------------------
# Step 3 – Percent ranks  (r_pipeline.txt lines 24-29)
# ---------------------------------------------------------------------------


def add_percent_ranks(df: pd.DataFrame) -> pd.DataFrame:
    """
    Within each athlete_relative_age group, compute percent rank (0-100)
    for total_distance_m, max_speed_kph, and session_load.
    Column names match the R script's w_soc_select output exactly.
    """
    df = df.copy()
    for metric, rank_col in RANK_COL_MAP.items():
        df[rank_col] = (
            df.groupby("athlete_relative_age")[metric]
            .rank(pct=True, method="average")
            .mul(100)
            .round(2)
        )
    return df


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


def build_athlete_metrics(
    df: pd.DataFrame,
    sport: Optional[str] = None,
    gender: Optional[str] = None,
    min_active_minutes: int = 70,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Full DS pipeline from r_pipeline.txt, generalised to any sport/gender.

    Parameters
    ----------
    df                  : cleaned dataframe from load_all_data() or ingest_data()
    sport               : e.g. "association_football"  (None = all sports)
    gender              : "male" / "female"            (None = all genders)
    min_active_minutes  : session filter threshold (default 70)

    Returns
    -------
    athlete_df  : row-per-session with percent ranks added (w_soc_select cols)
    summary_df  : row-per-age-group summary stats       (avgs cols)
    """
    filtered = filter_sessions(df, sport=sport, gender=gender, min_active_minutes=min_active_minutes)

    if filtered.empty:
        empty_athlete = pd.DataFrame(columns=ATHLETE_SELECT_COLS)
        empty_summary = pd.DataFrame(columns=["athlete_relative_age", "count"])
        return empty_athlete, empty_summary

    summary_df = compute_age_group_summary(filtered)
    ranked_df  = add_percent_ranks(filtered)

    # Keep only the columns defined in w_soc_select (+ context cols we added)
    available = [c for c in ATHLETE_SELECT_COLS if c in ranked_df.columns]
    athlete_df = ranked_df[available].reset_index(drop=True)

    return athlete_df, summary_df


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> None:
    df = load_all_data()
    print(f"Combined dataset: {len(df):,} rows, {len(df.columns)} columns")

    athlete_df, summary_df = build_athlete_metrics(
        df,
        sport="association_football",
        gender="female",
        min_active_minutes=70,
    )
    print(f"Women's soccer sessions (active_minutes>=70): {len(athlete_df):,} rows")
    print(f"Age-group summary: {len(summary_df)} groups")
    print(summary_df.to_string(index=False))


if __name__ == "__main__":
    main()
