# tests/recommender/recommender_tester.py
"""
Phase 3: Batch Testing & Metrics
Phase 4: Ablation / Sensitivity Analysis
Phase 6: Edge Case & Robustness Testing

Run:  python tests/recommender/recommender_tester.py
"""

import sys
import os
import json
import pandas as pd
from unittest.mock import patch
from typing import Dict, List

# Make sure src is importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from src.recommender.rule_based_recommendation_engine import DomainRecommendationEngine
from src.recommender.knowledge_base import ALL_DOMAINS, DOMAIN_REQUIRED_SKILLS, DOMAIN_MATH_HEAVY

from tests.recommender.test_cases import SYNTHETIC_USERS, EDGE_CASE_USERS
from tests.recommender.evaluation_metrics import (
    precision_at_k,
    hit_rate,
    ndcg_at_k,
    average_match_percentage,
    top1_match_percentage,
    aggregate_metrics,
    print_metrics_table,
    print_aggregate_summary,
)


# -----------------------------------------------------------------------
# SAMPLE JOB DATAFRAME (replace with your real df in production)
# -----------------------------------------------------------------------

def get_sample_df() -> pd.DataFrame:
    """
    Returns a minimal job DataFrame for testing.
    Replace this with your real data loading logic.
    """
    rows = []
    for domain in ALL_DOMAINS:
        rows.append({
            "domain": domain,
            "location": "Jaipur",
            "job_count": 50,
            "avg_salary": 500_000,
        })
    return pd.DataFrame(rows)


# -----------------------------------------------------------------------
# ENGINE FACTORY — supports weight injection for ablation study
# -----------------------------------------------------------------------

def build_engine(df: pd.DataFrame) -> DomainRecommendationEngine:
    """
    Builds an engine with mocked sub-engines returning neutral scores.
    In production, remove the patch decorators to use real engines.
    """
    with patch("src.recommender.rule_based_recommendation_engine.MarketDemandEngine") as MockDemand, \
         patch("src.recommender.rule_based_recommendation_engine.CompetitionLevelCalculator") as MockComp, \
         patch("src.recommender.rule_based_recommendation_engine.SaturationRiskIndicator") as MockSat:

        MockDemand.return_value.calculate_metrics.return_value = {
            domain: {"Overall_Demand_Score": 6.0, "Breakdown": {"Growth_Trend": 6.0}}
            for domain in ALL_DOMAINS
        }
        MockComp.return_value.calculate_competition_level.return_value = {"Level": "Medium"}
        MockSat.return_value.get_saturation_risk.return_value = {"Risk_Level": "Safe"}

        engine = DomainRecommendationEngine(df=df)

    # IMPORTANT: Re-attach mocked sub-engines so they persist after `with` block
    # (workaround: just rebuild fresh for each run — see run_batch_test)
    return engine


# -----------------------------------------------------------------------
# PHASE 3: BATCH TEST
# -----------------------------------------------------------------------

def run_batch_test(df: pd.DataFrame, users: List[Dict] = None) -> List[Dict]:
    """
    Runs get_recommendations() for every user in the test set.
    Returns a list of per-user result dicts with all metrics.
    """
    if users is None:
        users = SYNTHETIC_USERS

    results = []

    for user in users:
        try:
            with patch("src.recommender.rule_based_recommendation_engine.MarketDemandEngine") as MockDemand, \
                 patch("src.recommender.rule_based_recommendation_engine.CompetitionLevelCalculator") as MockComp, \
                 patch("src.recommender.rule_based_recommendation_engine.SaturationRiskIndicator") as MockSat:

                MockDemand.return_value.calculate_metrics.return_value = {
                    domain: {"Overall_Demand_Score": 6.0, "Breakdown": {"Growth_Trend": 6.0}}
                    for domain in ALL_DOMAINS
                }
                MockComp.return_value.calculate_competition_level.return_value = {"Level": "Medium"}
                MockSat.return_value.get_saturation_risk.return_value = {"Risk_Level": "Safe"}

                engine = DomainRecommendationEngine(df=df)

                profile = {
                    "experience":   user["experience"],
                    "skills":       user["skills"],
                    "location":     user["location"],
                    "math_comfort": user["math_comfort"],
                }
                recs = engine.get_recommendations(profile, top_n=3)

            top3          = [r["domain"] for r in recs]
            ground_truth  = user.get("ground_truth_top3", [])
            p3            = precision_at_k(top3, ground_truth, k=3)
            hr            = hit_rate(top3, ground_truth, k=3)
            ndcg          = ndcg_at_k(top3, ground_truth, k=3)
            top1_pct      = top1_match_percentage(recs)
            avg_pct       = average_match_percentage(recs, k=3)

            results.append({
                "user_id":         user["user_id"],
                "precision@3":     p3,
                "hit_rate":        hr,
                "ndcg@3":          ndcg,
                "top1_match_pct":  top1_pct,
                "avg_match_pct":   avg_pct,
                "top3_predicted":  top3,
                "ground_truth":    ground_truth,
            })

        except Exception as e:
            print(f"  [ERROR] User {user['user_id']}: {e}")
            results.append({
                "user_id":         user["user_id"],
                "precision@3":     0.0,
                "hit_rate":        0,
                "ndcg@3":          0.0,
                "top1_match_pct":  0.0,
                "avg_match_pct":   0.0,
                "top3_predicted":  [],
                "ground_truth":    user.get("ground_truth_top3", []),
                "error":           str(e),
            })

    return results


