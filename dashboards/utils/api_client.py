"""
API Client for Job Trend Predictor
====================================
Sends HTTP requests to the Flask backend (run.py).
The UI does NOT load data directly — it only sends request params.

URL structure (matches reorganized run.py blueprints)
------------------------------------------------------
  Global
      GET  /api/health

  Fresher feature  →  /api/fresher/
      POST /api/fresher/recommend
      GET  /api/fresher/recommend/domains
      POST /api/fresher/recommend/analyze
      POST /api/fresher/recommend/compare
      GET  /api/fresher/market/signals/<domain>
      POST /api/fresher/analytics/market/demand
      POST /api/fresher/analytics/market/competition
      POST /api/fresher/analytics/market/saturation
      POST /api/fresher/analytics/market/salary
      POST /api/fresher/analytics/market/velocity
      POST /api/fresher/analytics/career/path
      POST /api/fresher/analytics/career/role-evaluation
      POST /api/fresher/analytics/domain/ai-risk
      POST /api/fresher/analytics/domain/stability
      POST /api/fresher/analytics/domain/salary-growth
      POST /api/fresher/analytics/domain/skill-transferability
      POST /api/fresher/analytics/barriers/interview-difficulty
      POST /api/fresher/analytics/barriers/hidden-blockers
      POST /api/fresher/analytics/barriers/prerequisites
      POST /api/fresher/analytics/barriers/project-complexity
      POST /api/fresher/analytics/comprehensive
      POST /api/fresher/analytics/domain-comprehensive
      GET  /api/fresher/data/stats

  Counselor feature  →  /api/counselor/
      GET  /api/counselor/health
      GET  /api/counselor/filters/options
      ... (market pulse, skill gap, domain comparison, salary, companies)

Sections
--------
  1. Core helpers            (_get, _post, _common_params)
  2. Global                  (health_check)
  3. Fresher — Recommendations
  4. Fresher — Analytics
  5. Counselor — Utility
  6. Counselor — Feature 1: Market Pulse
  7. Counselor — Feature 2: Domain Comparison
  8. Counselor — Feature 3: Skill Gap Analyzer
  9. Counselor — Feature 4: Salary Intelligence
 10. Counselor — Feature 5: Company Intelligence
"""

import os
import requests
from typing import Any, Dict, List, Optional

# Allows  `from api_client import api_client`  in dashboard code
api_client = __import__(__name__)

# ── connection config ─────────────────────────────────────────────────────────
BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:5000")
TIMEOUT  = 30

# ── blueprint prefixes ────────────────────────────────────────────────────────
_FR = "/api/fresher"    # Fresher feature
_CC = "/api/counselor"  # Career Counselor feature


# =============================================================================
# 1. Core helpers
# =============================================================================

def _get(url: str, params: Optional[Dict] = None) -> Optional[Dict]:
    """GET request → returns parsed JSON or None on any error."""
    try:
        r = requests.get(f"{BASE_URL}{url}", params=params, timeout=TIMEOUT)
        r.raise_for_status()
        return r.json()
    except requests.HTTPError as e:
        # surface the server's error message when available
        try:
            return {"_error": True, "status_code": e.response.status_code,
                    "detail": e.response.json()}
        except Exception:
            pass
    except requests.RequestException:
        pass
    except ValueError:
        pass
    return None


def _post(url: str, json: Optional[Dict] = None) -> Optional[Dict]:
    """POST request → returns parsed JSON or None on any error."""
    try:
        r = requests.post(f"{BASE_URL}{url}", json=json or {}, timeout=TIMEOUT)
        r.raise_for_status()
        return r.json()
    except requests.HTTPError as e:
        try:
            return {"_error": True, "status_code": e.response.status_code,
                    "detail": e.response.json()}
        except Exception:
            pass
    except requests.RequestException:
        pass
    except ValueError:
        pass
    return None


