"""
AnalyticsPipeline — Three-Phase Orchestrator
=============================================

Phase 1 — Global     : No user data needed. Safe to cache globally via @st.cache_data.
                       Only MarketDemandEngine qualifies.

Phase 2 — Domain     : Needs domain + experience_band + location.
                       Triggered immediately after user selects domain on the form.
                       Includes RoleEvolutionEngine (only needs a role string).
                       Accepts recommended_domains (top 3 from recommender) to
                       slice the cached global market_demand report — no
                       recomputation needed.

Phase 3 — Profile    : Needs user_skills + user_project_stats + prior_knowledge.
                       Triggered after full profile form submission.
                       CareerPathEngine is injected with sub-engines to avoid
                       duplicate computation — it internally calls HiddenBlockerDetector,
                       InterviewDifficultyEngine, ProjectComplexityEvaluator, and
                       RoleEvolutionEngine rather than running them separately.

Streamlit Usage
---------------
    # app.py

    @st.cache_data
    def get_global_metrics(_df):
        return AnalyticsPipeline(_df).run_global_phase()

    # After domain form submitted:
    if domain_submitted:
        pipeline = AnalyticsPipeline(df)

        # Pass top 3 domains from your recommender — Phase 2 slices the
        # cached global market_demand report automatically, no recomputation.
        recommended = recommender.get_top_domains(user_profile, n=3)

        st.session_state["domain_analytics"] = pipeline.run_domain_phase(
            domain=domain,
            experience_band=experience_band,
            location=location,
            recommended_domains=recommended,  # ["Data Scientist", "ML Engineer", ...]
        )

    # After full profile form submitted:
    if profile_submitted:
        pipeline = AnalyticsPipeline(df)
        st.session_state["profile_analytics"] = pipeline.run_profile_phase(
            domain=domain,
            experience_band=experience_band,
            location=location,
            user_skills=user_skills,
            prior_knowledge=prior_knowledge,
            user_project_stats=user_project_stats,
            domain_results=st.session_state["domain_analytics"],
            target_domain_2=target_domain_2,   # optional
        )

    # On any dashboard page — just read, never recompute:
    analytics = st.session_state.get("profile_analytics")
    domain_analytics = st.session_state.get("domain_analytics")
"""

import json
import logging
import datetime
import pandas as pd
from typing import Dict, List, Optional, Tuple

# ── Career Insights ────────────────────────────────────────────────────────────
from src.analytics.career_insights.career_path_engine import CareerPathEngine

# NOTE: The file is named role_evaluation_engine.py but the class inside
#       is RoleEvolutionEngine — import accordingly.
from src.analytics.career_insights.role_evaluation_engine import RoleEvolutionEngine

# ── Domain Analysis ────────────────────────────────────────────────────────────
from src.analytics.domain_analysis.ai_replacement_risk_engine import AIReplacementRiskEngine
from src.analytics.domain_analysis.domain_stability_engine import DomainStabilityEngine
from src.analytics.domain_analysis.salary_growth_engine import SalaryGrowthEngine
from src.analytics.domain_analysis.skill_transferability_engine import SkillTransferabilityEngine

# ── Entry Barriers ─────────────────────────────────────────────────────────────
from src.analytics.entry_barriers.hidden_blocker_detector import HiddenBlockerDetector
from src.analytics.entry_barriers.interview_difficulty_engine import InterviewDifficultyEngine
from src.analytics.entry_barriers.prequisite_engine import PrerequisiteEngine
from src.analytics.entry_barriers.project_complexity_evaluator import ProjectComplexityEvaluator

# ── Market Analysis ────────────────────────────────────────────────────────────
from src.analytics.market_analysis.average_salary_calculator import AverageSalaryRangeCalculator
from src.analytics.market_analysis.competition_level_calculator import CompetitionLevelCalculator
from src.analytics.market_analysis.demand_score_calculator import MarketDemandEngine
from src.analytics.market_analysis.job_market_velocity_calculator import JobMarketVelocityCalculator
from src.analytics.market_analysis.saturation_risk_indicator import SaturationRiskIndicator

# ── Real Talk ──────────────────────────────────────────────────────────────────
from src.analytics.real_talk.adaptive_real_talk_engine import AdaptiveRealTalkEngine

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────────────────────
# JSON Encoder — handles date/datetime objects returned by some engines
# ──────────────────────────────────────────────────────────────────────────────
class SafeJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (datetime.date, datetime.datetime)):
            return obj.isoformat()
        if isinstance(obj, float) and (obj != obj):  # NaN check
            return None
        return super().default(obj)


