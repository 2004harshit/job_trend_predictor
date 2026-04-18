"""
SalaryIntelligenceService
=========================
Salary analytics for the Career Counselor dashboard.

Key constraint: avg_salary / min_salary / max_salary are ~80% NULL in
general_job_data because Naukri marks most salaries as "not disclosed".
Every method is built around this reality:
  - salary_stats() from data_constraints is used everywhere.
  - Every response carries coverage_pct so the UI can show a caveat.
  - Methods that would produce meaningless results with <10% coverage
    return available=False instead of a number.

Methods
-------
    get_salary_ranges(domain, location, fresher_only, days)
        → salary distribution (p10–p90) for a domain+location slice

    get_jaipur_vs_national(domain, days)
        → side-by-side Jaipur vs national salary comparison

    get_top_10_percent_skills(domain, days, location)
        → skills most common among high-salary freshers in the domain

    get_salary_by_experience_band(domain, days, location)
        → salary at different experience levels (0-1, 1-3, 3-5 years)

Columns used
------------
    department, avg_salary, min_salary, max_salary,
    min_experience, max_experience, skills, location,
    company, posted_timestamp
"""

from __future__ import annotations

import logging
from collections import Counter
from typing import Optional

import pandas as pd

from src.analytics.career_counselor.services.base_service import BaseService
from src.analytics.career_counselor.utils.data_constraints import (
    salary_stats,
    filter_location,
    filter_freshers,
    SALARY_MIN_COVERAGE,
)
from src.analytics.career_counselor.utils.skill_utils import parse_skills
from src.analytics.career_counselor.utils.calculation_utils import safe_pct

logger = logging.getLogger(__name__)

# Experience bands for breakdown
_EXP_BANDS = [
    ("fresher (0–1 yr)", 0.0, 1.0),
    ("junior (1–3 yr)",  1.0, 3.0),
    ("mid (3–5 yr)",     3.0, 5.0),
]

# Jaipur salary is typically 30–45% lower than Bangalore national average.
# We surface this as a contextual note wherever relevant.
_JAIPUR_DISCOUNT_NOTE = (
    "Jaipur salaries are typically 30–45% lower than the national (Bangalore-weighted) "
    "average for equivalent roles. These figures reflect actual disclosed postings only."
)


