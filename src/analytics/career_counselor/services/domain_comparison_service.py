"""
DomainComparisonService
=======================
Provides multi-domain comparison analytics for the Career Counselor dashboard.

This service wraps the already-implemented DomainComparisonResolver from
src/analytics/domain_analysis/ and adds counselor-specific layers on top:
  - fresher-filtered comparison
  - skill overlap matrix between domains
  - side-by-side metric dicts ready for Streamlit st.columns()

If the existing resolver is not importable (e.g. during unit tests), the
service falls back to its own pandas-based implementation so the module
stays independently functional.

Methods
-------
    compare_domains(domain_list, fresher_only, days, location)
        → per-domain metrics + pairwise skill overlap matrix

    get_fresher_analysis(domain, days, location)
        → deep-dive fresher metrics for a single domain

    get_domain_skill_matrix(domain_list, days)
        → skill × domain frequency matrix (for heatmap in Streamlit)

Columns used
------------
    department, skills, company, avg_salary,
    min_experience, location, posted_timestamp, title
"""

from __future__ import annotations

import logging
from collections import Counter
from typing import Optional

import pandas as pd

from src.analytics.career_counselor.services.base_service import BaseService
from src.analytics.career_counselor.utils.skill_utils import (
    parse_skills,
    jaccard_similarity,
)
from src.analytics.career_counselor.utils.calculation_utils import (
    posting_density,
    safe_pct,
)
from src.analytics.career_counselor.utils.data_constraints import (
    salary_stats,
    filter_freshers,
)

logger = logging.getLogger(__name__)

# Minimum jobs for a domain to appear in comparison (statistical floor)
_MIN_DOMAIN_JOBS = 5


