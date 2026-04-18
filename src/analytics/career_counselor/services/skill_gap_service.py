"""
SkillGapAnalyzerService
=======================
Implements skill-gap analysis for a student against a target domain.

    analyze_skill_gap(student_skills, target_domain, top_roles, days, location)
        → match_percentage
        → matched_skills
        → missing_skills  (ranked by how many extra jobs they unlock)
        → recommended_skills  (same list, just named for the UI)
        → impact_summary  (human-readable actionable strings)
        → jobs_accessible_now  (jobs the student can apply to today)

Design decisions
----------------
- "Match" is computed against the TOP `top_roles` postings in the domain,
  not the full domain corpus.  Reason: a domain may have 2000 jobs but the
  top 20 by recency represent what's actually being hired right now.
- For each missing skill we compute `extra_jobs_if_added` by counting how many
  jobs in the domain pool list that skill — i.e. adding it would make the
  student eligible for that many more postings.
- Salary impact is intentionally NOT computed here because 80% salary nulls
  make per-skill salary deltas statistically meaningless.  SalaryIntelligence
  handles salary; we reference it honestly.
- `jobs_accessible_now` is the count of domain jobs where the student already
  matches >= match_threshold (default 60%) of required skills.

Columns used
------------
    department, skills, title, company, location,
    min_experience, posted_timestamp
"""

from __future__ import annotations

import logging
from collections import Counter
from typing import Optional

import pandas as pd

from src.analytics.career_counselor.services.base_service import BaseService
from src.analytics.career_counselor.utils.skill_utils import (
    parse_skills,
    normalize_skill,
    skill_match_percentage,
)
from src.analytics.career_counselor.utils.calculation_utils import safe_pct

logger = logging.getLogger(__name__)

# Minimum skill-match fraction for a job to be "accessible"
_ACCESSIBLE_THRESHOLD = 0.60