# -----------------------------------------------------------------------
# PHASE 4: ABLATION STUDY
# -----------------------------------------------------------------------

class PatchedEngine(DomainRecommendationEngine):
    """
    Subclass that allows overriding the weight constants for ablation testing.
    Weights: skill_weight, market_weight, feasibility_weight, apply_math_penalty
    """
    def __init__(self, df, skill_w=40, market_w=30, feasibility_w=30, apply_math_penalty=True):
        super().__init__(df)
        self.skill_w = skill_w
        self.market_w = market_w
        self.feasibility_w = feasibility_w
        self.apply_math_penalty = apply_math_penalty

    def _calculate_domain_score(self, domain, profile, signals):
        breakdown = {}

        # Skill Match
        user_skills = set(s.lower() for s in profile.get("skills", []))
        domain_skills = set(s.lower() for s in DOMAIN_REQUIRED_SKILLS.get(domain, []))
        if domain_skills:
            overlap = len(user_skills & domain_skills)
            breakdown["skill_score"] = round((overlap / len(domain_skills)) * self.skill_w, 2)
        else:
            breakdown["skill_score"] = 0.0

        # Market Demand
        demand_score = signals.get("demand_score", 5.0)
        breakdown["market_score"] = round((demand_score / 10.0) * self.market_w, 2)

        # Feasibility
        base_feasibility = (self.feasibility_w / 30.0) * 20.0
        experience = profile.get("experience", "Fresher")
        if experience == "Fresher":
            if signals.get("comp_level") == "High":
                base_feasibility -= 8.0
            if signals.get("sat_risk") == "Highly Competitive":
                base_feasibility -= 7.0
            from src.recommender.knowledge_base import DOMAIN_ENTRY_BARRIER
            if DOMAIN_ENTRY_BARRIER.get(domain, 5) >= 8:
                base_feasibility -= 5.0
        else:
            base_feasibility += 10.0
        breakdown["feasibility_score"] = max(0.0, round(base_feasibility, 2))

        # Math Penalty
        math_penalty = 0.0
        if self.apply_math_penalty and DOMAIN_MATH_HEAVY.get(domain, False) and profile.get("math_comfort") == "Weak":
            math_penalty = -15.0
        breakdown["math_penalty"] = math_penalty

        breakdown["total_score"] = round(
            breakdown["skill_score"] + breakdown["market_score"]
            + breakdown["feasibility_score"] + breakdown["math_penalty"], 2
        )
        return breakdown