def _common_params(
    days: int,
    location: Optional[str],
    fresher_only: bool,
) -> Dict[str, Any]:
    """Build standard query-param dict used by most GET endpoints."""
    p: Dict[str, Any] = {
        "days":         days,
        "fresher_only": str(fresher_only).lower(),
    }
    if location:
        p["location"] = location
    return p


def _band_tuple_to_label(band: tuple) -> str:
    """Convert experience tuple like (0,3) → 'fresher' / 'junior' / 'mid'."""
    low = band[0] if band else 0
    if   low == 0: return "fresher"
    elif low <= 2: return "junior"
    else:          return "mid"


# =============================================================================
# 2. Global
# =============================================================================

def health_check() -> bool:
    """
    GET /api/health
    Returns True if the API server is reachable and healthy.
    """
    data = _get("/api/health")
    return data is not None and data.get("status") == "healthy"


# =============================================================================
# 3. Fresher — Recommendations
# =============================================================================

def fresher_health() -> bool:
    """
    GET /api/fresher/health
    Returns True if the fresher blueprint is healthy.
    """
    data = _get(f"{_FR}/health")
    return data is not None and data.get("status") == "healthy"


def get_recommendations(
    user_profile: Dict[str, Any],
    top_n: int = 3,
) -> Optional[List[Dict]]:
    """
    POST /api/fresher/recommend
    Get domain recommendations for a fresher profile.

    user_profile keys: skills (list), experience, location, math_comfort
    Returns: list of { domain, match_percentage, reasoning, pros, cons,
                        timeline, market_metrics }
    """
    skills = user_profile.get("skills", []) or ["Python"]
    data = _post(f"{_FR}/recommend", json={
        "skills":       skills,
        "experience":   user_profile.get("experience",   "Fresher"),
        "location":     user_profile.get("location",     "Jaipur"),
        "math_comfort": user_profile.get("math_comfort", "Moderate"),
        "top_n":        top_n,
    })
    if data and data.get("success") and "recommendations" in data:
        return data["recommendations"]
    return None


def get_all_domains() -> Optional[List[str]]:
    """
    GET /api/fresher/recommend/domains
    Returns a list of all available domain names.
    """
    data = _get(f"{_FR}/recommend/domains")
    if data and data.get("success") and "domains" in data:
        return data["domains"]
    return None


def get_domain_compatibility(
    user_profile: Dict[str, Any],
    selected_domain: str,
) -> Optional[Dict]:
    """
    POST /api/fresher/recommend/analyze
    Get compatibility score for a single domain.
    Returns: { match_percentage, reasoning, pros, cons, ... }
    """
    data = _post(f"{_FR}/recommend/analyze", json={
        "domain": selected_domain,
        "user_profile": {
            "skills":       user_profile.get("skills",       []),
            "experience":   user_profile.get("experience",   "Fresher"),
            "location":     user_profile.get("location",     "Jaipur"),
            "math_comfort": user_profile.get("math_comfort", "Moderate"),
        },
    })
    if data and data.get("success") and "analysis" in data:
        return data["analysis"].get("detailed_analysis")
    return None


def compare_domains(
    domains: List[str],
    user_profile: Dict[str, Any],
) -> Optional[Dict]:
    """
    POST /api/fresher/recommend/compare
    Compare multiple domains side-by-side for a user profile.
    Returns: { comparisons: [...], ranking_summary: [...] }
    """
    return _post(f"{_FR}/recommend/compare", json={
        "domains":      domains,
        "user_profile": {
            "skills":       user_profile.get("skills",       []),
            "experience":   user_profile.get("experience",   "Fresher"),
            "location":     user_profile.get("location",     "Jaipur"),
            "math_comfort": user_profile.get("math_comfort", "Moderate"),
        },
    })


def get_market_signals(
    domain: str,
    location: str = "Jaipur",
) -> Optional[Dict]:
    """
    GET /api/fresher/market/signals/<domain>
    Returns: { demand_score, comp_level, sat_risk, growth_trend }
    """
    return _get(f"{_FR}/market/signals/{domain}", params={"location": location})


