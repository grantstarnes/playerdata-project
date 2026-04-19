from __future__ import annotations

from pathlib import Path
from typing import Dict, List

import pandas as pd

ROOT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_INPUT_PATH = ROOT_DIR / "data" / "raw" / "sample_data.csv"

REQUIRED_COLUMNS: List[str] = [
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

NUMERIC_COLUMNS: Dict[str, str] = {
	"athlete_number": "Int64",
	"athlete_relative_age": "Int64",
	"active_minutes": "Int64",
	"contributing_seconds": "Int64",
	"total_distance_m": "float64",
	"total_high_intensity_distance_m": "float64",
	"total_sprint_distance_m": "float64",
	"high_intensity_events": "Int64",
	"sprint_events": "Int64",
	"avg_speed_kph": "float64",
	"max_speed_kph": "float64",
	"acceleration_events": "Int64",
	"deceleration_events": "Int64",
	"max_acceleration": "float64",
	"max_deceleration": "float64",
	"metres_per_minute": "float64",
	"percentage_max_speed_kph": "float64",
	"session_load": "float64",
}

STRING_COLUMNS: List[str] = [
	"athlete_gender_marker",
	"athlete_sport",
	"club_division",
]


def _validate_schema(df: pd.DataFrame) -> pd.DataFrame:
	missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
	if missing:
		raise ValueError(f"Input file is missing required columns: {missing}")

	return df[REQUIRED_COLUMNS].copy()


def _coerce_numeric_columns(df: pd.DataFrame) -> pd.DataFrame:
	for col, dtype in NUMERIC_COLUMNS.items():
		normalized = df[col].astype(str).str.replace(",", "", regex=False).str.strip()
		coerced = pd.to_numeric(normalized, errors="coerce")
		if dtype == "Int64":
			df[col] = coerced.round().astype("Int64")
		else:
			df[col] = coerced.astype(dtype)

	return df


def _clean_strings(df: pd.DataFrame) -> pd.DataFrame:
	for col in STRING_COLUMNS:
		df[col] = df[col].astype("string").str.strip().str.lower()
	return df


def ingest_data(input_path: str | Path = DEFAULT_INPUT_PATH) -> pd.DataFrame:
	"""Read raw athlete session data and return a cleaned, schema-validated dataframe."""
	path = Path(input_path)
	if not path.exists():
		raise FileNotFoundError(f"Input file not found: {path}")

	raw_df = pd.read_csv(path, dtype=str)
	cleaned_df = _validate_schema(raw_df)
	cleaned_df = _coerce_numeric_columns(cleaned_df)
	cleaned_df = _clean_strings(cleaned_df)

	cleaned_df = cleaned_df.dropna(subset=REQUIRED_COLUMNS)
	cleaned_df = cleaned_df.drop_duplicates().reset_index(drop=True)

	return cleaned_df


def main() -> None:
	df = ingest_data()
	print(f"Loaded clean dataframe with {len(df):,} rows and {len(df.columns)} columns.")


if __name__ == "__main__":
	main()
