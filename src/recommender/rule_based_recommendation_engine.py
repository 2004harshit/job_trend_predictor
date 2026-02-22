


"""
rule_based_recommendation_engine.py
Produces ranked domain recommendations by combining user-profile signals
with live market data from the specialised analytics engines.
"""

import pandas as pd
from typing import Dict, List, Any

from .knowledge_base_store.knowledge_base import (
    DOMAIN_REQUIRED_SKILLS,
    DOMAIN_MATH_HEAVY,
    DOMAIN_LOCATION_FLEXIBLE,
    DOMAIN_ENTRY_BARRIER,
    DOMAIN_COMPETITION,
    DOMAIN_FRESHER_SALARY_RANGE,
    ALL_DOMAINS,
)

# Analytics engines
from src.analytics.market_analysis.demand_score_calculator import MarketDemandEngine
from src.analytics.market_analysis.competition_level_calculator import CompetitionLevelCalculator
from src.analytics.market_analysis.saturation_risk_indicator import SaturationRiskIndicator


class DomainRecommendationEngine:
    """
    Scores every domain in the knowledge base against a user profile and
    returns the top-N best matches with human-readable explanations.

    user_profile schema
    -------------------
    {
        "experience":    str   – "Fresher" | "1-2 years" | "3-5 years" | "5+ years"
        "skills":        list  – e.g. ["Python", "SQL"]
        "location":      str   – e.g. "Jaipur"
        "math_comfort":  str   – "Weak" | "Moderate" | "Strong"
    }
    """

    def __init__(self, df: pd.DataFrame):
        self.df = df
        self.domains = ALL_DOMAINS

        # Sub-engines
        self.demand_engine = MarketDemandEngine(data=df)
        self.comp_calculator = CompetitionLevelCalculator()
        self.saturation_indicator = SaturationRiskIndicator()

    # ------------------------------------------------------------------
    # PUBLIC API
    # ------------------------------------------------------------------

    def get_recommendations(
        self, user_profile: Dict[str, Any], top_n: int = 3
    ) -> List[Dict]:
        """
        Returns a list of up to *top_n* recommendation dicts, ranked by
        total score (highest first).
        """
        scores: Dict[str, Dict] = {}
        location = user_profile.get("location", "Jaipur")

        for domain in self.domains:
            market_signals = self._fetch_market_signals(domain, location)
            scores[domain] = self._calculate_domain_score(
                domain, user_profile, market_signals
            )

        ranked = sorted(
            scores.items(),
            key=lambda x: x[1]["total_score"],
            reverse=True,
        )[:top_n]

        return [
            self._format_output(domain, score_breakdown, user_profile)
            for domain, score_breakdown in ranked
        ]

    # ------------------------------------------------------------------
    # PRIVATE HELPERS
    # ------------------------------------------------------------------

    def _fetch_market_signals(self, domain: str, location: str) -> Dict:
        """Query the specialised engines for live market signals."""
        try:
            demand_data = self.demand_engine.calculate_metrics(
                domains=[domain]
            ).get(domain, {})
        except Exception:
            demand_data = {}

        try:
            comp_data = self.comp_calculator.calculate_competition_level(
                self.df, domain
            )
        except Exception:
            comp_data = {}

        try:
            sat_data = self.saturation_indicator.get_saturation_risk(
                self.df, domain
            )
        except Exception:
            sat_data = {}

        return {
            "demand_score": demand_data.get("Overall_Demand_Score", 5.0),
            "comp_level": comp_data.get("Level", "Medium"),
            "sat_risk": sat_data.get("Risk_Level", "Safe"),
            "growth_trend": demand_data.get("Breakdown", {}).get(
                "Growth_Trend", 5.0
            ),
        }

    def _calculate_domain_score(
        self, domain: str, profile: Dict, signals: Dict
    ) -> Dict:
        """
        Scoring breakdown (max 100 pts):
          Skill Match      : 40 pts
          Market Demand    : 30 pts
          Entry Feasibility: 30 pts
          Math Penalty     : up to -15 pts
        """
        breakdown: Dict[str, float] = {}

        # 1. Skill Match (40 pts)
        user_skills = set(s.lower() for s in profile.get("skills", []))
        domain_skills = set(
            s.lower() for s in DOMAIN_REQUIRED_SKILLS.get(domain, [])
        )
        if domain_skills:
            overlap = len(user_skills & domain_skills)
            breakdown["skill_score"] = round(
                (overlap / len(domain_skills)) * 40, 2
            )
        else:
            breakdown["skill_score"] = 0.0

        # 2. Market Demand (30 pts)
        demand_score = signals.get("demand_score", 5.0)
        breakdown["market_score"] = round((demand_score / 10.0) * 30, 2)

        # 3. Entry Feasibility (30 pts)
        base_feasibility = 20.0
        experience = profile.get("experience", "Fresher")

        if experience == "Fresher":
            if signals.get("comp_level") == "High":
                base_feasibility -= 8.0
            if signals.get("sat_risk") == "Highly Competitive":
                base_feasibility -= 7.0
            # Also check static entry barrier
            entry_barrier = DOMAIN_ENTRY_BARRIER.get(domain, 5)
            if entry_barrier >= 8:
                base_feasibility -= 5.0
        else:
            # Experienced candidates handle competitive domains better
            base_feasibility += 10.0

        breakdown["feasibility_score"] = max(0.0, round(base_feasibility, 2))

        # 4. Math Penalty (hard filter)
        math_penalty = 0.0
        if (
            DOMAIN_MATH_HEAVY.get(domain, False)
            and profile.get("math_comfort") == "Weak"
        ):
            math_penalty = -15.0
        breakdown["math_penalty"] = math_penalty

        # Total
        breakdown["total_score"] = round(
            breakdown["skill_score"]
            + breakdown["market_score"]
            + breakdown["feasibility_score"]
            + breakdown["math_penalty"],
            2,
        )

        return breakdown

    def _format_output(
        self, domain: str, score_breakdown: Dict, profile: Dict
    ) -> Dict:
        """Builds the final recommendation dict consumed by the UI."""
        return {
            "domain": domain,
            "match_percentage": round(
                max(0.0, min(100.0, score_breakdown["total_score"])), 1
            ),
            "reasoning": self._generate_explanation(domain, score_breakdown, profile),
            "pros": self._get_pros(domain, profile),
            "cons": self._get_cons(domain, score_breakdown),
            "timeline": self._estimate_timeline(domain, profile),
            "market_metrics": self._get_market_metrics(domain),
        }

    def _generate_explanation(
        self, domain: str, scores: Dict, profile: Dict
    ) -> List[str]:
        reasons: List[str] = []

        if scores.get("skill_score", 0) >= 20:
            reasons.append(
                "Strong alignment with your current technical skill set."
            )
        elif scores.get("skill_score", 0) >= 10:
            reasons.append(
                "Moderate overlap with your skills — a manageable skill gap exists."
            )
        else:
            reasons.append(
                "Low initial skill overlap, but the role is learnable with focused prep."
            )

        if scores.get("market_score", 0) >= 20:
            reasons.append(
                f"The market for {domain} is currently expanding with strong hiring signals."
            )

        if scores.get("math_penalty", 0) < 0:
            reasons.append(
                "⚠️ Heavy mathematical requirements — consider upskilling first."
            )

        if DOMAIN_LOCATION_FLEXIBLE.get(domain) and profile.get(
            "location"
        ) not in ["Bangalore", "Hyderabad"]:
            reasons.append(
                "Remote-friendly role — location is not a limiting factor."
            )

        return reasons

    def _get_pros(self, domain: str, profile: Dict) -> List[str]:
        pros: List[str] = ["High global demand", "Strong career growth trajectory"]

        if DOMAIN_LOCATION_FLEXIBLE.get(domain, False):
            pros.append("Remote / hybrid work friendly")

        if DOMAIN_ENTRY_BARRIER.get(domain, 5) <= 5:
            pros.append("Relatively low entry barrier for freshers")

        salary_range = DOMAIN_FRESHER_SALARY_RANGE.get(domain, (3.0, 7.0))
        if salary_range[1] >= 9.0:
            pros.append(f"High earning potential (up to ₹{salary_range[1]} LPA fresher)")

        return pros

    def _get_cons(self, domain: str, score_breakdown: Dict) -> List[str]:
        cons: List[str] = []

        if DOMAIN_ENTRY_BARRIER.get(domain, 5) >= 8:
            cons.append("Steep learning curve — requires significant preparation")

        if DOMAIN_COMPETITION.get(domain, 5) >= 8:
            cons.append("Highly competitive job market with many candidates")

        if DOMAIN_MATH_HEAVY.get(domain, False):
            cons.append("Requires strong mathematical and statistical foundations")

        if score_breakdown.get("math_penalty", 0) < 0:
            cons.append("Your current math comfort level may be a bottleneck")

        return cons

    def _estimate_timeline(self, domain: str, profile: Dict) -> str:
        """Returns a rough upskilling timeline based on barrier and experience."""
        barrier = DOMAIN_ENTRY_BARRIER.get(domain, 5)
        experience = profile.get("experience", "Fresher")

        if experience != "Fresher":
            return "2-3 Months"
        if barrier <= 4:
            return "2-3 Months"
        if barrier <= 7:
            return "4-6 Months"
        return "8-12 Months"

    def _get_market_metrics(self, domain: str) -> Dict:
        """Pulls average salary from the dataset; falls back to knowledge base."""
        try:
            avg_sal = self.df[self.df["domain"] == domain]["avg_salary"].mean()
            if not pd.isna(avg_sal):
                return {
                    "avg_starting_salary": f"₹{avg_sal / 100_000:.1f} LPA"
                }
        except Exception:
            pass

        # Fallback to static knowledge base salary range
        low, high = DOMAIN_FRESHER_SALARY_RANGE.get(domain, (3.0, 7.0))
        return {"avg_starting_salary": f"₹{low:.1f} – ₹{high:.1f} LPA"}


# ------------------------------------------------------------------
# Quick smoke-test
# ------------------------------------------------------------------
if __name__ == "__main__":
    sample_df = pd.DataFrame(
        [
            {
                "domain": "Data Scientist",
                "location": "Jaipur",
                "job_count": 45,
                "avg_salary": 600_000,
            },
            {
                "domain": "Web Developer",
                "location": "Jaipur",
                "job_count": 120,
                "avg_salary": 450_000,
            },
        ]
    )

    engine = DomainRecommendationEngine(sample_df)

    user_profile = {
        "location": "Jaipur",
        "experience": "Fresher",
        "skills": ["Python", "SQL"],
        "math_comfort": "Strong",
    }

    results = engine.get_recommendations(user_profile, top_n=3)
    for r in results:
        print(r)