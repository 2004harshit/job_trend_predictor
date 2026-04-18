# tests/recommender/test_unit.py
"""
Phase 1: Unit Tests for DomainRecommendationEngine
Run with:  pytest tests/recommender/test_unit.py -v
"""

import pytest
import pandas as pd
from unittest.mock import MagicMock, patch

from src.recommender.rule_based_recommendation_engine import DomainRecommendationEngine
from src.recommender.knowledge_base import ALL_DOMAINS


# -----------------------------------------------------------------------
# FIXTURES
# -----------------------------------------------------------------------

@pytest.fixture
def sample_df():
    """Minimal DataFrame to initialise the engine."""
    return pd.DataFrame([
        {"domain": "Data Scientist",  "location": "Jaipur",     "job_count": 45,  "avg_salary": 600_000},
        {"domain": "Web Developer",   "location": "Jaipur",     "job_count": 120, "avg_salary": 450_000},
        {"domain": "Data Analyst",    "location": "Bangalore",  "job_count": 80,  "avg_salary": 500_000},
        {"domain": "QA Automation",   "location": "Pune",       "job_count": 60,  "avg_salary": 400_000},
        {"domain": "Software Engineer","location": "Chennai",   "job_count": 90,  "avg_salary": 520_000},
    ])


@pytest.fixture
def engine(sample_df):
    """Engine instance with mocked sub-engines to avoid network/DB calls."""
    with patch("src.recommender.rule_based_recommendation_engine.MarketDemandEngine") as MockDemand, \
         patch("src.recommender.rule_based_recommendation_engine.CompetitionLevelCalculator") as MockComp, \
         patch("src.recommender.rule_based_recommendation_engine.SaturationRiskIndicator") as MockSat:

        # Default mock return values
        MockDemand.return_value.calculate_metrics.return_value = {
            domain: {"Overall_Demand_Score": 5.0, "Breakdown": {"Growth_Trend": 5.0}}
            for domain in ALL_DOMAINS
        }
        MockComp.return_value.calculate_competition_level.return_value = {"Level": "Medium"}
        MockSat.return_value.get_saturation_risk.return_value = {"Risk_Level": "Safe"}

        eng = DomainRecommendationEngine(df=sample_df)
    return eng


# -----------------------------------------------------------------------
# TEST 1: Engine initialises without crash
# -----------------------------------------------------------------------

def test_engine_initialises(sample_df):
    with patch("src.recommender.rule_based_recommendation_engine.MarketDemandEngine"), \
         patch("src.recommender.rule_based_recommendation_engine.CompetitionLevelCalculator"), \
         patch("src.recommender.rule_based_recommendation_engine.SaturationRiskIndicator"):
        eng = DomainRecommendationEngine(df=sample_df)
        assert eng is not None
        assert len(eng.domains) == 13


# -----------------------------------------------------------------------
# TEST 2: _calculate_domain_score — Skill Match component (40 pts max)
# -----------------------------------------------------------------------

def test_skill_score_full_match(engine):
    """User has ALL required skills → skill_score = 40.0"""
    profile = {
        "experience": "Fresher",
        "skills": ["Selenium", "Python", "Testing Concepts", "Jira"],
        "location": "Jaipur",
        "math_comfort": "Moderate",
    }
    signals = {"demand_score": 5.0, "comp_level": "Medium", "sat_risk": "Safe"}
    breakdown = engine._calculate_domain_score("QA Automation", profile, signals)
    assert breakdown["skill_score"] == 40.0, f"Expected 40.0, got {breakdown['skill_score']}"


def test_skill_score_zero_overlap(engine):
    """User has NO matching skills → skill_score = 0.0"""
    profile = {
        "experience": "Fresher",
        "skills": ["Photoshop", "Illustrator"],
        "location": "Jaipur",
        "math_comfort": "Moderate",
    }
    signals = {"demand_score": 5.0, "comp_level": "Medium", "sat_risk": "Safe"}
    breakdown = engine._calculate_domain_score("QA Automation", profile, signals)
    assert breakdown["skill_score"] == 0.0


