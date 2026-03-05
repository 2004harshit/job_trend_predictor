import re
import logging
from typing import Dict, List, Tuple, Optional
import pandas as pd

class SkillTransferabilityEngine:
    
    MIN_SAMPLES = 10
    
    # Skills so generic they appear everywhere — downweight them
    GENERIC_SKILLS = {
        'communication', 'teamwork', 'problem solving', 'microsoft office',
        'excel', 'powerpoint', 'time management', 'leadership', 'english',
        'ms office', 'presentation', 'analytical skills', 'attention to detail'
    }
    
    # Learning time estimates in weeks for skill categories
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
    DEFAULT_WEEKS = 6  # Default for unknown skills
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def _filter_domain(self, df: pd.DataFrame,
                        target_domain: str,
                        experience_band: Tuple = (0, 3)) -> pd.DataFrame:
        """Job_Type first, Title fallback. Safe copy. Experience filtered."""
        df = df.copy()

        if 'TItle_Cleaned' in df.columns and 'Title_Cleaned' not in df.columns:
            df = df.rename(columns={'TItle_Cleaned': 'Title_Cleaned'})

        # 1. Job_Type exact match
        if 'Job_Type' in df.columns:
            result = df[df['Job_Type'].str.lower() == target_domain.lower()]
            if 'Min_Experience' in result.columns:
                result = result[
                    (result['Min_Experience'] >= experience_band[0]) &
                    (result['Min_Experience'] <= experience_band[1] + 1)
                ]
            if len(result) >= 5:
                return result

        # 2. Title_Cleaned fallback
        title_col = 'Title_Cleaned' if 'Title_Cleaned' in df.columns else None
        if title_col:
            result = df[df[title_col].str.contains(target_domain, case=False, na=False)]
            if not result.empty:
                return result

        return pd.DataFrame()

    def _extract_skill_profile(self, domain_df: pd.DataFrame) -> Dict[str, float]:
        """
        Build weighted skill importance profile.

        Key fixes:
        1. NaN-safe skill extraction
        2. Star_Skills get 2x weight (must-have vs nice-to-have)
        3. Generic skills downweighted via TF-IDF-like approach
        4. Frequency normalized correctly per posting (not per skill token)
        """
        if domain_df.empty:
            return {}

        total_postings = len(domain_df)
        skill_weighted_counts = {}

        # Process each skill column with its weight
        skill_columns = {
            'Star_Skills':     2.0,   # Must-have — double weight
            'Combined_Skills': 1.0,   # Standard weight
            'Normal_Skills':   0.7,   # Nice-to-have — reduced weight
        }

        for col, weight in skill_columns.items():
            if col not in domain_df.columns:
                continue
            
            # NaN-safe: fillna before processing
            skills_series = domain_df[col].fillna('').astype(str)

            for skills_str in skills_series:
                if not skills_str.strip():
                    continue
                
                # Parse comma-separated skills
                skills = [
                    s.strip().lower() 
                    for s in skills_str.split(',') 
                    if s.strip() and len(s.strip()) > 1
                ]

                for skill in skills:
                    # Normalize skill name
                    skill = re.sub(r'\s+', ' ', skill).strip()
                    if not skill:
                        continue
                    skill_weighted_counts[skill] = (
                        skill_weighted_counts.get(skill, 0) + weight
                    )

        if not skill_weighted_counts:
            return {}

        # Convert to per-posting frequency (importance)
        skill_importance = {
            skill: count / total_postings
            for skill, count in skill_weighted_counts.items()
        }

        # Downweight generic skills (they appear everywhere — low domain signal)
        for generic in self.GENERIC_SKILLS:
            if generic in skill_importance:
                skill_importance[generic] *= 0.2

        # Remove near-zero importance skills
        skill_importance = {
            k: v for k, v in skill_importance.items() if v > 0.01
        }

        return skill_importance

    def _calculate_overlap_metrics(self,
                                     source_profile: Dict[str, float],
                                     target_profile: Dict[str, float]) -> dict:
        """
        Fix: TWO overlap ratios are needed, not one.

        Coverage Ratio:  What % of TARGET skills does source already have?
                         "How much of the destination is already covered?"
                         → Key metric for switch difficulty

        Portability Ratio: What % of SOURCE skills transfer to target?
                           "How much of your investment carries over?"
                           → Key metric for sunk cost protection

        Previous code only computed Portability — missed the crucial Coverage metric.
        """
        source_skills = set(source_profile.keys())
        target_skills = set(target_profile.keys())
        common_skills  = source_skills & target_skills

        # Portability: fraction of your skills that are useful in target
        portability = len(common_skills) / len(source_skills) if source_skills else 0.0

        # Coverage: fraction of target requirements you already meet
        coverage = len(common_skills) / len(target_skills) if target_skills else 0.0

        # Weighted overlap: sum of (target_importance) for skills you already have
        # This measures how IMPORTANT your overlapping skills are IN THE TARGET
        weighted_coverage = sum(
            target_profile.get(skill, 0)
            for skill in common_skills
        )
        max_possible_weighted = sum(target_profile.values())

        normalized_weighted = (
            weighted_coverage / max_possible_weighted
            if max_possible_weighted > 0 else 0.0
        )

        # Composite transferability: 
        # 60% coverage (can you do the job?) + 40% portability (does your investment transfer?)
        composite = 0.60 * normalized_weighted + 0.40 * portability

        return {
            "composite":             round(composite, 3),
            "coverage_ratio":        round(coverage, 3),
            "portability_ratio":     round(portability, 3),
            "normalized_weighted":   round(normalized_weighted, 3),
            "common_count":          len(common_skills),
            "source_skill_count":    len(source_skills),
            "target_skill_count":    len(target_skills),
            "gap_count":             len(target_skills - source_skills)
        }

    def _analyze_skill_gap(self,
                             source_profile: Dict[str, float],
                             target_profile: Dict[str, float]) -> dict:
        """
        Gap skills ranked by TARGET IMPORTANCE (not random).
        User learns highest-impact skills first.

        Also estimates total reskilling time in weeks.
        """
        source_skills = set(source_profile.keys())
        target_skills = set(target_profile.keys())

        # Skills needed but not currently held
        gap_skills = target_skills - source_skills

        # Rank by importance in target domain
        gap_ranked = sorted(
            [(skill, target_profile[skill]) for skill in gap_skills],
            key=lambda x: x[1],
            reverse=True
        )

        # Bridge skills: shared AND high-importance in target
        common_skills = source_skills & target_skills
        bridge_ranked = sorted(
            [(skill, target_profile[skill]) for skill in common_skills],
            key=lambda x: x[1],
            reverse=True
        )

        # Obsolete skills: in source but NOT in target (don't transfer)
        obsolete = source_skills - target_skills
        obsolete_ranked = sorted(
            [(skill, source_profile[skill]) for skill in obsolete],
            key=lambda x: x[1],
            reverse=True
        )

        # Estimate reskilling time
        total_weeks = 0
        weeks_breakdown = {}
        for skill, importance in gap_ranked[:10]:  # Top 10 gaps
            weeks = self.SKILL_COMPLEXITY.get(skill, self.DEFAULT_WEEKS)
            # Weight by importance: high-importance skills need more depth
            adjusted_weeks = weeks * (1 + importance)
            weeks_breakdown[skill] = round(adjusted_weeks)
            total_weeks += adjusted_weeks

        # Assume 10 hrs/week learning pace
        months_estimate = round(total_weeks / 4.3, 1)  # 4.3 weeks/month

        return {
            "priority_gaps": [
                {
                    "skill":      s,
                    "importance": round(imp, 3),
                    "weeks":      self.SKILL_COMPLEXITY.get(s, self.DEFAULT_WEEKS)
                }
                for s, imp in gap_ranked[:8]  # Top 8 most important gaps
            ],
            "bridge_skills": [
                {"skill": s, "target_importance": round(imp, 3)}
                for s, imp in bridge_ranked[:8]
            ],
            "obsolete_skills": [s for s, _ in obsolete_ranked[:5]],
            "total_gap_skills":     len(gap_skills),
            "total_bridge_skills":  len(common_skills),
            "estimated_months":     months_estimate,
            "learning_hrs_assumed": 10
        }

    def _classify_transferability(self,
                                    composite: float,
                                    coverage: float,
                                    gap_count: int,
                                    estimated_months: float) -> dict:
        """
        Replace hardcoded 0.3/0.6 thresholds with multi-dimensional classification.

        Two axes:
        - Composite score (how much transfers)
        - Gap count (how much needs to be learned)
        """
        # Primary classification by composite score
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

        # Time-based modifier
        if estimated_months <= 2:
            time_label = "Quick transition (≤2 months)"
        elif estimated_months <= 6:
            time_label = f"Medium transition (~{estimated_months:.0f} months)"
        elif estimated_months <= 12:
            time_label = f"Long transition (~{estimated_months:.0f} months)"
        else:
            time_label = f"Extended transition (~{estimated_months:.0f}+ months)"

        # Coverage warning: even if composite is good,
        # low coverage means you'll struggle on day 1
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
        """
        Compare median salary in source vs target.
        Answers: "Will I take a pay cut if I switch?"
        """
        if 'Avg_Salary' not in source_df.columns:
            return {"available": False}

        def safe_median(df):
            sal = pd.to_numeric(df['Avg_Salary'], errors='coerce').dropna()
            # IQR outlier removal
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
            "available":      True,
            "source_median":  round(src_med / 100000, 2),  # In LPA
            "target_median":  round(tgt_med / 100000, 2),
            "delta_pct":      round(delta_pct, 1),
            "signal":         signal
        }

    def _bidirectional_note(self,
                              fwd_composite: float,
                              rev_composite: float,
                              source: str,
                              target: str) -> str:
        """
        Check if the reverse path is easier.
        Useful insight: "Going ML→WebDev is easier than WebDev→ML"
        """
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
        """
        Main entry point. Full bidirectional transferability analysis.
        """
        # 1. Filter domains
        source_df = self._filter_domain(df, source_domain, experience_band)
        target_df = self._filter_domain(df, target_domain, experience_band)

        if source_df.empty:
            return {"error": f"No data for source domain: '{source_domain}'"}
        if target_df.empty:
            return {"error": f"No data for target domain: '{target_domain}'"}

        # 2. Build skill profiles
        source_profile = self._extract_skill_profile(source_df)
        target_profile = self._extract_skill_profile(target_df)

        if not source_profile:
            return {"error": f"No skill data found for: '{source_domain}'"}
        if not target_profile:
            return {"error": f"No skill data found for: '{target_domain}'"}

        # 3. Overlap metrics (forward direction)
        metrics = self._calculate_overlap_metrics(source_profile, target_profile)

        # 4. Reverse direction for bidirectional note
        rev_metrics = self._calculate_overlap_metrics(target_profile, source_profile)
        bidir_note  = self._bidirectional_note(
            metrics["composite"], rev_metrics["composite"],
            source_domain, target_domain
        )

        # 5. Skill gap analysis
        gap = self._analyze_skill_gap(source_profile, target_profile)

        # 6. Classification
        classification = self._classify_transferability(
            metrics["composite"],
            metrics["coverage_ratio"],
            gap["total_gap_skills"],
            gap["estimated_months"]
        )

        # 7. Salary impact
        salary = self._calculate_salary_impact(source_df, target_df)

        # 8. Domain complexity comparison
        src_complexity = source_df['Skill_Count'].median() if 'Skill_Count' in source_df else None
        tgt_complexity = target_df['Skill_Count'].median() if 'Skill_Count' in target_df else None

        return {
            "Path":            f"{source_domain} → {target_domain}",
            "Experience_Band": experience_band,

            "Transferability": {
                "Composite_Score":    metrics["composite"],
                "Coverage_Ratio":     metrics["coverage_ratio"],    # % of target covered
                "Portability_Ratio":  metrics["portability_ratio"], # % of source that transfers
                "Label":              classification["label"],
                "Difficulty":         classification["difficulty"],
                "Time_Estimate":      classification["time_estimate"],
                "Coverage_Warning":   classification["coverage_warning"],
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

            "Salary_Impact":       salary,
            "Bidirectional_Note":  bidir_note,

            "Sample_Sizes": {
                "Source_Listings": len(source_df),
                "Target_Listings": len(target_df),
            }
        }
    
# Example usage