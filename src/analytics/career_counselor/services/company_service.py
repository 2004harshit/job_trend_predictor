"""
CompanyIntelligenceService
==========================
Company-level hiring analytics for the Career Counselor dashboard.

Methods
-------
    get_top_hiring_companies(domain, fresher_only, limit, days, location)
        → ranked companies by job count

    get_company_type_split(domain, days, location)
        → Service vs Product vs Startup % breakdown

    get_hiring_frequency(company, days)
        → posting cadence for a specific company

    get_jaipur_companies(domain, days)
        → Jaipur-specific company hiring table

Note on null columns
--------------------
    no_of_applicant and no_of_opening are 100% null — not used anywhere.
    avg_salary is included per-company but always routed through salary_stats()
    with its null-guard so the UI sees "unavailable" rather than 0.

Company type classification
---------------------------
There is no "company_type" column in the DB.  We infer type from company
name keywords.  This is approximate — the UI must label it as estimated.

    Product companies  → known product co names or "technologies", "labs",
                         "systems", "software" suffix patterns
    Startups           → very low job count (<= 3 in window) or name patterns
    Service companies  → default category (TCS, Infosys, Wipro, Accenture etc.)

Columns used
------------
    company, department, location, min_experience,
    avg_salary, title, skills, posted_timestamp
"""

from __future__ import annotations

import logging
import re
from collections import Counter
from typing import Optional

import pandas as pd

from src.analytics.career_counselor.services.base_service import BaseService
from src.analytics.career_counselor.utils.data_constraints import (
    salary_stats,
    filter_location,
    filter_freshers,
)
from src.analytics.career_counselor.utils.skill_utils import parse_skills
from src.analytics.career_counselor.utils.calculation_utils import safe_pct

logger = logging.getLogger(__name__)

# Known large Indian IT service companies (lower-cased, substring match)
_SERVICE_COMPANY_SIGNALS = {
    "tcs", "infosys", "wipro", "hcl", "tech mahindra", "cognizant",
    "capgemini", "accenture", "mphasis", "ltimindtree", "lti",
    "hexaware", "niit", "sonata", "mastech", "cyient", "persistent",
    "birlasoft", "zensar", "coforge", "kpit",
}

# Signals that suggest a product-oriented company
_PRODUCT_SIGNALS = re.compile(
    r"\b(technologies|labs|systems|platforms|solutions|ai|analytics|"
    r"networks|semiconductor|embedded|iot|saas|fintech|edtech|healthtech)\b",
    re.IGNORECASE,
)

# Low posting count that might indicate startup
_STARTUP_MAX_JOBS = 3