# ──────────────────────────────────────────────────────────────────────────────
# Column Normalizer — maps legacy PascalCase/typo columns to snake_case
#
# All DataFrame columns MUST be lowercase + snake_case.
# This map handles older CSVs or upstream sources that use different naming.
# ──────────────────────────────────────────────────────────────────────────────
COLUMN_MAP = {
    'TItle_Cleaned': 'title_cleaned',
    'Title_Cleaned': 'title_cleaned',
    'Company_Cleaned': 'company_cleaned',
    'Min_Experience': 'min_experience',
    'Max_Experience': 'max_experience',
    'Min_Salary': 'min_salary',
    'Max_Salary': 'max_salary',
    'Avg_Salary': 'avg_salary',
    'Job_Type': 'job_type',
    'Combined_Skills': 'combined_skills',
    'Star_Skills': 'star_skills',
    'Skill_Count': 'skill_count',
    'Description_Cleaned': 'description_cleaned',
    'Scraped_At_Cleaned': 'scraped_at_cleaned',
    'Posted_Date': 'posted_date',
    'Location': 'location',
    'UG_Degree': 'ug_degree',
    'PG_Degree': 'pg_degree',
    'No of applicant applied cleaned': 'no_of_applicant_applied_cleaned',
    'No of job opening cleaned ': 'no_of_job_opening_cleaned',
    'Job Title': 'job_title',
    'Employment Type': 'employment_type',
}

