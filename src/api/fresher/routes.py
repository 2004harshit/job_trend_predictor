"""
src/api/fresher/routes.py
=========================
Fresher-facing endpoints — recommendations & deep analytics.

All routes are mounted under  /api/fresher/  by the app factory.

Endpoint map
------------
Health
    GET  /api/fresher/health

Recommendations
    POST /api/fresher/recommend
    GET  /api/fresher/recommend/domains
    POST /api/fresher/recommend/analyze
    POST /api/fresher/recommend/compare
    GET  /api/fresher/market/signals/<domain>

Market Analytics
    POST /api/fresher/analytics/market/demand
    POST /api/fresher/analytics/market/competition
    POST /api/fresher/analytics/market/saturation
    POST /api/fresher/analytics/market/salary
    POST /api/fresher/analytics/market/velocity

Career Insights
    POST /api/fresher/analytics/career/path
    POST /api/fresher/analytics/career/role-evaluation

Domain Analysis
    POST /api/fresher/analytics/domain/ai-risk
    POST /api/fresher/analytics/domain/stability
    POST /api/fresher/analytics/domain/salary-growth
    POST /api/fresher/analytics/domain/skill-transferability

Entry Barriers
    POST /api/fresher/analytics/barriers/interview-difficulty
    POST /api/fresher/analytics/barriers/hidden-blockers
    POST /api/fresher/analytics/barriers/prerequisites
    POST /api/fresher/analytics/barriers/project-complexity

Comprehensive
    POST /api/fresher/analytics/comprehensive
    POST /api/fresher/analytics/domain-comprehensive

Data
    GET  /api/fresher/data/stats
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Dict, List, Any

import numpy as np
from flask import Blueprint, request, jsonify

from src.api.data_loader import get_job_data

# ── analytics engines ─────────────────────────────────────────────────────────
from src.recommender.rule_based_recommendation_engine import DomainRecommendationEngine
from src.preprocessing.postgres_ingestor import PostgreSQLIngestor, DatabaseIngestionFactory

from src.analytics.market_analysis.demand_score_calculator          import MarketDemandEngine
from src.analytics.market_analysis.competition_level_calculator     import CompetitionLevelCalculator
from src.analytics.market_analysis.saturation_risk_indicator        import SaturationRiskIndicator
from src.analytics.market_analysis.average_salary_calculator        import AverageSalaryRangeCalculator
from src.analytics.market_analysis.job_market_velocity_calculator   import JobMarketVelocityCalculator

from src.analytics.career_insights.career_path_engine               import CareerPathEngine
from src.analytics.career_insights.role_evaluation_engine           import RoleEvolutionEngine

from src.analytics.domain_analysis.ai_replacement_risk_engine       import AIReplacementRiskEngine
from src.analytics.domain_analysis.domain_stability_engine          import DomainStabilityEngine
from src.analytics.domain_analysis.salary_growth_engine             import SalaryGrowthEngine
from src.analytics.domain_analysis.skill_transferability_engine     import SkillTransferabilityEngine

from src.analytics.entry_barriers.interview_difficulty_engine       import InterviewDifficultyEngine
from src.analytics.entry_barriers.hidden_blocker_detector           import HiddenBlockerDetector
from src.analytics.entry_barriers.prequisite_engine                 import PrerequisiteEngine
from src.analytics.entry_barriers.project_complexity_evaluator      import ProjectComplexityEvaluator

from pipelines.analytics_pipeline import AnalyticsPipeline

logger    = logging.getLogger(__name__)
fresher_bp = Blueprint("fresher", __name__)

# ── module-level engine cache ─────────────────────────────────────────────────
_recommender: DomainRecommendationEngine | None = None
_global_analytics_cache = None


# ── helpers ───────────────────────────────────────────────────────────────────

def sanitize_for_json(obj):
    """Recursively convert numpy types → native Python for JSON serialization."""
    if isinstance(obj, dict):
        return {k: sanitize_for_json(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [sanitize_for_json(i) for i in obj]
    if isinstance(obj, np.bool_):    return bool(obj)
    if isinstance(obj, np.integer):  return int(obj)
    if isinstance(obj, np.floating): return float(obj)
    if isinstance(obj, np.ndarray):  return obj.tolist()
    return obj


def _get_recommender() -> DomainRecommendationEngine:
    global _recommender
    if _recommender is None:
        df          = get_job_data()
        _recommender = DomainRecommendationEngine(df)
        logger.info("DomainRecommendationEngine initialised")
    return _recommender


def _get_global_analytics():
    global _global_analytics_cache
    if _global_analytics_cache is None:
        df                     = get_job_data()
        pipeline               = AnalyticsPipeline(df)
        _global_analytics_cache = pipeline.run_global_phase()
    return _global_analytics_cache


def _validate_profile(profile: Dict) -> tuple[bool, list]:
    errors = []
    for field in ("skills", "experience", "location"):
        if field not in profile:
            errors.append(f"Missing required field: {field}")
    if "skills" in profile:
        if not isinstance(profile["skills"], list):
            errors.append("skills must be a list")
        elif len(profile["skills"]) == 0:
            errors.append("skills list cannot be empty")
    if "experience" in profile:
        valid = ["Fresher", "1-2 years", "3-5 years", "5+ years"]
        if profile["experience"] not in valid:
            errors.append(f"experience must be one of: {valid}")
    if "math_comfort" in profile:
        valid = ["Weak", "Moderate", "Strong"]
        if profile["math_comfort"] not in valid:
            errors.append(f"math_comfort must be one of: {valid}")
    return len(errors) == 0, errors


# ═══════════════════════════════════════════════════════════════════════════════
# Health
# ═══════════════════════════════════════════════════════════════════════════════

@fresher_bp.route("/health", methods=["GET"])
def health():
    df = get_job_data()
    return jsonify({
        "status":    "healthy",
        "module":    "fresher",
        "data_rows": len(df) if df is not None else 0,
        "timestamp": datetime.now().isoformat(),
    })


# ═══════════════════════════════════════════════════════════════════════════════
# Recommendations
# ═══════════════════════════════════════════════════════════════════════════════

@fresher_bp.route("/recommend", methods=["POST"])
def get_recommendations():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        is_valid, errors = _validate_profile(data)
        if not is_valid:
            return jsonify({"error": "Invalid profile", "errors": errors}), 400
        top_n = data.get("top_n", 3)
        if not isinstance(top_n, int) or not (1 <= top_n <= 10):
            return jsonify({"error": "top_n must be an integer between 1 and 10"}), 400
        recs = _get_recommender().get_recommendations(data, top_n)
        return jsonify({"success": True, "timestamp": datetime.now().isoformat(),
                        "user_profile": data, "recommendations": recs,
                        "total_recommendations": len(recs)})
    except Exception as e:
        logger.error(f"get_recommendations: {e}")
        return jsonify({"error": "Internal server error", "details": str(e)}), 500


@fresher_bp.route("/recommend/domains", methods=["GET"])
def get_all_domains():
    try:
        domains = _get_recommender().domains
        return jsonify({"success": True, "timestamp": datetime.now().isoformat(),
                        "domains": domains, "total_domains": len(domains)})
    except Exception as e:
        logger.error(f"get_all_domains: {e}")
        return jsonify({"error": "Internal server error", "details": str(e)}), 500


@fresher_bp.route("/recommend/analyze", methods=["POST"])
def analyze_domain():
    try:
        data = request.get_json()
        if not data or "domain" not in data:
            return jsonify({"error": "Missing domain"}), 400
        domain       = data["domain"]
        user_profile = data.get("user_profile", {})
        engine       = _get_recommender()
        if domain not in engine.domains:
            return jsonify({"error": f'Domain "{domain}" not found',
                            "available_domains": engine.domains}), 400
        is_valid, errors = _validate_profile(user_profile)
        if not is_valid:
            return jsonify({"error": "Invalid profile", "errors": errors}), 400
        location       = user_profile.get("location", "Bangalore")
        market_signals = engine._fetch_market_signals(domain, location)
        score          = engine._calculate_domain_score(domain, user_profile, market_signals)
        return jsonify({"success": True, "analysis": {
            "domain": domain, "user_profile": user_profile,
            "market_signals": market_signals, "score_breakdown": score,
            "detailed_analysis": engine._format_output(domain, score, user_profile),
            "timestamp": datetime.now().isoformat(),
        }})
    except Exception as e:
        logger.error(f"analyze_domain: {e}")
        return jsonify({"error": "Internal server error", "details": str(e)}), 500


@fresher_bp.route("/recommend/compare", methods=["POST"])
def compare_domains():
    try:
        data = request.get_json()
        if not data or "domains" not in data:
            return jsonify({"error": "Missing domains list"}), 400
        domains      = data["domains"]
        user_profile = data.get("user_profile", {})
        engine       = _get_recommender()
        if not isinstance(domains, list) or len(domains) == 0:
            return jsonify({"error": "domains must be a non-empty list"}), 400
        bad = [d for d in domains if d not in engine.domains]
        if bad:
            return jsonify({"error": f"Unknown domains: {bad}",
                            "available_domains": engine.domains}), 400
        is_valid, errors = _validate_profile(user_profile)
        if not is_valid:
            return jsonify({"error": "Invalid profile", "errors": errors}), 400
        location    = user_profile.get("location", "Bangalore")
        comparisons = []
        for d in domains:
            sig   = engine._fetch_market_signals(d, location)
            score = engine._calculate_domain_score(d, user_profile, sig)
            comparisons.append({"domain": d, "score_breakdown": score,
                                 "detailed_analysis": engine._format_output(d, score, user_profile),
                                 "market_signals": sig})
        comparisons.sort(key=lambda x: x["score_breakdown"]["total_score"], reverse=True)
        return jsonify({"success": True, "timestamp": datetime.now().isoformat(),
                        "user_profile": user_profile, "comparisons": comparisons,
                        "ranking_summary": [{"rank": i + 1, "domain": c["domain"],
                                             "total_score": c["score_breakdown"]["total_score"],
                                             "match_percentage": c["detailed_analysis"]["match_percentage"]}
                                            for i, c in enumerate(comparisons)]})
    except Exception as e:
        logger.error(f"compare_domains: {e}")
        return jsonify({"error": "Internal server error", "details": str(e)}), 500


@fresher_bp.route("/market/signals/<domain>", methods=["GET"])
def get_market_signals(domain):
    try:
        engine = _get_recommender()
        if domain not in engine.domains:
            return jsonify({"error": f'Domain "{domain}" not found',
                            "available_domains": engine.domains}), 400
        location = request.args.get("location", "Bangalore")
        signals  = engine._fetch_market_signals(domain, location)
        return jsonify({"success": True, "domain": domain, "location": location,
                        "market_signals": signals, "timestamp": datetime.now().isoformat()})
    except Exception as e:
        logger.error(f"get_market_signals: {e}")
        return jsonify({"error": "Internal server error", "details": str(e)}), 500


# ═══════════════════════════════════════════════════════════════════════════════
# Analytics — Market
# ═══════════════════════════════════════════════════════════════════════════════

@fresher_bp.route("/analytics/market/demand", methods=["POST"])
def market_demand():
    try:
        data    = request.get_json() or {}
        domains = data.get("domains", [])
        weights = data.get("weights", {})
        if not domains:
            return jsonify({"error": "domains list is required"}), 400
        df     = get_job_data()
        engine = MarketDemandEngine(df)
        result = {d: engine.calculate_demand_score(d, weights) for d in domains}
        return jsonify(sanitize_for_json({"success": True,
                        "timestamp": datetime.now().isoformat(),
                        "domains": domains, "demand_analysis": result,
                        "total_domains_analyzed": len(result)}))
    except Exception as e:
        logger.error(f"market_demand: {e}")
        return jsonify({"error": "Internal server error", "details": str(e)}), 500


@fresher_bp.route("/analytics/market/competition", methods=["POST"])
def market_competition():
    try:
        data    = request.get_json() or {}
        domains = data.get("domains", [])
        if not domains:
            return jsonify({"error": "domains list is required"}), 400
        location = data.get("location", "Bangalore")
        exp_band = tuple(data.get("experience_band", [0, 3]))
        df     = get_job_data()
        engine = CompetitionLevelCalculator(df)
        result = {d: engine.calculate_competition(d, location, exp_band) for d in domains}
        return jsonify(sanitize_for_json({"success": True,
                        "timestamp": datetime.now().isoformat(),
                        "domains": domains, "location": location,
                        "experience_band": list(exp_band),
                        "competition_analysis": result,
                        "total_domains_analyzed": len(result)}))
    except Exception as e:
        logger.error(f"market_competition: {e}")
        return jsonify({"error": "Internal server error", "details": str(e)}), 500


@fresher_bp.route("/analytics/market/saturation", methods=["POST"])
def market_saturation():
    try:
        data    = request.get_json() or {}
        domains = data.get("domains", [])
        if not domains:
            return jsonify({"error": "domains list is required"}), 400
        df     = get_job_data()
        engine = SaturationRiskIndicator(df)
        result = {d: engine.calculate_saturation_risk(d) for d in domains}
        return jsonify(sanitize_for_json({"success": True,
                        "timestamp": datetime.now().isoformat(),
                        "domains": domains, "saturation_analysis": result,
                        "total_domains_analyzed": len(result)}))
    except Exception as e:
        logger.error(f"market_saturation: {e}")
        return jsonify({"error": "Internal server error", "details": str(e)}), 500


@fresher_bp.route("/analytics/market/salary", methods=["POST"])
def market_salary():
    try:
        data    = request.get_json() or {}
        domains = data.get("domains", [])
        if not domains:
            return jsonify({"error": "domains list is required"}), 400
        exp_level = data.get("experience_level", "entry")
        df     = get_job_data()
        engine = AverageSalaryRangeCalculator(df)
        result = {d: engine.calculate_salary_range(d, exp_level) for d in domains}
        return jsonify(sanitize_for_json({"success": True,
                        "timestamp": datetime.now().isoformat(),
                        "domains": domains, "experience_level": exp_level,
                        "salary_analysis": result,
                        "total_domains_analyzed": len(result)}))
    except Exception as e:
        logger.error(f"market_salary: {e}")
        return jsonify({"error": "Internal server error", "details": str(e)}), 500


@fresher_bp.route("/analytics/market/velocity", methods=["POST"])
def market_velocity():
    try:
        data    = request.get_json() or {}
        domains = data.get("domains", [])
        if not domains:
            return jsonify({"error": "domains list is required"}), 400
        df     = get_job_data()
        engine = JobMarketVelocityCalculator(df)
        result = {d: engine.calculate_velocity(d) for d in domains}
        return jsonify(sanitize_for_json({"success": True,
                        "timestamp": datetime.now().isoformat(),
                        "domains": domains, "velocity_analysis": result,
                        "total_domains_analyzed": len(result)}))
    except Exception as e:
        logger.error(f"market_velocity: {e}")
        return jsonify({"error": "Internal server error", "details": str(e)}), 500


# ═══════════════════════════════════════════════════════════════════════════════
# Analytics — Career Insights
# ═══════════════════════════════════════════════════════════════════════════════

@fresher_bp.route("/analytics/career/path", methods=["POST"])
def career_path():
    try:
        data = request.get_json() or {}
        if "target_domain" not in data:
            return jsonify({"error": "target_domain is required"}), 400
        df     = get_job_data()
        engine = CareerPathEngine(df)
        result = engine.analyze_career_path(
            data["target_domain"],
            data.get("user_skills", []),
            data.get("current_experience", 0),
            data.get("math_comfort", "Moderate"),
        )
        return jsonify(sanitize_for_json({"success": True, "timestamp": datetime.now().isoformat(),
                        **data, "career_path_analysis": result}))
    except Exception as e:
        logger.error(f"career_path: {e}")
        return jsonify({"error": "Internal server error", "details": str(e)}), 500


@fresher_bp.route("/analytics/career/role-evaluation", methods=["POST"])
def role_evaluation():
    try:
        data = request.get_json() or {}
        if "target_role" not in data:
            return jsonify({"error": "target_role is required"}), 400
        df     = get_job_data()
        engine = RoleEvolutionEngine(df)
        result = engine.evaluate_role(data["target_role"], data.get("user_profile", {}))
        return jsonify(sanitize_for_json({"success": True, "timestamp": datetime.now().isoformat(),
                        **data, "role_evaluation": result}))
    except Exception as e:
        logger.error(f"role_evaluation: {e}")
        return jsonify({"error": "Internal server error", "details": str(e)}), 500


# ═══════════════════════════════════════════════════════════════════════════════
# Analytics — Domain
# ═══════════════════════════════════════════════════════════════════════════════

@fresher_bp.route("/analytics/domain/ai-risk", methods=["POST"])
def domain_ai_risk():
    try:
        data    = request.get_json() or {}
        domains = data.get("domains", [])
        if not domains:
            return jsonify({"error": "domains list is required"}), 400
        df     = get_job_data()
        engine = AIReplacementRiskEngine(df)
        result = {d: engine.calculate_ai_risk(d) for d in domains}
        return jsonify(sanitize_for_json({"success": True,
                        "timestamp": datetime.now().isoformat(),
                        "domains": domains, "ai_risk_analysis": result,
                        "total_domains_analyzed": len(result)}))
    except Exception as e:
        logger.error(f"domain_ai_risk: {e}")
        return jsonify({"error": "Internal server error", "details": str(e)}), 500


@fresher_bp.route("/analytics/domain/stability", methods=["POST"])
def domain_stability():
    try:
        data    = request.get_json() or {}
        domains = data.get("domains", [])
        if not domains:
            return jsonify({"error": "domains list is required"}), 400
        df     = get_job_data()
        engine = DomainStabilityEngine(df)
        result = {d: engine.calculate_stability(d) for d in domains}
        return jsonify(sanitize_for_json({"success": True,
                        "timestamp": datetime.now().isoformat(),
                        "domains": domains, "stability_analysis": result,
                        "total_domains_analyzed": len(result)}))
    except Exception as e:
        logger.error(f"domain_stability: {e}")
        return jsonify({"error": "Internal server error", "details": str(e)}), 500


@fresher_bp.route("/analytics/domain/salary-growth", methods=["POST"])
def domain_salary_growth():
    try:
        data    = request.get_json() or {}
        domains = data.get("domains", [])
        if not domains:
            return jsonify({"error": "domains list is required"}), 400
        df     = get_job_data()
        engine = SalaryGrowthEngine(df)
        result = {d: engine.calculate_salary_growth(d) for d in domains}
        return jsonify(sanitize_for_json({"success": True,
                        "timestamp": datetime.now().isoformat(),
                        "domains": domains, "salary_growth_analysis": result,
                        "total_domains_analyzed": len(result)}))
    except Exception as e:
        logger.error(f"domain_salary_growth: {e}")
        return jsonify({"error": "Internal server error", "details": str(e)}), 500


@fresher_bp.route("/analytics/domain/skill-transferability", methods=["POST"])
def domain_skill_transferability():
    try:
        data    = request.get_json() or {}
        domains = data.get("domains", [])
        if not domains:
            return jsonify({"error": "domains list is required"}), 400
        df     = get_job_data()
        engine = SkillTransferabilityEngine(df)
        result = {d: engine.calculate_transferability(d) for d in domains}
        return jsonify(sanitize_for_json({"success": True,
                        "timestamp": datetime.now().isoformat(),
                        "domains": domains, "skill_transferability_analysis": result,
                        "total_domains_analyzed": len(result)}))
    except Exception as e:
        logger.error(f"domain_skill_transferability: {e}")
        return jsonify({"error": "Internal server error", "details": str(e)}), 500


# ═══════════════════════════════════════════════════════════════════════════════
# Analytics — Entry Barriers
# ═══════════════════════════════════════════════════════════════════════════════

@fresher_bp.route("/analytics/barriers/interview-difficulty", methods=["POST"])
def barriers_interview():
    try:
        data    = request.get_json() or {}
        domains = data.get("domains", [])
        if not domains:
            return jsonify({"error": "domains list is required"}), 400
        df     = get_job_data()
        engine = InterviewDifficultyEngine(df)
        result = {d: engine.calculate_difficulty(d) for d in domains}
        return jsonify(sanitize_for_json({"success": True,
                        "timestamp": datetime.now().isoformat(),
                        "domains": domains, "interview_difficulty_analysis": result,
                        "total_domains_analyzed": len(result)}))
    except Exception as e:
        logger.error(f"barriers_interview: {e}")
        return jsonify({"error": "Internal server error", "details": str(e)}), 500


@fresher_bp.route("/analytics/barriers/hidden-blockers", methods=["POST"])
def barriers_hidden_blockers():
    try:
        data    = request.get_json() or {}
        domains = data.get("domains", [])
        if not domains:
            return jsonify({"error": "domains list is required"}), 400
        user_profile = data.get("user_profile", {})
        df     = get_job_data()
        engine = HiddenBlockerDetector(df)
        result = {d: engine.detect_blockers(d, user_profile) for d in domains}
        return jsonify(sanitize_for_json({"success": True,
                        "timestamp": datetime.now().isoformat(),
                        "domains": domains, "user_profile": user_profile,
                        "hidden_blockers_analysis": result,
                        "total_domains_analyzed": len(result)}))
    except Exception as e:
        logger.error(f"barriers_hidden_blockers: {e}")
        return jsonify({"error": "Internal server error", "details": str(e)}), 500


@fresher_bp.route("/analytics/barriers/prerequisites", methods=["POST"])
def barriers_prerequisites():
    try:
        data    = request.get_json() or {}
        domains = data.get("domains", [])
        if not domains:
            return jsonify({"error": "domains list is required"}), 400
        df     = get_job_data()
        engine = PrerequisiteEngine(df)
        result = {d: engine.get_prerequisites(d) for d in domains}
        return jsonify(sanitize_for_json({"success": True,
                        "timestamp": datetime.now().isoformat(),
                        "domains": domains, "prerequisites_analysis": result,
                        "total_domains_analyzed": len(result)}))
    except Exception as e:
        logger.error(f"barriers_prerequisites: {e}")
        return jsonify({"error": "Internal server error", "details": str(e)}), 500


@fresher_bp.route("/analytics/barriers/project-complexity", methods=["POST"])
def barriers_project_complexity():
    try:
        data    = request.get_json() or {}
        domains = data.get("domains", [])
        if not domains:
            return jsonify({"error": "domains list is required"}), 400
        df     = get_job_data()
        engine = ProjectComplexityEvaluator(df)
        result = {d: engine.evaluate_complexity(d) for d in domains}
        return jsonify(sanitize_for_json({"success": True,
                        "timestamp": datetime.now().isoformat(),
                        "domains": domains, "project_complexity_analysis": result,
                        "total_domains_analyzed": len(result)}))
    except Exception as e:
        logger.error(f"barriers_project_complexity: {e}")
        return jsonify({"error": "Internal server error", "details": str(e)}), 500


# ═══════════════════════════════════════════════════════════════════════════════
# Analytics — Comprehensive
# ═══════════════════════════════════════════════════════════════════════════════

@fresher_bp.route("/analytics/comprehensive", methods=["POST"])
def analytics_comprehensive():
    try:
        data    = request.get_json() or {}
        domains = data.get("domains", [])
        if not domains:
            return jsonify({"error": "domains list is required"}), 400
        user_profile     = data.get("user_profile", {})
        include_market   = data.get("include_market", True)
        include_career   = data.get("include_career", True)
        include_domain   = data.get("include_domain", True)
        include_barriers = data.get("include_barriers", True)
        df               = get_job_data()
        analysis         = {}

        if include_market:
            analysis["market_analysis"] = {
                "demand":      {d: MarketDemandEngine(df).calculate_demand_score(d)           for d in domains},
                "competition": {d: CompetitionLevelCalculator(df).calculate_competition(d)    for d in domains},
                "saturation":  {d: SaturationRiskIndicator(df).calculate_saturation_risk(d)   for d in domains},
                "salary":      {d: AverageSalaryRangeCalculator(df).calculate_salary_range(d) for d in domains},
            }
        if include_career:
            career_engine = CareerPathEngine(df)
            role_engine   = RoleEvolutionEngine(df)
            analysis["career_analysis"] = {
                "path":            {d: career_engine.analyze_career_path(d) for d in domains},
                "role_evaluation": {d: role_engine.evaluate_role(d, user_profile) for d in domains},
            }
        if include_domain:
            analysis["domain_analysis"] = {
                "ai_risk":              {d: AIReplacementRiskEngine(df).calculate_ai_risk(d)          for d in domains},
                "stability":            {d: DomainStabilityEngine(df).calculate_stability(d)           for d in domains},
                "salary_growth":        {d: SalaryGrowthEngine(df).calculate_salary_growth(d)         for d in domains},
                "skill_transferability":{d: SkillTransferabilityEngine(df).calculate_transferability(d) for d in domains},
            }
        if include_barriers:
            analysis["barriers_analysis"] = {
                "interview_difficulty": {d: InterviewDifficultyEngine(df).calculate_difficulty(d)    for d in domains},
                "hidden_blockers":      {d: HiddenBlockerDetector(df).detect_blockers(d, user_profile) for d in domains},
                "prerequisites":        {d: PrerequisiteEngine(df).get_prerequisites(d)               for d in domains},
                "project_complexity":   {d: ProjectComplexityEvaluator(df).evaluate_complexity(d)     for d in domains},
            }

        return jsonify(sanitize_for_json({
            "success": True, "timestamp": datetime.now().isoformat(),
            "domains": domains, "user_profile": user_profile,
            "analysis_categories": {
                "market_analysis":   include_market,
                "career_analysis":   include_career,
                "domain_analysis":   include_domain,
                "barriers_analysis": include_barriers,
            },
            "comprehensive_analysis": analysis,
            "total_domains_analyzed": len(domains),
        }))
    except Exception as e:
        logger.error(f"analytics_comprehensive: {e}")
        return jsonify({"error": "Internal server error", "details": str(e)}), 500


# @fresher_bp.route("/analytics/domain-comprehensive", methods=["POST"])
# def domain_comprehensive():
#     try:
#         data = request.get_json() or {}
#         if "domain" not in data:
#             return jsonify({"error": "domain is required"}), 400
#         domain           = data["domain"]
#         location         = data.get("location", "Bangalore")
#         exp_band         = tuple(data.get("experience_band", [0, 3]))
#         user_profile     = data.get("user_profile")
#         recommended_domains = data.get("recommended_domains")

#         df = get_job_data()
#         if df is None or df.empty:
#             return jsonify({"error": "Job data not loaded"}), 503

#         global_results = _get_global_analytics()
#         pipeline       = AnalyticsPipeline(df)
#         domain_results = pipeline.run_domain_phase(
#             domain=domain, experience_band=exp_band, location=location,
#             recommended_domains=recommended_domains, global_results=global_results,
#         )
#         profile_results = None
#         if user_profile and isinstance(user_profile, dict):
#             skills = user_profile.get("skills", [])
#             if not isinstance(skills, list):
#                 skills = []
#             _MAP = {"weak": "none", "moderate": "basic", "strong": "intermediate",
#                     "none": "none", "basic": "basic", "intermediate": "intermediate", "advanced": "advanced"}
#             prior = _MAP.get(str(user_profile.get("math_comfort", "basic")).lower(), "basic")
#             profile_results = pipeline.run_profile_phase(
#                 domain=domain, experience_band=exp_band, location=location,
#                 user_skills=skills, prior_knowledge=prior, user_project_stats={},
#                 domain_results=domain_results,
#             )
#         return jsonify(sanitize_for_json({
#             "success": True, "domain_analytics": domain_results,
#             "profile_analytics": profile_results, "global_analytics": global_results,
#             "timestamp": datetime.now().isoformat(),
#         }))
#     except Exception as e:
#         logger.error(f"domain_comprehensive: {e}")
#         return jsonify({"error": "Internal server error", "details": str(e)}), 500
@fresher_bp.route("/analytics/domain-comprehensive", methods=["POST"])
def domain_comprehensive():
    try:
        data = request.get_json() or {}
        if "domain" not in data:
            return jsonify({"error": "domain is required"}), 400
            
        domain = data["domain"]
        location = data.get("location", "Bangalore")
        # Ensure exp_band is a tuple (tuples are hashable, lists are not)
        exp_band = tuple(data.get("experience_band", [0, 3]))
        
        user_profile = data.get("user_profile")
        # If recommended_domains is a list, convert to tuple to make it hashable
        recommended_domains = data.get("recommended_domains")
        if isinstance(recommended_domains, list):
            recommended_domains = tuple(recommended_domains)

        df = get_job_data()
        if df is None or df.empty:
            return jsonify({"error": "Job data not loaded"}), 503

        global_results = _get_global_analytics()
        pipeline = AnalyticsPipeline(df)
        
        # FIX: Ensure all arguments passed here are hashable 
        # (strings, tuples, ints are fine. dicts/lists are NOT)
        domain_results = pipeline.run_domain_phase(
            domain=domain, 
            experience_band=exp_band, 
            location=location,
            recommended_domains=recommended_domains, 
            global_results=global_results, # Assuming this is a dict, check if run_domain_phase caches this!
        )

        profile_results = None
        if user_profile and isinstance(user_profile, dict):
            # Extract only what's needed as hashable types
            skills = tuple(user_profile.get("skills", [])) 
            
            _MAP = {"weak": "none", "moderate": "basic", "strong": "intermediate",
                    "none": "none", "basic": "basic", "intermediate": "intermediate", "advanced": "advanced"}
            
            prior = _MAP.get(str(user_profile.get("math_comfort", "basic")).lower(), "basic")
            
            profile_results = pipeline.run_profile_phase(
                domain=domain, 
                experience_band=exp_band, 
                location=location,
                user_skills=list(skills), # Convert back to list if the engine specifically needs a list
                prior_knowledge=prior, 
                user_project_stats={}, 
                domain_results=domain_results,
            )

        return jsonify(sanitize_for_json({
            "success": True, 
            "domain_analytics": domain_results,
            "profile_analytics": profile_results, 
            "global_analytics": global_results,
            "timestamp": datetime.now().isoformat()
        }))

    except Exception as e:
        logger.error(f"domain_comprehensive: {e}")
        # This will now catch the error and return 500 with details
        return jsonify({"error": "Internal server error", "details": str(e)}), 500

# ═══════════════════════════════════════════════════════════════════════════════
# Data Stats
# ═══════════════════════════════════════════════════════════════════════════════

@fresher_bp.route("/data/stats", methods=["GET"])
def data_stats():
    try:
        df = get_job_data()
        stats = {
            "total_records":          len(df),
            "job_types":              df["job_type"].value_counts().to_dict()  if "job_type"        in df.columns else {},
            "experience_distribution":df["min_experience"].value_counts().to_dict() if "min_experience" in df.columns else {},
            "location_distribution":  df["location"].value_counts().to_dict() if "location"         in df.columns else {},
            "salary_stats": {
                "mean":   float(df["salary_lakhs"].mean())   if "salary_lakhs" in df.columns else None,
                "median": float(df["salary_lakhs"].median()) if "salary_lakhs" in df.columns else None,
                "min":    float(df["salary_lakhs"].min())    if "salary_lakhs" in df.columns else None,
                "max":    float(df["salary_lakhs"].max())    if "salary_lakhs" in df.columns else None,
            },
            "data_columns": list(df.columns),
            "data_source":  os.environ.get("DATA_SOURCE", "csv"),
            "last_updated": datetime.now().isoformat(),
        }
        return jsonify({"success": True, "stats": stats})
    except Exception as e:
        logger.error(f"data_stats: {e}")
        return jsonify({"error": "Internal server error", "details": str(e)}), 500


import os  # noqa: E402 (needed for data_stats above)