# =============================================================================
# 4. Fresher — Analytics
# =============================================================================

def get_domain_analytics(
    domain: str,
    location: str = "Jaipur",
    experience_band: tuple = (0, 3),
    user_profile: Optional[Dict[str, Any]] = None,
    recommended_domains: Optional[List[str]] = None,
) -> Optional[Dict[str, Any]]:
    """
    POST /api/fresher/analytics/domain-comprehensive
    Full pipeline analytics for one domain (global + domain + optional profile phase).

    Returns: { domain_analytics, profile_analytics, global_analytics }
    """
    payload: Dict[str, Any] = {
        "domain":          domain,
        "location":        location,
        "experience_band": list(experience_band),
    }
    if user_profile:
        payload["user_profile"] = {
            "skills":       user_profile.get("skills",       []),
            "experience":   user_profile.get("experience",   "Fresher"),
            "location":     user_profile.get("location",     location),
            "math_comfort": user_profile.get("math_comfort", "Moderate"),
        }
    if recommended_domains:
        payload["recommended_domains"] = recommended_domains

    data = _post(f"{_FR}/analytics/domain-comprehensive", json=payload)
    if data and data.get("success"):
        return data
    return None


def get_market_demand(
    domains: List[str],
    weights: Optional[Dict[str, float]] = None,
) -> Optional[Dict]:
    """
    POST /api/fresher/analytics/market/demand
    Returns: { demand_analysis: { domain: { Overall_Demand_Score, Breakdown, ... } } }
    """
    body: Dict[str, Any] = {"domains": domains}
    if weights:
        body["weights"] = weights
    return _post(f"{_FR}/analytics/market/demand", json=body)


def get_market_competition(
    domains: List[str],
    location: str = "Jaipur",
    experience_band: tuple = (0, 3),
) -> Optional[Dict]:
    """
    POST /api/fresher/analytics/market/competition
    Returns: { competition_analysis: { domain: { Level, Applicant_to_Opening_Ratio, ... } } }
    """
    return _post(f"{_FR}/analytics/market/competition", json={
        "domains":          domains,
        "location":         location,
        "experience_band":  list(experience_band),
    })


def get_market_saturation(domains: List[str]) -> Optional[Dict]:
    """
    POST /api/fresher/analytics/market/saturation
    Returns: { saturation_analysis: { domain: { Risk_Level, Saturation_Score, ... } } }
    """
    return _post(f"{_FR}/analytics/market/saturation", json={"domains": domains})


def get_market_salary(
    domains: List[str],
    experience_level: str = "entry",
) -> Optional[Dict]:
    """
    POST /api/fresher/analytics/market/salary
    Returns: { salary_analysis: { domain: { Average_Salary, Salary_Range, ... } } }
    """
    return _post(f"{_FR}/analytics/market/salary", json={
        "domains":          domains,
        "experience_level": experience_level,
    })


def get_market_velocity(domains: List[str]) -> Optional[Dict]:
    """
    POST /api/fresher/analytics/market/velocity
    Returns: { velocity_analysis: { domain: { Hiring_Velocity, Market_Trend, ... } } }
    """
    return _post(f"{_FR}/analytics/market/velocity", json={"domains": domains})


def get_career_path(
    target_domain: str,
    user_skills: Optional[List[str]] = None,
    current_experience: int = 0,
    math_comfort: str = "Moderate",
) -> Optional[Dict]:
    """
    POST /api/fresher/analytics/career/path
    Returns: { career_path_analysis: { Readiness_Score, Learning_Path, Skill_Gaps, ... } }
    """
    return _post(f"{_FR}/analytics/career/path", json={
        "target_domain":       target_domain,
        "user_skills":         user_skills or [],
        "current_experience":  current_experience,
        "math_comfort":        math_comfort,
    })


