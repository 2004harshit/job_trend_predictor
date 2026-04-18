import re
import ast
import logging
from typing import Dict, List, Tuple, Optional
import pandas as pd


# ── Central Skills Parser ─────────────────────────────────────────────────────
def parse_skills_column(raw) -> List[str]:
    if raw is None or (isinstance(raw, float) and pd.isna(raw)):
        return []
    raw = str(raw).strip()
    if not raw:
        return []
    if raw.startswith('['):
        try:
            parsed = ast.literal_eval(raw)
            if isinstance(parsed, list):
                return [re.sub(r'\s+', ' ', str(s).strip().lower())
                        for s in parsed if str(s).strip()]
        except (ValueError, SyntaxError):
            pass
    return [re.sub(r"['\"\\[\\]]", '', s).strip().lower()
            for s in raw.split(',')
            if re.sub(r"['\"\\[\\]]", '', s).strip()]
# ─────────────────────────────────────────────────────────────────────────────


class SkillTransferabilityEngine:

    MIN_SAMPLES = 10

    GENERIC_SKILLS = {
        'communication', 'teamwork', 'problem solving', 'microsoft office',
        'excel', 'powerpoint', 'time management', 'leadership', 'english',
        'ms office', 'presentation', 'analytical skills', 'attention to detail'
    }

    SKILL_COMPLEXITY = {
        'python':            4,   'javascript':        4,
        'machine learning':  16,  'deep learning':     20,
        'react':             8,   'node.js':           6,
        'sql':               3,   'mongodb':           4,
        'docker':            3,   'kubernetes':        6,
        'aws':               8,   'tensorflow':        12,
        'pytorch':           12,  'spark':             8,
        'kafka':             6,   'system design':     12,
        'data science':      20,  'nlp':               14,
        'java':              10,  'spring boot':       8,
    }
    DEFAULT_WEEKS = 6

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def _filter_domain(self, df: pd.DataFrame,
                       target_domain: str,
                       experience_band: Tuple = (0, 3)) -> pd.DataFrame:
        df = df.copy()
        if 'title_cleaned' in df.columns and 'title' not in df.columns:
            df = df.rename(columns={'title_cleaned': 'title'})

        if 'title' in df.columns:
            result = df[df['title'].str.lower() == target_domain.lower()]
            if 'min_experience' in result.columns:
                result = result[
                    (result['min_experience'] >= experience_band[0]) &
                    (result['min_experience'] <= experience_band[1] + 1)
                ]
            if len(result) >= 5:
                return result

        title_col = 'title' if 'title' in df.columns else None
        if title_col:
            result = df[df[title_col].str.contains(target_domain, case=False, na=False)]
            if not result.empty:
                return result

        return pd.DataFrame()

    def _extract_skill_profile(self, domain_df: pd.DataFrame) -> Dict[str, float]:
        """
        Build weighted skill importance profile from the 'skills' column.
        Parses both old list-repr format and new plain-string format.
        Generic skills are downweighted.
        """
        if domain_df.empty:
            return {}

        if 'skills' not in domain_df.columns:
            return {}

        total_postings = len(domain_df)
        skill_weighted_counts: Dict[str, float] = {}

        # Single 'skills' column — uniform weight 1.0
        # (Previously star_skills=2.0, combined=1.0, normal=0.7; now unified)
        for raw in domain_df['skills'].fillna(''):
            skills = parse_skills_column(raw)
            for skill in skills:
                skill = re.sub(r'\s+', ' ', skill).strip()
                if not skill:
                    continue
                skill_weighted_counts[skill] = skill_weighted_counts.get(skill, 0) + 1.0

        if not skill_weighted_counts:
            return {}

        # Per-posting frequency
        skill_importance = {
            skill: count / total_postings
            for skill, count in skill_weighted_counts.items()
        }

        # Downweight generic skills
        for generic in self.GENERIC_SKILLS:
            if generic in skill_importance:
                skill_importance[generic] *= 0.2

        # Remove near-zero
        skill_importance = {k: v for k, v in skill_importance.items() if v > 0.01}

        return skill_importance

    def _calculate_overlap_metrics(self,
                                    source_profile: Dict[str, float],
                                    target_profile: Dict[str, float]) -> dict:
        source_skills = set(source_profile.keys())
        target_skills = set(target_profile.keys())
        common_skills = source_skills & target_skills

        portability = len(common_skills) / len(source_skills) if source_skills else 0.0
        coverage    = len(common_skills) / len(target_skills) if target_skills else 0.0

        weighted_coverage = sum(
            target_profile.get(skill, 0) for skill in common_skills
        )
        max_possible_weighted = sum(target_profile.values())
        normalized_weighted = (
            weighted_coverage / max_possible_weighted
            if max_possible_weighted > 0 else 0.0
        )

        composite = 0.60 * normalized_weighted + 0.40 * portability

        return {
            "composite":           round(composite, 3),
            "coverage_ratio":      round(coverage, 3),
            "portability_ratio":   round(portability, 3),
            "normalized_weighted": round(normalized_weighted, 3),
            "common_count":        len(common_skills),
            "source_skill_count":  len(source_skills),
            "target_skill_count":  len(target_skills),
            "gap_count":           len(target_skills - source_skills)
        }

    def _analyze_skill_gap(self,
                            source_profile: Dict[str, float],
                            target_profile: Dict[str, float]) -> dict:
        source_skills = set(source_profile.keys())
        target_skills = set(target_profile.keys())

        gap_skills = target_skills - source_skills
        gap_ranked = sorted(
            [(skill, target_profile[skill]) for skill in gap_skills],
            key=lambda x: x[1], reverse=True
        )

        common_skills = source_skills & target_skills
        bridge_ranked = sorted(
            [(skill, target_profile[skill]) for skill in common_skills],
            key=lambda x: x[1], reverse=True
        )

        obsolete = source_skills - target_skills
        obsolete_ranked = sorted(
            [(skill, source_profile[skill]) for skill in obsolete],
            key=lambda x: x[1], reverse=True
        )

        total_weeks = 0
        for skill, importance in gap_ranked[:10]:
            weeks = self.SKILL_COMPLEXITY.get(skill, self.DEFAULT_WEEKS)
            adjusted_weeks = weeks * (1 + importance)
            total_weeks += adjusted_weeks

        months_estimate = round(total_weeks / 4.3, 1)

        return {
            "priority_gaps": [
                {"skill": s, "importance": round(imp, 3),
                 "weeks": self.SKILL_COMPLEXITY.get(s, self.DEFAULT_WEEKS)}
                for s, imp in gap_ranked[:8]
            ],
            "bridge_skills": [
                {"skill": s, "target_importance": round(imp, 3)}
                for s, imp in bridge_ranked[:8]
            ],
            "obsolete_skills":    [s for s, _ in obsolete_ranked[:5]],
            "total_gap_skills":   len(gap_skills),
            "total_bridge_skills": len(common_skills),
            "estimated_months":   months_estimate,
            "learning_hrs_assumed": 10
        }

    def _classify_transferability(self,
                                    composite: float,
                                    coverage: float,
                                    gap_count: int,
                                    estimated_months: float) -> dict:
        if composite >= 0.65:
            base_label = "🟢 High Transferability"
            difficulty  = "Easy Switch"
        elif composite >= 0.45:
            base_label = "🟡 Moderate Transferability"
            difficulty  = "Moderate Effort"
        elif composite >= 0.25:
            base_label = "🟠 Low Transferability"
            difficulty  = "Significant Reskilling"
        else:
            base_label = "🔴 Very Low Transferability"
            difficulty  = "Near Full Restart"

        if estimated_months <= 2:
            time_label = "Quick transition (≤2 months)"
        elif estimated_months <= 6:
            time_label = f"Medium transition (~{estimated_months:.0f} months)"
        elif estimated_months <= 12:
            time_label = f"Long transition (~{estimated_months:.0f} months)"
        else:
            time_label = f"Extended transition (~{estimated_months:.0f}+ months)"

        coverage_warning = None
        if coverage < 0.30:
            coverage_warning = (
                f"⚠️  You currently cover only {coverage*100:.0f}% of target requirements. "
                f"Expect steep learning curve even after transition."
            )

        return {
            "label":            base_label,
            "difficulty":       difficulty,
            "time_estimate":    time_label,
            "coverage_warning": coverage_warning,
        }

    def _calculate_salary_impact(self,
                                  source_df: pd.DataFrame,
                                  target_df: pd.DataFrame) -> dict:
        # Use lowercase 'avg_salary' — matches actual schema
        if 'avg_salary' not in source_df.columns:
            return {"available": False}

        def safe_median(df):
            sal = pd.to_numeric(df['avg_salary'], errors='coerce').dropna()
            if len(sal) >= 4:
                Q1, Q3 = sal.quantile(0.25), sal.quantile(0.75)
                sal = sal[(sal >= Q1 - 1.5*(Q3-Q1)) & (sal <= Q3 + 1.5*(Q3-Q1))]
            return sal.median() if not sal.empty else None

        src_med = safe_median(source_df)
        tgt_med = safe_median(target_df)

        if src_med is None or tgt_med is None:
            return {"available": False}

        delta_pct = ((tgt_med - src_med) / src_med) * 100

        if delta_pct > 10:
            signal = f"📈 Salary upgrade: +{delta_pct:.1f}% median compensation gain"
        elif delta_pct < -10:
            signal = f"📉 Salary cut: {delta_pct:.1f}% reduction — factor into timing"
        else:
            signal = f"⚖️  Similar compensation (±{abs(delta_pct):.1f}%)"

        return {
            "available":     True,
            "source_median": round(src_med / 100000, 2),
            "target_median": round(tgt_med / 100000, 2),
            "delta_pct":     round(delta_pct, 1),
            "signal":        signal
        }

    def _bidirectional_note(self, fwd_composite: float, rev_composite: float,
                             source: str, target: str) -> str:
        if abs(fwd_composite - rev_composite) < 0.05:
            return f"↔️  Both directions are similarly feasible ({fwd_composite:.0%} vs {rev_composite:.0%})."
        elif rev_composite > fwd_composite:
            gain = (rev_composite - fwd_composite) * 100
            return (
                f"💡 The reverse path ({target}→{source}) is {gain:.0f}% easier. "
                f"Consider building {target} skills first, then switching."
            )
        else:
            return f"✅ Forward path ({source}→{target}) is the more natural direction."

    def calculate_transferability(self,
                                   df: pd.DataFrame,
                                   source_domain: str,
                                   target_domain: str,
                                   experience_band: Tuple = (0, 5)) -> dict:
        source_df = self._filter_domain(df, source_domain, experience_band)
        target_df = self._filter_domain(df, target_domain, experience_band)

        if source_df.empty:
            return {"error": f"No data for source domain: '{source_domain}'"}
        if target_df.empty:
            return {"error": f"No data for target domain: '{target_domain}'"}

        source_profile = self._extract_skill_profile(source_df)
        target_profile = self._extract_skill_profile(target_df)

        if not source_profile:
            return {"error": f"No skill data found for: '{source_domain}'"}
        if not target_profile:
            return {"error": f"No skill data found for: '{target_domain}'"}

        metrics     = self._calculate_overlap_metrics(source_profile, target_profile)
        rev_metrics = self._calculate_overlap_metrics(target_profile, source_profile)
        bidir_note  = self._bidirectional_note(
            metrics["composite"], rev_metrics["composite"],
            source_domain, target_domain
        )

        gap = self._analyze_skill_gap(source_profile, target_profile)

        classification = self._classify_transferability(
            metrics["composite"],
            metrics["coverage_ratio"],
            gap["total_gap_skills"],
            gap["estimated_months"]
        )

        salary = self._calculate_salary_impact(source_df, target_df)

        # Use lowercase 'skill_count' — matches actual schema
        src_complexity = source_df['skill_count'].median() if 'skill_count' in source_df.columns else None
        tgt_complexity = target_df['skill_count'].median() if 'skill_count' in target_df.columns else None

        return {
            "Path":            f"{source_domain} → {target_domain}",
            "Experience_Band": experience_band,

            "Transferability": {
                "Composite_Score":   metrics["composite"],
                "Coverage_Ratio":    metrics["coverage_ratio"],
                "Portability_Ratio": metrics["portability_ratio"],
                "Label":             classification["label"],
                "Difficulty":        classification["difficulty"],
                "Time_Estimate":     classification["time_estimate"],
                "Coverage_Warning":  classification["coverage_warning"],
            },

            "Skill_Gap": {
                "Priority_Skills_To_Learn": gap["priority_gaps"],
                "Bridge_Skills":            gap["bridge_skills"],
                "Skills_Becoming_Obsolete": gap["obsolete_skills"],
                "Total_Gap_Skills":         gap["total_gap_skills"],
                "Total_Bridge_Skills":      gap["total_bridge_skills"],
                "Estimated_Months":         gap["estimated_months"],
            },

            "Domain_Complexity": {
                "Source_Median_Skills": round(src_complexity, 1) if src_complexity else None,
                "Target_Median_Skills": round(tgt_complexity, 1) if tgt_complexity else None,
                "Complexity_Jump": (
                    round(tgt_complexity - src_complexity, 1)
                    if src_complexity and tgt_complexity else None
                )
            },

            "Salary_Impact":      salary,
            "Bidirectional_Note": bidir_note,

            "Sample_Sizes": {
                "Source_Listings": len(source_df),
                "Target_Listings": len(target_df),
            }
        }