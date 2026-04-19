from pathlib import Path

import numpy as np
import pandas as pd

NUM_ROWS = 10000

ROOT_DIR = Path(__file__).resolve().parents[1]
SAMPLE_FILE = ROOT_DIR /"DE" / "data" / "raw" / "sample_data.csv"
OUTPUT_DIR = ROOT_DIR / "DE" / "data" / "raw" / "synthetic"

OUTPUT_COLUMNS = [
    "athlete_number",
    "athlete_relative_age",
    "athlete_gender_marker",
    "athlete_sport",
    "club_division",
    "active_minutes",
    "contributing_seconds",
    "total_distance_m",
    "total_high_intensity_distance_m",
    "total_sprint_distance_m",
    "high_intensity_events",
    "sprint_events",
    "avg_speed_kph",
    "max_speed_kph",
    "acceleration_events",
    "deceleration_events",
    "max_acceleration",
    "max_deceleration",
    "metres_per_minute",
    "percentage_max_speed_kph",
    "session_load",
]

NUMERIC_COLUMNS = [
    "athlete_number",
    "athlete_relative_age",
    "active_minutes",
    "contributing_seconds",
    "total_distance_m",
    "total_high_intensity_distance_m",
    "total_sprint_distance_m",
    "high_intensity_events",
    "sprint_events",
    "avg_speed_kph",
    "max_speed_kph",
    "acceleration_events",
    "deceleration_events",
    "max_acceleration",
    "max_deceleration",
    "metres_per_minute",
    "percentage_max_speed_kph",
    "session_load",
]

COUNT_COLUMNS = {
    "athlete_number",
    "athlete_relative_age",
    "active_minutes",
    "contributing_seconds",
    "high_intensity_events",
    "sprint_events",
    "acceleration_events",
    "deceleration_events",
}


def load_sample_data(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, dtype=str)
    missing = [col for col in OUTPUT_COLUMNS if col not in df.columns]
    if missing:
        raise ValueError(f"sample_data.csv is missing required columns: {missing}")

    df = df[OUTPUT_COLUMNS].copy()
    for col in NUMERIC_COLUMNS:
        cleaned = df[col].astype(str).str.replace(",", "", regex=False)
        df[col] = pd.to_numeric(cleaned, errors="coerce")

    return df.dropna(subset=["athlete_gender_marker", "athlete_sport", "club_division"])


def clip_series(values: pd.Series, source: pd.Series, min_floor: float = 0.0) -> pd.Series:
    lower = max(min_floor, float(source.min(skipna=True)))
    upper = float(source.max(skipna=True))
    if upper < lower:
        upper = lower
    return values.clip(lower=lower, upper=upper)


def generate_synthetic_dataset(
    sample_df: pd.DataFrame,
    gender: str,
    num_rows: int,
    age_mean: float,
    age_std: float,
    age_min: int,
    age_max: int,
) -> pd.DataFrame:
    gender_sample = sample_df[sample_df["athlete_gender_marker"] == gender].copy()
    if gender_sample.empty:
        raise ValueError(f"No sample rows found for gender '{gender}'.")

    base = gender_sample.sample(n=num_rows, replace=True, random_state=None).reset_index(drop=True)

    athlete_count = max(1, num_rows // 4)
    sessions_per_athlete = np.random.choice([3, 4, 5, 6], size=athlete_count)
    athlete_ids = []
    for idx, sessions in enumerate(sessions_per_athlete, start=1000):
        athlete_ids.extend([idx] * int(sessions))
        if len(athlete_ids) >= num_rows:
            break
    athlete_ids = athlete_ids[:num_rows]

    athlete_ages = np.random.normal(age_mean, age_std, len(set(athlete_ids)))
    athlete_ages = np.clip(athlete_ages, age_min, age_max).astype(int)
    age_map = dict(zip(sorted(set(athlete_ids)), athlete_ages))

    out = pd.DataFrame(index=range(num_rows))
    out["athlete_number"] = athlete_ids
    out["athlete_relative_age"] = out["athlete_number"].map(age_map)
    out["athlete_gender_marker"] = gender
    out["athlete_sport"] = base["athlete_sport"].values
    out["club_division"] = base["club_division"].values

    for col in NUMERIC_COLUMNS:
        if col in {"athlete_number", "athlete_relative_age", "active_minutes", "contributing_seconds"}:
            continue
        noise = np.random.normal(1.0, 0.08, size=num_rows)
        out[col] = base[col].values * noise
        out[col] = clip_series(out[col], gender_sample[col], min_floor=0.0)

    out["contributing_seconds"] = (base["contributing_seconds"].values * np.random.normal(1.0, 0.04, num_rows)).round()
    out["contributing_seconds"] = clip_series(out["contributing_seconds"], gender_sample["contributing_seconds"], min_floor=600.0)
    out["contributing_seconds"] = (out["contributing_seconds"] / 60).round() * 60

    out["active_minutes"] = (out["contributing_seconds"] / 60).round().astype(int)
    out["max_speed_kph"] = np.maximum(out["max_speed_kph"], out["avg_speed_kph"])

    positive_minutes = out["active_minutes"].replace(0, 1)
    out["metres_per_minute"] = out["total_distance_m"] / positive_minutes
    out["metres_per_minute"] = clip_series(out["metres_per_minute"], gender_sample["metres_per_minute"], min_floor=0.0)

    speed_ratio = (out["avg_speed_kph"] / out["max_speed_kph"].replace(0, 1.0)) * 100
    out["percentage_max_speed_kph"] = clip_series(speed_ratio, gender_sample["percentage_max_speed_kph"], min_floor=0.0)

    out["session_load"] = (
        (out["total_distance_m"] * 0.09)
        + (out["total_high_intensity_distance_m"] * 0.9)
        + (out["high_intensity_events"] * 2.0)
        + (out["sprint_events"] * 4.0)
    )
    out["session_load"] = clip_series(out["session_load"], gender_sample["session_load"], min_floor=0.0)

    for col in COUNT_COLUMNS:
        out[col] = np.maximum(0, np.rint(out[col])).astype(int)

    decimal_cols = [col for col in NUMERIC_COLUMNS if col not in COUNT_COLUMNS]
    for col in decimal_cols:
        out[col] = out[col].round(2)

    return out[OUTPUT_COLUMNS]


def main() -> None:
    sample_df = load_sample_data(SAMPLE_FILE)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    mens_df = generate_synthetic_dataset(
        sample_df,
        gender="Male",
        num_rows=NUM_ROWS,
        age_mean=26.2,
        age_std=3.5,
        age_min=17,
        age_max=39,
    )
    womens_df = generate_synthetic_dataset(
        sample_df,
        gender="Female",
        num_rows=NUM_ROWS,
        age_mean=22.5,
        age_std=3.0,
        age_min=16,
        age_max=35,
    )

    mens_path = OUTPUT_DIR / "mens_synthetic_data.csv"
    womens_path = OUTPUT_DIR / "womens_synthetic_data.csv"
    mens_df.to_csv(mens_path, index=False)
    womens_df.to_csv(womens_path, index=False)

    print(
        f"Synthetic files created: {mens_path} ({len(mens_df):,} rows), "
        f"{womens_path} ({len(womens_df):,} rows)."
    )


if __name__ == "__main__":
    main()