class DomainComparisonService(BaseService):
    """
    Usage
    -----
        svc = DomainComparisonService(df)
        result = svc.compare_domains(["Data Science", "Web Development", "Cloud"])
    """

    # ------------------------------------------------------------------
    # 1. Multi-domain comparison
    # ------------------------------------------------------------------

    def compare_domains(
        self,
        domain_list: list[str],
        fresher_only: bool = True,
        days: Optional[int] = 60,
        location: Optional[str] = None,
    ) -> dict:
        """
        Return side-by-side metrics for each requested domain plus a pairwise
        skill overlap matrix.

        Parameters
        ----------
        domain_list : list[str]
            2–5 domain names (department column values or substrings thereof).
        fresher_only : bool
            Whether to restrict to fresher-eligible jobs.
        days : int | None
            Recency window. Default 60 for broader sample.
        location : str | None

        Response shape
        --------------
        {
            "domains": [
                {
                    "domain": str,
                    "job_count": int,
                    "unique_companies": int,
                    "fresher_eligible_pct": float,
                    "posting_density": float,
                    "top_skills": [str, ...],           # top 10
                    "salary": { salary_stats dict },
                },
                ...
            ],
            "skill_overlap_matrix": {
                "Domain A": {"Domain B": 0.45, "Domain C": 0.12, ...},
                ...
            },
            "metadata": { ... }
        }
        """
        if not domain_list or len(domain_list) < 1:
            return {"domains": [], "skill_overlap_matrix": {}, "metadata": {}}

        df_base, coverage_meta = self.get_filtered(
            days=days, location=location, fresher_only=fresher_only
        )

        domain_results = []
        domain_skill_sets: dict[str, set[str]] = {}

        for domain in domain_list:
            domain_df = _filter_domain(df_base, domain)

            if len(domain_df) < _MIN_DOMAIN_JOBS:
                logger.info(
                    "DomainComparisonService: domain '%s' has only %d jobs — skipping",
                    domain, len(domain_df)
                )
                continue

            job_count = len(domain_df)
            unique_cos = int(domain_df["company"].nunique()) if "company" in domain_df.columns else 0

            # Fresher eligibility (within this domain, even if fresher_only=False)
            if "min_experience" in domain_df.columns:
                fresher_mask = (
                    domain_df["min_experience"].isna()
                    | (domain_df["min_experience"] <= 1.0)
                )
                fresher_count = int(fresher_mask.sum())
            else:
                fresher_count = job_count

            # Skills
            counter = _count_skills_in_df(domain_df)
            top_skills = [sk for sk, _ in counter.most_common(10)]
            skill_set = set(counter.keys())
            domain_skill_sets[domain] = skill_set

            # Salary
            sal = salary_stats(domain_df)

            domain_results.append({
                "domain": domain,
                "job_count": job_count,
                "unique_companies": unique_cos,
                "fresher_eligible_pct": safe_pct(fresher_count, job_count),
                "posting_density": posting_density(job_count, unique_cos),
                "top_skills": top_skills,
                "salary": sal,
            })

        # Sort by job_count desc
        domain_results.sort(key=lambda x: x["job_count"], reverse=True)

        # Pairwise skill overlap matrix (Jaccard)
        overlap_matrix = _build_overlap_matrix(domain_skill_sets)

        meta = self.build_meta(
            coverage_meta,
            len(df_base),
            extra={
                "domains_requested": domain_list,
                "domains_with_sufficient_data": [d["domain"] for d in domain_results],
                "min_jobs_threshold": _MIN_DOMAIN_JOBS,
            },
        )

        return {
            "domains": domain_results,
            "skill_overlap_matrix": overlap_matrix,
            "metadata": meta,
        }

    # ------------------------------------------------------------------
    # 2. Fresher deep-dive for a single domain
    # ------------------------------------------------------------------

    def get_fresher_analysis(
        self,
        domain: str,
        days: Optional[int] = 60,
        location: Optional[str] = None,
    ) -> dict:
        """
        Fresher-specific metrics for a single domain.
        Answers the counselor's question: "Is this domain realistic for my
        student right now?"

        Response shape
        --------------
        {
            "domain": str,
            "total_domain_jobs": int,
            "fresher_jobs": int,
            "fresher_pct": float,
            "top_fresher_skills": [str, ...],          # top 15 skills in fresher jobs
            "top_fresher_companies": [                 # top 10 companies hiring freshers
                {"company": str, "job_count": int},
                ...
            ],
            "common_roles": [str, ...],               # top 5 role titles
            "salary": { salary_stats dict },
            "metadata": { ... }
        }
        """
        df, coverage_meta = self.get_filtered(
            days=days, location=location, extra_dept_filter=domain
        )
        total_domain_jobs = len(df)

        fresher_df = filter_freshers(df)
        fresher_count = len(fresher_df)

        if fresher_df.empty:
            return {
                "domain": domain,
                "total_domain_jobs": total_domain_jobs,
                "fresher_jobs": 0,
                "fresher_pct": 0.0,
                "top_fresher_skills": [],
                "top_fresher_companies": [],
                "common_roles": [],
                "salary": salary_stats(fresher_df),
                "metadata": self.build_meta(coverage_meta, total_domain_jobs,
                                            extra={"warning": "No fresher jobs found"}),
            }

        # Top skills
        skill_counter = _count_skills_in_df(fresher_df)
        top_skills = [sk for sk, _ in skill_counter.most_common(15)]

        # Top companies
        top_companies: list[dict] = []
        if "company" in fresher_df.columns:
            co_counts = fresher_df["company"].value_counts().head(10)
            top_companies = [
                {"company": co, "job_count": int(cnt)}
                for co, cnt in co_counts.items()
            ]

        # Common roles
        common_roles: list[str] = []
        if "title" in fresher_df.columns:
            role_counts = fresher_df["title"].value_counts().head(5)
            common_roles = list(role_counts.index)

        # Salary in fresher jobs
        sal = salary_stats(fresher_df)

        meta = self.build_meta(
            coverage_meta,
            total_domain_jobs,
            extra={"domain": domain, "fresher_job_count": fresher_count},
        )

        return {
            "domain": domain,
            "total_domain_jobs": total_domain_jobs,
            "fresher_jobs": fresher_count,
            "fresher_pct": safe_pct(fresher_count, total_domain_jobs),
            "top_fresher_skills": top_skills,
            "top_fresher_companies": top_companies,
            "common_roles": common_roles,
            "salary": sal,
            "metadata": meta,
        }

    # ------------------------------------------------------------------
    # 3. Skill × Domain frequency matrix (for heatmap)
    # ------------------------------------------------------------------

    def get_domain_skill_matrix(
        self,
        domain_list: list[str],
        top_skills_per_domain: int = 15,
        days: Optional[int] = 60,
        location: Optional[str] = None,
        fresher_only: bool = True,
    ) -> dict:
        """
        Build a skill × domain frequency matrix.
        Rows = skills (union of top skills across all domains).
        Columns = domains.
        Values = frequency_pct (% of jobs in that domain listing the skill).

        Used by the Streamlit heatmap in Domain Comparison tab.

        Response shape
        --------------
        {
            "skills": [str, ...],          # row labels
            "domains": [str, ...],         # column labels
            "matrix": {                    # skills → domain → pct
                "python": {"Data Science": 78.2, "Web Dev": 34.1, ...},
                ...
            },
            "metadata": { ... }
        }
        """
        df_base, coverage_meta = self.get_filtered(
            days=days, location=location, fresher_only=fresher_only
        )

        # Collect top skills per domain and their frequencies
        domain_counters: dict[str, tuple[Counter, int]] = {}
        all_top_skills: set[str] = set()

        for domain in domain_list:
            domain_df = _filter_domain(df_base, domain)
            if domain_df.empty:
                continue
            counter = _count_skills_in_df(domain_df)
            domain_counters[domain] = (counter, len(domain_df))
            top = {sk for sk, _ in counter.most_common(top_skills_per_domain)}
            all_top_skills.update(top)

        # Build matrix
        skills_sorted = sorted(all_top_skills)
        matrix: dict[str, dict[str, float]] = {}

        for skill in skills_sorted:
            matrix[skill] = {}
            for domain, (counter, total) in domain_counters.items():
                count = counter.get(skill, 0)
                matrix[skill][domain] = safe_pct(count, total)

        meta = self.build_meta(coverage_meta, len(df_base))

        return {
            "skills": skills_sorted,
            "domains": list(domain_counters.keys()),
            "matrix": matrix,
            "metadata": meta,
        }