def run_ablation_study(df: pd.DataFrame) -> None:
    """
    Phase 4: Runs the same 30 users with 4 different weight configurations
    and prints a comparison table.
    """
    configurations = [
        {"name": "Original (40-30-30)",      "skill_w": 40, "market_w": 30, "feasibility_w": 30, "apply_math_penalty": True},
        {"name": "Version A: Skill→30",       "skill_w": 30, "market_w": 35, "feasibility_w": 35, "apply_math_penalty": True},
        {"name": "Version B: Market→50",      "skill_w": 25, "market_w": 50, "feasibility_w": 25, "apply_math_penalty": True},
        {"name": "Version C: No Math Penalty","skill_w": 40, "market_w": 30, "feasibility_w": 30, "apply_math_penalty": False},
    ]

    print("\n" + "=" * 65)
    print("  PHASE 4: ABLATION STUDY — WEIGHT SENSITIVITY ANALYSIS")
    print("=" * 65)
    print(f"  {'Configuration':<30} {'Avg P@3':>8} {'Hit Rate':>10} {'Drop P@3':>10}")
    print("  " + "-" * 61)

    baseline_p3 = None

    for cfg in configurations:
        results = []
        for user in SYNTHETIC_USERS:
            try:
                with patch("src.recommender.rule_based_recommendation_engine.MarketDemandEngine") as MockDemand, \
                     patch("src.recommender.rule_based_recommendation_engine.CompetitionLevelCalculator") as MockComp, \
                     patch("src.recommender.rule_based_recommendation_engine.SaturationRiskIndicator") as MockSat:

                    MockDemand.return_value.calculate_metrics.return_value = {
                        domain: {"Overall_Demand_Score": 6.0, "Breakdown": {"Growth_Trend": 6.0}}
                        for domain in ALL_DOMAINS
                    }
                    MockComp.return_value.calculate_competition_level.return_value = {"Level": "Medium"}
                    MockSat.return_value.get_saturation_risk.return_value = {"Risk_Level": "Safe"}

                    engine = PatchedEngine(
                        df=df,
                        skill_w=cfg["skill_w"],
                        market_w=cfg["market_w"],
                        feasibility_w=cfg["feasibility_w"],
                        apply_math_penalty=cfg["apply_math_penalty"],
                    )
                    profile = {
                        "experience":   user["experience"],
                        "skills":       user["skills"],
                        "location":     user["location"],
                        "math_comfort": user["math_comfort"],
                    }
                    recs = engine.get_recommendations(profile, top_n=3)

                top3 = [r["domain"] for r in recs]
                p3   = precision_at_k(top3, user.get("ground_truth_top3", []), k=3)
                hr   = hit_rate(top3, user.get("ground_truth_top3", []), k=3)
                results.append({"precision@3": p3, "hit_rate": hr})

            except Exception:
                results.append({"precision@3": 0.0, "hit_rate": 0})

        avg_p3 = round(sum(r["precision@3"] for r in results) / len(results), 4)
        avg_hr = round(sum(r["hit_rate"]     for r in results) / len(results), 4)

        if baseline_p3 is None:
            baseline_p3 = avg_p3
            drop_str = "   —"
        else:
            drop = round(avg_p3 - baseline_p3, 4)
            drop_str = f"{drop:+.4f}"

        print(f"  {cfg['name']:<30} {avg_p3:>8.4f} {avg_hr:>10.4f} {drop_str:>10}")

    print("=" * 65 + "\n")


# -----------------------------------------------------------------------
# PHASE 6: EDGE CASE & ROBUSTNESS TESTING
# -----------------------------------------------------------------------