def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Rename columns from your actual CSV to what all engines expect.
    Call this once when loading the dataframe — never modify it again.
    """
    df = df.copy()
    rename = {k: v for k, v in COLUMN_MAP.items() if k in df.columns}
    if rename:
        df = df.rename(columns=rename)
        logger.info(f"Column normalizer applied: {rename}")
    return df


class AnalyticsPipeline:
    """
    Orchestrates all analytics engines across three phases.
    Each phase is a separate method — call them at the right moment in the UI.
    """

    # ── Experience band label → tuple mapping ─────────────────────────────────
    # Accepts both string labels (from Streamlit UI) and raw tuples (from code).
    # All internal engines expect Tuple[int, int] — never a string.
    _BAND_MAP: Dict[str, Tuple[int, int]] = {
        "fresher":      (0, 1),
        "junior":       (1, 3),
        "mid":          (3, 6),
        "senior":       (6, 12),
        "intermediate": (2, 5),   # alias used in prior_knowledge field
        "basic":        (0, 1),   # alias for prior_knowledge="basic"
        "advanced":     (5, 12),  # alias for prior_knowledge="advanced"
    }

    @classmethod
    def _resolve_band(cls, experience_band) -> Tuple[int, int]:
        """
        Normalize experience_band to Tuple[int, int].

        Accepts:
          - Tuple/List:  (0, 3)  → (0, 3)   (passthrough)
          - String:     "fresher" → (0, 1)
          - None:        → (0, 5)  (safe default)
        """
        if experience_band is None:
            return (0, 5)
        if isinstance(experience_band, (tuple, list)) and len(experience_band) == 2:
            return (int(experience_band[0]), int(experience_band[1]))
        if isinstance(experience_band, str):
            key = experience_band.lower().strip()
            if key in cls._BAND_MAP:
                return cls._BAND_MAP[key]
            logger.warning(
                f"Unknown experience_band string '{experience_band}'. "
                f"Falling back to (0, 5). Valid values: {list(cls._BAND_MAP.keys())}"
            )
            return (0, 5)
        logger.warning(f"Unrecognised experience_band type {type(experience_band)}. Using (0, 5).")
        return (0, 5)
    # ──────────────────────────────────────────────────────────────────────────

    def __init__(self, data: pd.DataFrame):
        # Normalize column names once — all engines see clean names
        self.data = normalize_columns(data)

    # ──────────────────────────────────────────────────────────────────────────
    # PHASE 1 — Global metrics (no user data needed)
    # Safe to wrap with @st.cache_data in Streamlit.
    # ──────────────────────────────────────────────────────────────────────────
    def run_global_phase(self) -> dict:
        """
        Run once at app startup. Results are shared across all users.
        Only MarketDemandEngine qualifies — it needs no user info at all.

        Streamlit usage:
            @st.cache_data
            def get_global_metrics(_df):
                return AnalyticsPipeline(_df).run_global_phase()
        """
        logger.info("Phase 1 | Running global metrics")
        results = {}

        try:
            # MarketDemandEngine takes df in __init__, then .calculate_metrics()
            results["market_demand"] = MarketDemandEngine(self.data).calculate_metrics()
            logger.info("Phase 1 | market_demand ✓")
        except Exception as e:
            logger.error(f"Phase 1 | MarketDemandEngine failed: {e}")
            results["market_demand"] = None

        return results

    # ──────────────────────────────────────────────────────────────────────────
    # PHASE 2 — Domain-level metrics
    # Triggered after user selects domain + experience + location on the form.
    # Does NOT need user_skills or user_project_stats.
    # ──────────────────────────────────────────────────────────────────────────
    def run_domain_phase(
        self,
        domain: str,
        experience_band: Tuple[int, int],
        location: str,
        nearby_cities: Optional[List[str]] = None,
        recommended_domains: Optional[List[str]] = None,
        global_results: Optional[Dict] = None,
    ) -> dict:
        """
        Parameters
        ----------
        domain               : Target job role, e.g. "Data Scientist"
        experience_band      : Experience range as tuple, e.g. (0, 3)
        location             : Target city, e.g. "Bangalore"
        nearby_cities        : Optional list of nearby cities for velocity calc
        recommended_domains  : Top 3 domains from your recommender engine,
                               e.g. ["Data Scientist", "ML Engineer", "Data Analyst"].
                               Used to slice the cached global market_demand report.
                               If None, market_demand_top3 is not added to results.
        global_results       : Output of run_global_phase() from session_state.
                               Required if recommended_domains is provided.
        """
        logger.info(f"Phase 2 | Running domain metrics — domain={domain}")
        experience_band = self._resolve_band(experience_band)   # accept str or tuple
        nearby_cities = nearby_cities or []
        results = {}

        # ── Slice market_demand from Phase 1 cache — zero recomputation ──────
        # MarketDemandEngine scores are relative (max_freq normalization), so
        # we MUST compute all domains in Phase 1 and only slice here.
        if recommended_domains and global_results:
            full_demand = global_results.get("market_demand") or {}
            results["market_demand_top3"] = {
                d: full_demand[d]
                for d in recommended_domains
                if d in full_demand
            }
            missing = [d for d in recommended_domains if d not in full_demand]
            if missing:
                logger.warning(
                    f"Phase 2 | market_demand_top3: domains not found in "
                    f"global cache — {missing}. Check domain name spelling."
                )
            logger.info(
                f"Phase 2 | market_demand_top3 ✓ "
                f"({list(results['market_demand_top3'].keys())})"
            )
        elif recommended_domains and not global_results:
            logger.warning(
                "Phase 2 | recommended_domains provided but global_results is "
                "None — market_demand_top3 skipped. Pass global_results from "
                "st.session_state['global_analytics']."
            )

        # 1. AI Replacement Risk
        try:
            results["ai_risk"] = AIReplacementRiskEngine().calculate_ai_risk(
                self.data, domain
            )
            logger.info("Phase 2 | ai_risk ✓")
        except Exception as e:
            logger.error(f"Phase 2 | AIReplacementRiskEngine failed: {e}")
            results["ai_risk"] = None

        # 2. Domain Stability
        try:
            results["stability"] = DomainStabilityEngine().calculate_stability_score(
                self.data, domain
            )
            logger.info("Phase 2 | stability ✓")
        except Exception as e:
            logger.error(f"Phase 2 | DomainStabilityEngine failed: {e}")
            results["stability"] = None

        # 3. Salary Growth Projection
        try:
            results["salary_growth"] = SalaryGrowthEngine().project_growth(
                self.data, domain
            )
            logger.info("Phase 2 | salary_growth ✓")
        except Exception as e:
            logger.error(f"Phase 2 | SalaryGrowthEngine failed: {e}")
            results["salary_growth"] = None

        # 4. Saturation Risk
        try:
            results["saturation"] = SaturationRiskIndicator().get_saturation_risk(
                self.data, target_domain=domain
            )
            logger.info("Phase 2 | saturation ✓")
        except Exception as e:
            logger.error(f"Phase 2 | SaturationRiskIndicator failed: {e}")
            results["saturation"] = None

        # 5. Job Market Velocity
        try:
            results["velocity"] = JobMarketVelocityCalculator(
                nearby_cities=nearby_cities,
                use_real_date=True,
            ).calculate_velocity(
                df=self.data,
                domain_keywords=[domain],
                target_location=location,
                experience_band=experience_band,
            )
            logger.info("Phase 2 | velocity ✓")
        except Exception as e:
            logger.error(f"Phase 2 | JobMarketVelocityCalculator failed: {e}")
            results["velocity"] = None

        # 6. Average Salary Range
        try:
            results["avg_salary"] = AverageSalaryRangeCalculator(
                lambda_val=0.1
            ).calculate_salary_metrics(
                df=self.data,
                target_domain=domain,
                target_location=location,
                experience_band=experience_band,
            )
            logger.info("Phase 2 | avg_salary ✓")
        except Exception as e:
            logger.error(f"Phase 2 | AverageSalaryRangeCalculator failed: {e}")
            results["avg_salary"] = None

        # 7. Role Evolution Path
        # RoleEvolutionEngine only needs a role string — no user skills required.
        # NOTE: class is RoleEvolutionEngine, not RoleEvaluationEngine.
        try:
            results["role_evolution"] = RoleEvolutionEngine().predict_evolution_path(
                df=self.data,
                current_role=domain,
                steps=3,
                show_branches=True,
            )
            logger.info("Phase 2 | role_evolution ✓")
        except Exception as e:
            logger.error(f"Phase 2 | RoleEvolutionEngine failed: {e}")
            results["role_evolution"] = None

        return results

    # ──────────────────────────────────────────────────────────────────────────
    # PHASE 3 — Full profile metrics
    # Triggered after complete profile form submission (skills + project stats).
    # CareerPathEngine is injected with sub-engines so it orchestrates them
    # internally — avoids double-running HiddenBlockerDetector,
    # InterviewDifficultyEngine, ProjectComplexityEvaluator, RoleEvolutionEngine.
    # AdaptiveRealTalkEngine always runs LAST — it consumes Phase 2 + Phase 3.
    # ──────────────────────────────────────────────────────────────────────────
    def run_profile_phase(
        self,
        domain: str,
        experience_band: Tuple[int, int],
        location: str,
        user_skills: List[str],
        prior_knowledge: str,
        user_project_stats: Dict,
        domain_results: Dict,
        target_domain_2: Optional[str] = None,
    ) -> dict:
        """
        Parameters
        ----------
        domain              : Target job role, e.g. "Data Scientist"
        experience_band     : Experience range as tuple, e.g. (0, 3)
        location            : Target city, e.g. "Bangalore"
        user_skills         : List of user's skills, e.g. ["Python", "SQL"]
        prior_knowledge     : "none" | "basic" | "intermediate" | "advanced"
        user_project_stats  : Dict with keys: features, tech_count,
                              integrations, deployment
        domain_results      : Output of run_domain_phase() — required for
                              AdaptiveRealTalkEngine
        target_domain_2     : Optional second domain for SkillTransferability
        """
        logger.info(f"Phase 3 | Running profile metrics — domain={domain}")
        experience_band = self._resolve_band(experience_band)   # accept str or tuple
        results = {}

        # 1. Competition Level (needs user_skills)
        try:
            results["competition"] = CompetitionLevelCalculator().calculate_competition_level(
                self.data,
                target_domain=domain,
                user_skills=user_skills,
            )
            logger.info("Phase 3 | competition ✓")
        except Exception as e:
            logger.error(f"Phase 3 | CompetitionLevelCalculator failed: {e}")
            results["competition"] = None

        # 2. Prerequisite Analysis (needs user_skills)
        try:
            results["prerequisites"] = PrerequisiteEngine().analyze_prerequisites(
                df=self.data,
                target_domain=domain,
                user_skills=user_skills,
                experience_band=experience_band,
            )
            logger.info("Phase 3 | prerequisites ✓")
        except Exception as e:
            logger.error(f"Phase 3 | PrerequisiteEngine failed: {e}")
            results["prerequisites"] = None

        # 3. Career Path Readiness — CareerPathEngine orchestrates sub-engines
        #    internally via injection. This avoids re-running HiddenBlockerDetector,
        #    InterviewDifficultyEngine, ProjectComplexityEvaluator, and
        #    RoleEvolutionEngine separately.
        try:
            career_engine = CareerPathEngine(
                prerequisite_engine=PrerequisiteEngine(),
                project_evaluator=ProjectComplexityEvaluator(),
                interview_engine=InterviewDifficultyEngine(),
                blocker_detector=HiddenBlockerDetector(),
                evolution_engine=RoleEvolutionEngine(),
                # transferability_engine not injected — handled separately below
            )

            results["career_path"] = career_engine.calculate_learning_readiness(
                df=self.data,
                target_domain=domain,
                user_skills=user_skills,
                prior_knowledge=prior_knowledge,
                user_project_stats=user_project_stats,
                experience_band=experience_band,
            )
            logger.info("Phase 3 | career_path ✓")
        except Exception as e:
            logger.error(f"Phase 3 | CareerPathEngine failed: {e}")
            results["career_path"] = None

        # 4. Skill Transferability — only if second domain selected by user
        if target_domain_2:
            try:
                results["transferability"] = SkillTransferabilityEngine().calculate_transferability(
                    self.data, domain, target_domain_2
                )
                logger.info(f"Phase 3 | transferability ✓ ({domain} → {target_domain_2})")
            except Exception as e:
                logger.error(f"Phase 3 | SkillTransferabilityEngine failed: {e}")
                results["transferability"] = None

        # 5. AdaptiveRealTalkEngine — ALWAYS runs last.
        #    Consumes both Phase 2 (domain_results) and Phase 3 (results so far).
        #    career_path output maps directly to career_path_report parameter.
        #    NOTE: actual signature uses saturation_report (not saturation_results)
        #    and does NOT have a separate saturation_report param — it uses
        #    build_metrics_from_engines() internally which reads saturation_report.
        try:
            results["real_talk"] = AdaptiveRealTalkEngine().generate_real_talk(
                domain=domain,
                career_path_report=results.get("career_path"),
                experience_level=prior_knowledge,
                demand_report=domain_results.get("market_demand_top3", {}).get(domain),
                saturation_report=domain_results.get("saturation"),
                ai_risk_report=domain_results.get("ai_risk"),
                velocity_report=domain_results.get("velocity"),
                transferability_report=results.get("transferability"),
            )
            logger.info("Phase 3 | real_talk ✓")
        except Exception as e:
            logger.error(f"Phase 3 | AdaptiveRealTalkEngine failed: {e}")
            results["real_talk"] = None

        return results


# ──────────────────────────────────────────────────────────────────────────────
# Quick local test (not for Streamlit use)
# ──────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import json
    from src.preprocessing.ingest_data import CSVIngestor
    from src.storage.json_storage_handler import JSONStorageHandler

    file_path = r"D:\DATA SCIENCE AND ML\Project\job_trend_predictor\data\processed\cleaned\cleaned_job_data.csv"

    # Load and normalize columns ONCE here
    # AnalyticsPipeline.__init__ also calls normalize_columns internally,
    # so this is just for the print diagnostic below
    raw_df = CSVIngestor().ingest(file_path)
    df = normalize_columns(raw_df)
    print("Columns after normalization:", df.columns.tolist())

    pipeline = AnalyticsPipeline(df)   # normalize_columns called again internally (safe — idempotent)

    # Phase 1 — run once, cache globally
    global_results = pipeline.run_global_phase()
    print("Phase 1 done:", list(global_results.keys()))
    print("Domains in market_demand:", list((global_results.get("market_demand") or {}).keys()))

    # Simulate top 3 from your recommender
    recommended_domains = ["Data Scientist", "Machine Learning Engineer", "Data Analyst"]

    # Phase 2 — pass global_results + recommended_domains
    domain_results = pipeline.run_domain_phase(
        domain="Data Scientist",
        experience_band=(0, 3),
        location="Bangalore",
        nearby_cities=["Hyderabad", "Chennai"],
        recommended_domains=recommended_domains,
        global_results=global_results,
    )
    print("Phase 2 done:", list(domain_results.keys()))
    print("market_demand_top3 keys:", list((domain_results.get("market_demand_top3") or {}).keys()))

    # Phase 3
    profile_results = pipeline.run_profile_phase(
        domain="Data Scientist",
        experience_band=(0, 3),
        location="Bangalore",
        user_skills=["Python", "SQL", "Machine Learning"],
        prior_knowledge="basic",
        user_project_stats={
            "features": 4,
            "tech_count": 5,
            "integrations": 1,
            "deployment": "cloud_basic",
        },
        domain_results=domain_results,
        target_domain_2="Machine Learning Engineer",  # optional
    )
    print("Phase 3 done:", list(profile_results.keys()))

    # Save all results — SafeJSONEncoder handles date objects and NaN
    all_results = {
        "global": global_results,
        "domain": domain_results,
        "profile": profile_results,
    }
    with open("analytics_output.json", "w") as f:
        json.dump(all_results, f, indent=4, cls=SafeJSONEncoder)
    print("Saved to analytics_output.json")

    # ── In Streamlit, the pattern is: ────────────────────────────────────────
    # st.session_state["global_analytics"]  ← set once via @st.cache_data
    # st.session_state["domain_analytics"]  ← set after domain form submit
    # st.session_state["profile_analytics"] ← set after profile form submit
    #
    # Phase 2 call in Streamlit:
    #   pipeline.run_domain_phase(
    #       ...
    #       recommended_domains=recommender.get_top_domains(user_profile, n=3),
    #       global_results=st.session_state.get("global_analytics"),
    #   )