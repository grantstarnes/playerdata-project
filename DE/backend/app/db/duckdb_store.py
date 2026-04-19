"""DuckDB store — seeded once from the CSV sources, re-seedable on demand.

The canonical table `sessions` mirrors the ingest.py schema. Re-seed by
deleting the DuckDB file or calling `seed_from_csvs(force=True)`.
"""

from __future__ import annotations

import logging
from pathlib import Path

import duckdb
import pandas as pd

from app.config import Settings, get_settings
from app.pipeline.ingest import ingest_data

log = logging.getLogger(__name__)

_SAMPLE_FILES = ["sample_data.csv", "legacy/sample_data.csv"]
_SYNTHETIC_FILES = [
    "synthetic/mens_synthetic_data.csv",
    "synthetic/womens_synthetic_data.csv",
]


def _load_all_csvs(data_dir: Path) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    for rel in _SAMPLE_FILES:
        path = data_dir / rel
        if path.exists():
            log.info("ingest (sample): %s", path)
            df = ingest_data(path)
            df["data_source"] = "sample"
            frames.append(df)
    for rel in _SYNTHETIC_FILES:
        path = data_dir / rel
        if path.exists():
            log.info("ingest (synthetic): %s", path)
            df = ingest_data(path)
            df["data_source"] = "synthetic"
            frames.append(df)
    if not frames:
        raise FileNotFoundError(f"No CSVs under {data_dir}")
    return pd.concat(frames, ignore_index=True).drop_duplicates().reset_index(drop=True)


def _connect(path: Path) -> duckdb.DuckDBPyConnection:
    path.parent.mkdir(parents=True, exist_ok=True)
    return duckdb.connect(str(path))


def seed_from_csvs(force: bool = False, settings: Settings | None = None) -> int:
    """Create/refresh the `sessions` table from CSVs. Returns row count."""
    s = settings or get_settings()
    con = _connect(s.duckdb_path)
    try:
        existing = con.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='sessions'"
        ).fetchone()
        if existing and not force:
            count = con.execute("SELECT COUNT(*) FROM sessions").fetchone()[0]
            log.info("duckdb seeded already (%d rows)", count)
            return count

        df = _load_all_csvs(s.data_dir)
        con.execute("DROP TABLE IF EXISTS sessions")
        con.register("sessions_df", df)
        con.execute("CREATE TABLE sessions AS SELECT * FROM sessions_df")
        con.unregister("sessions_df")
        count = con.execute("SELECT COUNT(*) FROM sessions").fetchone()[0]
        log.info("duckdb seeded: %d rows", count)
        return count
    finally:
        con.close()


def get_connection() -> duckdb.DuckDBPyConnection:
    """Caller-managed read-only connection. Close after use."""
    s = get_settings()
    return _connect(s.duckdb_path)