def get_role_evaluation(
    target_role: str,
    user_profile: Optional[Dict[str, Any]] = None,
) -> Optional[Dict]:
    """
    POST /api/fresher/analytics/career/role-evaluation
    Returns: { role_evaluation: { Fit_Score, Strengths, Gaps, Readiness_Level, ... } }
    """
    return _post(f"{_FR}/analytics/career/role-evaluation", json={
        "target_role":  target_role,
        "user_profile": user_profile or {},
    })


def get_ai_risk(domains: List[str]) -> Optional[Dict]:
    """
    POST /api/fresher/analytics/domain/ai-risk
    Returns: { ai_risk_analysis: { domain: { Automation_Risk, Risk_Score, ... } } }
    """
    return _post(f"{_FR}/analytics/domain/ai-risk", json={"domains": domains})


def get_domain_stability(domains: List[str]) -> Optional[Dict]:
    """
    POST /api/fresher/analytics/domain/stability
    Returns: { stability_analysis: { domain: { Stability_Score, ... } } }
    """
    return _post(f"{_FR}/analytics/domain/stability", json={"domains": domains})


def get_salary_growth(domains: List[str]) -> Optional[Dict]:
    """
    POST /api/fresher/analytics/domain/salary-growth
    Returns: { salary_growth_analysis: { domain: { Growth_Rate, ... } } }
    """
    return _post(f"{_FR}/analytics/domain/salary-growth", json={"domains": domains})


def get_skill_transferability(domains: List[str]) -> Optional[Dict]:
    """
    POST /api/fresher/analytics/domain/skill-transferability
    Returns: { skill_transferability_analysis: { domain: { Transferability_Score, ... } } }
    """
    return _post(f"{_FR}/analytics/domain/skill-transferability", json={"domains": domains})


def get_interview_difficulty(domains: List[str]) -> Optional[Dict]:
    """
    POST /api/fresher/analytics/barriers/interview-difficulty
    Returns: { interview_difficulty_analysis: { domain: { Difficulty_Level, ... } } }
    """
    return _post(f"{_FR}/analytics/barriers/interview-difficulty", json={"domains": domains})


def get_hidden_blockers(
    domains: List[str],
    user_profile: Optional[Dict[str, Any]] = None,
) -> Optional[Dict]:
    """
    POST /api/fresher/analytics/barriers/hidden-blockers
    Returns: { hidden_blockers_analysis: { domain: { Identified_Blockers, ... } } }
    """
    return _post(f"{_FR}/analytics/barriers/hidden-blockers", json={
        "domains":      domains,
        "user_profile": user_profile or {},
    })


def get_prerequisites(domains: List[str]) -> Optional[Dict]:
    """
    POST /api/fresher/analytics/barriers/prerequisites
    Returns: { prerequisites_analysis: { domain: { Essential_Skills, ... } } }
    """
    return _post(f"{_FR}/analytics/barriers/prerequisites", json={"domains": domains})


def get_project_complexity(domains: List[str]) -> Optional[Dict]:
    """
    POST /api/fresher/analytics/barriers/project-complexity
    Returns: { project_complexity_analysis: { domain: { Complexity_Level, ... } } }
    """
    return _post(f"{_FR}/analytics/barriers/project-complexity", json={"domains": domains})


def get_comprehensive_analytics(
    domains: List[str],
    user_profile: Optional[Dict[str, Any]] = None,
    include_market: bool = True,
    include_career: bool = True,
    include_domain: bool = True,
    include_barriers: bool = True,
) -> Optional[Dict]:
    """
    POST /api/fresher/analytics/comprehensive
    Single call that runs all four analytics categories.
    Returns: { comprehensive_analysis: { market_analysis, career_analysis,
                                          domain_analysis, barriers_analysis } }
    """
    return _post(f"{_FR}/analytics/comprehensive", json={
        "domains":          domains,
        "user_profile":     user_profile or {},
        "include_market":   include_market,
        "include_career":   include_career,
        "include_domain":   include_domain,
        "include_barriers": include_barriers,
    })


