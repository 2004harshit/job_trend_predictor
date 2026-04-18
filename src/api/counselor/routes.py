"""
src/api/counselor/routes.py
===========================
Career-Counselor endpoints — mounted under  /api/counselor/

Endpoint map
------------
Health
    GET  /api/counselor/health

Market Pulse (Feature 1)
    GET  /api/counselor/market-pulse/snapshot
    GET  /api/counselor/market-pulse/top-domains
    GET  /api/counselor/market-pulse/skills
    POST /api/counselor/market-pulse/momentum
    GET  /api/counselor/market-pulse/saturation

Skill Gap Analyzer (Feature 3)
    POST /api/counselor/skill-gap/analyze
    GET  /api/counselor/skill-gap/popular-skills

Domain Comparison (Feature 2)
    POST /api/counselor/domain/compare
    GET  /api/counselor/domain/fresher-analysis
    POST /api/counselor/domain/skill-matrix

Salary Intelligence (Feature 4)
    GET  /api/counselor/salary/ranges
    GET  /api/counselor/salary/jaipur-vs-national
    GET  /api/counselor/salary/top-skills
    GET  /api/counselor/salary/by-experience

Company Intelligence (Feature 5)
    GET  /api/counselor/companies/top
    GET  /api/counselor/companies/type-split
    GET  /api/counselor/companies/hiring-frequency
    GET  /api/counselor/companies/jaipur

Utility
    GET  /api/counselor/filters/options
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Optional

import numpy as np
from flask import Blueprint, request, jsonify

from src.api.data_loader import get_job_data

from src.analytics.career_counselor.services.market_pulse_service    import MarketPulseService
from src.analytics.career_counselor.services.skill_gap_service       import SkillGapAnalyzerService
from src.analytics.career_counselor.services.domain_comparison_service import DomainComparisonService
from src.analytics.career_counselor.services.salary_service          import SalaryIntelligenceService
from src.analytics.career_counselor.services.company_service         import CompanyIntelligenceService

logger       = logging.getLogger(__name__)
counselor_bp = Blueprint("counselor", __name__)


# ── shared helpers ────────────────────────────────────────────────────────────

def _sanitize(obj):
    if isinstance(obj, dict):   return {k: _sanitize(v) for k, v in obj.items()}
    if isinstance(obj, list):   return [_sanitize(i) for i in obj]
    if isinstance(obj, np.bool_):    return bool(obj)
    if isinstance(obj, np.integer):  return int(obj)
    if isinstance(obj, np.floating): return float(obj)
    if isinstance(obj, np.ndarray):  return obj.tolist()
    return obj

def _ok(data: dict):
    data["timestamp"] = datetime.now().isoformat()
    data["status"]    = "success"
    return jsonify(_sanitize(data)), 200

def _err(message: str, details: str = "", code: int = 400):
    return jsonify({"status": "error", "message": message, "details": details,
                    "timestamp": datetime.now().isoformat()}), code

def _load_df():
    df = get_job_data()
    return None if (df is None or df.empty) else df

def _parse_common_params() -> dict:
    try:
        days = max(1, min(int(request.args.get("days", 30)), 365))
    except (ValueError, TypeError):
        days = 30
    location = request.args.get("location") or None
    if location and location.strip().lower() in ("all", "national", ""):
        location = None
    fresher_only = request.args.get("fresher_only", "false").lower() in ("1", "true", "yes")
    return {"days": days, "location": location, "fresher_only": fresher_only}


# ── health ────────────────────────────────────────────────────────────────────

@counselor_bp.route("/health", methods=["GET"])
def health():
    df = _load_df()
    return jsonify({"status": "healthy", "module": "counselor",
                    "data_loaded": df is not None,
                    "total_rows": len(df) if df is not None else 0,
                    "timestamp": datetime.now().isoformat()}), 200


# ── Feature 1 — Market Pulse ──────────────────────────────────────────────────

@counselor_bp.route("/market-pulse/snapshot", methods=["GET"])
def market_pulse_snapshot():
    params = _parse_common_params()
    df = _load_df()
    if df is None: return _err("Job data not loaded", code=503)
    try:
        return _ok(MarketPulseService(df).get_snapshot(**params))
    except Exception as e:
        logger.exception("market_pulse_snapshot failed")
        return _err("Snapshot failed", str(e), 500)


@counselor_bp.route("/market-pulse/top-domains", methods=["GET"])
def market_pulse_top_domains():
    params = _parse_common_params()
    try:
        limit = max(1, min(int(request.args.get("limit", 10)), 30))
    except (ValueError, TypeError):
        limit = 10
    df = _load_df()
    if df is None: return _err("Job data not loaded", code=503)
    try:
        return _ok(MarketPulseService(df).get_top_domains(limit=limit, **params))
    except Exception as e:
        logger.exception("market_pulse_top_domains failed")
        return _err("Top domains failed", str(e), 500)


@counselor_bp.route("/market-pulse/skills", methods=["GET"])
def market_pulse_skills():
    params = _parse_common_params()
    try:
        top_n = max(1, min(int(request.args.get("top_n", 20)), 50))
    except (ValueError, TypeError):
        top_n = 20
    domain = request.args.get("domain") or None
    df = _load_df()
    if df is None: return _err("Job data not loaded", code=503)
    try:
        return _ok(MarketPulseService(df).get_skill_frequency(top_n=top_n, domain=domain, **params))
    except Exception as e:
        logger.exception("market_pulse_skills failed")
        return _err("Skill frequency failed", str(e), 500)


@counselor_bp.route("/market-pulse/momentum", methods=["POST"])
def market_pulse_momentum():
    body = request.get_json(silent=True) or {}
    skills_list = body.get("skills", None)
    if skills_list is not None and not isinstance(skills_list, list):
        return _err("'skills' must be a list of strings")
    try:
        days = max(1, min(int(body.get("days", 30)), 365))
    except (ValueError, TypeError):
        days = 30
    location = body.get("location") or None
    if location and location.strip().lower() in ("all", "national", ""):
        location = None
    try:
        top_n_auto = max(5, min(int(body.get("top_n_auto", 20)), 50))
    except (ValueError, TypeError):
        top_n_auto = 20
    df = _load_df()
    if df is None: return _err("Job data not loaded", code=503)
    try:
        return _ok(MarketPulseService(df).get_momentum_badges(
            skills_list=skills_list, days=days, location=location, top_n_auto=top_n_auto))
    except Exception as e:
        logger.exception("market_pulse_momentum failed")
        return _err("Momentum failed", str(e), 500)


@counselor_bp.route("/market-pulse/saturation", methods=["GET"])
def market_pulse_saturation():
    params = _parse_common_params()
    params.pop("fresher_only")
    try:
        min_jobs = max(1, int(request.args.get("min_jobs", 10)))
    except (ValueError, TypeError):
        min_jobs = 10
    df = _load_df()
    if df is None: return _err("Job data not loaded", code=503)
    try:
        return _ok(MarketPulseService(df).get_saturation_indicators(min_jobs=min_jobs, **params))
    except Exception as e:
        logger.exception("market_pulse_saturation failed")
        return _err("Saturation failed", str(e), 500)


# ── Feature 3 — Skill Gap Analyzer ───────────────────────────────────────────

@counselor_bp.route("/skill-gap/analyze", methods=["POST"])
def skill_gap_analyze():
    body          = request.get_json(silent=True) or {}
    student_skills = body.get("student_skills", [])
    if not isinstance(student_skills, list) or len(student_skills) == 0:
        return _err("'student_skills' is required and must be a non-empty list")
    target_domain = body.get("target_domain", "").strip()
    if not target_domain:
        return _err("'target_domain' is required")
    try:
        top_roles = max(5, min(int(body.get("top_roles", 20)), 100))
    except (ValueError, TypeError):
        top_roles = 20
    try:
        days = max(1, min(int(body.get("days", 60)), 365))
    except (ValueError, TypeError):
        days = 60
    location = body.get("location") or None
    if location and location.strip().lower() in ("all", "national", ""): location = None
    fresher_only = bool(body.get("fresher_only", True))
    df = _load_df()
    if df is None: return _err("Job data not loaded", code=503)
    try:
        return _ok(SkillGapAnalyzerService(df).analyze_skill_gap(
            student_skills=student_skills, target_domain=target_domain,
            top_roles=top_roles, days=days, location=location, fresher_only=fresher_only))
    except Exception as e:
        logger.exception("skill_gap_analyze failed")
        return _err("Skill gap analysis failed", str(e), 500)


@counselor_bp.route("/skill-gap/popular-skills", methods=["GET"])
def skill_gap_popular_skills():
    domain = request.args.get("domain", "").strip()
    if not domain: return _err("'domain' query parameter is required")
    try:
        top_n = max(5, min(int(request.args.get("top_n", 30)), 50))
    except (ValueError, TypeError):
        top_n = 30
    try:
        days = max(1, min(int(request.args.get("days", 60)), 365))
    except (ValueError, TypeError):
        days = 60
    fresher_only = request.args.get("fresher_only", "true").lower() in ("1", "true", "yes")
    df = _load_df()
    if df is None: return _err("Job data not loaded", code=503)
    try:
        return _ok(SkillGapAnalyzerService(df).get_popular_skills_for_domain(
            domain=domain, top_n=top_n, days=days, fresher_only=fresher_only))
    except Exception as e:
        logger.exception("skill_gap_popular_skills failed")
        return _err("Popular skills failed", str(e), 500)


# ── Feature 2 — Domain Comparison ────────────────────────────────────────────

@counselor_bp.route("/domain/compare", methods=["POST"])
def domain_compare():
    body = request.get_json(silent=True) or {}
    domains = body.get("domains", [])
    if not isinstance(domains, list) or len(domains) < 2:
        return _err("'domains' must be a list of at least 2 domain names")
    if len(domains) > 5:
        return _err("Maximum 5 domains per comparison")
    fresher_only = bool(body.get("fresher_only", True))
    try:
        days = max(1, min(int(body.get("days", 60)), 365))
    except (ValueError, TypeError):
        days = 60
    location = body.get("location") or None
    if location and location.strip().lower() in ("all", "national", ""): location = None
    df = _load_df()
    if df is None: return _err("Job data not loaded", code=503)
    try:
        return _ok(DomainComparisonService(df).compare_domains(
            domain_list=domains, fresher_only=fresher_only, days=days, location=location))
    except Exception as e:
        logger.exception("domain_compare failed")
        return _err("Domain comparison failed", str(e), 500)


@counselor_bp.route("/domain/fresher-analysis", methods=["GET"])
def domain_fresher_analysis():
    domain = request.args.get("domain", "").strip()
    if not domain: return _err("'domain' query parameter is required")
    try:
        days = max(1, min(int(request.args.get("days", 60)), 365))
    except (ValueError, TypeError):
        days = 60
    location = request.args.get("location") or None
    if location and location.strip().lower() in ("all", "national", ""): location = None
    df = _load_df()
    if df is None: return _err("Job data not loaded", code=503)
    try:
        return _ok(DomainComparisonService(df).get_fresher_analysis(domain=domain, days=days, location=location))
    except Exception as e:
        logger.exception("domain_fresher_analysis failed")
        return _err("Fresher analysis failed", str(e), 500)


@counselor_bp.route("/domain/skill-matrix", methods=["POST"])
def domain_skill_matrix():
    body = request.get_json(silent=True) or {}
    domains = body.get("domains", [])
    if not isinstance(domains, list) or len(domains) < 2:
        return _err("'domains' must be a list of at least 2 domain names")
    try:
        top_n = max(5, min(int(body.get("top_skills_per_domain", 15)), 30))
    except (ValueError, TypeError):
        top_n = 15
    try:
        days = max(1, min(int(body.get("days", 60)), 365))
    except (ValueError, TypeError):
        days = 60
    location     = body.get("location") or None
    fresher_only = bool(body.get("fresher_only", True))
    df = _load_df()
    if df is None: return _err("Job data not loaded", code=503)
    try:
        return _ok(DomainComparisonService(df).get_domain_skill_matrix(
            domain_list=domains, top_skills_per_domain=top_n,
            days=days, location=location, fresher_only=fresher_only))
    except Exception as e:
        logger.exception("domain_skill_matrix failed")
        return _err("Skill matrix failed", str(e), 500)


# ── Feature 4 — Salary Intelligence ──────────────────────────────────────────

@counselor_bp.route("/salary/ranges", methods=["GET"])
def salary_ranges():
    domain   = request.args.get("domain") or None
    location = request.args.get("location") or None
    if location and location.strip().lower() in ("all", "national", ""): location = None
    fresher_only = request.args.get("fresher_only", "true").lower() in ("1", "true", "yes")
    days: Optional[int] = None
    days_raw = request.args.get("days")
    if days_raw:
        try: days = max(1, min(int(days_raw), 365))
        except (ValueError, TypeError): pass
    df = _load_df()
    if df is None: return _err("Job data not loaded", code=503)
    try:
        return _ok(SalaryIntelligenceService(df).get_salary_ranges(
            domain=domain, location=location, fresher_only=fresher_only, days=days))
    except Exception as e:
        logger.exception("salary_ranges failed")
        return _err("Salary ranges failed", str(e), 500)


@counselor_bp.route("/salary/jaipur-vs-national", methods=["GET"])
def salary_jaipur_vs_national():
    domain       = request.args.get("domain") or None
    fresher_only = request.args.get("fresher_only", "true").lower() in ("1", "true", "yes")
    days: Optional[int] = None
    days_raw = request.args.get("days")
    if days_raw:
        try: days = max(1, min(int(days_raw), 365))
        except (ValueError, TypeError): pass
    df = _load_df()
    if df is None: return _err("Job data not loaded", code=503)
    try:
        return _ok(SalaryIntelligenceService(df).get_jaipur_vs_national(
            domain=domain, days=days, fresher_only=fresher_only))
    except Exception as e:
        logger.exception("salary_jaipur_vs_national failed")
        return _err("Jaipur vs national failed", str(e), 500)


@counselor_bp.route("/salary/top-skills", methods=["GET"])
def salary_top_skills():
    domain   = request.args.get("domain") or None
    location = request.args.get("location") or None
    if location and location.strip().lower() in ("all", "national", ""): location = None
    try:
        top_n = max(5, min(int(request.args.get("top_n", 15)), 30))
    except (ValueError, TypeError):
        top_n = 15
    df = _load_df()
    if df is None: return _err("Job data not loaded", code=503)
    try:
        return _ok(SalaryIntelligenceService(df).get_top_10_percent_skills(
            domain=domain, location=location, top_n=top_n))
    except Exception as e:
        logger.exception("salary_top_skills failed")
        return _err("Top salary skills failed", str(e), 500)


@counselor_bp.route("/salary/by-experience", methods=["GET"])
def salary_by_experience():
    domain   = request.args.get("domain") or None
    location = request.args.get("location") or None
    if location and location.strip().lower() in ("all", "national", ""): location = None
    days: Optional[int] = None
    days_raw = request.args.get("days")
    if days_raw:
        try: days = max(1, min(int(days_raw), 365))
        except (ValueError, TypeError): pass
    df = _load_df()
    if df is None: return _err("Job data not loaded", code=503)
    try:
        return _ok(SalaryIntelligenceService(df).get_salary_by_experience_band(
            domain=domain, location=location, days=days))
    except Exception as e:
        logger.exception("salary_by_experience failed")
        return _err("Salary by experience failed", str(e), 500)


# ── Feature 5 — Company Intelligence ─────────────────────────────────────────

@counselor_bp.route("/companies/top", methods=["GET"])
def companies_top():
    params = _parse_common_params()
    domain = request.args.get("domain") or None
    try:
        limit = max(1, min(int(request.args.get("limit", 15)), 50))
    except (ValueError, TypeError):
        limit = 15
    df = _load_df()
    if df is None: return _err("Job data not loaded", code=503)
    try:
        return _ok(CompanyIntelligenceService(df).get_top_hiring_companies(domain=domain, limit=limit, **params))
    except Exception as e:
        logger.exception("companies_top failed")
        return _err("Top companies failed", str(e), 500)


@counselor_bp.route("/companies/type-split", methods=["GET"])
def companies_type_split():
    params = _parse_common_params()
    domain = request.args.get("domain") or None
    df = _load_df()
    if df is None: return _err("Job data not loaded", code=503)
    try:
        return _ok(CompanyIntelligenceService(df).get_company_type_split(domain=domain, **params))
    except Exception as e:
        logger.exception("companies_type_split failed")
        return _err("Company type split failed", str(e), 500)


@counselor_bp.route("/companies/hiring-frequency", methods=["GET"])
def companies_hiring_frequency():
    company = request.args.get("company", "").strip()
    if not company: return _err("'company' query parameter is required")
    try:
        days = max(1, min(int(request.args.get("days", 90)), 365))
    except (ValueError, TypeError):
        days = 90
    df = _load_df()
    if df is None: return _err("Job data not loaded", code=503)
    try:
        return _ok(CompanyIntelligenceService(df).get_hiring_frequency(company=company, days=days))
    except Exception as e:
        logger.exception("companies_hiring_frequency failed")
        return _err("Hiring frequency failed", str(e), 500)


@counselor_bp.route("/companies/jaipur", methods=["GET"])
def companies_jaipur():
    domain = request.args.get("domain") or None
    try:
        days = max(1, min(int(request.args.get("days", 60)), 365))
    except (ValueError, TypeError):
        days = 60
    try:
        limit = max(1, min(int(request.args.get("limit", 20)), 50))
    except (ValueError, TypeError):
        limit = 20
    fresher_only = request.args.get("fresher_only", "false").lower() in ("1", "true", "yes")
    df = _load_df()
    if df is None: return _err("Job data not loaded", code=503)
    try:
        return _ok(CompanyIntelligenceService(df).get_jaipur_companies(
            domain=domain, days=days, fresher_only=fresher_only, limit=limit))
    except Exception as e:
        logger.exception("companies_jaipur failed")
        return _err("Jaipur companies failed", str(e), 500)


# ── Utility ───────────────────────────────────────────────────────────────────

@counselor_bp.route("/filters/options", methods=["GET"])
def filters_options():
    df = _load_df()
    if df is None: return _err("Job data not loaded", code=503)
    try:
        domains   = sorted(df["department"].dropna().unique().tolist()) if "department" in df.columns else []
        locations = sorted(df["location"].dropna().unique().tolist())   if "location"   in df.columns else []
        companies = sorted(df["company"].dropna().unique().tolist())    if "company"    in df.columns else []
        return _ok({"domains": domains, "locations": locations, "companies": companies})
    except Exception as e:
        logger.exception("filters_options failed")
        return _err("Filter options failed", str(e), 500)