def test_skill_score_fifty_percent(engine):
    """User has 50% of required skills → skill_score ≈ 20.0"""
    # QA Automation requires: Selenium, Python, Testing Concepts, Jira (4 skills)
    # User has 2 out of 4 → 2/4 * 40 = 20.0
    profile = {
        "experience": "Fresher",
        "skills": ["Selenium", "Python"],
        "location": "Jaipur",
        "math_comfort": "Moderate",
    }
    signals = {"demand_score": 5.0, "comp_level": "Medium", "sat_risk": "Safe"}
    breakdown = engine._calculate_domain_score("QA Automation", profile, signals)
    assert breakdown["skill_score"] == 20.0, f"Expected 20.0, got {breakdown['skill_score']}"


# -----------------------------------------------------------------------
# TEST 3: Math Penalty — exactly -15 for Weak user on math-heavy domain
# -----------------------------------------------------------------------

def test_math_penalty_weak_user_math_heavy_domain(engine):
    """Weak math + Data Scientist → math_penalty = -15.0"""
    profile = {
        "experience": "Fresher",
        "skills": ["Python", "SQL"],
        "location": "Jaipur",
        "math_comfort": "Weak",
    }
    signals = {"demand_score": 5.0, "comp_level": "Medium", "sat_risk": "Safe"}
    breakdown = engine._calculate_domain_score("Data Scientist", profile, signals)
    assert breakdown["math_penalty"] == -15.0, f"Expected -15.0, got {breakdown['math_penalty']}"


def test_math_penalty_strong_user_math_heavy_domain(engine):
    """Strong math + Data Scientist → math_penalty = 0.0 (no penalty)"""
    profile = {
        "experience": "Fresher",
        "skills": ["Python", "SQL"],
        "location": "Jaipur",
        "math_comfort": "Strong",
    }
    signals = {"demand_score": 5.0, "comp_level": "Medium", "sat_risk": "Safe"}
    breakdown = engine._calculate_domain_score("Data Scientist", profile, signals)
    assert breakdown["math_penalty"] == 0.0


def test_math_penalty_weak_user_non_math_domain(engine):
    """Weak math + Web Developer (not math-heavy) → math_penalty = 0.0"""
    profile = {
        "experience": "Fresher",
        "skills": ["HTML", "CSS"],
        "location": "Jaipur",
        "math_comfort": "Weak",
    }
    signals = {"demand_score": 5.0, "comp_level": "Medium", "sat_risk": "Safe"}
    breakdown = engine._calculate_domain_score("Web Developer", profile, signals)
    assert breakdown["math_penalty"] == 0.0


# -----------------------------------------------------------------------
# TEST 4: Market Score — 30 pts max
# -----------------------------------------------------------------------

def test_market_score_max(engine):
    """demand_score = 10 → market_score = 30.0"""
    profile = {"experience": "Fresher", "skills": [], "location": "Jaipur", "math_comfort": "Moderate"}
    signals = {"demand_score": 10.0, "comp_level": "Medium", "sat_risk": "Safe"}
    breakdown = engine._calculate_domain_score("Web Developer", profile, signals)
    assert breakdown["market_score"] == 30.0


def test_market_score_fallback(engine):
    """demand_score fallback = 5.0 → market_score = 15.0"""
    profile = {"experience": "Fresher", "skills": [], "location": "Jaipur", "math_comfort": "Moderate"}
    signals = {"demand_score": 5.0, "comp_level": "Medium", "sat_risk": "Safe"}
    breakdown = engine._calculate_domain_score("Web Developer", profile, signals)
    assert breakdown["market_score"] == 15.0


# -----------------------------------------------------------------------
# TEST 5: Feasibility — Fresher vs Experienced
# -----------------------------------------------------------------------

def test_feasibility_experienced_higher_than_fresher(engine):
    """Experienced user should always score higher on feasibility than Fresher."""
    signals = {"demand_score": 5.0, "comp_level": "Medium", "sat_risk": "Safe"}

    fresher_profile = {"experience": "Fresher", "skills": [], "location": "Jaipur", "math_comfort": "Moderate"}
    exp_profile     = {"experience": "3-5 years", "skills": [], "location": "Jaipur", "math_comfort": "Moderate"}

    fresher_score = engine._calculate_domain_score("Software Engineer", fresher_profile, signals)
    exp_score     = engine._calculate_domain_score("Software Engineer", exp_profile, signals)

    assert exp_score["feasibility_score"] > fresher_score["feasibility_score"]