def get_data_stats() -> Optional[Dict]:
    """
    GET /api/fresher/data/stats
    Returns job data statistics: total records, distributions, salary stats.
    Also shows which data source (csv / neon / postgres) is active.
    """
    return _get(f"{_FR}/data/stats")


# =============================================================================
# 5. Counselor — Utility
# =============================================================================

def cc_health() -> bool:
    """
    GET /api/counselor/health
    Returns True if the counselor blueprint is healthy.
    """
    data = _get(f"{_CC}/health")
    return data is not None and data.get("status") == "healthy"


def cc_filter_options() -> Optional[Dict]:
    """
    GET /api/counselor/filters/options
    Returns unique domains, locations, companies for sidebar dropdowns.
    Response: { domains: [str], locations: [str], companies: [str] }
    """
    return _get(f"{_CC}/filters/options")


# =============================================================================
# 6. Counselor — Feature 1: Market Pulse
# =============================================================================

def cc_market_snapshot(
    days: int = 30,
    location: Optional[str] = None,
    fresher_only: bool = False,
) -> Optional[Dict]:
    """
    GET /api/counselor/market-pulse/snapshot
    Returns: total_jobs, active_domains, top_skill, salary_snapshot, metadata
    """
    return _get(f"{_CC}/market-pulse/snapshot",
                params=_common_params(days, location, fresher_only))


def cc_top_domains(
    days: int = 30,
    limit: int = 10,
    location: Optional[str] = None,
    fresher_only: bool = False,
) -> Optional[Dict]:
    """
    GET /api/counselor/market-pulse/top-domains
    Returns: { domains: [{domain, job_count, percentage, unique_companies,
                          fresher_eligible_pct, avg_salary}], total_jobs, metadata }
    """
    params = _common_params(days, location, fresher_only)
    params["limit"] = limit
    return _get(f"{_CC}/market-pulse/top-domains", params=params)


def cc_skill_frequency(
    days: int = 30,
    top_n: int = 20,
    location: Optional[str] = None,
    fresher_only: bool = False,
    domain: Optional[str] = None,
) -> Optional[Dict]:
    """
    GET /api/counselor/market-pulse/skills
    Returns: { skills: [{skill, job_count, frequency_pct, rank}], total_jobs, metadata }
    """
    params = _common_params(days, location, fresher_only)
    params["top_n"] = top_n
    if domain:
        params["domain"] = domain
    return _get(f"{_CC}/market-pulse/skills", params=params)


def cc_momentum_badges(
    days: int = 30,
    skills: Optional[List[str]] = None,
    location: Optional[str] = None,
    top_n_auto: int = 20,
) -> Optional[Dict]:
    """
    POST /api/counselor/market-pulse/momentum
    Returns: { badges: [{skill, current_count, previous_count, change_pct,
                         trend, arrow, comparison_window_days}], window_days, metadata }
    """
    body: Dict[str, Any] = {"days": days, "top_n_auto": top_n_auto}
    if skills:
        body["skills"] = skills
    if location:
        body["location"] = location
    return _post(f"{_CC}/market-pulse/momentum", json=body)


def cc_saturation(
    days: int = 30,
    location: Optional[str] = None,
    min_jobs: int = 10,
) -> Optional[Dict]:
    """
    GET /api/counselor/market-pulse/saturation
    Returns: { indicators: [{domain, job_count, unique_companies,
                              posting_density, saturation_score, interpretation}],
               total_jobs, metadata }
    """
    params: Dict[str, Any] = {"days": days, "min_jobs": min_jobs}
    if location:
        params["location"] = location
    return _get(f"{_CC}/market-pulse/saturation", params=params)


# =============================================================================
# 7. Counselor — Feature 2: Domain Comparison
# =============================================================================