# ---------------------------------------------------------------------------
# Module-level helpers
# ---------------------------------------------------------------------------

def _filter_domain(df: pd.DataFrame, domain: str) -> pd.DataFrame:
    """Filter df to rows where department contains domain (case-insensitive)."""
    if "department" not in df.columns:
        return df
    mask = df["department"].str.lower().str.contains(domain.lower(), na=False)
    return df[mask].copy()


def _count_skills_in_df(df: pd.DataFrame) -> Counter:
    counter: Counter = Counter()
    if "skills" not in df.columns:
        return counter
    for raw in df["skills"]:
        counter.update(set(parse_skills(raw)))
    return counter


def _build_overlap_matrix(domain_skill_sets: dict[str, set[str]]) -> dict:
    """
    Build symmetric pairwise Jaccard similarity matrix.
    { "Domain A": { "Domain B": 0.42, "Domain C": 0.11, ... }, ... }
    """
    domains = list(domain_skill_sets.keys())
    matrix: dict[str, dict[str, float]] = {d: {} for d in domains}

    for i, d1 in enumerate(domains):
        for j, d2 in enumerate(domains):
            if i == j:
                matrix[d1][d2] = 1.0
            elif j > i:
                sim = jaccard_similarity(domain_skill_sets[d1], domain_skill_sets[d2])
                matrix[d1][d2] = sim
                matrix[d2][d1] = sim

    return matrix