def test_feasibility_never_negative(engine):
    """Feasibility score should never go below 0.0 even with all penalties."""
    profile = {"experience": "Fresher", "skills": [], "location": "Jaipur", "math_comfort": "Weak"}
    signals = {"demand_score": 0.0, "comp_level": "High", "sat_risk": "Highly Competitive"}
    breakdown = engine._calculate_domain_score("Data Scientist", profile, signals)
    assert breakdown["feasibility_score"] >= 0.0


# -----------------------------------------------------------------------
# TEST 6: _fetch_market_signals — fallback on engine failure
# -----------------------------------------------------------------------

def test_fetch_market_signals_fallback(sample_df):
    """If sub-engines raise exceptions, fallback values should be used."""
    with patch("src.recommender.rule_based_recommendation_engine.MarketDemandEngine") as MockDemand, \
         patch("src.recommender.rule_based_recommendation_engine.CompetitionLevelCalculator") as MockComp, \
         patch("src.recommender.rule_based_recommendation_engine.SaturationRiskIndicator") as MockSat:

        MockDemand.return_value.calculate_metrics.side_effect = Exception("Network error")
        MockComp.return_value.calculate_competition_level.side_effect = Exception("DB error")
        MockSat.return_value.get_saturation_risk.side_effect = Exception("Timeout")

        eng = DomainRecommendationEngine(df=sample_df)
        signals = eng._fetch_market_signals("Data Scientist", "Jaipur")

        assert signals["demand_score"] == 5.0
        assert signals["comp_level"] == "Medium"
        assert signals["sat_risk"] == "Safe"
        assert signals["growth_trend"] == 5.0


# -----------------------------------------------------------------------
# TEST 7: get_recommendations — returns correct structure
# -----------------------------------------------------------------------

def test_get_recommendations_returns_top3(engine):
    """get_recommendations should return exactly 3 results by default."""
    profile = {
        "experience": "Fresher",
        "skills": ["Python", "SQL"],
        "location": "Jaipur",
        "math_comfort": "Moderate",
    }
    results = engine.get_recommendations(profile, top_n=3)
    assert len(results) == 3


def test_get_recommendations_output_fields(engine):
    """Each recommendation must have required fields."""
    profile = {
        "experience": "Fresher",
        "skills": ["Python", "SQL"],
        "location": "Jaipur",
        "math_comfort": "Moderate",
    }
    results = engine.get_recommendations(profile, top_n=3)
    required_fields = {"domain", "match_percentage", "reasoning", "pros", "cons", "timeline", "market_metrics"}
    for rec in results:
        assert required_fields.issubset(rec.keys()), f"Missing fields: {required_fields - rec.keys()}"


def test_get_recommendations_sorted_descending(engine):
    """Recommendations must be sorted by match_percentage (highest first)."""
    profile = {
        "experience": "1-2 years",
        "skills": ["Python", "SQL", "Pandas", "Tableau"],
        "location": "Bangalore",
        "math_comfort": "Strong",
    }
    results = engine.get_recommendations(profile, top_n=5)
    scores = [r["match_percentage"] for r in results]
    assert scores == sorted(scores, reverse=True), "Results not sorted in descending order"


# -----------------------------------------------------------------------
# TEST 8: Score components sum correctly
# -----------------------------------------------------------------------

def test_total_score_is_sum_of_components(engine):
    """total_score should equal skill + market + feasibility + math_penalty."""
    profile = {
        "experience": "Fresher",
        "skills": ["Python", "SQL"],
        "location": "Jaipur",
        "math_comfort": "Strong",
    }
    signals = {"demand_score": 7.0, "comp_level": "Medium", "sat_risk": "Safe"}
    breakdown = engine._calculate_domain_score("Data Analyst", profile, signals)

    expected_total = round(
        breakdown["skill_score"]
        + breakdown["market_score"]
        + breakdown["feasibility_score"]
        + breakdown["math_penalty"],
        2,
    )
    assert breakdown["total_score"] == expected_total, (
        f"Total mismatch: {breakdown['total_score']} != {expected_total}"
    )