def cc_compare_domains(
    domains: List[str],
    fresher_only: bool = True,
    days: int = 60,
    location: Optional[str] = None,
) -> Optional[Dict]:
    """
    POST /api/counselor/domain/compare
    Returns: {
        domains: [{domain, job_count, unique_companies, fresher_eligible_pct,
                   posting_density, top_skills, salary}],
        skill_overlap_matrix: { domain: { domain: jaccard_float } },
        metadata
    }
    """
    body: Dict[str, Any] = {"domains": domains, "fresher_only": fresher_only, "days": days}
    if location:
        body["location"] = location
    return _post(f"{_CC}/domain/compare", json=body)


def cc_fresher_analysis(
    domain: str,
    days: int = 60,
    location: Optional[str] = None,
) -> Optional[Dict]:
    """
    GET /api/counselor/domain/fresher-analysis
    Returns: {
        domain, total_domain_jobs, fresher_jobs, fresher_pct,
        top_fresher_skills, top_fresher_companies, common_roles, salary, metadata
    }
    """
    params: Dict[str, Any] = {"domain": domain, "days": days}
    if location:
        params["location"] = location
    return _get(f"{_CC}/domain/fresher-analysis", params=params)


def cc_domain_skill_matrix(
    domains: List[str],
    top_skills_per_domain: int = 15,
    days: int = 60,
    fresher_only: bool = True,
) -> Optional[Dict]:
    """
    POST /api/counselor/domain/skill-matrix
    Returns: { skills: [str], domains: [str], matrix: {skill: {domain: pct}} }
    """
    return _post(f"{_CC}/domain/skill-matrix", json={
        "domains":               domains,
        "top_skills_per_domain": top_skills_per_domain,
        "days":                  days,
        "fresher_only":          fresher_only,
    })


# =============================================================================
# 8. Counselor — Feature 3: Skill Gap Analyzer
# =============================================================================

def cc_skill_gap_analyze(
    student_skills: List[str],
    target_domain: str,
    top_roles: int = 20,
    days: int = 60,
    location: Optional[str] = None,
    fresher_only: bool = True,
) -> Optional[Dict]:
    """
    POST /api/counselor/skill-gap/analyze
    Returns: {
        target_domain, student_skills, match_percentage,
        jobs_accessible_now, total_domain_jobs,
        matched_skills, missing_skills, recommended_skills,
        impact_summary, top_benchmark_roles, metadata
    }
    missing_skills items: { skill, frequency_in_domain, frequency_pct,
                            extra_jobs_if_added, priority_rank }
    """
    body: Dict[str, Any] = {
        "student_skills": student_skills,
        "target_domain":  target_domain,
        "top_roles":      top_roles,
        "days":           days,
        "fresher_only":   fresher_only,
    }
    if location:
        body["location"] = location
    return _post(f"{_CC}/skill-gap/analyze", json=body)


def cc_popular_skills(
    domain: str,
    top_n: int = 30,
    days: int = 60,
    fresher_only: bool = True,
) -> Optional[List[Dict]]:
    """
    GET /api/counselor/skill-gap/popular-skills
    Returns list of { skill, frequency_pct } for multiselect pre-population.
    """
    data = _get(f"{_CC}/skill-gap/popular-skills", params={
        "domain":       domain,
        "top_n":        top_n,
        "days":         days,
        "fresher_only": str(fresher_only).lower(),
    })
    if data and "skills" in data:
        return data["skills"]
    return None


# =============================================================================
# 9. Counselor — Feature 4: Salary Intelligence
# =============================================================================

def cc_salary_ranges(
    domain: Optional[str] = None,
    location: Optional[str] = None,
    fresher_only: bool = True,
    days: Optional[int] = None,
) -> Optional[Dict]:
    """
    GET /api/counselor/salary/ranges
    Returns: { domain, location, fresher_only, salary: {available, p10..p90, note} }
    days=None means all-time (recommended — sparse salary data needs max sample).
    """
    params: Dict[str, Any] = {"fresher_only": str(fresher_only).lower()}
    if domain:   params["domain"]   = domain
    if location: params["location"] = location
    if days is not None: params["days"] = days
    return _get(f"{_CC}/salary/ranges", params=params)


