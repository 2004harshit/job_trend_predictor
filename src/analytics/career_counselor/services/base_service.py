"""
BaseService — shared foundation for all career counselor services.

Responsibilities
----------------
- Holds the job DataFrame (injected at construction time — no globals).
- Exposes filtered sub-DataFrames so every service starts from the same
  clean, constraint-aware slice.
- Provides `build_meta()` so every API response carries consistent metadata.

Design rule: NO business logic here. Only data access + filtering.
"""

from __future__ import annotations

import logging
from typing import Optional

import pandas as pd

from src.analytics.career_counselor.utils.data_constraints import (
    filter_by_recency,
    filter_freshers,
    filter_location,
    DROPPED_COLUMNS,
)

logger = logging.getLogger(__name__)


class BaseService:
    """
    Constructed once per request (lightweight — df is a reference, not a copy).

    Parameters
    ----------
    df : pd.DataFrame
        The normalized job dataframe returned by routes.get_analytics_data().
        All column names must already be lowercased and _cleaned-stripped.
    """

    # Columns we actively refuse to expose downstream
    _BLOCKED_COLS = set(DROPPED_COLUMNS)

    def __init__(self, df: pd.DataFrame) -> None:
        self._df = self._drop_blocked(df)
        logger.debug("BaseService initialized with %d rows", len(self._df))

    # ------------------------------------------------------------------
    # Core filtered accessors
    # ------------------------------------------------------------------

    def get_filtered(
        self,
        days: Optional[int] = 30,
        location: Optional[str] = None,
        fresher_only: bool = False,
        extra_dept_filter: Optional[str] = None,
    ) -> tuple[pd.DataFrame, dict]:
        """
        Return (filtered_df, coverage_meta) based on the standard set of
        sidebar controls that all 5 dashboard features share.

        Parameters
        ----------
        days : int | None
            Rolling window on posted_timestamp. None → no recency filter.
        location : str | None
            Location string (e.g. "Jaipur"). None / "all" → no location filter.
        fresher_only : bool
            If True, keep only rows where min_experience <= 1.
        extra_dept_filter : str | None
            Optional department/domain substring filter.

        Returns
        -------
        (df, meta)
            df   — filtered dataframe, ready for computation.
            meta — dict to include in API response metadata.
        """
        df = self._df.copy()
        meta: dict = {}

        # 1. Recency (most important — must come first to reduce dataset)
        if days is not None:
            df, recency_meta = filter_by_recency(df, days=days)
            meta["recency"] = recency_meta
        else:
            meta["recency"] = {"recency_filter_applied": False}

        # 2. Location
        df = filter_location(df, location)
        meta["location_filter"] = location or "all"

        # 3. Fresher
        if fresher_only:
            df = filter_freshers(df)
        meta["fresher_only"] = fresher_only

        # 4. Department / domain substring
        if extra_dept_filter and "department" in df.columns:
            mask = df["department"].str.lower().str.contains(
                extra_dept_filter.lower(), na=False
            )
            df = df[mask]
        meta["department_filter"] = extra_dept_filter or "all"

        meta["rows_used"] = len(df)
        return df, meta

    # ------------------------------------------------------------------
    # Metadata builder
    # ------------------------------------------------------------------

    @staticmethod
    def build_meta(
        coverage_meta: dict,
        total_rows: int,
        extra: Optional[dict] = None,
    ) -> dict:
        """
        Build the standard `metadata` block that wraps every API response.

        {
            "total_jobs_considered": int,
            "data_coverage": { ... recency info ... },
            "data_quality_warnings": [ ... ],
            ...extra...
        }
        """
        warnings: list[str] = []

        recency = coverage_meta.get("recency", {})
        if recency.get("coverage_warning"):
            warnings.append(
                "Actual posting data covers fewer days than requested window. "
                "Results may not represent the full period."
            )
        if recency.get("rows_missing_timestamp", 0) > 0:
            missing = recency["rows_missing_timestamp"]
            warnings.append(
                f"{missing:,} rows excluded due to missing posted_timestamp."
            )

        meta = {
            "total_jobs_considered": total_rows,
            "data_coverage": recency,
            "location_filter": coverage_meta.get("location_filter", "all"),
            "fresher_only": coverage_meta.get("fresher_only", False),
            "data_quality_warnings": warnings,
        }
        if extra:
            meta.update(extra)
        return meta

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _drop_blocked(self, df: pd.DataFrame) -> pd.DataFrame:
        """Remove columns that must never be used (null / misleading)."""
        cols_to_drop = [c for c in self._BLOCKED_COLS if c in df.columns]
        if cols_to_drop:
            logger.debug("BaseService dropping blocked columns: %s", cols_to_drop)
            df = df.drop(columns=cols_to_drop)
        return df

    @property
    def total_jobs(self) -> int:
        """Total jobs in the unfiltered (but blocked-col-dropped) dataframe."""
        return len(self._df)