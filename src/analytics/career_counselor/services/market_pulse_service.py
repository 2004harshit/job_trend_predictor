"""
MarketPulseService
==================
Implements the four Market Pulse analytics methods:

    1. get_top_domains(limit, days)         → top domains by job count
    2. get_skill_frequency(top_n, days)     → most demanded skills
    3. get_momentum_badges(skills, days)    → rising / falling skill trends
    4. get_saturation_indicators(days)      → posting concentration per domain

Data contract (columns expected from BaseService / normalized df)
-----------------------------------------------------------------
    department          TEXT    — domain / category bucket
    skills              TEXT    — pipe/comma separated raw skill string
    company             TEXT    — hiring company name
    posted_timestamp    TEXT    — ISO date string of when job was posted
    min_experience      FLOAT   — years (0 = fresher)
    avg_salary          FLOAT   — may be null (~80% of rows)
    location            TEXT    — city string

Columns intentionally NOT used
--------------------------------
    no_of_applicant     — 100% null
    no_of_opening       — 100% null
    timestamp           — scrape time, biased; use posted_timestamp

Author: Career Counselor Module
"""

from __future__ import annotations

import logging
from collections import Counter
from typing import Optional

import pandas as pd

from src.analytics.career_counselor.services.base_service import BaseService
from src.analytics.career_counselor.utils.skill_utils import parse_skills
from src.analytics.career_counselor.utils.calculation_utils import (
    calculate_momentum,
    saturation_score,
    safe_pct,
    split_into_windows,
)
from src.analytics.career_counselor.utils.data_constraints import salary_stats

logger = logging.getLogger(__name__)