def cc_jaipur_vs_national(
    domain: Optional[str] = None,
    fresher_only: bool = True,
) -> Optional[Dict]:
    """
    GET /api/counselor/salary/jaipur-vs-national
    Returns: {
        domain, jaipur: {salary_stats}, national: {salary_stats},
        comparison: {median_diff_pct, jaipur_lower_by_pct, note}
    }
    """
    params: Dict[str, Any] = {"fresher_only": str(fresher_only).lower()}
    if domain:
        params["domain"] = domain
    return _get(f"{_CC}/salary/jaipur-vs-national", params=params)


def cc_salary_top_skills(
    domain: Optional[str] = None,
    location: Optional[str] = None,
    top_n: int = 15,
) -> Optional[List[Dict]]:
    """
    GET /api/counselor/salary/top-skills
    Returns list of { skill, top10_pct_frequency, overall_frequency, premium_signal }
    sorted by premium_signal desc.
    """
    params: Dict[str, Any] = {"top_n": top_n}
    if domain:   params["domain"]   = domain
    if location: params["location"] = location
    data = _get(f"{_CC}/salary/top-skills", params=params)
    if data and "skills" in data:
        return data["skills"]
    return None


def cc_salary_by_experience(
    domain: Optional[str] = None,
    location: Optional[str] = None,
) -> Optional[List[Dict]]:
    """
    GET /api/counselor/salary/by-experience
    Returns list of { band_label, min_exp, max_exp, job_count, salary: {stats} }
    """
    params: Dict[str, Any] = {}
    if domain:   params["domain"]   = domain
    if location: params["location"] = location
    data = _get(f"{_CC}/salary/by-experience", params=params)
    if data and "bands" in data:
        return data["bands"]
    return None


# =============================================================================
# 10. Counselor — Feature 5: Company Intelligence
# =============================================================================

def cc_top_companies(
    domain: Optional[str] = None,
    days: int = 30,
    location: Optional[str] = None,
    fresher_only: bool = False,
    limit: int = 15,
) -> Optional[Dict]:
    """
    GET /api/counselor/companies/top
    Returns: { companies: [{company, job_count, fresher_jobs, fresher_pct,
                             unique_roles, estimated_type, salary, top_skills,
                             locations}], total_jobs, metadata }
    """
    params = _common_params(days, location, fresher_only)
    params["limit"] = limit
    if domain:
        params["domain"] = domain
    return _get(f"{_CC}/companies/top", params=params)


def cc_company_type_split(
    domain: Optional[str] = None,
    days: int = 30,
    location: Optional[str] = None,
    fresher_only: bool = False,
) -> Optional[Dict]:
    """
    GET /api/counselor/companies/type-split
    Returns: {
        type_split: {
            Service:  { job_count, pct, unique_companies, sample_companies },
            Product:  { ... },
            Startup:  { ... }
        },
        note: str
    }
    """
    params = _common_params(days, location, fresher_only)
    if domain:
        params["domain"] = domain
    return _get(f"{_CC}/companies/type-split", params=params)


def cc_hiring_frequency(
    company: str,
    days: int = 90,
) -> Optional[Dict]:
    """
    GET /api/counselor/companies/hiring-frequency
    Returns: { company, total_jobs, weekly_buckets: [{week_start, job_count}],
               avg_jobs_per_week, peak_week }
    """
    return _get(f"{_CC}/companies/hiring-frequency",
                params={"company": company, "days": days})


def cc_jaipur_companies(
    domain: Optional[str] = None,
    days: int = 60,
    fresher_only: bool = False,
    limit: int = 20,
) -> Optional[Dict]:
    """
    GET /api/counselor/companies/jaipur
    Returns: { companies: [...], total_jaipur_jobs, total_national_jobs,
               jaipur_share_pct, metadata }
    """
    params: Dict[str, Any] = {
        "days":         days,
        "limit":        limit,
        "fresher_only": str(fresher_only).lower(),
    }
    if domain:
        params["domain"] = domain
    return _get(f"{_CC}/companies/jaipur", params=params)