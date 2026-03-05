import re
import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple

class CareerPathEngine:
    
    MIN_SAMPLES = 8
    BASE_HOURS_PER_SKILL = 35  # Reduced from 40 — more realistic for focused learners
    
    # Prior knowledge multipliers — FIXED (advanced should REDUCE time)
    PRIOR_KNOWLEDGE_FACTORS = {
        "none":     1.30,  # No background → 30% more time needed
        "basic":    1.00,  # Baseline
        "intermediate": 0.75,  # 25% faster
        "advanced": 0.50,  # 50% faster — inverted from original 1.5
    }
    
    # Domain weight profiles (consistent with InterviewDifficultyEngine)
    DOMAIN_WEIGHTS = {
        'data scientist':           {'alpha': 0.20, 'beta': 0.55, 'gamma': 0.25},
        'ml engineer':              {'alpha': 0.25, 'beta': 0.45, 'gamma': 0.30},
        'software engineer':        {'alpha': 0.50, 'beta': 0.30, 'gamma': 0.20},
        'backend developer':        {'alpha': 0.45, 'beta': 0.30, 'gamma': 0.25},
        'frontend developer':       {'alpha': 0.35, 'beta': 0.55, 'gamma': 0.10},
        'full stack developer':     {'alpha': 0.40, 'beta': 0.40, 'gamma': 0.20},
        'devops engineer':          {'alpha': 0.25, 'beta': 0.40, 'gamma': 0.35},
        'data analyst':             {'alpha': 0.10, 'beta': 0.70, 'gamma': 0.20},
        'cybersecurity engineer':   {'alpha': 0.20, 'beta': 0.60, 'gamma': 0.20},
    }
    
    # Readiness score thresholds for final verdict
    READINESS_THRESHOLDS = {
        (80, 100): ("🟢 Ready to Apply",       "green"),
        (60, 79):  ("🟡 Almost Ready",          "yellow"),
        (40, 59):  ("🟠 Meaningful Gap",        "orange"),
        (20, 39):  ("🔴 Significant Work Ahead","red"),
        (0,  19):  ("⚪ Starting From Scratch", "gray"),
    }
    
    def __init__(self,
                 prerequisite_engine=None,
                 transferability_engine=None,
                 project_evaluator=None,
                 interview_engine=None,
                 blocker_detector=None,
                 evolution_engine=None):
        """
        Accepts injected sub-engines for orchestration.
        Falls back to internal calculations if engines not provided.
        This design allows full standalone use OR rich orchestrated use.
        """
        self.prereq_engine    = prerequisite_engine
        self.transfer_engine  = transferability_engine
        self.project_engine   = project_evaluator
        self.interview_engine = interview_engine
        self.blocker_engine   = blocker_detector
        self.evolution_engine = evolution_engine
        self.logger           = logging.getLogger(__name__)


    def _filter_domain(self, df: pd.DataFrame,
                        target_domain: str,
                        experience_band: Tuple = (0, 3)) -> pd.DataFrame:
        """Job_Type first, Title fallback. Safe copy. Experience filtered."""
        df = df.copy()

        if 'TItle_Cleaned' in df.columns and 'Title_Cleaned' not in df.columns:
            df = df.rename(columns={'TItle_Cleaned': 'Title_Cleaned'})

        if 'Job_Type' in df.columns:
            exact = df[df['Job_Type'].str.lower() == target_domain.lower()]
            domain_df = exact if len(exact) >= self.MIN_SAMPLES else pd.DataFrame()
        else:
            domain_df = pd.DataFrame()

        if domain_df.empty:
            col = 'Title_Cleaned' if 'Title_Cleaned' in df.columns else None
            if col:
                pattern = r'\b' + re.escape(target_domain) + r'\b'
                domain_df = df[df[col].str.contains(
                    pattern, case=False, na=False, regex=True
                )]

        if domain_df.empty:
            return pd.DataFrame()

        if 'Min_Experience' in domain_df.columns:
            min_e, max_e = experience_band
            domain_df = domain_df[
                (domain_df['Min_Experience'] >= min_e) &
                (domain_df['Min_Experience'] <= max_e + 1)
            ]

        return domain_df.copy()

    def _extract_required_skills(self, domain_df: pd.DataFrame) -> Dict[str, float]:
        """
        NaN-safe skill extraction with importance weighting.
        Returns {skill_name_lowercase: importance_score}
        """
        if domain_df.empty:
            return {}

        total   = len(domain_df)
        counts  = {}
        weights = {'Star_Skills': 2.0, 'Combined_Skills': 1.0, 'Normal_Skills': 0.6}

        for col, w in weights.items():
            if col not in domain_df.columns:
                continue
            for skills_str in domain_df[col].fillna('').astype(str):
                for skill in skills_str.split(','):
                    s = re.sub(r'\s+', ' ', skill.strip().lower())
                    if s and len(s) > 1:
                        counts[s] = counts.get(s, 0) + w

        return {
            skill: count / total
            for skill, count in counts.items()
            if count / total > 0.02
        }

    def _normalize_user_skills(self, user_skills: List[str]) -> set:
        """Lowercase + alias resolution for user skill input."""
        ALIASES = {
            'python3': 'python', 'py': 'python',
            'js': 'javascript', 'react.js': 'react', 'reactjs': 'react',
            'node': 'node.js', 'nodejs': 'node.js',
            'ml': 'machine learning', 'dl': 'deep learning',
            'sklearn': 'scikit-learn', 'scikit learn': 'scikit-learn',
            'postgres': 'postgresql', 'mongo': 'mongodb',
            'k8s': 'kubernetes', 'ts': 'typescript',
        }
        normalized = set()
        for skill in user_skills:
            cleaned  = re.sub(r'\s+', ' ', skill.lower().strip())
            resolved = ALIASES.get(cleaned, cleaned)
            normalized.add(resolved)
        return normalized

    def _calculate_learning_time(self,
                                   required_profile: Dict[str, float],
                                   user_skills: set,
                                   prior_knowledge: str) -> dict:
        """
        Fix 1: Only count GAP skills — not all required skills.
        Fix 2: Prior knowledge REDUCES time (advanced = 0.5x, not 1.5x).
        Fix 3: Weight by importance — high-importance gaps take more time.
        """
        gap_skills = {
            skill: imp
            for skill, imp in required_profile.items()
            if skill not in user_skills
        }

        if not gap_skills:
            return {
                "gap_skills_count": 0,
                "total_hours":      0,
                "weeks_at_10hrs":   0,
                "months":           0,
                "label":            "✅ No learning gap detected"
            }

        # Importance-weighted hours per skill
        # High-importance skills (score > 0.5) need more depth → 1.5x hours
        total_hours = sum(
            self.BASE_HOURS_PER_SKILL * (1.5 if imp > 0.5 else 1.0)
            for imp in gap_skills.values()
        )

        # Apply prior knowledge multiplier (FIXED — advanced reduces, not increases)
        pk_factor   = self.PRIOR_KNOWLEDGE_FACTORS.get(prior_knowledge, 1.0)
        total_hours = total_hours * pk_factor

        weeks   = round(total_hours / 10, 1)   # Assumes 10 hrs/week
        months  = round(weeks / 4.3, 1)

        return {
            "gap_skills_count": len(gap_skills),
            "total_hours":      round(total_hours),
            "weeks_at_10hrs":   weeks,
            "months":           months,
            "prior_factor":     pk_factor,
            "label": (
                f"~{months} months at 10hrs/week" if months >= 1
                else f"~{weeks} weeks at 10hrs/week"
            ),
            "top_gap_skills":   sorted(
                gap_skills.items(), key=lambda x: x[1], reverse=True
            )[:5]
        }

    def _calculate_skill_overlap(self,
                                   required_profile: Dict[str, float],
                                   user_skills: set) -> dict:
        """
        Fix: Denominator = actual required skill count, not avg_req_skills.
        Importance-weighted: having high-importance skills counts more.
        5-tier readiness status replaces binary.
        """
        if not required_profile:
            return {"score": 0.0, "status": "No data", "weighted_coverage": 0.0}

        total_importance   = sum(required_profile.values())
        covered_importance = sum(
            imp for skill, imp in required_profile.items()
            if skill in user_skills
        )

        common_count  = len(set(required_profile.keys()) & user_skills)
        count_ratio   = common_count / len(required_profile)
        weighted_cov  = covered_importance / total_importance if total_importance > 0 else 0.0

        # Composite: 60% weighted coverage, 40% count ratio
        composite = round(0.60 * weighted_cov + 0.40 * count_ratio, 3)

        if composite >= 0.75:
            status = "🟢 Strong overlap — minor gaps only"
        elif composite >= 0.55:
            status = "🟡 Good base — a few key skills missing"
        elif composite >= 0.35:
            status = "🟠 Moderate overlap — meaningful upskilling needed"
        elif composite >= 0.15:
            status = "🔴 Thin overlap — significant gap"
        else:
            status = "⚪ Minimal overlap — building from scratch"

        matched = sorted(
            [s for s in required_profile if s in user_skills],
            key=lambda s: required_profile[s], reverse=True
        )

        return {
            "composite_score":   composite,
            "weighted_coverage": round(weighted_cov, 3),
            "count_ratio":       round(count_ratio, 3),
            "matched_count":     common_count,
            "required_count":    len(required_profile),
            "matched_skills":    matched[:8],
            "status":            status
        }

    def _get_project_benchmark(self, df: pd.DataFrame,
                                  target_domain: str,
                                  user_project_stats: Optional[Dict],
                                  experience_band: Tuple) -> dict:
        """Call ProjectComplexityEvaluator if available, else internal fallback."""
        if self.project_engine is not None:
            try:
                return self.project_engine.evaluate_portfolio_readiness(
                    df, target_domain, user_project_stats, experience_band
                )
            except Exception as e:
                self.logger.warning(f"ProjectComplexityEvaluator failed: {e}")

        # Internal fallback — uses Skill_Count median as proxy
        domain_df = self._filter_domain(df, target_domain, experience_band)
        if domain_df.empty or 'Skill_Count' not in domain_df.columns:
            return {"Market_Benchmark": {"Score": 5.0, "Label": "Medium Complexity (estimated)"}}

        median_skills = pd.to_numeric(
            domain_df['Skill_Count'], errors='coerce'
        ).median()
        score = min(10.0, (median_skills / 20) * 10) if not pd.isna(median_skills) else 5.0

        label = (
            "Advanced / Production-Ready" if score >= 6.5 else
            "Medium Complexity"           if score >= 4.0 else
            "Basic / CRUD Level"
        )
        return {"Market_Benchmark": {"Score": round(score, 1), "Label": label}}

    def _get_interview_difficulty(self, df: pd.DataFrame,
                                    target_domain: str,
                                    experience_band: Tuple) -> dict:
        """Call InterviewDifficultyEngine if available, else internal fallback."""
        if self.interview_engine is not None:
            try:
                return self.interview_engine.calculate_interview_difficulty(
                    df, target_domain, experience_band
                )
            except Exception as e:
                self.logger.warning(f"InterviewDifficultyEngine failed: {e}")

        # Internal fallback — weight-based estimate only
        domain_lower = target_domain.lower()
        weights = self.DOMAIN_WEIGHTS.get(
            domain_lower,
            {'alpha': 0.35, 'beta': 0.40, 'gamma': 0.25}
        )

        # Conservative mid-point estimate per pillar
        estimated_index = (
            weights['alpha'] * 5.0 +   # DSA: moderate
            weights['beta']  * 5.0 +   # Domain: moderate
            weights['gamma'] * 4.5     # System design: slightly lower
        )

        return {
            "Difficulty": {
                "Index": round(estimated_index, 1),
                "Label": "Estimated (InterviewDifficultyEngine not connected)",
            }
        }

    def _get_blockers(self, df: pd.DataFrame,
                       target_domain: str,
                       experience_band: Tuple) -> dict:
        """Call HiddenBlockerDetector if available, else internal fallback."""
        if self.blocker_engine is not None:
            try:
                return self.blocker_engine.scan_for_blockers(
                    df, target_domain, experience_band
                )
            except Exception as e:
                self.logger.warning(f"HiddenBlockerDetector failed: {e}")

        # Internal fallback — fresher % check only
        domain_df = self._filter_domain(df, target_domain, experience_band)
        blockers  = []

        if not domain_df.empty and 'Min_Experience' in domain_df.columns:
            fresher_pct = (domain_df['Min_Experience'] <= 1).mean() * 100
            if fresher_pct < 30:
                blockers.append({
                    "blocker_id": "experience_inflation",
                    "severity":   round(((30 - fresher_pct) / 30) * 0.90, 3),
                    "message":    f"Only {fresher_pct:.1f}% of roles accept 0-1yr exp.",
                    "resolution": "Target internships and open-source to build experience."
                })

        return {"Detected_Blockers": blockers, "Overall_Risk": {"score": 0.0}}

    def _get_evolution_path(self, df: pd.DataFrame,
                              target_domain: str) -> Optional[dict]:
        """Call RoleEvolutionEngine if available."""
        if self.evolution_engine is not None:
            try:
                return self.evolution_engine.predict_evolution_path(
                    df, target_domain, steps=2
                )
            except Exception as e:
                self.logger.warning(f"RoleEvolutionEngine failed: {e}")
        return None

    def _compute_readiness_score(self,
                                   overlap: dict,
                                   learning_time: dict,
                                   blocker_data: dict,
                                   interview_data: dict) -> dict:
        """
        Single 0-100 readiness score from all dimensions.

        Components:
        - Skill overlap (40%): most important — do you have what they need?
        - Blocker severity (25%): hidden walls can block even skilled candidates
        - Interview readiness proxy (20%): difficulty vs your preparation level
        - Time manageability (15%): is the gap achievable in a reasonable timeframe?
        """
        # Component 1: Skill overlap (0-100)
        overlap_component = overlap.get("composite_score", 0.5) * 100

        # Component 2: Blocker penalty (0-100, inverted — high blockers = low score)
        blocker_risk  = blocker_data.get("Overall_Risk", {}).get("score", 0.0)
        blocker_component = (1 - blocker_risk) * 100

        # Component 3: Interview manageability
        # Lower difficulty → higher readiness (simpler interviews are more passable)
        interview_index = interview_data.get("Difficulty", {}).get("Index", 5.0)
        interview_component = max(0, (10 - interview_index) / 10 * 100)

        # Component 4: Time manageability
        # <3 months = highly achievable, >12 months = very challenging
        months = learning_time.get("months", 6)
        if months <= 0:
            time_component = 100
        elif months <= 3:
            time_component = 90
        elif months <= 6:
            time_component = 70
        elif months <= 12:
            time_component = 45
        else:
            time_component = 20

        # Weighted composite
        composite = (
            overlap_component    * 0.40 +
            blocker_component    * 0.25 +
            interview_component  * 0.20 +
            time_component       * 0.15
        )
        composite = round(float(np.clip(composite, 0, 100)), 1)

        # Label lookup
        label, color = "Unknown", "gray"
        for (low, high), (lbl, clr) in self.READINESS_THRESHOLDS.items():
            if low <= composite <= high:
                label, color = lbl, clr
                break
            
        return {
            "score":       composite,
            "label":       label,
            "color":       color,
            "components": {
                "skill_overlap_score":    round(overlap_component, 1),
                "blocker_clearance":      round(blocker_component, 1),
                "interview_manageability": round(interview_component, 1),
                "time_manageability":     round(time_component, 1),
            }
        }

    def calculate_learning_readiness(self,
                                       df: pd.DataFrame,
                                       target_domain: str,
                                       user_skills: List[str],
                                       prior_knowledge: str = "basic",
                                       user_project_stats: Optional[Dict] = None,
                                       experience_band: Tuple = (0, 3)) -> dict:
        """
        Master readiness report. Orchestrates all sub-engines.

        Parameters:
            df:                Job postings DataFrame
            target_domain:     Target job role/domain
            user_skills:       List of user's current skills
            prior_knowledge:   "none" | "basic" | "intermediate" | "advanced"
            user_project_stats: Optional project stats for ProjectComplexityEvaluator
            experience_band:   Experience range to filter domain data
        """
        # 1. Filter domain
        domain_df = self._filter_domain(df, target_domain, experience_band)

        if domain_df.empty:
            return {"error": f"No data found for domain: '{target_domain}'"}

        if len(domain_df) < self.MIN_SAMPLES:
            return {
                "error": f"Insufficient data: {len(domain_df)} records "
                         f"(need {self.MIN_SAMPLES}+)."
            }

        # 2. Extract required skills profile
        required_profile  = self._extract_required_skills(domain_df)
        user_skills_norm  = self._normalize_user_skills(user_skills)

        # 3. METRIC 1: Skill overlap
        overlap = self._calculate_skill_overlap(required_profile, user_skills_norm)

        # 4. METRIC 2: Learning time (gap skills only, correct prior factor)
        learning_time = self._calculate_learning_time(
            required_profile, user_skills_norm, prior_knowledge
        )

        # 5. METRIC 3: Project complexity benchmark
        project_data = self._get_project_benchmark(
            df, target_domain, user_project_stats, experience_band
        )

        # 6. METRIC 4: Interview difficulty
        interview_data = self._get_interview_difficulty(
            df, target_domain, experience_band
        )

        # 7. METRIC 5: Hidden blockers
        blocker_data = self._get_blockers(df, target_domain, experience_band)

        # 8. Optional: Evolution path (where does this role lead?)
        evolution = self._get_evolution_path(df, target_domain)

        # 9. Composite readiness score
        readiness = self._compute_readiness_score(
            overlap, learning_time, blocker_data, interview_data
        )

        # 10. Domain salary benchmark
        salary_signal = None
        if 'Avg_Salary' in domain_df.columns:
            sal = pd.to_numeric(domain_df['Avg_Salary'], errors='coerce').dropna()
            if len(sal) >= 5:
                Q1, Q3 = sal.quantile(0.25), sal.quantile(0.75)
                sal = sal[(sal >= Q1 - 1.5*(Q3-Q1)) & (sal <= Q3 + 1.5*(Q3-Q1))]
                salary_signal = {
                    "median_lpa": round(sal.median() / 100000, 2),
                    "p25_lpa":    round(sal.quantile(0.25) / 100000, 2),
                    "p75_lpa":    round(sal.quantile(0.75) / 100000, 2),
                }

        # 11. Priority next action
        next_action = self._derive_next_action(
            overlap, learning_time, blocker_data, readiness
        )

        return {
            "Target_Domain":   target_domain,
            "Experience_Band": experience_band,
            "Sample_Size":     len(domain_df),

            "Readiness_Score": readiness,

            "Skill_Overlap": {
                **overlap,
                "Prior_Knowledge_Level": prior_knowledge,
            },

            "Learning_Plan": {
                **learning_time,
                "Prior_Knowledge_Factor": learning_time.get("prior_factor"),
            },

            "Project_Benchmark": project_data.get("Market_Benchmark"),

            "Interview_Difficulty": interview_data.get("Difficulty"),

            "Hidden_Blockers": {
                "Count":           len(blocker_data.get("Detected_Blockers", [])),
                "Overall_Risk":    blocker_data.get("Overall_Risk", {}).get("label", "Unknown"),
                "Top_Blockers":    blocker_data.get("Detected_Blockers", [])[:3],
            },

            "Salary_Benchmark": salary_signal,

            "Evolution_Preview": {
                "first_step":       evolution["Evolution_Path"][0]["to"] if evolution and evolution.get("Evolution_Path") else None,
                "years_to_senior":  evolution["Journey_Summary"]["Total_Years"] if evolution else None,
            } if evolution else None,

            "Priority_Action": next_action,

            "Data_Sources_Used": {
                "PrerequisiteEngine":          self.prereq_engine    is not None,
                "SkillTransferabilityEngine":  self.transfer_engine  is not None,
                "ProjectComplexityEvaluator":  self.project_engine   is not None,
                "InterviewDifficultyEngine":   self.interview_engine is not None,
                "HiddenBlockerDetector":       self.blocker_engine   is not None,
                "RoleEvolutionEngine":         self.evolution_engine is not None,
            }
        }

    def _derive_next_action(self, overlap: dict,
                              learning_time: dict,
                              blocker_data: dict,
                              readiness: dict) -> str:
        """Single most impactful action based on dominant weakness."""
        score = readiness["score"]

        # Check blockers first — they can block regardless of skills
        blockers = blocker_data.get("Detected_Blockers", [])
        if blockers:
            top_blocker = max(blockers, key=lambda b: b.get("severity", 0))
            sev = top_blocker.get("severity", 0)
            if sev > 0.70:
                return (
                    f"🚨 Address critical blocker first: "
                    f"{top_blocker.get('resolution', top_blocker.get('message', ''))}"
                )

        # Then check skill gap
        top_gaps = learning_time.get("top_gap_skills", [])
        if top_gaps and overlap.get("composite_score", 1) < 0.55:
            top_skill = top_gaps[0][0]
            months    = learning_time.get("months", 0)
            return (
                f"🎯 Start with highest-impact gap skill: '{top_skill}'. "
                f"Full preparation: ~{months} months at 10hrs/week."
            )

        if score >= 75:
            return "✅ Apply now — focus on interview prep and portfolio polish."
        elif score >= 55:
            return "🟡 Close the remaining skill gaps, then apply within 1-2 months."
        else:
            return (
                f"📚 Structured learning needed: "
                f"~{learning_time.get('months', '?')} months to job-ready. "
                f"Start today."
            )
        