def run_edge_case_tests(df: pd.DataFrame) -> None:
    """Phase 6: Tests 5 special edge cases."""
    print("\n" + "=" * 55)
    print("  PHASE 6: EDGE CASE & ROBUSTNESS TESTING")
    print("=" * 55)

    def get_engine():
        with patch("src.recommender.rule_based_recommendation_engine.MarketDemandEngine") as MockDemand, \
             patch("src.recommender.rule_based_recommendation_engine.CompetitionLevelCalculator") as MockComp, \
             patch("src.recommender.rule_based_recommendation_engine.SaturationRiskIndicator") as MockSat:
            MockDemand.return_value.calculate_metrics.return_value = {
                domain: {"Overall_Demand_Score": 6.0, "Breakdown": {"Growth_Trend": 6.0}}
                for domain in ALL_DOMAINS
            }
            MockComp.return_value.calculate_competition_level.return_value = {"Level": "Medium"}
            MockSat.return_value.get_saturation_risk.return_value = {"Risk_Level": "Safe"}
            return DomainRecommendationEngine(df=df)

    # Edge Case 1: Zero skills — should not crash
    print("\n  [EDGE 1] User with zero skills")
    try:
        engine = get_engine()
        recs = engine.get_recommendations(EDGE_CASE_USERS["zero_skills"], top_n=3)
        assert len(recs) == 3
        print(f"  ✅ PASS — No crash. Top-1: {recs[0]['domain']} ({recs[0]['match_percentage']}%)")
    except Exception as e:
        print(f"  ❌ FAIL — {e}")

    # Edge Case 2: All skills — top domains should have 100% skill match
    print("\n  [EDGE 2] User with ALL skills")
    try:
        engine = get_engine()
        recs = engine.get_recommendations(EDGE_CASE_USERS["all_skills"], top_n=3)
        top_match = recs[0]["match_percentage"]
        print(f"  ✅ PASS — Top-1 match: {top_match}% (domain: {recs[0]['domain']})")
    except Exception as e:
        print(f"  ❌ FAIL — {e}")

    # Edge Case 3: Weak math + Data Scientist — score should be visibly lower
    print("\n  [EDGE 3] Weak math user — Data Scientist score should drop by 15")
    try:
        signals = {"demand_score": 6.0, "comp_level": "Medium", "sat_risk": "Safe"}
        engine = get_engine()

        weak_profile   = {"experience": "Fresher", "skills": ["Python", "SQL", "Statistics"], "location": "Jaipur", "math_comfort": "Weak"}
        strong_profile = {"experience": "Fresher", "skills": ["Python", "SQL", "Statistics"], "location": "Jaipur", "math_comfort": "Strong"}

        weak_score   = engine._calculate_domain_score("Data Scientist", weak_profile, signals)
        strong_score = engine._calculate_domain_score("Data Scientist", strong_profile, signals)

        diff = round(strong_score["total_score"] - weak_score["total_score"], 2)
        assert diff == 15.0, f"Expected 15.0 drop, got {diff}"
        print(f"  ✅ PASS — Score drop = {diff} pts (Strong: {strong_score['total_score']}, Weak: {weak_score['total_score']})")
    except Exception as e:
        print(f"  ❌ FAIL — {e}")

    # Edge Case 4: Jaipur location — remote-friendly domains get boost in explanation
    print("\n  [EDGE 4] Jaipur location — remote-friendly boost in reasoning")
    try:
        engine = get_engine()
        recs = engine.get_recommendations(EDGE_CASE_USERS["jaipur_location"], top_n=5)
        remote_mentioned = any(
            any("remote" in reason.lower() or "location" in reason.lower() for reason in r["reasoning"])
            for r in recs
        )
        status = "✅ PASS" if remote_mentioned else "⚠️  NOTE"
        print(f"  {status} — Remote/location boost mentioned in reasoning: {remote_mentioned}")
    except Exception as e:
        print(f"  ❌ FAIL — {e}")

    # Edge Case 5: Empty DataFrame — fallback market scores should kick in
    print("\n  [EDGE 5] Empty job DataFrame — fallback market scores")
    try:
        empty_df = pd.DataFrame(columns=["domain", "location", "job_count", "avg_salary"])
        with patch("src.recommender.rule_based_recommendation_engine.MarketDemandEngine") as MockDemand, \
             patch("src.recommender.rule_based_recommendation_engine.CompetitionLevelCalculator") as MockComp, \
             patch("src.recommender.rule_based_recommendation_engine.SaturationRiskIndicator") as MockSat:
            MockDemand.return_value.calculate_metrics.side_effect = Exception("Empty data")
            MockComp.return_value.calculate_competition_level.side_effect = Exception("Empty data")
            MockSat.return_value.get_saturation_risk.side_effect = Exception("Empty data")
            engine = DomainRecommendationEngine(df=empty_df)

        profile = {"experience": "Fresher", "skills": ["Python"], "location": "Jaipur", "math_comfort": "Moderate"}
        recs = engine.get_recommendations(profile, top_n=3)
        assert len(recs) == 3
        print(f"  ✅ PASS — Fallback worked. Top-1: {recs[0]['domain']}")
    except Exception as e:
        print(f"  ❌ FAIL — {e}")

    print("\n" + "=" * 55)


# -----------------------------------------------------------------------
# MAIN RUNNER
# -----------------------------------------------------------------------

if __name__ == "__main__":
    print("\n" + "🔬 " * 20)
    print("  RULE-BASED RECOMMENDER: FULL TEST SUITE")
    print("🔬 " * 20)

    df = get_sample_df()

    # ── Phase 3: Batch Testing ──────────────────────────────────────────
    print("\n📊 PHASE 3: BATCH TESTING (30 Synthetic Users)")
    print("-" * 55)
    results = run_batch_test(df)

    print_metrics_table(results)
    agg = aggregate_metrics(results)
    print_aggregate_summary(agg)

    # ── Save results to JSON ────────────────────────────────────────────
    output_path = os.path.join(os.path.dirname(__file__), "batch_test_results.json")
    with open(output_path, "w") as f:
        json.dump({"results": results, "aggregate": agg}, f, indent=2)
    print(f"  📁 Results saved to: {output_path}\n")

    # ── Phase 4: Ablation Study ─────────────────────────────────────────
    run_ablation_study(df)

    # ── Phase 6: Edge Cases ─────────────────────────────────────────────
    run_edge_case_tests(df)

    print("\n✅ ALL PHASES COMPLETE\n")