class SkillGapAnalyzerService(BaseService):
    """
    Usage
    -----
        svc = SkillGapAnalyzerService(df)
        result = svc.analyze_skill_gap(
            student_skills=["python", "sql", "pandas"],
            target_domain="Data Science",
        )
    """

    def analyze_skill_gap(
        self,
        student_skills: list[str],
        target_domain: str,
        top_roles: int = 20,
        days: Optional[int] = 60,
        location: Optional[str] = None,
        fresher_only: bool = True,
    ) -> dict:
        """
        Full skill-gap analysis for one student against one domain.

        Parameters
        ----------
        student_skills : list[str]
            Raw skill strings the student enters (normalized internally).
        target_domain : str
            Exact or partial department/domain name (case-insensitive substring).
        top_roles : int
            Number of most-recent domain postings to use as the benchmark.
        days : int | None
            Recency window. Default 60 (wider than market pulse to get
            enough domain-specific postings).
        location : str | None
        fresher_only : bool
            Default True — counselors almost always use this for freshers.

        Response shape
        --------------
        {
            "target_domain": str,
            "student_skills": [str, ...],          # normalized
            "match_percentage": float,             # 0–100
            "jobs_accessible_now": int,            # jobs student can apply to
            "total_domain_jobs": int,
            "matched_skills": [str, ...],
            "missing_skills": [
                {
                    "skill": str,
                    "frequency_in_domain": int,    # jobs listing this skill
                    "frequency_pct": float,        # % of domain jobs
                    "extra_jobs_if_added": int,    # jobs unlocked (not yet accessible)
                    "priority_rank": int
                },
                ...
            ],
            "recommended_skills": [str, ...],      # ordered list for learning path
            "impact_summary": [str, ...],          # "Adding X opens +N jobs"
            "top_benchmark_roles": [               # sample of benchmark job titles
                {"title": str, "company": str, "match_pct": float},
                ...
            ],
            "metadata": { ... }
        }
        """
        # Normalize student skills once
        norm_student: set[str] = {normalize_skill(s.strip().lower()) for s in student_skills if s.strip()}

        # Filter to domain
        df, coverage_meta = self.get_filtered(
            days=days,
            location=location,
            fresher_only=fresher_only,
            extra_dept_filter=target_domain,
        )

        if df.empty:
            return self._empty_gap_response(target_domain, list(norm_student), coverage_meta)

        total_domain_jobs = len(df)

        # Sort by posted_timestamp desc (most recent first), take top_roles
        benchmark_df = _sort_by_recency(df, top_roles)

        # ----------------------------------------------------------------
        # Build domain skill universe from full domain pool (not just top_roles)
        # so that extra_jobs_if_added counts are meaningful.
        # ----------------------------------------------------------------
        domain_skill_counter = _count_skills_in_df(df)        # full pool
        benchmark_skill_counter = _count_skills_in_df(benchmark_df)  # benchmark

        # ----------------------------------------------------------------
        # Match percentage — against benchmark (current hiring bar)
        # ----------------------------------------------------------------
        all_benchmark_skills: set[str] = set(benchmark_skill_counter.keys())
        matched_skills: list[str] = sorted(norm_student & all_benchmark_skills)
        missing_from_benchmark: set[str] = all_benchmark_skills - norm_student

        if all_benchmark_skills:
            match_pct = safe_pct(len(matched_skills), len(all_benchmark_skills))
        else:
            match_pct = 0.0

        # ----------------------------------------------------------------
        # Jobs accessible now (full domain pool)
        # ----------------------------------------------------------------
        jobs_accessible_now = _count_accessible_jobs(df, norm_student)

        # ----------------------------------------------------------------
        # Missing skills — ranked by extra_jobs_if_added
        # ----------------------------------------------------------------
        missing_skills_data = []

        for skill in missing_from_benchmark:
            freq_in_domain = domain_skill_counter.get(skill, 0)
            if freq_in_domain == 0:
                continue

            # Extra jobs unlocked: jobs that list this skill AND student
            # can't currently access (match < threshold without this skill)
            extra = _count_extra_jobs_if_added(df, norm_student, skill)

            missing_skills_data.append({
                "skill": skill,
                "frequency_in_domain": freq_in_domain,
                "frequency_pct": safe_pct(freq_in_domain, total_domain_jobs),
                "extra_jobs_if_added": extra,
            })

        # Sort by extra_jobs_if_added desc, then frequency desc
        missing_skills_data.sort(
            key=lambda x: (x["extra_jobs_if_added"], x["frequency_in_domain"]),
            reverse=True,
        )
        for rank, item in enumerate(missing_skills_data, 1):
            item["priority_rank"] = rank

        # ----------------------------------------------------------------
        # Recommended skills (ordered list, top 10 for learning path)
        # ----------------------------------------------------------------
        recommended_skills = [s["skill"] for s in missing_skills_data[:10]]

        # ----------------------------------------------------------------
        # Impact summary — actionable strings for the UI cards
        # ----------------------------------------------------------------
        impact_summary = []
        for item in missing_skills_data[:5]:
            if item["extra_jobs_if_added"] > 0:
                impact_summary.append(
                    f"Adding '{item['skill']}' opens +{item['extra_jobs_if_added']:,} "
                    f"more jobs in {target_domain} "
                    f"(appears in {item['frequency_pct']:.0f}% of postings)"
                )

        if not impact_summary:
            if match_pct >= 80:
                impact_summary.append(
                    f"Strong match! You already meet {match_pct:.0f}% of "
                    f"{target_domain} requirements."
                )
            else:
                impact_summary.append(
                    f"Focus on the top missing skills to improve your "
                    f"{match_pct:.0f}% match rate."
                )

        # ----------------------------------------------------------------
        # Sample benchmark roles (for context)
        # ----------------------------------------------------------------
        top_benchmark_roles = _sample_benchmark_roles(
            benchmark_df, norm_student, limit=5
        )

        meta = self.build_meta(
            coverage_meta,
            total_domain_jobs,
            extra={
                "target_domain": target_domain,
                "top_roles_used_as_benchmark": min(top_roles, len(benchmark_df)),
                "fresher_only": fresher_only,
                "salary_note": (
                    "Salary impact per skill is not shown here — salary data has "
                    "~80% null coverage. See Salary Intelligence tab for estimates."
                ),
            },
        )

        return {
            "target_domain": target_domain,
            "student_skills": sorted(norm_student),
            "match_percentage": match_pct,
            "jobs_accessible_now": jobs_accessible_now,
            "total_domain_jobs": total_domain_jobs,
            "matched_skills": matched_skills,
            "missing_skills": missing_skills_data,
            "recommended_skills": recommended_skills,
            "impact_summary": impact_summary,
            "top_benchmark_roles": top_benchmark_roles,
            "metadata": meta,
        }

    def get_popular_skills_for_domain(
        self,
        domain: str,
        top_n: int = 30,
        days: Optional[int] = 60,
        fresher_only: bool = True,
    ) -> dict:
        """
        Return the most common skills in a domain.
        Used to pre-populate the student skill multiselect in Streamlit.

        Response shape
        --------------
        {
            "domain": str,
            "skills": [{"skill": str, "frequency_pct": float}, ...],
            "metadata": { ... }
        }
        """
        df, coverage_meta = self.get_filtered(
            days=days,
            fresher_only=fresher_only,
            extra_dept_filter=domain,
        )

        if df.empty or "skills" not in df.columns:
            return {"domain": domain, "skills": [], "metadata": self.build_meta(coverage_meta, 0)}

        counter = _count_skills_in_df(df)
        total = len(df)

        skills_list = [
            {"skill": sk, "frequency_pct": safe_pct(cnt, total)}
            for sk, cnt in counter.most_common(top_n)
        ]

        return {
            "domain": domain,
            "skills": skills_list,
            "metadata": self.build_meta(coverage_meta, total),
        }

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _empty_gap_response(self, domain: str, student_skills: list, meta: dict) -> dict:
        logger.warning("SkillGapService: no jobs found for domain '%s'", domain)
        return {
            "target_domain": domain,
            "student_skills": student_skills,
            "match_percentage": 0.0,
            "jobs_accessible_now": 0,
            "total_domain_jobs": 0,
            "matched_skills": [],
            "missing_skills": [],
            "recommended_skills": [],
            "impact_summary": [f"No jobs found for domain '{domain}' in the selected window."],
            "top_benchmark_roles": [],
            "metadata": self.build_meta(meta, 0, extra={"warning": "No domain data"}),
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


def _sort_by_recency(df: pd.DataFrame, limit: int) -> pd.DataFrame:
    """Return the `limit` most recent rows by posted_timestamp."""
    if "posted_timestamp" not in df.columns:
        return df.head(limit)
    ts = pd.to_datetime(df["posted_timestamp"], errors="coerce")
    return df.assign(_ts=ts).sort_values("_ts", ascending=False).drop(columns="_ts").head(limit)


def _count_accessible_jobs(df: pd.DataFrame, norm_student: set[str]) -> int:
    """Count jobs where student matches >= 60% of listed skills."""
    count = 0
    for raw in df.get("skills", pd.Series(dtype=str)):
        job_skills = parse_skills(raw)
        if not job_skills:
            continue
        if skill_match_percentage(list(norm_student), job_skills) >= _ACCESSIBLE_THRESHOLD:
            count += 1
    return count


def _count_extra_jobs_if_added(
    df: pd.DataFrame,
    current_student_skills: set[str],
    new_skill: str,
) -> int:
    """
    How many jobs become accessible (cross the 60% threshold) if we add
    `new_skill` to the student's skill set?
    Only counts jobs NOT already accessible.
    """
    augmented = current_student_skills | {new_skill}
    extra = 0
    for raw in df.get("skills", pd.Series(dtype=str)):
        job_skills = parse_skills(raw)
        if not job_skills:
            continue
        was_accessible = skill_match_percentage(list(current_student_skills), job_skills) >= _ACCESSIBLE_THRESHOLD
        now_accessible = skill_match_percentage(list(augmented), job_skills) >= _ACCESSIBLE_THRESHOLD
        if now_accessible and not was_accessible:
            extra += 1
    return extra


def _sample_benchmark_roles(
    benchmark_df: pd.DataFrame,
    norm_student: set[str],
    limit: int = 5,
) -> list[dict]:
    """Return a sample of benchmark job titles with per-role match %."""
    roles = []
    for _, row in benchmark_df.iterrows():
        job_skills = parse_skills(row.get("skills", ""))
        match_pct = round(skill_match_percentage(list(norm_student), job_skills) * 100, 1)
        roles.append({
            "title": str(row.get("title", "")).strip() or "N/A",
            "company": str(row.get("company", "")).strip() or "N/A",
            "match_pct": match_pct,
        })
        if len(roles) >= limit:
            break
    return sorted(roles, key=lambda x: x["match_pct"], reverse=True)