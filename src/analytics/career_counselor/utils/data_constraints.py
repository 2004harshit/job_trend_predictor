"""
Data constraint handlers for general_job_data.

Known constraints in the Neon DB table:
  1. avg_salary / min_salary / max_salary  →  ~80% NULL (Naukri "not disclosed")
  2. no_of_applicant / no_of_opening       →  100% NULL (never scraped)
  3. timestamp vs posted_timestamp         →  always filter on posted_timestamp
                                               to avoid scraping-time bias

Every service MUST use the helpers here instead of writing raw pandas filters.
This keeps the constraint logic in one place so that when data quality improves,
we only change this file.
"""

from __future__ import annotations

import logging
from typing import Optional

import pandas as pd

logger = logging.getLogger(__name__)

# Minimum fraction of rows that must have salary data for us to report a salary
# statistic. Below this threshold we return availability=False so the UI can
# show "salary data insufficient" instead of a misleading number.
SALARY_MIN_COVERAGE = 0.10   # 10 %


# ---------------------------------------------------------------------------
# 1. Recency filter — always use posted_timestamp
# ---------------------------------------------------------------------------

def filter_by_recency(
    df: pd.DataFrame,
    days: int = 30,
    timestamp_col: str = "posted_timestamp",
) -> tuple[pd.DataFrame, dict]:
    """
    Return rows where posted_timestamp is within the last `days` days,
    plus a metadata dict that the API layer should include in every response
    so the Streamlit dashboard can warn users about data coverage gaps.

    Parameters
    ----------
    df : pd.DataFrame
        Full job dataframe (normalized columns).
    days : int
        Rolling window size in days.
    timestamp_col : str
        Always 'posted_timestamp' — never 'timestamp' (scrape time).

    Returns
    -------
    (filtered_df, coverage_meta)
    """
    if timestamp_col not in df.columns:
        # Graceful degradation: return full df with a warning
        logger.warning(
            "Column '%s' not found. Returning full dataset without recency filter.",
            timestamp_col,
        )
        return df, {
            "recency_filter_applied": False,
            "reason": f"column '{timestamp_col}' missing",
            "total_rows": len(df),
        }

    ts = pd.to_datetime(df[timestamp_col], errors="coerce")
    cutoff = pd.Timestamp.now() - pd.Timedelta(days=days)

    valid_ts = ts.notna()
    in_window = valid_ts & (ts >= cutoff)

    filtered = df[in_window].copy()

    # Compute actual date range in the FILTERED data
    if len(filtered) > 0 and valid_ts.any():
        actual_min = ts[in_window].min()
        actual_max = ts[in_window].max()
        actual_span = (actual_max - actual_min).days
    else:
        actual_min = actual_max = None
        actual_span = 0

    coverage_meta = {
        "recency_filter_applied": True,
        "requested_window_days": days,
        "actual_span_days": actual_span,
        "rows_before_filter": len(df),
        "rows_after_filter": len(filtered),
        "rows_missing_timestamp": int((~valid_ts).sum()),
        "earliest_posting": actual_min.isoformat() if actual_min else None,
        "latest_posting": actual_max.isoformat() if actual_max else None,
        # Warn Streamlit when fewer than 50% of requested window has data
        "coverage_warning": actual_span < (days * 0.5) if actual_span else True,
    }

    return filtered, coverage_meta


# ---------------------------------------------------------------------------
# 2. Salary — guard against 80% nulls
# ---------------------------------------------------------------------------

def salary_stats(
    df: pd.DataFrame,
    salary_col: str = "avg_salary",
) -> dict:
    """
    Compute salary statistics only from rows where salary is disclosed.
    Always returns a dict — callers must check `available` before using numbers.

    Returns
    -------
    {
        "available": bool,
        "sample_size": int,
        "coverage_pct": float,     # % of rows that disclosed salary
        "min": float | None,
        "p10": float | None,
        "p25": float | None,
        "median": float | None,
        "p75": float | None,
        "p90": float | None,
        "max": float | None,
        "mean": float | None,
        "note": str                # human-readable caveat for UI
    }
    """
    if salary_col not in df.columns or len(df) == 0:
        return _salary_unavailable("salary column missing or empty dataframe")

    disclosed = df[df[salary_col].notna() & (df[salary_col] > 0)]
    coverage = len(disclosed) / len(df)

    if coverage < SALARY_MIN_COVERAGE:
        return _salary_unavailable(
            f"only {coverage:.1%} of jobs in this filter disclosed salary "
            f"(threshold: {SALARY_MIN_COVERAGE:.0%})"
        )

    s = disclosed[salary_col].astype(float)
    return {
        "available": True,
        "sample_size": len(disclosed),
        "total_rows": len(df),
        "coverage_pct": round(coverage * 100, 1),
        "min": round(s.min(), 2),
        "p10": round(s.quantile(0.10), 2),
        "p25": round(s.quantile(0.25), 2),
        "median": round(s.median(), 2),
        "p75": round(s.quantile(0.75), 2),
        "p90": round(s.quantile(0.90), 2),
        "max": round(s.max(), 2),
        "mean": round(s.mean(), 2),
        "note": (
            f"Based on {len(disclosed):,} of {len(df):,} jobs that disclosed salary "
            f"({coverage:.0%} coverage). Figures in LPA."
        ),
    }


def _salary_unavailable(reason: str) -> dict:
    return {
        "available": False,
        "sample_size": 0,
        "coverage_pct": 0.0,
        "min": None, "p10": None, "p25": None,
        "median": None, "p75": None, "p90": None,
        "max": None, "mean": None,
        "note": f"Salary data not available: {reason}.",
    }


# ---------------------------------------------------------------------------
# 3. Fresher filter
# ---------------------------------------------------------------------------

def filter_freshers(df: pd.DataFrame, max_exp: float = 1.0) -> pd.DataFrame:
    """
    Return rows where min_experience <= max_exp (default 1 year).
    Rows with null min_experience are included (conservative: benefit of doubt).
    """
    if "min_experience" not in df.columns:
        return df
    mask = df["min_experience"].isna() | (df["min_experience"] <= max_exp)
    return df[mask].copy()


# ---------------------------------------------------------------------------
# 4. Location filter
# ---------------------------------------------------------------------------

# Cities that belong to "Jaipur" for location matching
JAIPUR_VARIANTS = {"jaipur", "jaipur, rajasthan", "jaipur rajasthan"}


def filter_location(df: pd.DataFrame, location: Optional[str]) -> pd.DataFrame:
    """
    Filter by location string. Case-insensitive substring match.
    If location is None or 'all', return full df.
    """
    if not location or location.strip().lower() in ("all", "national", ""):
        return df
    if "location" not in df.columns:
        return df
    loc_lower = location.strip().lower()
    mask = df["location"].str.lower().str.contains(loc_lower, na=False)
    return df[mask].copy()


# ---------------------------------------------------------------------------
# 5. Dropped / unreliable columns reminder
# ---------------------------------------------------------------------------

# These columns are in the DB but must NOT be used in any computation.
# Reference here so that code reviewers can catch accidental use.
DROPPED_COLUMNS = [
    "no_of_applicant",    # 100% null
    "no_of_opening",      # 100% null
    "timestamp",          # scrape time — use posted_timestamp instead
]