class CompanyIntelligenceService(BaseService):
    """
    Usage
    -----
        svc = CompanyIntelligenceService(df)
        result = svc.get_top_hiring_companies(domain="Data Science", fresher_only=True)
    """

    # ------------------------------------------------------------------
    # 1. Top hiring companies
    # ------------------------------------------------------------------

    def get_top_hiring_companies(
        self,
        domain: Optional[str] = None,
        fresher_only: bool = False,
        limit: int = 15,
        days: int = 30,
        location: Optional[str] = None,
    ) -> dict:
        """
        Return the top `limit` companies by job count in the filtered window.

        Response shape
        --------------
        {
            "companies": [
                {
                    "company": str,
                    "job_count": int,
                    "fresher_jobs": int,
                    "fresher_pct": float,
                    "unique_roles": int,
                    "estimated_type": "Service" | "Product" | "Startup",
                    "salary": { salary_stats dict },
                    "top_skills": [str, ...],           # top 5
                    "locations": [str, ...],            # unique locations hiring
                },
                ...
            ],
            "total_jobs": int,
            "metadata": { ... }
        }
        """
        df, coverage_meta = self.get_filtered(
            days=days, location=location, fresher_only=fresher_only,
            extra_dept_filter=domain,
        )

        if df.empty or "company" not in df.columns:
            return self._empty_response("top_hiring_companies", coverage_meta)

        total_jobs = len(df)
        results = []

        for company, group in df.groupby("company", dropna=True):
            job_count = len(group)

            # Fresher jobs within this company
            fresher_df = filter_freshers(group)
            fresher_count = len(fresher_df)

            # Unique role titles
            unique_roles = (
                int(group["title"].nunique()) if "title" in group.columns else 0
            )

            # Salary
            sal = salary_stats(group)

            # Top skills
            skill_counter: Counter = Counter()
            for raw in group.get("skills", pd.Series(dtype=str)):
                skill_counter.update(set(parse_skills(raw)))
            top_skills = [sk for sk, _ in skill_counter.most_common(5)]

            # Unique locations this company is hiring in
            locations: list[str] = []
            if "location" in group.columns:
                locations = list(group["location"].dropna().unique())[:5]

            # Estimated company type
            estimated_type = _classify_company(company, job_count)

            results.append({
                "company": company,
                "job_count": job_count,
                "fresher_jobs": fresher_count,
                "fresher_pct": safe_pct(fresher_count, job_count),
                "unique_roles": unique_roles,
                "estimated_type": estimated_type,
                "salary": sal,
                "top_skills": top_skills,
                "locations": locations,
            })

        # Sort by job_count desc, slice
        results.sort(key=lambda x: x["job_count"], reverse=True)
        results = results[:limit]

        meta = self.build_meta(
            coverage_meta,
            total_jobs,
            extra={
                "domain": domain or "all",
                "limit": limit,
                "company_type_note": (
                    "Company type (Service/Product/Startup) is estimated from "
                    "name patterns — not from a verified data source."
                ),
            },
        )

        return {
            "companies": results,
            "total_jobs": total_jobs,
            "metadata": meta,
        }

    # ------------------------------------------------------------------
    # 2. Company type split
    # ------------------------------------------------------------------

    def get_company_type_split(
        self,
        domain: Optional[str] = None,
        days: int = 30,
        location: Optional[str] = None,
        fresher_only: bool = False,
    ) -> dict:
        """
        Breakdown of job postings by estimated company type:
        Service / Product / Startup.

        Response shape
        --------------
        {
            "domain": str | "all",
            "type_split": {
                "Service":  {"job_count": int, "pct": float, "companies": [str,...]},
                "Product":  {"job_count": int, "pct": float, "companies": [str,...]},
                "Startup":  {"job_count": int, "pct": float, "companies": [str,...]},
            },
            "total_jobs": int,
            "note": str,
            "metadata": { ... }
        }
        """
        df, coverage_meta = self.get_filtered(
            days=days, location=location, fresher_only=fresher_only,
            extra_dept_filter=domain,
        )

        if df.empty or "company" not in df.columns:
            return self._empty_response("company_type_split", coverage_meta)

        total_jobs = len(df)
        type_buckets: dict[str, list] = {"Service": [], "Product": [], "Startup": []}
        company_jobs: dict[str, int] = {}

        for company, group in df.groupby("company", dropna=True):
            cnt = len(group)
            company_jobs[company] = cnt
            ctype = _classify_company(company, cnt)
            type_buckets[ctype].append(company)

        type_split = {}
        for ctype, companies in type_buckets.items():
            job_count = sum(company_jobs[c] for c in companies)
            type_split[ctype] = {
                "job_count": job_count,
                "pct": safe_pct(job_count, total_jobs),
                "unique_companies": len(companies),
                "sample_companies": sorted(companies, key=lambda c: -company_jobs[c])[:5],
            }

        meta = self.build_meta(
            coverage_meta,
            total_jobs,
            extra={"domain": domain or "all"},
        )

        return {
            "domain": domain or "all",
            "type_split": type_split,
            "total_jobs": total_jobs,
            "note": (
                "Type classification is estimated from company name patterns. "
                "Accuracy is approximate."
            ),
            "metadata": meta,
        }

    # ------------------------------------------------------------------
    # 3. Hiring frequency for a specific company
    # ------------------------------------------------------------------

    def get_hiring_frequency(
        self,
        company: str,
        days: int = 90,
    ) -> dict:
        """
        Show how many jobs a specific company posted per week in the window.
        Useful to identify consistent vs burst hirers.

        Response shape
        --------------
        {
            "company": str,
            "total_jobs": int,
            "window_days": int,
            "weekly_buckets": [
                {"week_start": str, "job_count": int},
                ...
            ],
            "avg_jobs_per_week": float,
            "peak_week": str | None,
            "metadata": { ... }
        }
        """
        df, coverage_meta = self.get_filtered(days=days)

        if "company" not in df.columns:
            return self._empty_response("hiring_frequency", coverage_meta)

        co_df = df[df["company"].str.lower() == company.lower()].copy()

        if co_df.empty:
            return {
                "company": company,
                "total_jobs": 0,
                "window_days": days,
                "weekly_buckets": [],
                "avg_jobs_per_week": 0.0,
                "peak_week": None,
                "metadata": self.build_meta(coverage_meta, 0,
                                            extra={"warning": f"No jobs found for '{company}'"}),
            }

        if "posted_timestamp" not in co_df.columns:
            return {
                "company": company,
                "total_jobs": len(co_df),
                "window_days": days,
                "weekly_buckets": [],
                "avg_jobs_per_week": 0.0,
                "peak_week": None,
                "metadata": self.build_meta(coverage_meta, len(co_df),
                                            extra={"warning": "posted_timestamp missing"}),
            }

        co_df["_ts"] = pd.to_datetime(co_df["posted_timestamp"], errors="coerce")
        co_df = co_df.dropna(subset=["_ts"])
        co_df["_week"] = co_df["_ts"].dt.to_period("W").dt.start_time.dt.strftime("%Y-%m-%d")

        weekly = co_df.groupby("_week").size().reset_index(name="job_count")
        weekly = weekly.sort_values("_week")
        weekly_buckets = weekly.to_dict(orient="records")

        total = len(co_df)
        num_weeks = len(weekly_buckets) or 1
        avg_per_week = round(total / num_weeks, 2)
        peak_week = weekly.loc[weekly["job_count"].idxmax(), "_week"] if not weekly.empty else None

        meta = self.build_meta(coverage_meta, total, extra={"company": company})

        return {
            "company": company,
            "total_jobs": total,
            "window_days": days,
            "weekly_buckets": weekly_buckets,
            "avg_jobs_per_week": avg_per_week,
            "peak_week": peak_week,
            "metadata": meta,
        }

    # ------------------------------------------------------------------
    # 4. Jaipur-specific company table
    # ------------------------------------------------------------------

    def get_jaipur_companies(
        self,
        domain: Optional[str] = None,
        days: int = 60,
        fresher_only: bool = False,
        limit: int = 20,
    ) -> dict:
        """
        Companies actively hiring in Jaipur for a given domain.
        Produces the "Jaipur hiring" highlighted section in the dashboard.

        Response shape: same as get_top_hiring_companies() but location-locked
        to Jaipur and with a jaipur_exclusive flag.

        {
            "companies": [ ... same as top_hiring_companies ... ],
            "total_jaipur_jobs": int,
            "total_national_jobs": int,
            "jaipur_share_pct": float,
            "metadata": { ... }
        }
        """
        # National baseline (no location filter)
        df_national, coverage_meta = self.get_filtered(
            days=days, fresher_only=fresher_only, extra_dept_filter=domain
        )
        total_national = len(df_national)

        # Jaipur slice
        df_jaipur = filter_location(df_national, "Jaipur")
        total_jaipur = len(df_jaipur)

        if df_jaipur.empty or "company" not in df_jaipur.columns:
            return {
                "companies": [],
                "total_jaipur_jobs": 0,
                "total_national_jobs": total_national,
                "jaipur_share_pct": 0.0,
                "metadata": self.build_meta(coverage_meta, total_national,
                                            extra={"warning": "No Jaipur jobs found"}),
            }

        results = []
        for company, group in df_jaipur.groupby("company", dropna=True):
            job_count = len(group)
            fresher_df = filter_freshers(group)
            sal = salary_stats(group)

            skill_counter: Counter = Counter()
            for raw in group.get("skills", pd.Series(dtype=str)):
                skill_counter.update(set(parse_skills(raw)))

            results.append({
                "company": company,
                "job_count": job_count,
                "fresher_jobs": len(fresher_df),
                "fresher_pct": safe_pct(len(fresher_df), job_count),
                "estimated_type": _classify_company(company, job_count),
                "salary": sal,
                "top_skills": [sk for sk, _ in skill_counter.most_common(5)],
            })

        results.sort(key=lambda x: x["job_count"], reverse=True)
        results = results[:limit]

        meta = self.build_meta(
            coverage_meta,
            total_national,
            extra={"domain": domain or "all", "location": "Jaipur"},
        )

        return {
            "companies": results,
            "total_jaipur_jobs": total_jaipur,
            "total_national_jobs": total_national,
            "jaipur_share_pct": safe_pct(total_jaipur, total_national),
            "metadata": meta,
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _empty_response(self, method: str, meta: dict) -> dict:
        logger.warning("CompanyIntelligenceService.%s: empty df or missing column", method)
        return {
            "companies": [],
            "total_jobs": 0,
            "metadata": self.build_meta(meta, 0, extra={"warning": f"No data for {method}"}),
        }


# ---------------------------------------------------------------------------
# Module-level helpers
# ---------------------------------------------------------------------------

def _classify_company(company_name: str, job_count: int) -> str:
    """
    Estimate whether a company is Service / Product / Startup.
    Heuristic-based — not authoritative.
    """
    name_lower = company_name.lower()

    # Startup: very few postings (burst vs consistent hirer not distinguishable,
    # but small absolute count is a reasonable proxy)
    if job_count <= _STARTUP_MAX_JOBS:
        return "Startup"

    # Known service companies
    for signal in _SERVICE_COMPANY_SIGNALS:
        if signal in name_lower:
            return "Service"

    # Product company signals in name
    if _PRODUCT_SIGNALS.search(company_name):
        return "Product"

    # Default for larger companies not matched above
    return "Service"