class MarketPulseService(BaseService):
    """
    High-level analytics for the "Live Market Pulse" dashboard tab.

    Usage
    -----
        df = get_analytics_data()          # from routes.py helper
        svc = MarketPulseService(df)
        result = svc.get_top_domains(limit=10, days=30)
    """

    # ------------------------------------------------------------------
    # 1. Top Domains
    # ------------------------------------------------------------------

    def get_top_domains(
        self,
        limit: int = 10,
        days: int = 30,
        location: Optional[str] = None,
        fresher_only: bool = False,
    ) -> dict:
        """
        Return the top `limit` domains ranked by job count in the window.

        Response shape
        --------------
        {
            "domains": [
                {
                    "domain": str,
                    "job_count": int,
                    "percentage": float,        # share of total jobs in filter
                    "unique_companies": int,
                    "fresher_eligible_pct": float,
                    "avg_salary": dict          # from salary_stats(), may be unavailable
                },
                ...
            ],
            "total_jobs": int,
            "metadata": { ... }
        }
        """
        df, coverage_meta = self.get_filtered(
            days=days, location=location, fresher_only=fresher_only
        )

        if df.empty or "department" not in df.columns:
            return self._empty_response("top_domains", coverage_meta)

        total_jobs = len(df)
        results = []

        domain_groups = df.groupby("department", dropna=True)

        for domain, group in domain_groups:
            job_count = len(group)

            # Fresher eligibility within this domain
            if "min_experience" in group.columns:
                fresher_mask = group["min_experience"].isna() | (
                    group["min_experience"] <= 1.0
                )
                fresher_count = int(fresher_mask.sum())
            else:
                fresher_count = 0

            # Unique companies
            unique_cos = (
                int(group["company"].nunique())
                if "company" in group.columns
                else 0
            )

            # Salary (constraint-aware)
            sal = salary_stats(group)

            results.append({
                "domain": domain,
                "job_count": job_count,
                "percentage": safe_pct(job_count, total_jobs),
                "unique_companies": unique_cos,
                "fresher_eligible_pct": safe_pct(fresher_count, job_count),
                "avg_salary": sal,
            })

        # Sort by job count descending, slice to limit
        results.sort(key=lambda x: x["job_count"], reverse=True)
        results = results[:limit]

        meta = self.build_meta(
            coverage_meta,
            total_jobs,
            extra={"limit": limit, "total_domains_found": len(domain_groups)},
        )

        return {
            "domains": results,
            "total_jobs": total_jobs,
            "metadata": meta,
        }

    # ------------------------------------------------------------------
    # 2. Skill Frequency
    # ------------------------------------------------------------------

    def get_skill_frequency(
        self,
        top_n: int = 20,
        days: int = 30,
        location: Optional[str] = None,
        fresher_only: bool = False,
        domain: Optional[str] = None,
    ) -> dict:
        """
        Count how often each normalized skill appears across job postings
        in the filtered window.

        A skill "appears" in a job if it is present in that job's skills list —
        we count jobs-containing-skill, NOT raw skill mentions (to avoid
        one verbose posting inflating numbers).

        Response shape
        --------------
        {
            "skills": [
                {
                    "skill": str,
                    "job_count": int,           # jobs that list this skill
                    "frequency_pct": float,     # % of total filtered jobs
                    "rank": int
                },
                ...
            ],
            "total_jobs": int,
            "metadata": { ... }
        }
        """
        df, coverage_meta = self.get_filtered(
            days=days,
            location=location,
            fresher_only=fresher_only,
            extra_dept_filter=domain,
        )

        if df.empty or "skills" not in df.columns:
            return self._empty_response("skill_frequency", coverage_meta)

        total_jobs = len(df)

        # Count jobs-per-skill (not raw mentions)
        skill_job_counter: Counter = Counter()

        for raw_skills in df["skills"]:
            # parse_skills deduplicates within a single posting
            unique_in_job = set(parse_skills(raw_skills))
            skill_job_counter.update(unique_in_job)

        top_skills = skill_job_counter.most_common(top_n)

        results = [
            {
                "skill": skill,
                "job_count": count,
                "frequency_pct": safe_pct(count, total_jobs),
                "rank": rank + 1,
            }
            for rank, (skill, count) in enumerate(top_skills)
        ]

        meta = self.build_meta(
            coverage_meta,
            total_jobs,
            extra={
                "top_n": top_n,
                "total_unique_skills_found": len(skill_job_counter),
                "domain_filter": domain or "all",
            },
        )

        return {
            "skills": results,
            "total_jobs": total_jobs,
            "metadata": meta,
        }

    # ------------------------------------------------------------------
    # 3. Momentum Badges
    # ------------------------------------------------------------------

    def get_momentum_badges(
        self,
        skills_list: Optional[list[str]] = None,
        days: int = 30,
        location: Optional[str] = None,
        top_n_auto: int = 20,
    ) -> dict:
        """
        Compare skill demand between [current window] and [previous window]
        of equal length (days) to compute rising / falling / stable badges.

        If `skills_list` is provided, compute momentum only for those skills.
        If None, auto-select the top `top_n_auto` skills from the current window.

        Windows
        -------
            current  = last `days` days (by posted_timestamp)
            previous = `days` to `2 * days` ago

        Response shape
        --------------
        {
            "badges": [
                {
                    "skill": str,
                    "current_count": int,
                    "previous_count": int,
                    "change_pct": float,
                    "trend": "up" | "down" | "stable",
                    "arrow": "↑" | "↓" | "→",
                    "comparison_window_days": int
                },
                ...
            ],
            "window_days": int,
            "metadata": { ... }
        }

        Caveats returned in metadata
        ----------------------------
        - If previous window is very sparse (< 30 jobs), momentum is unreliable.
        - Scraping time inconsistency bias: if data was scraped in bursts, the
          two windows may have different base rates. We report both window job
          totals so the UI can show a caveat.
        """
        # We need the raw df with timestamps — apply only location filter here
        df_loc = filter_location_inline(self._df, location)

        if df_loc.empty or "posted_timestamp" not in df_loc.columns:
            return self._empty_response("momentum_badges", {})

        current_df, prev_df = split_into_windows(df_loc, days=days)

        # Build skill counters for each window
        current_counts = _count_skills(current_df)
        prev_counts = _count_skills(prev_df)

        # Determine skill set to badge
        if skills_list:
            from src.analytics.career_counselor.utils.skill_utils import normalize_skill
            target_skills = [normalize_skill(s.lower()) for s in skills_list]
        else:
            # Auto-pick top skills from current window
            target_skills = [
                skill for skill, _ in current_counts.most_common(top_n_auto)
            ]

        if not target_skills:
            return self._empty_response("momentum_badges", {})

        badges = []
        for skill in target_skills:
            curr = current_counts.get(skill, 0)
            prev = prev_counts.get(skill, 0)
            momentum = calculate_momentum(curr, prev)
            badges.append({
                "skill": skill,
                "current_count": curr,
                "previous_count": prev,
                "change_pct": momentum["change_pct"],
                "trend": momentum["trend"],
                "arrow": momentum["arrow"],
                "comparison_window_days": days,
            })

        # Sort: biggest movers first (absolute change_pct)
        badges.sort(key=lambda b: abs(b["change_pct"]), reverse=True)

        # Build metadata with bias warning
        current_total = len(current_df)
        prev_total = len(prev_df)
        warnings = []
        if prev_total < 30:
            warnings.append(
                f"Previous window has only {prev_total} jobs — "
                "momentum figures may be unreliable."
            )
        if current_total == 0:
            warnings.append("No jobs found in current window.")

        # Scraping bias check: warn if windows differ by >40% in total size
        if current_total > 0 and prev_total > 0:
            ratio = max(current_total, prev_total) / min(current_total, prev_total)
            if ratio > 1.4:
                warnings.append(
                    f"Current window ({current_total} jobs) and previous window "
                    f"({prev_total} jobs) differ significantly — scraping volume "
                    "inconsistency may bias trend signals."
                )

        meta = {
            "current_window_jobs": current_total,
            "previous_window_jobs": prev_total,
            "window_days": days,
            "location_filter": location or "all",
            "data_quality_warnings": warnings,
            "note": (
                "Momentum compares the last N days vs the preceding N days "
                "using posted_timestamp (not scrape time)."
            ),
        }

        return {
            "badges": badges,
            "window_days": days,
            "metadata": meta,
        }

    # ------------------------------------------------------------------
    # 4. Saturation Indicators
    # ------------------------------------------------------------------

    def get_saturation_indicators(
        self,
        days: int = 30,
        location: Optional[str] = None,
        min_jobs: int = 10,
    ) -> dict:
        """
        For each domain, compute a saturation score that indicates how
        concentrated (vs distributed) the job postings are.

        High saturation → few companies posting many jobs (concentrated demand).
        Low saturation  → many companies each posting a little (distributed).

        This is NOT a measure of "hard to get a job" — applicant data is
        unavailable. The UI must label this correctly.

        Parameters
        ----------
        min_jobs : int
            Domains with fewer than `min_jobs` postings in the window are
            excluded (insufficient data for a meaningful score).

        Response shape
        --------------
        {
            "indicators": [
                {
                    "domain": str,
                    "job_count": int,
                    "unique_companies": int,
                    "posting_density": float,   # jobs / companies
                    "saturation_score": float,  # 0.0–1.0
                    "interpretation": str       # human-readable label
                },
                ...
            ],
            "total_jobs": int,
            "metadata": { ... }
        }
        """
        df, coverage_meta = self.get_filtered(days=days, location=location)

        if df.empty or "department" not in df.columns:
            return self._empty_response("saturation_indicators", coverage_meta)

        total_jobs = len(df)
        results = []

        for domain, group in df.groupby("department", dropna=True):
            job_count = len(group)
            if job_count < min_jobs:
                continue

            unique_cos = (
                int(group["company"].nunique())
                if "company" in group.columns
                else 1
            )

            density = round(job_count / max(unique_cos, 1), 2)
            score = saturation_score(job_count, unique_cos, total_jobs)
            interpretation = _saturation_label(score)

            results.append({
                "domain": domain,
                "job_count": job_count,
                "unique_companies": unique_cos,
                "posting_density": density,
                "saturation_score": score,
                "interpretation": interpretation,
            })

        # Sort by saturation score descending (most saturated first)
        results.sort(key=lambda x: x["saturation_score"], reverse=True)

        meta = self.build_meta(
            coverage_meta,
            total_jobs,
            extra={
                "min_jobs_threshold": min_jobs,
                "domains_included": len(results),
                "saturation_note": (
                    "Saturation score measures posting concentration — "
                    "not actual competition (applicant data unavailable)."
                ),
            },
        )

        return {
            "indicators": results,
            "total_jobs": total_jobs,
            "metadata": meta,
        }

    # ------------------------------------------------------------------
    # Snapshot helper (used by the 4-metric header cards in Streamlit)
    # ------------------------------------------------------------------

    def get_snapshot(
        self,
        days: int = 30,
        location: Optional[str] = None,
        fresher_only: bool = False,
    ) -> dict:
        """
        Return the four headline numbers for the Market Pulse metric cards:
            - total_jobs
            - active_domains
            - top_skill         (most frequent skill)
            - salary_snapshot   (from data_constraints.salary_stats)

        Response shape
        --------------
        {
            "total_jobs": int,
            "active_domains": int,
            "top_skill": str | None,
            "salary_snapshot": dict,    # from salary_stats()
            "metadata": { ... }
        }
        """
        df, coverage_meta = self.get_filtered(
            days=days, location=location, fresher_only=fresher_only
        )

        if df.empty:
            return {
                "total_jobs": 0,
                "active_domains": 0,
                "top_skill": None,
                "salary_snapshot": salary_stats(df),
                "metadata": self.build_meta(coverage_meta, 0),
            }

        total_jobs = len(df)
        active_domains = (
            int(df["department"].nunique()) if "department" in df.columns else 0
        )

        # Top skill
        skill_counter: Counter = Counter()
        if "skills" in df.columns:
            for raw in df["skills"]:
                skill_counter.update(set(parse_skills(raw)))
        top_skill = skill_counter.most_common(1)[0][0] if skill_counter else None

        sal = salary_stats(df)

        meta = self.build_meta(coverage_meta, total_jobs)

        return {
            "total_jobs": total_jobs,
            "active_domains": active_domains,
            "top_skill": top_skill,
            "salary_snapshot": sal,
            "metadata": meta,
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _empty_response(self, method_name: str, coverage_meta: dict) -> dict:
        logger.warning(
            "MarketPulseService.%s: empty dataframe or missing required column.",
            method_name,
        )
        return {
            "data": [],
            "total_jobs": 0,
            "metadata": self.build_meta(
                coverage_meta, 0,
                extra={"warning": f"No data available for {method_name}"}
            ),
        }


# ---------------------------------------------------------------------------
# Module-level helpers (not methods — used by multiple services)
# ---------------------------------------------------------------------------

def _count_skills(df: pd.DataFrame) -> Counter:
    """Count skill occurrences across a dataframe's skills column."""
    counter: Counter = Counter()
    if df.empty or "skills" not in df.columns:
        return counter
    for raw in df["skills"]:
        counter.update(set(parse_skills(raw)))
    return counter


def _saturation_label(score: float) -> str:
    if score >= 0.75:
        return "Highly concentrated — few companies dominate postings"
    elif score >= 0.50:
        return "Moderately concentrated"
    elif score >= 0.25:
        return "Distributed — multiple companies hiring"
    else:
        return "Highly distributed — broad market participation"


def filter_location_inline(df: pd.DataFrame, location: Optional[str]) -> pd.DataFrame:
    """Thin wrapper so momentum method can apply location without full filter chain."""
    from src.analytics.career_counselor.utils.data_constraints import filter_location
    return filter_location(df, location)