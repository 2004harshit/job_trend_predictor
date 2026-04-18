"""
Pure calculation helpers — no pandas, no DB, no Flask.

All functions are stateless and independently testable.
"""

from __future__ import annotations

import math
from typing import Optional


# ---------------------------------------------------------------------------
# Momentum
# ---------------------------------------------------------------------------

def calculate_momentum(
    current_count: int,
    previous_count: int,
) -> dict:
    """
    Calculate percentage change between two periods and assign a trend label.

    Parameters
    ----------
    current_count : int
        Job / skill count in the current window.
    previous_count : int
        Job / skill count in the comparison (older) window.

    Returns
    -------
    {
        "change_pct": float,          # signed percentage, e.g. +23.5 or -8.0
        "trend": "up" | "down" | "stable",
        "arrow": "↑" | "↓" | "→",
    }

    Edge cases
    ----------
    - previous = 0, current > 0  → +100 % (new entrant)
    - previous > 0, current = 0  → -100 % (disappeared)
    - both 0                     → stable 0 %
    """
    if previous_count == 0 and current_count == 0:
        return {"change_pct": 0.0, "trend": "stable", "arrow": "→"}

    if previous_count == 0:
        return {"change_pct": 100.0, "trend": "up", "arrow": "↑"}

    pct = round(((current_count - previous_count) / previous_count) * 100, 2)

    if pct >= 5:
        trend, arrow = "up", "↑"
    elif pct <= -5:
        trend, arrow = "down", "↓"
    else:
        trend, arrow = "stable", "→"

    return {"change_pct": pct, "trend": trend, "arrow": arrow}


# ---------------------------------------------------------------------------
# Posting density (replaces "competition_score" — named honestly)
# ---------------------------------------------------------------------------

def posting_density(job_count: int, unique_companies: int) -> float:
    """
    How many postings exist per unique company in a domain.
    A high density means a few companies are posting a lot (concentrated demand).
    A low density means many companies each post a little (distributed demand).

    Named "posting_density" not "competition_score" because applicant data is
    unavailable; we cannot measure actual competition.

    Returns 0.0 if unique_companies is 0.
    """
    if unique_companies == 0:
        return 0.0
    return round(job_count / unique_companies, 2)


# ---------------------------------------------------------------------------
# Saturation score
# ---------------------------------------------------------------------------

def saturation_score(
    job_count: int,
    unique_companies: int,
    total_jobs_in_dataset: int,
) -> float:
    """
    Composite saturation score between 0.0 and 1.0.

    Formula (normalized)
    --------------------
        density_component = min(posting_density / 10, 1.0)
        volume_component  = min(job_count / total_jobs, 1.0) * (1 / 0.3)
        score = 0.6 * density_component + 0.4 * volume_component

    Interpretation
    --------------
    Higher score → domain is more concentrated (fewer companies posting many jobs).
    NOT the same as "hard to get a job in" — it measures posting concentration.

    Capped at 1.0.
    """
    if total_jobs_in_dataset == 0:
        return 0.0

    density = posting_density(job_count, unique_companies)
    density_component = min(density / 10.0, 1.0)

    volume_fraction = job_count / total_jobs_in_dataset
    # scale so that 30 % market share → ~1.0
    volume_component = min(volume_fraction / 0.30, 1.0)

    score = 0.6 * density_component + 0.4 * volume_component
    return round(min(score, 1.0), 4)


# ---------------------------------------------------------------------------
# Percentage helpers
# ---------------------------------------------------------------------------

def safe_pct(part: int | float, total: int | float, decimals: int = 2) -> float:
    """Return (part / total) * 100, or 0.0 if total is zero."""
    if not total:
        return 0.0
    return round((part / total) * 100, decimals)


def fresher_eligibility_pct(fresher_count: int, total_count: int) -> float:
    """Percentage of domain jobs that are fresher-eligible."""
    return safe_pct(fresher_count, total_count)


# ---------------------------------------------------------------------------
# Skill frequency helpers
# ---------------------------------------------------------------------------

def frequency_pct(skill_count: int, total_job_count: int) -> float:
    """
    In what percentage of jobs does this skill appear?
    skill_count  = number of jobs that list this skill.
    total_job_count = total jobs in the filtered set.
    """
    return safe_pct(skill_count, total_job_count)


# ---------------------------------------------------------------------------
# Momentum window splitter
# ---------------------------------------------------------------------------

def split_into_windows(
    df,                     # pd.DataFrame
    days: int,
    timestamp_col: str = "posted_timestamp",
):
    """
    Split df into (current_window, previous_window) where each window is `days` long.

    current  = last `days` days
    previous = `days` to `2*days` days ago

    Returns (current_df, previous_df). Either can be empty.
    """
    import pandas as pd  # local import keeps this module import-light

    ts = pd.to_datetime(df[timestamp_col], errors="coerce")
    now = pd.Timestamp.now()

    current_mask = ts >= (now - pd.Timedelta(days=days))
    previous_mask = (ts >= (now - pd.Timedelta(days=days * 2))) & (
        ts < (now - pd.Timedelta(days=days))
    )

    return df[current_mask].copy(), df[previous_mask].copy()