# Example Usage
if __name__ == "__main__":
    # Initialize the engine (standalone mode without sub-engines)
    career_engine = CareerPathEngine(
        prerequisite_engine=None,
        transferability_engine=None,
        project_evaluator=None,
        interview_engine=None,
        blocker_detector=None,
        evolution_engine=None
    )

    # Example 1: Basic usage with minimal parameters
    print("=" * 70)
    print("EXAMPLE 1: Data Scientist Readiness (Fresher, Basic Python Knowledge)")
    print("=" * 70)
    
    # Assume you have a DataFrame `jobs_df` with job postings
    # For demo, we'll show the structure:
    # jobs_df should have columns: Job_Type, Title_Cleaned, Star_Skills, Combined_Skills,
    # Normal_Skills, Min_Experience, Skill_Count, Avg_Salary
    jobs_df = pd.read_csv(r"D:\DATA SCIENCE AND ML\Project\job_trend_predictor\data\processed\cleaned\cleaned_job_data.csv")
    user_skills_1 = ["Python", "SQL", "Excel", "Statistics"]
    result_1 = career_engine.calculate_learning_readiness(
        df=jobs_df,  # Your job postings DataFrame
        target_domain="Data Scientist",
        user_skills=user_skills_1,
        prior_knowledge="basic",
        experience_band=(0, 1)  # Fresher band
    )
    
    if "error" not in result_1:
        print(f"Target Domain: {result_1['Target_Domain']}")
        print(f"Readiness Score: {result_1['Readiness_Score']['score']}/100 "
              f"({result_1['Readiness_Score']['label']})")
        print(f"Skill Overlap: {result_1['Skill_Overlap']['composite_score']*100:.1f}%")
        print(f"Learning Time: {result_1['Learning_Plan']['label']}")
        print(f"Priority Action: {result_1['Priority_Action']}\n")
    else:
        print(f"Error: {result_1['error']}\n")

    # Example 2: Advanced user with detailed project stats
    print("=" * 70)
    print("EXAMPLE 2: ML Engineer with Intermediate Experience & Projects")
    print("=" * 70)
    
    user_skills_2 = [
        "Python", "Machine Learning", "TensorFlow", "PyTorch",
        "Scikit-learn", "SQL", "Git", "Docker", "AWS"
    ]
    
    user_projects = {
        "project_count": 3,
        "avg_complexity_score": 7.5,
        "has_production_experience": True,
        "github_stars": 15
    }
    
    result_2 = career_engine.calculate_learning_readiness(
        df=jobs_df,
        target_domain="ML Engineer",
        user_skills=user_skills_2,
        prior_knowledge="intermediate",
        user_project_stats=user_projects,
        experience_band=(1, 3)
    )
    
    if "error" not in result_2:
        print(f"Target Domain: {result_2['Target_Domain']}")
        print(f"Readiness Score: {result_2['Readiness_Score']['score']}/100 "
              f"({result_2['Readiness_Score']['label']})")
        print(f"Matched Skills: {', '.join(result_2['Skill_Overlap']['matched_skills'][:5])}")
        print(f"Gap Skills to Learn: {result_2['Learning_Plan']['gap_skills_count']}")
        if result_2['Learning_Plan']['top_gap_skills']:
            print(f"Top Gap Skills: {', '.join([s[0] for s in result_2['Learning_Plan']['top_gap_skills'][:3]])}")
        print(f"Interview Difficulty: {result_2['Interview_Difficulty']['Label']}")
        print(f"Priority Action: {result_2['Priority_Action']}\n")
    else:
        print(f"Error: {result_2['error']}\n")

    # Example 3: Backend Developer transitioning from Frontend
    print("=" * 70)
    print("EXAMPLE 3: Frontend Developer Transitioning to Backend")
    print("=" * 70)
    
    user_skills_3 = [
        "JavaScript", "React", "TypeScript", "HTML", "CSS",
        "Node.js", "Express", "MongoDB", "Git"
    ]
    
    result_3 = career_engine.calculate_learning_readiness(
        df=jobs_df,
        target_domain="Backend Developer",
        user_skills=user_skills_3,
        prior_knowledge="advanced",  # Frontend experience counts as advanced in web dev
        experience_band=(2, 5)
    )
    
    if "error" not in result_3:
        print(f"Target Domain: {result_3['Target_Domain']}")
        print(f"Readiness Score: {result_3['Readiness_Score']['score']}/100 "
              f"({result_3['Readiness_Score']['label']})")
        print(f"Skill Overlap Status: {result_3['Skill_Overlap']['status']}")
        
        # Show salary expectations
        if result_3['Salary_Benchmark']:
            sal = result_3['Salary_Benchmark']
            print(f"Median Salary: ₹{sal['median_lpa']:.2f}L (P25: ₹{sal['p25_lpa']:.2f}L, "
                  f"P75: ₹{sal['p75_lpa']:.2f}L)")
        
        # Show hidden blockers
        if result_3['Hidden_Blockers']['Count'] > 0:
            print(f"⚠️  Detected {result_3['Hidden_Blockers']['Count']} blocker(s):")
            for blocker in result_3['Hidden_Blockers']['Top_Blockers']:
                print(f"   - {blocker['message']}")
        
        print(f"Priority Action: {result_3['Priority_Action']}\n")
    else:
        print(f"Error: {result_3['error']}\n")

    # Example 4: Handling errors gracefully
    print("=" * 70)
    print("EXAMPLE 4: Error Handling - Non-existent Domain")
    print("=" * 70)
    
    result_4 = career_engine.calculate_learning_readiness(
        df=jobs_df,
        target_domain="Unicorn Wrangler",  # Doesn't exist
        user_skills=["Magic", "Sparkles"],
        prior_knowledge="advanced"
    )
    
    if "error" in result_4:
        print(f"✗ {result_4['error']}")
        print("   → Try searching for roles like: Data Scientist, ML Engineer, Backend Developer\n")
    
    # Example 5: Accessing detailed readiness components
    print("=" * 70)
    print("EXAMPLE 5: Detailed Readiness Component Breakdown")
    print("=" * 70)
    
    if "error" not in result_2:
        components = result_2['Readiness_Score']['components']
        print(f"Skill Overlap Component:      {components['skill_overlap_score']:.1f}/100")
        print(f"Blocker Clearance Component:  {components['blocker_clearance']:.1f}/100")
        print(f"Interview Manageability:      {components['interview_manageability']:.1f}/100")
        print(f"Time Manageability:           {components['time_manageability']:.1f}/100")
        print(f"COMPOSITE READINESS SCORE:    {result_2['Readiness_Score']['score']:.1f}/100\n")