class SalaryIntelligenceService(BaseService):
    """
    Usage
    -----
        svc = SalaryIntelligenceService(df)
        result = svc.get_salary_ranges(domain="Data Science", location="Jaipur")
    """

    # ------------------------------------------------------------------
    # 1. Salary ranges for a domain + location slice
    # ------------------------------------------------------------------

    def get_salary_ranges(
        self,
        domain: Optional[str] = None,
        location: Optional[str] = None,
        fresher_only: bool = True,
        days: Optional[int] = None,
    ) -> dict:
        """
        Return the salary distribution (p10, p25, median, p75, p90) for a
        domain + location slice.  Uses all available data (days=None by default)
        to maximise the salary sample size — salary data is too sparse for a
        30-day window to be meaningful.

        Response shape
        --------------
        {
            "domain": str | "all",
            "location": str | "all",
            "salary": {
                "available": bool,
                "sample_size": int,
                "coverage_pct": float,
                "min": float, "p10": float, "p25": float,
                "median": float, "p75": float, "p90": float, "max": float,
                "mean": float,
                "note": str
            },
            "metadata": { ... }
        }
        """
        df, coverage_meta = self.get_filtered(
            days=days,
            location=location,
            fresher_only=fresher_only,
            extra_dept_filter=domain,
        )

        sal = salary_stats(df)

        meta = self.build_meta(
            coverage_meta,
            len(df),
            extra={
                "domain": domain or "all",
                "salary_coverage_note": (
                    "Salary data uses all available history (not time-windowed) "
                    "to maximise the disclosed-salary sample."
                    if days is None else None
                ),
            },
        )

        return {
            "domain": domain or "all",
            "location": location or "all",
            "fresher_only": fresher_only,
            "salary": sal,
            "metadata": meta,
        }

    # ------------------------------------------------------------------
    # 2. Jaipur vs National comparison
    # ------------------------------------------------------------------

    def get_jaipur_vs_national(
        self,
        domain: Optional[str] = None,
        days: Optional[int] = None,
        fresher_only: bool = True,
    ) -> dict:
        """
        Side-by-side salary comparison: Jaipur slice vs national (no location filter).

        Response shape
        --------------
        {
            "domain": str | "all",
            "jaipur": { salary_stats dict },
            "national": { salary_stats dict },
            "comparison": {
                "median_diff_pct": float | None,   # (jaipur - national) / national * 100
                "jaipur_lower_by_pct": float | None,
                "note": str
            },
            "metadata": { ... }
        }
        """
        df_national, cov_national = self.get_filtered(
            days=days, fresher_only=fresher_only, extra_dept_filter=domain
        )
        df_jaipur = filter_location(df_national, "Jaipur")

        sal_national = salary_stats(df_national)
        sal_jaipur   = salary_stats(df_jaipur)

        comparison = _build_comparison(sal_jaipur, sal_national)

        meta = self.build_meta(
            cov_national,
            len(df_national),
            extra={
                "domain": domain or "all",
                "jaipur_job_count": len(df_jaipur),
                "national_job_count": len(df_national),
            },
        )

        return {
            "domain": domain or "all",
            "jaipur": sal_jaipur,
            "national": sal_national,
            "comparison": comparison,
            "metadata": meta,
        }

    # ------------------------------------------------------------------
    # 3. Top 10% skills — skills common among high-salary freshers
    # ------------------------------------------------------------------

    def get_top_10_percent_skills(
        self,
        domain: Optional[str] = None,
        days: Optional[int] = None,
        location: Optional[str] = None,
        top_n: int = 15,
    ) -> dict:
        """
        Find skills that appear most often in the top-10%-salary jobs within
        a domain.  These are signals for what commands a salary premium.

        Caveat: with 80% salary nulls, this compares disclosed-salary jobs
        only.  Survivorship bias possible — companies that disclose salary
        may not be representative.

        Response shape
        --------------
        {
            "domain": str | "all",
            "skills": [
                {
                    "skill": str,
                    "top10_pct_frequency": float,  # % of top-10% jobs with skill
                    "overall_frequency": float,     # % of all domain jobs with skill
                    "premium_signal": float         # top10_freq / overall_freq ratio
                },
                ...
            ],
            "salary_threshold": float | None,      # p90 cutoff used
            "sample_size": int,                    # # of top-10% jobs
            "metadata": { ... }
        }
        """
        df, coverage_meta = self.get_filtered(
            days=days,
            location=location,
            fresher_only=True,      # top-10% skills for freshers specifically
            extra_dept_filter=domain,
        )

        total_jobs = len(df)

        if "avg_salary" not in df.columns or df.empty:
            return self._empty_salary_response("top_10_percent_skills", domain, coverage_meta)

        disclosed = df[df["avg_salary"].notna() & (df["avg_salary"] > 0)].copy()
        coverage = len(disclosed) / total_jobs if total_jobs > 0 else 0

        if coverage < SALARY_MIN_COVERAGE or len(disclosed) < 10:
            return {
                "domain": domain or "all",
                "skills": [],
                "salary_threshold": None,
                "sample_size": 0,
                "available": False,
                "note": (
                    f"Only {len(disclosed)} jobs disclosed salary in this filter "
                    f"({coverage:.1%} coverage). Cannot compute top-10% reliably."
                ),
                "metadata": self.build_meta(coverage_meta, total_jobs),
            }

        p90_threshold = float(disclosed["avg_salary"].quantile(0.90))
        top_10_df = disclosed[disclosed["avg_salary"] >= p90_threshold]

        # Skill frequencies in top-10% jobs
        top10_counter = _count_skills_in_df(top_10_df)
        overall_counter = _count_skills_in_df(df)

        top10_total = len(top_10_df)
        skills_data = []

        for skill, top10_count in top10_counter.most_common(top_n * 2):
            top10_freq = safe_pct(top10_count, top10_total)
            overall_count = overall_counter.get(skill, 0)
            overall_freq = safe_pct(overall_count, total_jobs)
            # Premium signal: how much more common in top-10% vs overall
            premium = round(top10_freq / overall_freq, 2) if overall_freq > 0 else 0.0

            skills_data.append({
                "skill": skill,
                "top10_pct_frequency": top10_freq,
                "overall_frequency": overall_freq,
                "premium_signal": premium,
            })

        # Sort by premium signal (most differentiating skills first)
        skills_data.sort(key=lambda x: x["premium_signal"], reverse=True)
        skills_data = skills_data[:top_n]

        meta = self.build_meta(
            coverage_meta,
            total_jobs,
            extra={
                "domain": domain or "all",
                "disclosed_salary_jobs": len(disclosed),
                "salary_coverage_pct": round(coverage * 100, 1),
                "survivorship_bias_note": (
                    "Only jobs with disclosed salary are included. "
                    "Companies that disclose salary may not be representative."
                ),
            },
        )

        return {
            "domain": domain or "all",
            "skills": skills_data,
            "salary_threshold": round(p90_threshold, 2),
            "sample_size": top10_total,
            "available": True,
            "metadata": meta,
        }

    # ------------------------------------------------------------------
    # 4. Salary by experience band
    # ------------------------------------------------------------------

    def get_salary_by_experience_band(
        self,
        domain: Optional[str] = None,
        location: Optional[str] = None,
        days: Optional[int] = None,
    ) -> dict:
        """
        Salary stats split by experience band (fresher / junior / mid).
        Useful for students to understand salary trajectory.

        Response shape
        --------------
        {
            "domain": str | "all",
            "bands": [
                {
                    "band_label": str,      e.g. "fresher (0–1 yr)"
                    "min_exp": float,
                    "max_exp": float,
                    "salary": { salary_stats dict }
                },
                ...
            ],
            "metadata": { ... }
        }
        """
        df, coverage_meta = self.get_filtered(
            days=days, location=location, extra_dept_filter=domain
        )

        bands = []
        for label, min_exp, max_exp in _EXP_BANDS:
            band_df = _filter_by_exp_band(df, min_exp, max_exp)
            sal = salary_stats(band_df)
            bands.append({
                "band_label": label,
                "min_exp": min_exp,
                "max_exp": max_exp,
                "job_count": len(band_df),
                "salary": sal,
            })

        meta = self.build_meta(
            coverage_meta,
            len(df),
            extra={"domain": domain or "all"},
        )

        return {
            "domain": domain or "all",
            "location": location or "all",
            "bands": bands,
            "metadata": meta,
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _empty_salary_response(self, method: str, domain: Optional[str], meta: dict) -> dict:
        logger.warning("SalaryIntelligenceService.%s: empty or no salary col", method)
        return {
            "domain": domain or "all",
            "skills": [],
            "available": False,
            "note": "No salary data available for this filter.",
            "metadata": self.build_meta(meta, 0),
        }


# ---------------------------------------------------------------------------
# Module-level helpers
# ---------------------------------------------------------------------------

def _count_skills_in_df(df: pd.DataFrame) -> Counter:
    counter: Counter = Counter()
    if "skills" not in df.columns:
        return counter
    for raw in df["skills"]:
        counter.update(set(parse_skills(raw)))
    return counter


def _filter_by_exp_band(df: pd.DataFrame, min_exp: float, max_exp: float) -> pd.DataFrame:
    if "min_experience" not in df.columns:
        return df
    mask = (
        df["min_experience"].fillna(0) >= min_exp
    ) & (
        df["min_experience"].fillna(0) < max_exp
    )
    return df[mask].copy()


def _build_comparison(sal_jaipur: dict, sal_national: dict) -> dict:
    """
    Compute Jaipur vs National comparison delta.
    Both inputs are salary_stats() dicts.
    """
    if not sal_jaipur["available"] or not sal_national["available"]:
        return {
            "median_diff_pct": None,
            "jaipur_lower_by_pct": None,
            "available": False,
            "note": _JAIPUR_DISCOUNT_NOTE,
        }

    jaipur_median  = sal_jaipur["median"]
    national_median = sal_national["median"]

    if national_median and national_median > 0:
        diff_pct = round((jaipur_median - national_median) / national_median * 100, 1)
        lower_by = round(-diff_pct, 1) if diff_pct < 0 else 0.0
    else:
        diff_pct = None
        lower_by = None

    return {
        "jaipur_median": jaipur_median,
        "national_median": national_median,
        "median_diff_pct": diff_pct,
        "jaipur_lower_by_pct": lower_by,
        "available": True,
        "note": _JAIPUR_DISCOUNT_NOTE,
    }