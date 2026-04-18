"""
src/api/data_loader.py
======================
Single source of truth for loading job data.

The active tier is controlled by the DATA_SOURCE environment variable
which is set by run.py via the --db argument:

    DATA_SOURCE=csv      → CSV file only
    DATA_SOURCE=neon     → Neon PostgreSQL only (no fallback)
    DATA_SOURCE=postgres → Local PostgreSQL only (no fallback)
    DATA_SOURCE=auto     → Neon → Local PG → CSV  (original 3-tier waterfall)

If the requested source fails, a clear error is raised so the developer
knows exactly what went wrong instead of silently loading sample data.

Public API
----------
    get_job_data()       → pd.DataFrame  (cached after first load)
    reload_job_data()    → pd.DataFrame  (force reload, clears cache)
"""

from __future__ import annotations

import logging
import os
import pandas as pd
from functools import lru_cache
from typing import Optional

logger = logging.getLogger(__name__)

# ── column normalisation (shared by both features) ────────────────────────────

def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize raw column names to a canonical lowercase snake_case form."""
    df = df.copy()
    mapping = {}
    for col in df.columns:
        new = col.lower()
        if new.endswith("_cleaned"):
            new = new[:-8]
        if "no of job opening" in new:
            new = "no_of_openings"
        elif "no of applicant" in new:
            new = "no_of_applicants"
        elif "job_type"       in new: new = "job_type"
        elif "posted_date"    in new: new = "posted_date"
        elif "scraped_at"     in new: new = "scraped_at"
        elif "min_experience" in new: new = "min_experience"
        elif "max_experience" in new: new = "max_experience"
        elif "salary_lakhs"   in new: new = "salary_lakhs"
        elif "company"        in new: new = "company"
        elif "location"       in new: new = "location"
        elif "skills"         in new: new = "skills"
        mapping[col] = new
    return df.rename(columns=mapping)


# ── individual loaders ────────────────────────────────────────────────────────

def _load_neon() -> pd.DataFrame:
    """Load from Neon cloud PostgreSQL using NEON_URL from environment."""
    url = os.environ.get("NEON_URL", "").strip()
    if not url:
        raise ValueError("NEON_URL environment variable is not set")
    from sqlalchemy import create_engine
    engine = create_engine(url, connect_args={"connect_timeout": 15})
    df = pd.read_sql("SELECT * FROM general_job_data;", engine)
    logger.info(f"[neon] Loaded {len(df)} records")
    return df


def _load_local_postgres() -> pd.DataFrame:
    """
    Load from a local / self-hosted PostgreSQL.
    Configure via environment variables:
        LOCAL_PG_HOST     (default: localhost)
        LOCAL_PG_PORT     (default: 5432)
        LOCAL_PG_DB       (default: job_trend_db)
        LOCAL_PG_USER     (default: postgres)
        LOCAL_PG_PASSWORD (required)
    """
    from sqlalchemy import create_engine
    host     = os.environ.get("LOCAL_PG_HOST",     "localhost")
    port     = os.environ.get("LOCAL_PG_PORT",     "5432")
    db       = os.environ.get("LOCAL_PG_DB",       "job_trend_db")
    user     = os.environ.get("LOCAL_PG_USER",     "postgres")
    password = os.environ.get("LOCAL_PG_PASSWORD", "")
    if not password:
        raise ValueError("LOCAL_PG_PASSWORD environment variable is not set")
    url    = f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{db}"
    engine = create_engine(url, connect_args={"connect_timeout": 10})
    df     = pd.read_sql("SELECT * FROM general_job_data;", engine)
    logger.info(f"[postgres] Loaded {len(df)} records from {host}:{port}/{db}")
    return df


def _load_csv() -> pd.DataFrame:
    """
    Load from a CSV file.  Search order:
      1. CSV_PATH env var  (set this on Render or any server)
      2. <project_root>/data/processed/cleaned/cleaned_data.csv
      3. <project_root>/data/processed/cleaned/cleaned_job_data.csv
    """
    env_path = os.environ.get("CSV_PATH", "").strip().strip('"').strip("'")
    if env_path and os.path.exists(env_path):
        df = pd.read_csv(env_path)
        logger.info(f"[csv] Loaded {len(df)} records from CSV_PATH: {env_path}")
        return df

    # walk up from this file to the project root  (src/api/data_loader.py → 3 levels up)
    root     = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    base_dir = os.path.join(root, "data", "processed", "cleaned")
    for fname in ("cleaned_data.csv", "cleaned_job_data.csv"):
        path = os.path.join(base_dir, fname)
        if os.path.exists(path):
            df = pd.read_csv(path)
            logger.info(f"[csv] Loaded {len(df)} records from: {path}")
            return df

    raise FileNotFoundError(
        "CSV file not found. Tried:\n"
        f"  CSV_PATH env var : '{env_path}'\n"
        f"  {os.path.join(base_dir, 'cleaned_data.csv')}\n"
        f"  {os.path.join(base_dir, 'cleaned_job_data.csv')}\n"
        "Set the CSV_PATH environment variable to the absolute path of your CSV."
    )


# ── main public function ──────────────────────────────────────────────────────

_cached_df: Optional[pd.DataFrame] = None


def get_job_data() -> pd.DataFrame:
    """
    Return the job DataFrame, loading it on first call and caching thereafter.
    Which source is used is controlled by the DATA_SOURCE environment variable.
    """
    global _cached_df
    if _cached_df is not None:
        return _cached_df

    source = os.environ.get("DATA_SOURCE", "csv").lower()
    logger.info(f"Loading job data — source: {source}")

    if source == "neon":
        df = _load_neon()

    elif source == "postgres":
        df = _load_local_postgres()

    elif source == "csv":
        df = _load_csv()

    elif source == "auto":
        # Legacy 3-tier waterfall (used when DATA_SOURCE is not explicitly set)
        for loader, name in [(_load_neon, "neon"), (_load_local_postgres, "postgres"), (_load_csv, "csv")]:
            try:
                df = loader()
                logger.info(f"[auto] Using {name}")
                break
            except Exception as err:
                logger.warning(f"[auto] {name} failed: {err}")
        else:
            raise RuntimeError("All data sources failed in auto mode")
    else:
        raise ValueError(f"Unknown DATA_SOURCE='{source}'. Use: csv, neon, postgres, auto")

    _cached_df = normalize_columns(df)
    logger.info(f"Job data ready — {len(_cached_df)} rows, {len(_cached_df.columns)} columns")
    return _cached_df


def reload_job_data() -> pd.DataFrame:
    """Force a fresh load (clears the cache)."""
    global _cached_df
    _cached_df = None
    return get_job_data()