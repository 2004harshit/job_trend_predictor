import json
import streamlit as st
import plotly.graph_objects as go
from typing import Any, Dict, List, Optional

# Backend: all analytics & recommendations via Flask API (dashboards.utils.api_client)
from dashboards.utils import api_client
from dashboards.utils.llm_verdict_ayer import generate_verdict

from src.recommender.knowledge_base_store.knowledge_base import ALL_DOMAINS


# ---------------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------------
LOCATION_OPTIONS = ["Jaipur", "Bangalore", "Hyderabad", "Pune", "Delhi NCR"]


def _get_domain_options() -> List[str]:
    """Cached domain list (loaded in render_path_2_flow with spinner)."""
    opts = st.session_state.get("dcr_domain_options")
    if opts:
        return opts
    return list(ALL_DOMAINS)


def _inject_styles() -> None:
    """Injects custom CSS for DCR with a premium, fresher-friendly aesthetic."""
    st.markdown("""
<style>
    /* DCR Global Variables & Animations */
    :root {
        --dcr-blue-primary: #1e40af;
        --dcr-blue-gradient: linear-gradient(135deg, #1e40af 0%, #3b82f6 100%);
        --dcr-indigo-gradient: linear-gradient(135deg, #4f46e5 0%, #6366f1 100%);
        --dcr-card-shadow: 0 10px 30px -5px rgba(0, 0, 0, 0.08);
        --dcr-text-main: #0f172a;
        --dcr-text-muted: #64748b;
        --dcr-border: rgba(0,0,0,0.06);
    }

    .dcr-root .dcr-animate {
        animation: fadeIn 0.6s cubic-bezier(0.4, 0, 0.2, 1) forwards;
    }
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(12px); }
        to { opacity: 1; transform: translateY(0); }
    }

    /* Headings & Typography */
    .dcr-root h1, .dcr-root h2, .dcr-root h3 { 
        font-weight: 850 !important; 
        color: var(--dcr-text-main) !important;
        letter-spacing: -0.025em !important;
    }
    .dcr-root .dcr-section-title { 
        font-size: 26px !important; 
        font-weight: 900 !important; 
        margin-top: 40px !important;
    }

    /* Hero & Verdict Cards */
    .dcr-root .hero-verdict {
        background: var(--dcr-blue-gradient);
        padding: 44px 36px;
        border-radius: 28px;
        color: white !important;
        margin: 32px 0 40px 0;
        box-shadow: 0 20px 35px -10px rgba(30, 64, 175, 0.4);
        position: relative;
        overflow: hidden;
    }
    .dcr-root .hero-verdict::after {
        content: '';
        position: absolute;
        bottom: -20%;
        right: -5%;
        width: 250px;
        height: 250px;
        background: rgba(255,255,255,0.08);
        border-radius: 50%;
    }
    .dcr-root .hero-verdict h2 { color: white !important; font-size: 29px !important; }
    .dcr-root .hero-verdict p { font-size: 16.5px; opacity: 0.94; line-height: 1.65; }

    /* Modern Table */
    .dcr-root .comp-table { width: 100%; border-collapse: collapse; margin: 0; background: transparent; }
    .dcr-root .comp-table th { 
        background: rgba(30, 64, 175, 0.03); padding: 18px 24px; 
        text-align: left; font-size: 11px; text-transform: uppercase; 
        letter-spacing: 0.12em; color: var(--dcr-blue-primary);
        border-bottom: 2px solid rgba(0,0,0,0.03);
    }
    .dcr-root .comp-table td { padding: 18px 24px; border-bottom: 1px solid var(--dcr-border); font-size: 14.5px; vertical-align: middle; }
    .dcr-root .comp-table tr:hover { background: rgba(30, 64, 175, 0.015); }
    .dcr-root .comp-table .domain-hl { font-weight: 700; color: var(--color-text-primary); font-size: 15px; }

    /* Segmented Tabs (Pills Style) */
    .dcr-root .stTabs [data-baseweb="tab-list"] { 
        gap: 8px; padding: 6px; background: #f1f5f9; 
        border-radius: 14px; margin-bottom: 36px; 
    }
    .dcr-root .stTabs [data-baseweb="tab-highlight"] { display: none !important; }
    .dcr-root .stTabs [data-baseweb="tab"] {
        height: 44px; min-width: 120px; border-radius: 10px; border: none;
        background: transparent; color: #64748b;
        font-weight: 600; font-size: 14px; transition: all 0.2s;
    }
    .dcr-root .stTabs [data-baseweb="tab"]:hover { background-color: rgba(255,255,255,0.5); color: var(--dcr-blue-primary); }
    .dcr-root .stTabs [aria-selected="true"] {
        background: white !important;
        color: var(--dcr-blue-primary) !important;
        box-shadow: 0 4px 10px rgba(0,0,0,0.05);
        font-weight: 800;
    }

    /* Action Timeline */
    .dcr-root .action-step {
        display: flex; gap: 20px; align-items: flex-start;
        background: white; padding: 28px; border-radius: 24px; margin-bottom: 18px;
        border: 1px solid var(--dcr-border);
        box-shadow: var(--dcr-card-shadow);
        position: relative;
        transition: all 0.3s ease;
    }
    .dcr-root .action-step:hover { transform: translateY(-3px); box-shadow: 0 15px 35px -5px rgba(0,0,0,0.1); }
    .dcr-root .step-num {
        background: #f1f5f9; color: var(--dcr-blue-primary);
        width: 40px; height: 40px; border-radius: 12px;
        display: flex; align-items: center; justify-content: center;
        flex-shrink: 0; font-weight: 900; font-size: 18px;
    }
    .dcr-root .action-mission {
        display: flex; align-items: center; gap: 12px;
        font-size: 14px; padding: 12px 16px; background: #f8fafc;
        border-radius: 12px; margin-top: 10px; border: 1px solid #f1f5f9;
        font-weight: 500;
    }
    .dcr-root .action-mission-icon { color: #3b82f6; font-weight: 900; }

    /* Premium Cards */
    .dcr-root .mcard {
        background: white; border: 1px solid var(--dcr-border);
        border-radius: 24px; padding: 28px;
        box-shadow: var(--dcr-card-shadow);
        height: 100%;
    }
    .dcr-root .mcard-title {
        font-size: 11px; font-weight: 750; text-transform: uppercase;
        letter-spacing: 0.1em; color: var(--dcr-text-muted); margin-bottom: 18px;
    }
    .dcr-root .mcard-value { font-size: 38px; font-weight: 950; color: var(--dcr-text-main); margin: 8px 0; }
    .dcr-root .mcard-value.sm { font-size: 26px; }

    /* Pills and Badges */
    .dcr-root .pill {
        padding: 6px 14px; border-radius: 9999px; font-size: 11px; font-weight: 750;
        display: inline-flex; align-items: center; gap: 6px; text-transform: uppercase;
    }
    .dcr-root .pill-green { background: rgba(16, 185, 129, 0.1); color: #059669; }
    .dcr-root .pill-amber { background: rgba(245, 158, 11, 0.1); color: #b45309; }
    .dcr-root .pill-red { background: rgba(239, 68, 68, 0.1); color: #b91c1c; }

    /* Modern Tabs (Pills) */
    .dcr-root .stTabs [data-baseweb="tab-list"] { 
        gap: 8px; padding: 6px; background: #f1f5f9; 
        border-radius: 14px; margin-bottom: 36px; border: none;
    }
    .dcr-root .stTabs [data-baseweb="tab-highlight"] { display: none !important; }
    .dcr-root .stTabs [data-baseweb="tab"] {
        height: 44px; min-width: 120px; border-radius: 10px; border: none;
        background: transparent; color: #64748b;
        font-weight: 600; font-size: 14px; transition: all 0.2s;
    }
    .dcr-root .stTabs [aria-selected="true"] {
        background: white !important;
        color: var(--dcr-blue-primary) !important;
        box-shadow: 0 4px 10px rgba(0,0,0,0.05);
        font-weight: 800;
    }

    /* Skills & Sliders */
    .dcr-root span[data-baseweb="tag"] { background: var(--dcr-blue-primary) !important; border-radius: 8px !important; }
    .dcr-root div[data-testid="stSlider"] label { font-weight: 700; color: var(--dcr-text-main); }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# BUG-3 FIX — Saturation Risk_Level normalisation map
# Engine returns:  "High Saturation" | "Medium Saturation" | "Low Saturation"
# Palette expects: "Highly Competitive" | "Growing Saturated" | "Safe"
# ---------------------------------------------------------------------------
_RISK_LEVEL_NORMALISE = {
    "High Saturation":         "Highly Competitive",
    "Medium Saturation":       "Growing Saturated",
    "Low Saturation":          "Safe",
    # pass-through for engines that already use the display labels
    "Highly Competitive":      "Highly Competitive",
    "Growing Saturated":       "Growing Saturated",
    "Safe":                    "Safe",
}


def get_trend_indicator(growth_score: float) -> str:
    if growth_score > 6.5:   return "↗"
    elif growth_score < 3.5: return "↘"
    return "→"

def get_competition_badge(level: str) -> tuple:
    badges = {
        "Low":    ("🟢", "var(--accent-green)", "green", "Low Pressure"),
        "Medium": ("🟡", "var(--accent-amber)", "amber", "Moderate Competition"),
        "High":   ("🔴", "var(--accent-red)",   "red",   "Highly Competitive"),
    }
    return badges.get(level, ("⚪", "var(--text-muted)", "indigo", "Neutral"))

def get_saturation_palette(risk_level: str) -> tuple:
    """
    Returns (emoji, color, border, background) for a given normalised risk level.
    Expects one of: "Safe" | "Growing Saturated" | "Highly Competitive"
    Use _RISK_LEVEL_NORMALISE to convert engine output before calling this.
    """
    p = {
        "Safe": (
            "🟢", "var(--accent-green)",
            "2px solid rgba(5,150,105,0.35)",
            "linear-gradient(135deg,rgba(5,150,105,0.07) 0%,rgba(13,148,136,0.04) 100%)",
        ),
        "Growing Saturated": (
            "🟡", "var(--accent-amber)",
            "2px solid rgba(217,119,6,0.35)",
            "linear-gradient(135deg,rgba(217,119,6,0.07) 0%,rgba(251,191,36,0.04) 100%)",
        ),
        "Highly Competitive": (
            "🔴", "var(--accent-red)",
            "2px solid rgba(220,38,38,0.35)",
            "linear-gradient(135deg,rgba(220,38,38,0.07) 0%,rgba(248,113,113,0.04) 100%)",
        ),
    }
    return p.get(risk_level, (
        "⚪", "var(--text-muted)",
        "2px solid rgba(100,116,139,0.22)",
        "rgba(248,250,252,0.5)",
    ))

def fetch_domain_analytics(
    domain: str,
    location: str = "Jaipur",
    user_profile: Optional[Dict[str, Any]] = None,
    recommended_domains: Optional[List[str]] = None,
) -> Optional[dict]:
    """
    Public wrapper — converts unhashable dicts/lists to hashable types so
    @st.cache_data can cache the underlying call. Cached for 1 hour.
    """
    _profile_key = json.dumps(user_profile, sort_keys=True) if user_profile else None
    _domains_key = tuple(recommended_domains) if recommended_domains else None
    return _fetch_domain_analytics_cached(domain, location, _profile_key, _domains_key)


@st.cache_data(ttl=3600, show_spinner=False)
def _fetch_domain_analytics_cached(
    domain: str,
    location: str,
    user_profile_json: Optional[str],
    recommended_domains_tuple: Optional[tuple],
) -> Optional[dict]:
    """
    Cached implementation. All args are hashable strings/tuples.
    Calls Flask API for domain analytics — maps response to card-ready shape.
    Stores raw Phase-2/3 payloads in session_state for growth / real-talk cards.
    """
    user_profile        = json.loads(user_profile_json) if user_profile_json else None
    recommended_domains = list(recommended_domains_tuple) if recommended_domains_tuple else None

    response = api_client.get_domain_analytics(
        domain=domain,
        location=location,
        experience_band=(0, 3),
        user_profile=user_profile,
        recommended_domains=recommended_domains,
    )
    if response is None:
        st.error("Server error — could not fetch analytics. Ensure Flask API is running.")
        return None

    results = response.get("domain_analytics") or {}
    profile_results = response.get("profile_analytics")
    global_results = response.get("global_analytics") or {}

    st.session_state["domain_analytics"] = results
    st.session_state["api_domain_bundle"] = response
    if profile_results:
        st.session_state["profile_analytics"] = profile_results

    # ── Global market demand (from API) ──────────────────────────────────────
    global_md = global_results.get("market_demand", {})
    domain_stats = global_md.get(domain, {})

    # ── Raw engine outputs ───────────────────────────────────────────────────
    avg_salary  = results.get("avg_salary")  or {}
    velocity    = results.get("velocity")    or {}
    sat_data    = results.get("saturation")  or {}
    sal_growth  = results.get("salary_growth") or {}

    # ── BUG-2 FIX: Salary ───────────────────────────────────────────────────
    # AverageSalaryRangeCalculator returns None for this dataset.
    # Fallback: read from salary_growth.Experience_Ladder which is always populated.
    salary_range = avg_salary.get("Market_Range", {})
    loc_adjusted = avg_salary.get("Location_Adjusted_Median", 0)

    if not salary_range or (
        salary_range.get("Low_25th", 0) == 0
        and salary_range.get("Median_50th", 0) == 0
    ):
        ladder   = sal_growth.get("Experience_Ladder", {})
        fresher  = ladder.get("fresher", {})
        junior   = ladder.get("junior",  {})
        mid      = ladder.get("mid",     {})

        low_val    = fresher.get("p25",    0) or 0
        median_val = fresher.get("median", 0) or junior.get("median", 0) or 0
        high_val   = mid.get("p75",        0) or junior.get("p75", 0) or 0

        salary_range = {
            "Low_25th":    low_val,
            "Median_50th": median_val,
            "High_75th":   high_val,
        }
        # Location-adjusted: use Baseline factor if available
        loc_factor   = sal_growth.get("Baseline", {}).get("Location_Factor", 1.0) or 1.0
        loc_adjusted = round(median_val * loc_factor, 2) if median_val else 0

    # ── BUG-1 FIX: Velocity key path ────────────────────────────────────────
    # Old (broken): velocity.get("Counts", {}).get("Local_Openings_30d", 0)
    # New (correct): velocity["Location_Intelligence"]["local_openings_30d"]
    loc_intel  = velocity.get("Location_Intelligence", {})
    local_vel  = velocity.get("Local_Velocity",        {})
    nat_vel    = velocity.get("National_Velocity",     {})

    local_30d        = int(loc_intel.get("local_openings_30d",    0) or 0)
    national_30d     = int(loc_intel.get("national_openings_30d", 0) or 0)
    local_growth_pct = float(local_vel.get("Recent_Growth_Pct",   0) or 0)
    nat_growth_pct   = float(nat_vel.get("Recent_Growth_Pct",     0) or 0)

    # ── BUG-3 FIX: Saturation Risk_Level normalisation ──────────────────────
    # Engine returns "High Saturation" / "Medium Saturation" / "Low Saturation"
    # Palette expects "Highly Competitive" / "Growing Saturated" / "Safe"
    raw_risk_level      = sat_data.get("Risk_Level", "Safe")
    normalised_risk     = _RISK_LEVEL_NORMALISE.get(raw_risk_level, "Safe")
    sat_score           = sat_data.get("Saturation_Score", 0) or 0
    sat_signals         = sat_data.get("Signals", {})

    # ── BUG-4 FIX: Competition derived from saturation when missing ──────────
    # CompetitionLevelCalculator only runs in Phase 3 and errors on the
    # experience-band filter, so Phase-2 results never contain competition data.
    # Derive a sensible competition level from saturation score which is always
    # available after Phase 2.
    comp_data = results.get("competition") or {}
    comp_error = isinstance(comp_data, dict) and "error" in comp_data

    if comp_error or not comp_data.get("Level"):
        # Derive from saturation score  (0–1 scale)
        if sat_score >= 0.60:
            derived_level = "High"
        elif sat_score >= 0.35:
            derived_level = "Medium"
        else:
            derived_level = "Low"

        supply_demand   = sat_data.get("Factor_Breakdown", {}).get("Supply_Demand", {})
        derived_ratio   = int(supply_demand.get("ratio", 0) or 0)
        # Cap unrealistically large ratio for display
        display_ratio   = min(derived_ratio, 9999)
        derived_index   = round(sat_score, 3)

        comp_data = {
            "Level":              derived_level,
            "Competition_Index":  derived_index,
            "Candidates_Per_Job": display_ratio,
        }

    # ── Phase 5: stamp fetch time for freshness indicator ───────────────────
    from datetime import datetime as _dt_now
    _fetched_at = _dt_now.now().strftime("%d %b %Y, %I:%M %p")

    # ── Assemble final payload ───────────────────────────────────────────────
    return {
        "domain":       domain,
        "location":     location,
        "fetched_at":   _fetched_at,          # Phase 5: freshness indicator
        "demand_score": domain_stats.get("Overall_Demand_Score", 0),
        "trend_score":  domain_stats.get("Breakdown", {}).get("Growth_Trend", 5.0),
        "breakdown":    domain_stats.get("Breakdown", {}),

        "competition": {
            "level":              comp_data.get("Level", "Medium"),
            "index":              comp_data.get("Competition_Index", 0),
            "candidates_per_job": int(comp_data.get("Candidates_Per_Job", 0) or 0),
        },

        "salary": {
            "low":               salary_range.get("Low_25th",    0),
            "median":            salary_range.get("Median_50th", 0),
            "high":              salary_range.get("High_75th",   0),
            "location_adjusted": loc_adjusted,
        },

        "job_openings": {
            "local_30d":           local_30d,
            "national_30d":        national_30d,
            "local_growth_pct":    local_growth_pct,
            "national_growth_pct": nat_growth_pct,
            # Fallback totals from saturation / market_demand (used when 30d counts = 0)
            "total_dataset":       int(sat_data.get("Sample_Size", 0) or 0),
            "total_domain_jobs":   int(domain_stats.get("Raw_Counts", {}).get("Total_Domain_Jobs", 0) or 0),
            "fresher_dataset":     int(domain_stats.get("Raw_Counts", {}).get("Fresher_Jobs", 0) or 0),
            "data_stale":          (local_30d == 0 and national_30d == 0),
            # Earliest velocity window start — tells user how old the data is
            "scraped_before":      (velocity.get("Time_Series") or [{}])[0].get("start", ""),
        },

        "saturation": {
            "score":      sat_score,
            "risk_level": normalised_risk,          # BUG-3 fixed — normalised label
            "color_code": sat_data.get("Color_Code", "Green"),
            "signals":    sat_signals,
        },
    }

def render_30_day_action_plan(domain_data: dict, user_profile: dict, verdict: dict):
    """Generates a practical 30-day starter plan for a fresher."""
    domain = domain_data['domain']
    skills = user_profile.get('skills', [])
    
    # Simple logic to adapt steps based on skills the user already has
    has_python = any(s.lower() == 'python' for s in skills)
    has_sql = any(s.lower() == 'sql' for s in skills)
    
    st.markdown(f"""
<div class="dcr-root market-header dcr-animate" style="margin-top:40px;">
<h3>🚀 Your 30-Day Starter Action Plan</h3>
<p style="color:var(--text-muted);">Small steps for massive momentum. Start today.</p>
</div>
""", unsafe_allow_html=True)

    weeks = [
        {
            "title": "Week 1: Fundamentals & Environment",
            "desc": f"Master the basic tools used in {domain}. " + 
                    (f"Since you already know Python, focus on {domain}-specific libraries." if has_python else "Start with basic Python syntax and environment setup."),
            "tasks": ["Set up VS Code & Python environment", f"Read 3 top articles on '{domain} for freshers'", "Fix your GitHub profile bio"]
        },
        {
            "title": "Week 2: Data & Core Logic",
            "desc": "Understand how data flows in this domain. " +
                    (f"Level up your SQL for {domain} pipelines." if has_sql else "Learn basic SQL and data manipulation."),
            "tasks": ["Build a small script to fetch data", "Document your first 'Fail' and how you fixed it", "Connect with 5 professionals in this field on LinkedIn"]
        },
        {
            "title": "Week 3: The 'Showcase' Project",
            "desc": "Build something real. Avoid generic tutorial projects.",
            "tasks": ["Choose a non-trivial project idea", "Create a README with an architecture diagram", "Push initial code to GitHub"]
        },
        {
            "title": "Week 4: Networking & Narrative",
            "desc": "Tell the world what you're building.",
            "tasks": ["Record a 2-minute Loom video of your project", "Write a LinkedIn post about your learnings", "Apply to 2 relevant internships for practice"]
        }
    ]

    for i, week in enumerate(weeks):
        tasks_html = ""
        for t in week['tasks']:
            tasks_html += f'<div class="action-mission"><span class="action-mission-icon">✓</span> <span>{t}</span></div>'
        
        st.markdown(f"""
<div class="dcr-root action-step dcr-animate" style="animation-delay:{i*0.1}s;">
<div class="step-num">{i+1}</div>
<div class="step-content">
<h4 style="margin:0 0 8px 0; font-size:18px; font-weight:800; color:var(--dcr-blue-primary);">{week['title']}</h4>
<p style="margin:0 0 16px 0; font-size:14.5px; opacity:0.8;">{week['desc']}</p>
<div style="background:rgba(30,64,175,0.02); padding:4px 0; border-radius:12px;">
{tasks_html}
</div>
</div>
</div>
""", unsafe_allow_html=True)

    st.info("💡 **Quick Tip:** Consistency beats intensity. 2 hours every day is better than 10 hours on Sunday.")

def render_verdict_card(verdict: dict, domain: str):
    """Clean, premium verdict card with ZERO HTML leakage risk"""
    if not verdict:
        st.info("Verdict not available yet.")
        return

    # Extract clean text safely
    title = verdict.get('verdict', f"{domain} is a strong recommendation for you.")
    why_not = verdict.get('why_not_others', '')
    reality = verdict.get('entry_reality', f"Getting hired as a {domain} will require consistent effort and a solid portfolio.")

    red_flag_html = ""
    if verdict.get("red_flag"):
        red_flag_html = f'<div style="margin-top:20px; padding:16px; background:rgba(220,38,38,0.12); border-left:5px solid #dc2626; border-radius:12px; font-size:14.5px;">⚠️ <strong>Important:</strong> {verdict["red_flag"]}</div>'

    why_not_html = f'<p>{why_not}</p>' if why_not else ''

    verdict_html = f"""<div class="dcr-root hero-verdict">
<div style="font-size:13px; font-weight:700; letter-spacing:2px; opacity:0.85; margin-bottom:12px;">THE COACH'S VERDICT</div>
<h2 style="margin:0 0 20px 0;">{title}</h2>
{why_not_html}
<div style="background:rgba(255,255,255,0.18); padding:24px; border-radius:16px; backdrop-filter:blur(12px);">
<strong>Reality Check</strong><br>
<span style="opacity:0.93; line-height:1.6;">{reality}</span>
</div>
{red_flag_html}
</div>"""
    st.markdown(verdict_html, unsafe_allow_html=True)
# ---------------------------------------------------------------------------
# MARKET REALITY CARD
# ---------------------------------------------------------------------------

def render_quick_wins_sidebar(domain: str):
    """Renders high-impact, low-effort tasks tailored to the domain."""
    
    # Domain-specific tasks to avoid placeholders
    domain_tasks = {
        "Data Analyst": [
            ("Setup Stack", "Install PowerBI/Tableau & Excel Analysis Toolpak"),
            ("Check Market", "Find 5 'Entry Level' listings on LinkedIn for Jaipur"),
            ("Build Proof", "Join Kaggle & download a Retail Sales dataset"),
            ("Quick Win", "Create a 1-page dashboard in Excel today")
        ],
        "Data Scientist": [
            ("Setup Stack", "Install Anaconda & VS Code Jupyter Extension"),
            ("Check Market", "Search for 'Junior Data Scientist' roles in Bangalore"),
            ("Build Proof", "Write a clean Titanic survival model script"),
            ("Quick Win", "Document one ML concept on LinkedIn")
        ],
        "Machine Learning Engineer": [
            ("Setup Stack", "Install Docker & PyTorch"),
            ("Check Market", "Search for 'MLOps' roles to see tech requirements"),
            ("Build Proof", "Deploy a simple Flask API for a model"),
            ("Quick Win", "Setup a GitHub Repo with a professional README")
        ]
    }
    
    default_tasks = [
        ("Setup Stack", f"Install VS Code & {domain} starter kit"),
        ("Read Roadmap", f"Download the 2024 {domain} Developer Roadmap"),
        ("Check Market", "Join 2 relevant Discord/Slack communities"),
        ("Quick Win", "Update your LinkedIn headline for this role")
    ]
    
    tasks = domain_tasks.get(domain, default_tasks)
    
    tasks_html = ""
    for title, desc in tasks:
        tasks_html += f"""<div style="display:flex; gap:12px; margin-bottom:16px;">
<div style="background:rgba(30,64,175,0.1); color:#1e40af; width:28px; height:28px; border-radius:6px; display:flex; align-items:center; justify-content:center; flex-shrink:0; font-size:12px; font-weight:800;">✓</div>
<div>
<div style="font-weight:700; font-size:13px; color:var(--dcr-text-main);">{title}</div>
<div style="font-size:11px; color:var(--dcr-text-muted);">{desc}</div>
</div>
</div>"""

    st.markdown(f"""<div class="dcr-root mcard dcr-animate" style="background:rgba(30,64,175,0.02); border:1px dashed rgba(30,64,175,0.3); height:auto; padding:24px;">
<div style="font-size:12px; font-weight:800; text-transform:uppercase; color:#1e40af; margin-bottom:20px; letter-spacing:0.1em;">⚡ ZERO TO ONE (30H PLAN)</div>
{tasks_html}
<div style="margin-top:10px; padding-top:16px; border-top:1px solid rgba(0,0,0,0.05); font-size:11px; color:var(--dcr-text-muted); font-style:italic;">Finish these 4 tasks in your first 30 hours of prep.</div>
</div>""", unsafe_allow_html=True)

def render_market_reality_card(domain_data: Dict[str, Any], gauge_key_suffix: str = ""):
    """
    Renders the full market reality card for a domain with improved UX.
    """
    _inject_styles()
    location   = domain_data.get("location", "Jaipur")
    fetched_at = domain_data.get("fetched_at", "")

    # ── Phase 5: Freshness indicator + manual cache-clear ───────────────────
    freshness_html = ""
    if fetched_at:
        freshness_html = (
            f'<div style="font-size:11px; color:var(--text-muted); margin-top:4px; display:flex; align-items:center; gap:4px;">'
            f'<span>🕒 Data from {fetched_at}</span>'
            f'</div>'
        )

    # ── Header ──────────────────────────────────────────────────────────────
    st.markdown(f"""
<div class="dcr-root hero-verdict" style="padding:28px; margin-bottom:32px; box-shadow:0 15px 30px -10px rgba(30,64,175,0.3);">
<div style="display:flex; justify-content:space-between; align-items:flex-start; position:relative; z-index:1;">
<div>
<div style="font-size:11px; font-weight:750; text-transform:uppercase; letter-spacing:0.12em; opacity:0.85; margin-bottom:8px;">Market Dynamics</div>
<h2 style="color:white !important; margin:0; font-size:26px;">{domain_data['domain']} in {location}</h2>
{freshness_html}
</div>
<div style="text-align:right;">
<div style="font-size:11px; font-weight:750; opacity:0.85; margin-bottom:4px;">MARKET FIT</div>
<div style="font-size:24px; font-weight:950;">HIGH VOLUME</div>
</div>
</div>
</div>
""", unsafe_allow_html=True)

    # Manual refresh button
    if st.button("🔄 Refresh Market Data", key=f"refresh_cache_{domain_data['domain']}_{location}_{gauge_key_suffix}"):
        _fetch_domain_analytics_cached.clear()
        st.rerun()

    # ── Row 1: Demand & Competition ─────────────────────────────────────────
    col1, col2 = st.columns(2)
    with col1:
        demand_score = domain_data.get("demand_score", 0)
        trend_icon   = get_trend_indicator(domain_data.get("trend_score", 5.0))
        if demand_score >= 7:
            d_color, d_pill, d_label = "var(--accent-green)", "pill-green", "High Hiring Volume"
        elif demand_score >= 4:
            d_color, d_pill, d_label = "var(--accent-amber)", "pill-amber", "Stable Hiring"
        else:
            d_color, d_pill, d_label = "var(--accent-red)", "pill-red", "Selective Hiring"

        vol        = domain_data.get("breakdown", {}).get("Volume", 0)
        entry_flex = domain_data.get("breakdown", {}).get("Entry_Flexibility", 0)

        st.markdown(f"""<div class="dcr-root mcard dcr-animate">
<div class="mcard-title">Hiring Pulse {trend_icon}</div>
<div class="mcard-value" style="color:{d_color};">{demand_score:.1f} <span style="font-size:16px; font-weight:400; color:var(--text-muted);">/ 10</span></div>
<span class="pill {d_pill}" style="margin-bottom:16px;">{d_label}</span>
<div style="font-size:13px; color:var(--text-secondary); border-top:1px solid var(--color-border-secondary); padding-top:12px;">💡 Job volume is <b>{vol:.1f}/10</b>. Entry flexibility for freshers scored at <b>{entry_flex:.1f}/10</b>.</div>
</div>""", unsafe_allow_html=True)

    with col2:
        comp       = domain_data.get("competition", {})
        level      = comp.get("level", "Medium")
        emoji, color, pill_cls, sub_label = get_competition_badge(level)
        cands      = comp.get("candidates_per_job", 0)
        c_idx      = comp.get("index", 0)

        st.markdown(f"""<div class="dcr-root mcard dcr-animate">
<div class="mcard-title">Competition Intensity</div>
<div class="mcard-value sm" style="color:{color};">{emoji} {level}</div>
<span class="pill pill-{pill_cls}" style="margin-bottom:16px;">{sub_label}</span>
<div style="font-size:13px; color:var(--text-secondary); border-top:1px solid var(--color-border-secondary); padding-top:12px;">Roughly <b>{cands:,} applicants</b> per open role in this domain. Index: <b>{c_idx:.2f}</b>.</div>
</div>""", unsafe_allow_html=True)

    # ── Row 2: Salary ────────────────────────────────────────────────────────
    sal      = domain_data.get("salary", {})
    low      = sal.get("low",    0)
    median   = sal.get("median", 0)
    high     = sal.get("high",   0)
    loc_adj  = sal.get("location_adjusted", median)
    bar_pct  = min(100, round((loc_adj / high * 100) if high > 0 else 50))

    st.markdown(f"""<div class="dcr-root mcard dcr-animate">
<div class="mcard-title">💰 What can you realistically earn as a fresher?</div>
<div class="mcard-value sm" style="color:var(--accent-teal);">₹{low:.1f} – ₹{high:.1f} <span class="unit" style="font-family:'Outfit',sans-serif;">LPA</span></div>
<div class="salary-bar-track"><div class="salary-bar-fill" style="width:{bar_pct}%;"></div></div>
<div class="salary-labels"><span>₹{low:.1f}L (25th %ile)</span><span>₹{median:.1f}L (national median)</span><span>₹{high:.1f}L (75th %ile)</span></div>
<div class="loc-chip">📍 In {location}: ₹{loc_adj:.2f} LPA adjusted</div>
</div>""", unsafe_allow_html=True)

    # ── Row 3: Job Openings ──────────────────────────────────────────────────
    o                = domain_data.get("job_openings", {})
    local            = o.get("local_30d",           0)
    national         = o.get("national_30d",        0)
    local_growth     = o.get("local_growth_pct",    0)
    national_growth  = o.get("national_growth_pct", 0)
    data_stale       = o.get("data_stale",          False)
    total_dataset    = o.get("total_dataset",       0)
    total_domain_jobs= o.get("total_domain_jobs",   0)
    fresher_dataset  = o.get("fresher_dataset",     0)
    scraped_before   = o.get("scraped_before",      "")

    # Format scraped_before date for display  e.g. "2025-11-05" → "Nov 2025"
    try:
        from datetime import datetime as _dt
        _sb = _dt.strptime(scraped_before, "%Y-%m-%d")
        scraped_label = _sb.strftime("%b %Y")
    except Exception:
        scraped_label = scraped_before or "recently"

    col3, col4 = st.columns(2)

    if data_stale:
        # Dataset predates the velocity window — show real dataset totals
        # with a clear disclaimer so users understand the context.
        _domain_name = domain_data.get("domain", "this domain")

        # Use the larger total_domain_jobs count when available, else fall back to sample
        display_total   = total_domain_jobs if total_domain_jobs > 0 else total_dataset
        fresher_pct     = round(fresher_dataset / display_total * 100) if display_total > 0 else 0

        with col3:
            fresher_bar = (
                '<div style="margin-top:10px;">'
                '<div style="display:flex; justify-content:space-between; '
                'font-size:12px; color:var(--text-muted); margin-bottom:4px;">'
                f'<span>Entry-level eligible</span><span>{fresher_dataset:,} ({fresher_pct}%)</span>'
                '</div>'
                '<div style="background:var(--divider); border-radius:4px; height:6px;">'
                f'<div style="background:var(--accent-indigo); width:{fresher_pct}%; '
                'height:6px; border-radius:4px;"></div></div></div>'
            ) if fresher_dataset > 0 else ""

            st.markdown(
                '<div class="dcr-root mcard dcr-animate">'
                f'<div class="mcard-title">📊 Dataset Listings — {_domain_name}</div>'
                f'<div class="mcard-value" style="color:var(--accent-indigo);">{display_total:,}</div>'
                '<div class="mcard-label">total listings in dataset</div>'
                + fresher_bar +
                f'<div class="mcard-sub" style="margin-top:10px; font-size:11px; color:var(--text-muted);">'
                f'⚠️ Live 30-day data unavailable — dataset was scraped before {scraped_label}. '
                f'Counts reflect full historical dataset.</div>'
                '</div>',
                unsafe_allow_html=True,
            )

        with col4:
            # Show demand score as a proxy signal for national activity
            demand_score = domain_data.get("demand_score", 0)
            growth_trend = domain_data.get("trend_score",  5.0)
            trend_label  = (
                "📈 Growing"  if growth_trend >= 6.5 else
                "→ Stable"    if growth_trend >= 4.0 else
                "📉 Declining"
            )
            trend_color  = (
                "var(--accent-green)" if growth_trend >= 6.5 else
                "var(--accent-amber)" if growth_trend >= 4.0 else
                "var(--accent-red)"
            )
            st.markdown(
                '<div class="dcr-root mcard dcr-animate">'
                '<div class="mcard-title">🇮🇳 National Demand Signal</div>'
                f'<div class="mcard-value" style="color:#8b5cf6;">{demand_score:.1f}<span style="font-size:16px; font-weight:400;">/10</span></div>'
                '<div class="mcard-label">overall demand score</div>'
                f'<div style="font-size:18px; font-weight:700; color:{trend_color}; margin-top:12px;">'
                f'{trend_label}</div>'
                f'<div class="mcard-sub" style="margin-top:8px; font-size:11px; color:var(--text-muted);">'
                f'30-day velocity unavailable — scraped data pre-dates {scraped_label}. '
                f'Re-scrape to get live counts.</div>'
                '</div>',
                unsafe_allow_html=True,
            )

    else:
        with col3:
            lt  = "↗" if local_growth > 0 else "↘" if local_growth < 0 else "→"
            lgc = "var(--accent-green)" if local_growth > 0 else "var(--accent-red)" if local_growth < 0 else "var(--text-muted)"
            st.markdown(f"""
<div class="dcr-root mcard dcr-animate">
<div class="mcard-title">📍 {location} Job Openings</div>
<div class="mcard-value" style="color:var(--accent-indigo);">{local:,}</div>
<div class="mcard-label">listings — last 30 days</div>
<div class="mcard-sub" style="font-family:'IBM Plex Mono'; font-size:16px; font-weight:700; color:{lgc}; margin-top:12px;">
{lt} {abs(local_growth):.1f}% MoM
</div>
</div>
""", unsafe_allow_html=True)

        with col4:
            nt  = "↗" if national_growth > 0 else "↘" if national_growth < 0 else "→"
            ngc = "var(--accent-green)" if national_growth > 0 else "var(--accent-red)" if national_growth < 0 else "var(--text-muted)"
            st.markdown(f"""
<div class="dcr-root mcard dcr-animate">
<div class="mcard-title">🇮🇳 National Job Openings</div>
<div class="mcard-value" style="color:#8b5cf6;">{national:,}</div>
<div class="mcard-label">listings — last 30 days</div>
<div class="mcard-sub" style="font-family:'IBM Plex Mono'; font-size:16px; font-weight:700; color:{ngc}; margin-top:12px;">
{nt} {abs(national_growth):.1f}% MoM
</div>
</div>
""", unsafe_allow_html=True)

        if national > 0:
            market_share = local / national * 100
            st.markdown(f"""
<div class="dcr-root mshare-bar dcr-animate">
<span>📍 {location} captures</span>
<strong>{market_share:.1f}%</strong>
<span>of national openings for this domain</span>
</div>
""", unsafe_allow_html=True)

    # ── Row 4: Saturation Risk ───────────────────────────────────────────────
    sat        = domain_data.get("saturation", {})
    risk_level = sat.get("risk_level", "Safe")   # already normalised in fetch_domain_analytics
    sat_score  = sat.get("score", 0)
    s_emoji, s_color, s_border, s_bg = get_saturation_palette(risk_level)

    st.markdown(f"""
<div class="dcr-root sat-card dcr-animate" style="border:{s_border}; background:{s_bg};">
<div class="mcard-title">⚠️ Is this field getting too crowded?</div>
<div class="sat-risk-header">
<span class="icon">{s_emoji}</span>
<div>
<div class="risk-name" style="color:{s_color};">{risk_level}</div>
<div class="risk-score">
Crowding score: <span style="font-family:'IBM Plex Mono';font-weight:700;font-size:17px;color:{s_color};">{sat_score:.2f}</span> / 1.0
</div>
</div>
</div>
<div class="sat-breakdown">
<div class="sat-bd-item">
<div class="bd-label">Is demand growing?</div>
<div class="bd-value">{sat.get('signals', {}).get('Demand_Trend', 'N/A')}</div>
</div>
<div class="sat-bd-item">
<div class="bd-label">How hard to get first job?</div>
<div class="bd-value">{sat.get('signals', {}).get('Experience_Barrier', 'N/A')}</div>
</div>
</div>
</div>
""", unsafe_allow_html=True)

    # ── Plotly Gauge ─────────────────────────────────────────────────────────
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=sat_score * 100,
        title={"text": "How crowded is this field?", "font": {"size": 17, "family": "Outfit"}},
        delta={"reference": 50, "increasing": {"color": "#dc2626"}, "decreasing": {"color": "#059669"}},
        number={"suffix": "%", "font": {"size": 44, "family": "IBM Plex Mono"}},
        gauge={
            "axis": {
                "range": [0, 100], "tickwidth": 1, "tickcolor": "#94a3b8",
                "tickfont": {"family": "IBM Plex Mono", "size": 12},
            },
            "bar": {"color": s_color, "thickness": 0.70},
            "bgcolor": "rgba(0,0,0,0)",
            "borderwidth": 0,
            "steps": [
                {"range": [0,  33], "color": "rgba(5,150,105,0.10)"},
                {"range": [33, 66], "color": "rgba(217,119,6,0.10)"},
                {"range": [66,100], "color": "rgba(220,38,38,0.10)"},
            ],
            "threshold": {"line": {"color": "#dc2626", "width": 3}, "thickness": 0.8, "value": 70},
        },
    ))
    fig.update_layout(
        height=295,
        margin=dict(l=20, r=20, t=65, b=20),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"family": "Outfit", "size": 14},
    )

    raw_key   = f"gauge_{domain_data['domain']}_{domain_data.get('location','default')}{gauge_key_suffix}"
    gauge_key = "".join(c if c.isalnum() or c == "_" else "_" for c in raw_key)
    st.plotly_chart(fig, use_container_width=True, key=gauge_key, config={"displayModeBar": False})

    # ── Insights & Recommendations ───────────────────────────────────────────
    st.markdown("""
<div class="dcr-root dcr-divider">
<hr/><span>Key Insights & Recommendations</span><hr/>
</div>
""", unsafe_allow_html=True)

    comp_level = domain_data.get("competition", {}).get("level", "Medium")
    insights: List[tuple] = []

    if demand_score >= 7:
        insights.append(("✅", "High market demand — excellent career prospects right now."))
    elif demand_score >= 4:
        insights.append(("⚠️", "Moderate demand — stable but competitive. Differentiation matters."))
    else:
        insights.append(("⚠️", "Lower demand — consider niche or emerging sub-domains."))

    if comp_level == "High":
        insights.append(("🔥", "High competition — build standout portfolio + unique skills."))
    elif comp_level == "Low":
        insights.append(("✨", "Lower competition — strong fundamentals are enough to start."))

    if risk_level == "Highly Competitive":
        insights.append(("🚨", "Saturation risk detected — explore niche specialisations."))
    elif risk_level == "Safe":
        insights.append(("📈", "Healthy market conditions — good time to enter."))

    if loc_adj > 0 and median > 0 and loc_adj > median:
        insights.append(("💰", f"Above-average salaries in {location} — location advantage."))

    for icon, text in insights:
        st.markdown(f"""
<div class="dcr-root insight-item dcr-animate">
<span class="insight-icon">{icon}</span>
<span>{text}</span>
</div>
""", unsafe_allow_html=True)

    with st.expander("🔍 Raw Analytics Data"):
        st.json(domain_data)

# ---------------------------------------------------------------------------
# ENTRY BARRIER CARD
# ---------------------------------------------------------------------------

def render_entry_barrier_card(domain: str, user_profile: Dict[str, Any] = None):
    _inject_styles()

    # Try to pull live data from session state (populated by Phase 3)
    profile_analytics = st.session_state.get("profile_analytics") or {}
    career_path       = profile_analytics.get("career_path") or {}
    prerequisites     = profile_analytics.get("prerequisites") or {}

    # ── Prerequisites text (must come BEFORE timeline so complexity is defined) ──
    complexity      = prerequisites.get("Domain_Complexity", {})
    prereq_text     = complexity.get("classification", "Basic Python + Linear Algebra & Statistics")
    deepest         = complexity.get("deepest_skills", [])
    if deepest:
        top_skills  = ", ".join(s["skill"].title() for s in deepest[:3])
        prereq_text = f"Core skills needed: {top_skills} (+ more)"

    # ── Time to job-ready ──
    # The engine has 2 different learning plans:
    #   career_path.Learning_Plan  → 5,862 hours for ALL 164 gap skills @ 10h/wk = 136 months (absurd)
    #   prerequisites.Learning_Path → 1,430 hours for 22 CORE skills @ 10h/wk = 33 months
    #
    # Real-world calibration: students typically spend 20-30h/week on upskilling.
    # 1,430 core hours @ 20h/wk = ~17 months | @ 30h/wk = ~11 months ← the 1-2yr range users expect.
    #
    # We always use prerequisites hours as the source and show 3 realistic paces.
    prereq_lp       = prerequisites.get("Learning_Path", {})
    core_hours_raw  = float(sum(
        s.get("weeks_to_learn", 0) * 10
        for s in prereq_lp.get("Ordered_Steps", [])
    ))
    # Fallback: derive from Estimated_Months if steps not available
    if core_hours_raw <= 0:
        core_months_10 = float(prereq_lp.get("Estimated_Months") or 0)
        core_hours_raw = core_months_10 * 10 * 4.33   # months × 10h/wk × 4.33wk/mo

    # Still no data — last resort: take career_path hours and scale to core-skills fraction
    if core_hours_raw <= 0:
        all_hours = float(career_path.get("Learning_Plan", {}).get("total_hours") or 0)
        core_hours_raw = all_hours * 0.25  # core skills ≈ 25% of full skill tree

    WEEKS_PER_MONTH = 4.33

    def _months_fmt(h: float, hrs_per_week: float) -> str:
        if h <= 0 or hrs_per_week <= 0:
            return "—"
        mo = h / hrs_per_week / WEEKS_PER_MONTH
        if mo >= 24:
            return f"~{mo/12:.1f} yrs"
        return f"~{int(round(mo))} mo"

    pace_10_display = _months_fmt(core_hours_raw, 10)   # baseline reference (not primary)
    pace_20_display = _months_fmt(core_hours_raw, 20)   # realistic student
    pace_30_display = _months_fmt(core_hours_raw, 30)   # dedicated / bootcamp

    # Sub-note: strip emoji from Quick_Summary
    import re as _re
    quick_summary_text = prerequisites.get("Quick_Summary", "")
    clean_summary = _re.sub(r'[^\x00-\x7F]+', '', quick_summary_text).strip().lstrip(" ").strip()
    barrier       = complexity.get("barrier_level", "")
    timeline_sub  = clean_summary[:130] if clean_summary else (
        f"Entry barrier: {barrier}" if barrier else "Structured, consistent learning required."
    )

    # ── Project complexity ──
    pb              = career_path.get("Project_Benchmark", {})
    project_label   = pb.get("Label", "Medium to Advanced (2–3 portfolio-grade projects)")
    example_project = pb.get("Example_Project", "")
    # Use double-quoted style attr to avoid breaking outer f-string HTML
    if example_project:
        project_display = (
            f'{project_label}<br>'
            f'<small style="color:var(--text-muted);">{example_project}</small>'
        )
    else:
        project_display = project_label

    # ── Interview difficulty ──
    iv              = career_path.get("Interview_Difficulty", {})
    interview_score = iv.get("Index", 7)
    interview_label = iv.get("Label", "")

    # ── Domain knowledge score — use Domain_Complexity.complexity_index ──
    # FIX: old formula was `10 - skill_overlap_score * 10` which gives 10 when
    # overlap = 0 (user knows nothing), which is backwards.
    # Now: complexity_index reflects how deep the domain prereqs go (1–10 scale).
    complexity_idx  = complexity.get("complexity_index", 5.0) or 5.0
    domain_score    = round(min(10.0, max(1.0, complexity_idx * 1.5)), 1)

    # ── Overall difficulty — from readiness score ──
    readiness       = career_path.get("Readiness_Score", {})
    r_score         = readiness.get("score", 50)
    if r_score >= 70:
        diff_level, diff_score, diff_color = "Low",         round(r_score / 10, 1), "green"
    elif r_score >= 40:
        diff_level, diff_score, diff_color = "Medium",      round(r_score / 10, 1), "amber"
    else:
        diff_level, diff_score, diff_color = "High",        round((100 - r_score) / 10, 1), "red"

    # ── Hidden blockers ──
    hb_data         = career_path.get("Hidden_Blockers", {})
    blockers_raw    = hb_data.get("Top_Blockers", [])
    hidden_blockers = []
    for b in blockers_raw:
        sev  = b.get("severity", 0)
        btype = "critical" if sev >= 0.5 else "warning"
        hidden_blockers.append({"type": btype, "text": b.get("message", "") + " — " + b.get("evidence", "")})

    # Fallback static blockers if none found
    if not hidden_blockers:
        hidden_blockers = [
            {"type": "warning",  "text": "Math-heavy — discomfort with calculus/probability will hurt"},
            {"type": "critical", "text": "Most good roles expect at least one strong internship or open-source contribution"},
            {"type": "warning",  "text": "Portfolio is extremely important — generic GitHub repos won't cut it"},
        ]

    st.markdown(f"""
<div class="dcr-root market-header dcr-animate" style="margin-top:32px;">
<h2>⚡ Breaking In: {domain}</h2>
<div style="color:var(--text-muted); font-weight:500;">Realistic timelines, prerequisites, and hidden blockers</div>
</div>
""", unsafe_allow_html=True)

    cols = st.columns(3)
    with cols[0]:
        st.markdown(f"""
<div class="dcr-root mcard dcr-animate">
<div class="mcard-title">⏱️ Time to Job-Ready</div>
<div style="padding:16px; background:rgba(79,70,229,0.05); border-radius:12px; margin-bottom:12px; border:1px solid rgba(79,70,229,0.1);">
<div style="font-size:12px; font-weight:700; color:var(--accent-indigo);">20 hrs/week (Student Pace)</div>
<div class="mcard-value sm" style="color:var(--accent-indigo); margin:4px 0;">{pace_20_display}</div>
</div>
<div style="padding:12px; background:rgba(5,150,105,0.05); border-radius:12px; margin-bottom:12px; border:1px solid rgba(5,150,105,0.1);">
<div style="font-size:20px; font-weight:700; color:var(--accent-green);">{pace_30_display}</div>
<div style="font-size:12px; font-weight:700; color:var(--accent-green);">30 hrs/week (Bootcamp Pace)</div>
</div>
<div style="font-size:12px; color:var(--text-muted); line-height:1.4;">{timeline_sub}</div>
</div>
""", unsafe_allow_html=True)

    with cols[1]:
        st.markdown(f"""
<div class="dcr-root mcard dcr-animate">
<div class="mcard-title">📋 Prerequisites</div>
<div style="font-size:15px; line-height:1.6; color:var(--color-text-primary); margin-bottom:16px;">
{prereq_text}
</div>
<div style="font-size:12px; font-weight:700; text-transform:uppercase; color:var(--text-muted); margin-bottom:8px;">Typical Barrier</div>
<span class="pill pill-amber">Intermediate Logic</span>
</div>
""", unsafe_allow_html=True)

    with cols[2]:
        st.markdown(f"""<div class="dcr-root mcard dcr-animate">
<div class="mcard-title">📚 Project Complexity</div>
<div style="font-size:18px; font-weight:700; color:var(--accent-red); margin-bottom:12px;">{project_display}</div>
<div style="font-size:12px; color:var(--text-muted);">Generic GitHub repos won't cut it. You'll need deployed, documented work.</div>
</div>""", unsafe_allow_html=True)

    col_dsa, col_dom = st.columns(2)
    with col_dsa:
        st.markdown(f"""<div class="dcr-root mcard dcr-animate">
<div class="mcard-title">💻 Interview Difficulty</div>
<div style="display:flex; align-items:center; gap:16px;">
<div class="mcard-value" style="color:var(--accent-red);">{interview_score}<span style="font-size:16px; font-weight:400;">/10</span></div>
<div style="font-size:14px; color:var(--text-secondary);">{interview_label}</div>
</div>
</div>""", unsafe_allow_html=True)

    with col_dom:
        st.markdown(f"""<div class="dcr-root mcard dcr-animate">
<div class="mcard-title">🎯 Domain Depth</div>
<div style="display:flex; align-items:center; gap:16px;">
<div class="mcard-value" style="color:var(--accent-amber);">{domain_score}<span style="font-size:16px; font-weight:400;">/10</span></div>
<div style="font-size:14px; color:var(--text-secondary);">System design + domain concepts are tested.</div>
</div>
</div>""", unsafe_allow_html=True)

    st.markdown(f"""
<div class="dcr-root mcard dcr-animate" style="background:var(--dcr-gradient-danger); color:white !important; text-align:center; padding:30px;">
<div class="mcard-title" style="color:rgba(255,255,255,0.7);">Overall Hiring Difficulty</div>
<div style="font-size:48px; font-weight:800; margin:10px 0;">{diff_level}</div>
<div style="font-size:14px; opacity:0.9;">Difficulty Score ≈ {diff_score}/10</div>
</div>
""", unsafe_allow_html=True)

    if hidden_blockers:
        st.markdown("""<div class="dcr-root dcr-divider"><hr/><span>🚨 Hidden Blocker Alerts</span><hr/></div>""", unsafe_allow_html=True)
        for b in hidden_blockers:
            icon = "🟡" if b["type"] == "warning" else "🔴" if b["type"] == "critical" else "ℹ️"
            st.markdown(f"""
<div class="dcr-root insight-item dcr-animate">
    <span class="insight-icon">{icon}</span>
    <span style="font-size:14px;">{b['text']}</span>
</div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# GROWTH TRAJECTORY CARD
# ---------------------------------------------------------------------------

def render_growth_trajectory_card(domain: str):
    _inject_styles()

    # Pull live data from session state if Phase 3 has run
    profile_analytics = st.session_state.get("profile_analytics") or {}
    career_path       = profile_analytics.get("career_path") or {}
    domain_analytics  = st.session_state.get("domain_analytics") or {}
    sal_growth        = domain_analytics.get("salary_growth") or {}
    ai_risk_data      = domain_analytics.get("ai_risk") or {}
    stability_data    = domain_analytics.get("stability") or {}

    # ── Salary progression — use Experience_Ladder (always populated) ──
    # BUG-3 FIX: salary_growth.Scenarios use Baseline.Fresher_Median_LPA which
    # is 0.0 in this dataset (salary column not scraped for fresher band).
    # Experience_Ladder.fresher/mid are computed from actual CSV salary data.
    ladder  = sal_growth.get("Experience_Ladder", {})
    fresher = ladder.get("fresher", {})
    junior  = ladder.get("junior",  {})
    mid     = ladder.get("mid",     {})
    senior  = ladder.get("senior",  {})

    f_lo = fresher.get("p25",    0) or 0
    f_hi = (junior.get("median", 0) or fresher.get("p75", 0) or fresher.get("median", 0) or 0)
    m_lo = mid.get("p25",        0) or 0
    m_hi = mid.get("p75",        0) or 0

    # Guarantee non-zero display — fallback to senior band if mid is also 0
    if m_hi == 0:
        m_hi = senior.get("p75", 0) or senior.get("median", 0) or 0
    if f_hi == 0:
        f_hi = junior.get("p75", 0) or mid.get("p25", 0) or 0

    # salary_0_2y / salary_3_5y replaced by _fmt_sal() helper below

    # ── Role evolution path — built from live RoleEvolutionEngine data ──
    # BUG-4 FIX: was using a hardcoded static role_path array for every domain.
    # Now reads domain_analytics["role_evolution"]["Evolution_Path"] which contains
    # domain-specific steps: from/to roles, cumulative years, transition probability.
    role_evolution_data = domain_analytics.get("role_evolution") or {}
    evo_steps           = role_evolution_data.get("Evolution_Path", [])

    if evo_steps:
        # Build role_path from live engine data
        # First entry: current role (year 0) → first step
        starting_role = role_evolution_data.get("Starting_Role", domain).title()
        role_path = []

        prev_years = 0
        for i, step in enumerate(evo_steps):
            cum_yrs   = step.get("cumulative_years", prev_years + 2)
            from_role = step.get("from", "").title()
            to_role   = step.get("to",   "").title()
            prob      = step.get("transition_probability", "")
            move_type = step.get("move_type", "Promotion").replace("⬆️", "").strip()

            # Year range label
            if i == 0:
                yr_label = f"0–{cum_yrs:.0f}"
            else:
                yr_label = f"{prev_years:.0f}–{cum_yrs:.0f}"

            desc = f"{move_type} · {prob} probability" if prob else move_type
            role_path.append((yr_label, from_role, desc))
            prev_years = cum_yrs

        # Append the final destination role
        last_step   = evo_steps[-1]
        final_role  = last_step.get("to", "Principal / Architect").title()
        final_years = last_step.get("cumulative_years", prev_years)
        role_path.append((f"{final_years:.0f}+", final_role, "org-wide strategy & leadership"))
    else:
        # Fallback only if engine returned no steps at all
        evo_preview = career_path.get("Evolution_Preview") or {}
        first       = evo_preview.get("first_step", "Mid-level").title()
        yrs         = evo_preview.get("years_to_senior", 4.0)
        role_path   = [
            ("0–2",            "Junior / Associate",    "core skills + clean code"),
            (f"2–{yrs:.0f}",   first,                   "ownership + mentoring"),
            (f"{yrs:.0f}–9",   "Lead / Staff",          "architecture + cross-team impact"),
            ("9+",             "Principal / Architect", "org-wide strategy"),
        ]

    # ── Stability ──
    stab_score  = 7.8   # fallback
    stab_rating = "Good"
    stab_text   = "Strong demand expected till 2030+"
    if stability_data and "error" not in stability_data:
        stab_score  = round(stability_data.get("Stability_Score", 7.8), 1)
        stab_rating = stability_data.get("Rating", "Good")
        stab_text   = stability_data.get("Interpretation", stab_text)

    # ── Skill Transferability ──
    trans_data  = profile_analytics.get("transferability") or {}
    trans_score = trans_data.get("Transferability", {}).get("Score", 8.1) if trans_data else 8.1
    trans_label = trans_data.get("Transferability", {}).get("Label", "High") if trans_data else "High"
    trans_path  = trans_data.get("Path", f"{domain} → Related Roles") if trans_data else f"{domain} → Related Roles"

    # ── AI Risk ──
    ai_risk_score = round(float(ai_risk_data.get("AI_Risk_Score", 0.52)) * 10, 1)
    ai_risk_cat   = ai_risk_data.get("Risk_Category", "Medium Risk")
    ai_risk_adv   = ai_risk_data.get("Actionable_Advice", "Stay updated with AI tools.")
    ai_risk_level = (
        "Low"    if ai_risk_score < 3.5 else
        "Medium" if ai_risk_score < 6.5 else
        "High"
    )

    # Format salary display — show meaningful fallback when data is unavailable
    def _fmt_sal(lo, hi):
        if lo == 0 and hi == 0:
            return "Data not available for this band"
        elif lo == 0:
            return f"up to ₹{hi:.0f} LPA"
        return f"₹{lo:.0f} – ₹{hi:.0f} LPA"

    sal_0_2_display = _fmt_sal(f_lo, f_hi)
    sal_3_5_display = _fmt_sal(m_lo, m_hi)

    st.markdown(f"""
<div class="dcr-root market-header dcr-animate" style="margin-top:32px;">
<h2>📈 Career Growth — {domain}</h2>
<div style="color:var(--text-muted); font-weight:500;">Your potential trajectory over the next 5–10 years</div>
</div>
""", unsafe_allow_html=True)

    st.markdown(f"""<div class="dcr-root mcard dcr-animate">
<div class="mcard-title">💰 Salary Progression (India)</div>
<div style="display:grid; grid-template-columns:1fr 1fr; gap:24px; margin-top:16px;">
<div style="padding:20px; background:rgba(13,148,136,0.05); border-radius:16px; border:1px solid rgba(13,148,136,0.1);">
<div style="font-size:12px; font-weight:700; color:var(--accent-teal); text-transform:uppercase;">0–2 years (Entry)</div>
<div style="font-size:24px; font-weight:800; color:var(--accent-teal); margin-top:8px;">{sal_0_2_display}</div>
</div>
<div style="padding:20px; background:rgba(79,70,229,0.05); border-radius:16px; border:1px solid rgba(79,70,229,0.1);">
<div style="font-size:12px; font-weight:700; color:var(--accent-indigo); text-transform:uppercase;">3–5 years (Mid-lvl)</div>
<div style="font-size:24px; font-weight:800; color:var(--accent-indigo); margin-top:8px;">{sal_3_5_display}</div>
</div>
</div>
</div>""", unsafe_allow_html=True)

    st.markdown("""<div class="dcr-root dcr-divider"><hr/><span>🎯 Next Milestone Steps</span><hr/></div>""", unsafe_allow_html=True)

    for i, (years_label, title, desc) in enumerate(role_path):
        alt_line = ""
        if evo_steps and i < len(evo_steps):
            alts = evo_steps[i].get("alternative_paths", [])
            if alts:
                parts = []
                for a in alts[:3]:
                    role_name = a.get("role", "").title()
                    prob      = a.get("probability", "")
                    parts.append(f"{role_name} ({prob})")
                alt_line = "↔ Alt: " + " · ".join(parts)

        alt_html = f'<div style="font-size:11px; color:var(--text-muted); margin-top:8px; display:flex; align-items:center; gap:4px;"><span>{alt_line}</span></div>' if alt_line else ""

        st.markdown(f"""
<div class="dcr-root mcard dcr-animate" style="margin-bottom:12px; padding:20px; border-left:4px solid var(--accent-indigo);">
<div style="display:flex; justify-content:space-between; align-items:flex-start;">
<div>
<div style="font-size:18px; font-weight:700; color:var(--color-text-primary);">{title}</div>
<div style="font-size:14px; color:var(--text-secondary); margin-top:4px;">{desc}</div>
{alt_html}
</div>
<div class="pill pill-green" style="font-family:'IBM Plex Mono'; font-weight:700;">{years_label} YRS</div>
</div>
</div>
""", unsafe_allow_html=True)

    cols = st.columns(3)
    with cols[0]:
        st.markdown(f"""
<div class="dcr-root mcard dcr-animate" style="text-align:center;">
<div class="mcard-title">Domain Stability</div>
<div class="mcard-value sm" style="color:var(--accent-green);">{stab_score}<span style="font-size:14px;">/10</span></div>
<span class="pill pill-green">{stab_rating}</span>
<div style="font-size:12px; color:var(--text-muted); margin-top:12px;">{stab_text}</div>
</div>
""", unsafe_allow_html=True)

    with cols[1]:
        st.markdown(f"""
<div class="dcr-root mcard dcr-animate" style="text-align:center;">
<div class="mcard-title">Transferability</div>
<div class="mcard-value sm" style="color:var(--accent-teal);">{trans_score}<span style="font-size:14px;">/10</span></div>
<span class="pill pill-green">{trans_label}</span>
<div style="font-size:12px; color:var(--text-muted); margin-top:12px;">{trans_path}</div>
</div>
""", unsafe_allow_html=True)

    with cols[2]:
        ai_color    = "var(--accent-amber)" if ai_risk_level == "Medium" else ("var(--accent-red)" if ai_risk_level == "High" else "var(--accent-green)")
        ai_pill_cls = "amber" if ai_risk_level == "Medium" else ("red" if ai_risk_level == "High" else "green")
        st.markdown(f"""
<div class="dcr-root mcard dcr-animate" style="text-align:center;">
<div class="mcard-title">AI Displacement Risk</div>
<div class="mcard-value sm" style="color:{ai_color};">{ai_risk_level}</div>
<span class="pill pill-{ai_pill_cls}">Risk: {ai_risk_score}/10</span>
<div style="font-size:12px; color:var(--text-muted); margin-top:12px;">{ai_risk_adv}</div>
</div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# REAL TALK SECTION
# ---------------------------------------------------------------------------

def render_real_talk_section(domain: str):
    _inject_styles()

    # Pull live data from AdaptiveRealTalkEngine output (Phase 3)
    profile_analytics = st.session_state.get("profile_analytics") or {}
    rt_data           = profile_analytics.get("real_talk") or {}
    rt_inner          = rt_data.get("real_talk") or {}

    # ── Harsh truth & silver lining ──
    harsh  = rt_inner.get("harsh_truth",  "Very high competition at entry level — 70–80% of beginners never land a proper role in this domain.")
    silver = rt_inner.get("silver_lining","Once you cross the 1.5–2 year mark with good projects, salary and opportunity curve becomes steep.")

    # ── Traps — engine key is 'beginner_traps' ──
    traps_raw = (
        rt_inner.get("beginner_traps") or
        rt_inner.get("common_traps")   or
        rt_inner.get("traps")          or
        []
    )
    traps = traps_raw if traps_raw else [
        "Stuck in tutorial hell — watching 200+ videos without building anything meaningful",
        "Copy-pasting projects from YouTube / GitHub without understanding → interviewers spot it instantly",
        "Expecting job after doing only basic courses — market now demands deployed + documented work",
    ]

    # ── Success patterns ──
    patterns_raw = rt_inner.get("success_patterns") or rt_inner.get("patterns") or []
    patterns = patterns_raw if patterns_raw else [
        "Build 2–3 non-trivial projects → deploy them → write clear READMEs + architecture diagrams",
        "Contribute to open source or create public tools → gets noticed more than certificates",
        "Network + share progress on LinkedIn / Twitter → many offers come from visibility",
    ]

    # ── Timeline ──
    urgency  = rt_data.get("urgency") or {}
    p_action = rt_data.get("priority_action") or ""
    timeline = urgency.get("message") or p_action or "6–18 months of serious effort separates the 10–20% who succeed from the rest"

    # ── Persona — build HTML without nested f-string quotes ──
    persona      = rt_data.get("persona") or {}
    persona_name = persona.get("name", "")
    persona_tag  = persona.get("tagline", "")
    persona_emoji = persona.get("emoji", "")

    # ── Salary context — override if engine shows ₹0.0 ──
    salary_ctx = rt_data.get("salary_context", "")
    if not salary_ctx or "0.0" in salary_ctx:
        # Build from salary_growth Experience_Ladder which is always populated
        domain_analytics = st.session_state.get("domain_analytics") or {}
        ladder   = (domain_analytics.get("salary_growth") or {}).get("Experience_Ladder", {})
        f_med    = (ladder.get("fresher") or {}).get("median", 0) or 0
        mid_med  = (ladder.get("mid")     or {}).get("median", 0) or 0
        f_p25    = (ladder.get("fresher") or {}).get("p25",    0) or 0
        mid_p75  = (ladder.get("mid")     or {}).get("p75",    0) or 0
        if f_med > 0 or mid_med > 0:
            salary_ctx = f"💰 Fresher median: ₹{f_med:.1f} LPA · Mid-level: ₹{mid_med:.1f} LPA (P25: ₹{f_p25:.1f} | P75: ₹{mid_p75:.1f} LPA)"
        else:
            salary_ctx = ""

    st.markdown(f"""<div class="dcr-root market-header dcr-animate" style="margin-top:32px; background:var(--dcr-gradient-danger); padding:24px; border-radius:16px;">
<h2 style="color:white !important; margin:0;">🎯 Real Talk: {domain}</h2>
<div style="color:rgba(255,255,255,0.8); font-weight:500;">No motivational fluff. Just career reality.</div>
</div>""", unsafe_allow_html=True)

    if persona_name:
        st.markdown(f"""<div class="dcr-root mcard dcr-animate" style="text-align:center; border:1px solid var(--accent-indigo); margin-bottom:16px;">
<div class="mcard-title">Your Success Persona</div>
<div style="font-size:24px; font-weight:800; color:var(--accent-indigo);">{persona_emoji} {persona_name}</div>
<div style="font-size:14px; color:var(--text-secondary); margin-top:4px;">{persona_tag}</div>
</div>""", unsafe_allow_html=True)

    if salary_ctx:
        st.markdown(f"""
<div class="dcr-root mshare-bar dcr-animate" style="margin-bottom:20px; background:rgba(0,0,0,0.02); border:1px solid var(--color-border-secondary);">
<span style="font-weight:600; color:var(--color-text-primary);">{salary_ctx}</span>
</div>
""", unsafe_allow_html=True)

    col_h, col_s = st.columns(2)
    with col_h:
        st.markdown(f"""
<div class="dcr-root mcard dcr-animate" style="border-top:4px solid var(--accent-red); background:rgba(220,38,38,0.02);">
<div style="color:var(--accent-red); font-size:14px; font-weight:700; text-transform:uppercase; letter-spacing:0.1em; margin-bottom:12px;">⚠️ The Harsh Truth</div>
<div style="font-size:15px; line-height:1.6; color:var(--color-text-primary);">{harsh}</div>
</div>
""", unsafe_allow_html=True)

    with col_s:
        st.markdown(f"""
<div class="dcr-root mcard dcr-animate" style="border-top:4px solid var(--accent-green); background:rgba(5,150,105,0.02);">
<div style="color:var(--accent-green); font-size:14px; font-weight:700; text-transform:uppercase; letter-spacing:0.1em; margin-bottom:12px;">✨ The Silver Lining</div>
<div style="font-size:15px; line-height:1.6; color:var(--color-text-primary);">{silver}</div>
</div>
""", unsafe_allow_html=True)

    st.markdown("""<div class="dcr-root dcr-divider"><hr/><span>🚨 Common Beginner Traps</span><hr/></div>""", unsafe_allow_html=True)
    trap_cols = st.columns(len(traps) if traps else 1)
    for i, t in enumerate(traps):
        with trap_cols[i % len(trap_cols)]:
            st.markdown(f"""
<div class="dcr-root mcard dcr-animate" style="padding:16px; margin-bottom:12px; height:auto;">
<div style="display:flex; gap:12px; align-items:flex-start;">
<span style="font-size:20px;">⚠️</span>
<div style="font-size:13px; color:var(--text-secondary); line-height:1.4;">{t}</div>
</div>
</div>
""", unsafe_allow_html=True)

    st.markdown("""<div class="dcr-root dcr-divider"><hr/><span>✅ High-Success Patterns</span><hr/></div>""", unsafe_allow_html=True)
    for p in patterns:
        st.markdown(f"""
<div class="dcr-root insight-item dcr-animate">
<span class="insight-icon">✔️</span>
<span style="font-size:14px; font-weight:500;">{p}</span>
</div>
""", unsafe_allow_html=True)

    st.markdown(f"""<div class="dcr-root mcard dcr-animate" style="margin-top:24px; text-align:center; background:var(--dcr-glass-bg); border:1px dashed var(--accent-indigo);">
<div class="mcard-title">⏳ Realistic Success Timeline</div>
<div style="font-size:18px; color:var(--accent-indigo); font-weight:700; line-height:1.5; padding:10px 0;">{timeline}</div>
</div>""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# COMPLETE ANALYSIS
# ---------------------------------------------------------------------------

def render_comparison_table(recommendations: List[dict]):
    """Renders a comparison table for the top 3 domains."""
    if not recommendations:
        return

    rows_html = ""
    for rec in recommendations:
        domain = rec.get("domain", "N/A")
        match  = f"{rec.get('match_percentage', 0)}%"
        salary = rec.get("market_metrics", {}).get("avg_starting_salary", "N/A")
        time   = rec.get("timeline", "N/A")
        comp   = rec.get("market_metrics", {}).get("competition_level", "Medium")
        
        _, color, _, _ = get_competition_badge(comp)

        # Build row as a single line to prevent Streamlit markdown parsing issues
        # Use a hidden <span> or data attribute if we wanted to trigger JS, but here we just render
        action_btn_html = f'<div style="color:var(--accent-indigo); font-weight:700; cursor:pointer; font-size:12px;">SCROLL DOWN TO ANALYZE ↓</div>'
        rows_html += f'<tr><td class="domain-hl">{domain}</td><td style="font-weight:700; color:var(--accent-indigo);">{match}</td><td>{salary}</td><td>{time}</td><td><span class="pill" style="background:{color}22; color:{color}; border:1px solid {color}44;">{comp}</span></td><td>{action_btn_html}</td></tr>'

    st.markdown(f"""<div class="dcr-root mcard dcr-animate" style="margin-top:24px; padding:0; overflow:hidden;">
<div class="mcard-title" style="padding:20px 24px; margin-bottom:0; background:rgba(0,0,0,0.02); border-bottom:1px solid var(--color-border-secondary);">📊 Market Fit Comparison</div>
<div style="padding:12px; overflow-x:auto;">
<table class="comp-table"><thead><tr><th>Domain</th><th>Match %</th><th>Avg. Salary</th><th>Time to Ready</th><th>Competition</th><th>Action</th></tr></thead>
<tbody>{rows_html}</tbody>
</table></div></div>""", unsafe_allow_html=True)

def render_complete_domain_analysis(
    domain: str,
    location: str,
    user_profile: Optional[Dict[str, Any]] = None,
    skip_market_card: bool = False,
    recommended_domains: Optional[List[str]] = None,
):
    """
    Renders the full domain breakdown using a tabbed interface.
    """
    with st.spinner("Fetching market analytics…"):
        market_data = fetch_domain_analytics(
            domain,
            location,
            user_profile,
            recommended_domains=recommended_domains,
        )

    if not market_data:
        st.error(f"Could not load data for {domain}")
        return

    # Fix Verdict Mismatch: Ensure LLM focuses strictly on the selected domain as the winner
    # We pass the selected domain first, and filter it out from the 'others'
    other_domains = [d for d in (recommended_domains or []) if d != domain]
    _top_domains = [{"domain": domain, "match_percentage": 100}] # Force focus on selected
    for d in other_domains[:2]:
        _top_domains.append({"domain": d, "match_percentage": 0})

    with st.spinner("Analyzing your career match…"):
        verdict = generate_verdict(user_profile, _top_domains, market_data)

    # 1. Subtle Verdict Card (Introduction to analysis)
    render_verdict_card(verdict, domain)

    # 2. Main Analysis Tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Overview & Plan", 
        "🏢 Market Reality", 
        "⚡ Path to Entry", 
        "📈 Long-term Growth", 
        "🎯 Real Talk"
    ])

    with tab1:
        col_plan, col_quick = st.columns([2, 1])
        with col_plan:
            render_30_day_action_plan(market_data, user_profile or {}, verdict)
        with col_quick:
            render_quick_wins_sidebar(domain)

    with tab2:
        render_market_reality_card(market_data, gauge_key_suffix="_tab")

    with tab3:
        render_entry_barrier_card(domain, user_profile or {})

    with tab4:
        render_growth_trajectory_card(domain)

    with tab5:
        render_real_talk_section(domain)

    with st.expander("🔍 Developer Debug: View Raw JSON"):
        st.json(market_data)

# ---------------------------------------------------------------------------
# PATH 1 – Help Me Decide
# ---------------------------------------------------------------------------

def render_path_1_flow():
    
    st.markdown("""
<div class="dcr-root dcr-section-title">
<span class="step-badge">STEP 01</span> Tell us about yourself
</div>
""", unsafe_allow_html=True)

    if "p1_recommendations"  not in st.session_state:
        st.session_state.p1_recommendations  = None
    if "p1_selected_domain"  not in st.session_state:
        st.session_state.p1_selected_domain  = None
    if "p1_location"         not in st.session_state:
        st.session_state.p1_location         = "Jaipur"

    with st.form("p1_recommendation_form"):
        pref_col1, pref_col2 = st.columns(2)
        with pref_col1:
            experience = st.selectbox(
                "Experience Level",
                ["Fresher", "1-2 years", "3-5 years", "5+ years"],
                key="p1_exp",
            )
            interest = st.multiselect(
                "Skills you already have",
                [
                    "Python", "SQL", "Machine Learning", "Statistics", "Pandas",
                    "HTML", "CSS", "JavaScript", "React", "Node.js",
                    "Docker", "AWS", "Terraform", "Linux", "Kubernetes",
                    "TensorFlow", "PyTorch", "Java", "APIs", "LLMs",
                ],
                key="p1_int",
            )
        with pref_col2:
            location_pref = st.selectbox("Preferred Location", LOCATION_OPTIONS, key="p1_loc")
            math_comfort  = st.select_slider(
                "Math Comfort Level",
                options=["Weak", "Moderate", "Strong"],
                value="Moderate",
                key="p1_math",
            )
        submitted = st.form_submit_button("Get My Recommendations →", use_container_width=True)

    if submitted:
        st.session_state.p1_location       = location_pref
        st.session_state.p1_selected_domain = None
        user_profile = {
            "experience":   experience,
            "skills":       interest,
            "location":     location_pref,
            "math_comfort": math_comfort,
        }
        with st.spinner("Fetching recommendations from server…"):
            recs = api_client.get_recommendations(user_profile, top_n=3)
            if recs is None:
                st.error("Server error — could not get recommendations. Ensure Flask API is running.")
                st.session_state.p1_recommendations = None
                st.session_state["recommendations"] = None
            else:
                st.session_state.p1_recommendations = recs
                st.session_state["recommendations"] = recs

    if st.session_state.p1_recommendations:
        st.markdown(f"""
<div class="dcr-root dcr-section-title" style="margin-bottom:24px;">
<span class="step-badge">STEP 02</span> Your Recommended Career Paths
</div>
""", unsafe_allow_html=True)

        recs = st.session_state.p1_recommendations
        
        # ── Hero Next Step Area ──────────────────────────────────────────────
        top_rec = recs[0]
        location_display = st.session_state.p1_location if st.session_state.p1_location else "your local"
        st.markdown(f"""<div class="dcr-root hero-verdict">
<div style="position:absolute; top:-20px; right:-20px; font-size:120px; opacity:0.1; transform:rotate(15deg);">🎯</div>
<div style="display:flex; justify-content:space-between; align-items:center; position:relative; z-index:1;">
<div>
<div style="font-size:12px; font-weight:700; text-transform:uppercase; letter-spacing:0.15em; opacity:0.8; margin-bottom:12px; display:inline-block; padding:4px 12px; background:rgba(255,255,255,0.15); border-radius:4px;">Recommended Next Step</div>
<h2 style="color:white !important; margin:10px 0; font-size:40px; font-weight:800; letter-spacing:-0.02em;">{top_rec['domain']}</h2>
<p style="margin-top:16px; font-size:17px; opacity:0.9; max-width:550px; line-height:1.6;">The {location_display} market is currently showing high demand for this skillset. With a <strong>{top_rec['match_percentage']}% skill match</strong>, you have a clear lead over other applicants.</p>
</div>
<div style="text-align:right;">
<div style="font-size:62px; font-weight:800; line-height:1; letter-spacing:-0.03em;">{top_rec['match_percentage']}%</div>
<div style="font-size:13px; font-weight:700; opacity:0.8; margin-top:8px;">COMPATIBILITY score</div>
</div>
</div>
</div>""", unsafe_allow_html=True)

        # ── Comparison Table ─────────────────────────────────────────────────
        render_comparison_table(recs)

        # ── Selection Buttons ──────────────────────────────────────────────────
        st.markdown("""
<div class="dcr-root mcard" style="margin-bottom:24px; background:rgba(79,70,229,0.05); border:1px dashed var(--accent-indigo); text-align:center;">
<div style="font-size:14px; font-weight:600; color:var(--accent-indigo);">Select a domain below for personalized deep-dive analysis</div>
</div>
""", unsafe_allow_html=True)
        
        btn_cols = st.columns(len(recs))
        for i, rec in enumerate(recs):
            with btn_cols[i]:
                is_selected = (st.session_state.p1_selected_domain == rec["domain"])
                if st.button(
                    f"Analyze {rec['domain']} →", 
                    key=f"p1_btn_{rec['domain']}", 
                    use_container_width=True, 
                    type="primary" if is_selected else "secondary"
                ):
                    st.session_state.p1_selected_domain = rec["domain"]
                    st.rerun()

    if st.session_state.p1_selected_domain:
        # Show a small "Recap" of top matches for context
        with st.expander("🔙 Change Domain / See All Matches", expanded=False):
            st.info("You are currently analyzing " + st.session_state.p1_selected_domain)
            if st.button("Browse all 3 recommendations"):
                st.session_state.p1_selected_domain = None
                st.rerun()

        # ── Step 03: Deep Analysis ──────────────────────────────────────────
        st.markdown(f"""
<div class="dcr-root analysis-container">
<div class="dcr-section-title" style="margin-bottom:32px;">
<span class="step-badge">STEP 03</span> Personalized Analysis: {st.session_state.p1_selected_domain}
</div>
</div>
""", unsafe_allow_html=True)

        user_profile = {
            "experience":   st.session_state.get("p1_exp",  "Fresher"),
            "skills":       st.session_state.get("p1_int",  []),
            "location":     st.session_state.p1_location,
            "math_comfort": st.session_state.get("p1_math", "Moderate"),
        }

        top3 = [r["domain"] for r in (st.session_state.p1_recommendations or [])[:3]]
        
        # render_complete_domain_analysis calls st.tabs, so we use a container
        # for proper layout instead of split HTML tags which cause leakage.
        analysis_container = st.container()
        with analysis_container:
            render_complete_domain_analysis(
                domain=st.session_state.p1_selected_domain,
                location=st.session_state.p1_location,
                user_profile=user_profile,
                skip_market_card=False,
                recommended_domains=top3 or None,
            )

# ---------------------------------------------------------------------------
# PATH 2 – I Know My Domain
# ---------------------------------------------------------------------------

def render_path_2_flow():
    _inject_styles()

    if "dcr_domain_options" not in st.session_state:
        with st.spinner("Loading domain list from server…"):
            raw = api_client.get_all_domains()
            st.session_state["dcr_domain_options"] = raw if raw else list(ALL_DOMAINS)

    st.markdown("""
<div class="dcr-root dcr-section-title">
<span class="step-badge">STEP 01</span> Explore Market Reality
</div>
""", unsafe_allow_html=True)

    col1, col2 = st.columns([2, 1])
    with col1:
        selected_domain = st.selectbox("Choose Domain", _get_domain_options(), key="p2_dom")
    with col2:
        location = st.selectbox("Location", LOCATION_OPTIONS, key="p2_loc")

    if st.button("📊 Load Analytics", type="primary", key="p2_load_btn", use_container_width=True):
        with st.spinner("Fetching from server…"):
            data = fetch_domain_analytics(selected_domain, location)
        if data:
            st.session_state.p2_market_data         = data
            st.session_state.p2_show_full_analysis  = False
        else:
            st.session_state.pop("p2_market_data", None)

    if "p2_market_data" in st.session_state:
        render_market_reality_card(
            st.session_state.p2_market_data,
            gauge_key_suffix="_standalone",
        )

        st.markdown("""
<div class="dcr-root dcr-section-title" style="margin-top:40px;">
📈 Want the Full Picture?
</div>
""", unsafe_allow_html=True)

        # ── Inline profile form — needed so Phase 3 has real user data ──────
        # Without this, Entry Barrier / Real Talk / Growth all show generic
        # content because they have no skills to compare against.
        st.markdown("""
<div class="dcr-root mcard" style="margin-bottom:16px;">
<div class="mcard-title" style="font-size:14px; text-transform:none; letter-spacing:0; color:var(--text-secondary);">
📋 Quick profile — gets you personalised Entry Barrier, Growth & Real Talk analysis
</div>
</div>
""", unsafe_allow_html=True)

        with st.form("p2_profile_form"):
            fc1, fc2 = st.columns(2)
            with fc1:
                p2_exp    = st.selectbox(
                    "Experience Level",
                    ["Fresher", "1-2 years", "3-5 years", "5+ years"],
                    key="p2_exp_sel",
                )
                p2_skills = st.multiselect(
                    "Skills you already have",
                    ["Python", "SQL", "Machine Learning", "Statistics", "Pandas",
                     "HTML", "CSS", "JavaScript", "React", "Node.js", "Docker",
                     "AWS", "Terraform", "Linux", "Kubernetes", "TensorFlow",
                     "PyTorch", "Java", "APIs", "LLMs"],
                    key="p2_skills_sel",
                )
            with fc2:
                p2_math = st.select_slider(
                    "Math Comfort Level",
                    options=["Weak", "Moderate", "Strong"],
                    value="Moderate",
                    key="p2_math_sel",
                )
            p2_submitted = st.form_submit_button(
                "Show Complete Domain Analysis (Barriers + Growth + Real Talk)",
                type="primary",
                use_container_width=True,
            )

        if p2_submitted:
            st.session_state.p2_user_profile = {
                "experience":   p2_exp,
                "skills":       p2_skills,
                "math_comfort": p2_math,
                "location":     st.session_state.p2_market_data["location"],
            }
            st.session_state.p2_show_full_analysis = True

        if st.session_state.get("p2_show_full_analysis", False):
            render_complete_domain_analysis(
                domain=st.session_state.p2_market_data["domain"],
                location=st.session_state.p2_market_data["location"],
                user_profile=st.session_state.get("p2_user_profile"),
                skip_market_card=True,
            )

        st.markdown("""
<div class="dcr-root dcr-section-title" style="margin-top:32px;">
🤔 Quick Compatibility Check
</div>
""", unsafe_allow_html=True)

        if st.checkbox("Show Compatibility Engine", key="p2_compat_check"):
            render_inline_recommendation_interface(
                selected_domain=st.session_state.p2_market_data["domain"],
                location=st.session_state.p2_market_data["location"],
            )

# ---------------------------------------------------------------------------
# INLINE COMPATIBILITY CHECK
# ---------------------------------------------------------------------------

def render_inline_recommendation_interface(selected_domain: str = "", location: str = "Jaipur"):
    _inject_styles()

    with st.form("inline_compat_form"):
        st.markdown("""
<div class="dcr-root mcard-title" style="margin-bottom:12px; font-size:15px; text-transform:none; letter-spacing:0; color:var(--text-secondary);">
Your profile — how do you fit this domain?
</div>
""", unsafe_allow_html=True)

        c1, c2 = st.columns(2)
        with c1:
            experience = st.selectbox("Experience Level", ["Fresher", "1-2 years", "3-5 years", "5+ years"], key="ic_exp")
            skills     = st.multiselect(
                "Skills you already have",
                ["Python", "SQL", "Machine Learning", "Statistics", "Pandas", "HTML", "CSS",
                 "JavaScript", "React", "Node.js", "Docker", "AWS", "Terraform", "Linux",
                 "Kubernetes", "TensorFlow", "PyTorch", "Java", "APIs", "LLMs"],
                key="ic_skills",
            )
        with c2:
            math_comfort = st.select_slider("Math Comfort Level", ["Weak", "Moderate", "Strong"], value="Moderate", key="ic_math")

        submitted = st.form_submit_button("Check My Compatibility →", use_container_width=True)

    if submitted:
        user_profile = {
            "experience":   experience,
            "skills":       skills,
            "location":     location,
            "math_comfort": math_comfort,
        }
        with st.spinner("Fetching from server…"):
            target = api_client.get_domain_compatibility(user_profile, selected_domain)

        if target:
            match_pct = target["match_percentage"]
            color = "#059669" if match_pct >= 65 else "#d97706" if match_pct >= 40 else "#dc2626"

            st.markdown(f"""
<div class="dcr-root compat-result dcr-animate" style="background:var(--color-background-secondary); border:1px solid var(--color-border-secondary); padding:32px; border-radius:24px; text-align:center; margin-bottom:24px;">
<div style="font-size:12px; font-weight:700; color:var(--text-muted); text-transform:uppercase; letter-spacing:0.1em; margin-bottom:8px;">Your Compatibility Score</div>
<div style="font-size:20px; font-weight:500; color:var(--text-secondary);">{selected_domain}</div>
<div style="font-size:64px; font-weight:800; color:{color}; line-height:1; margin:16px 0;">{match_pct}%</div>
<div style="display:inline-flex; align-items:center; gap:8px; padding:6px 16px; background:{color}11; color:{color}; border-radius:999px; font-weight:600; font-size:14px;">
⏱ {target.get('timeline','N/A')} to job-ready
</div>
</div>
""", unsafe_allow_html=True)

            col_p, col_c = st.columns(2)
            with col_p:
                pros_html = "".join([f'<div class="insight-item" style="font-size:13px;"><span>{p}</span></div>' for p in target.get("pros", [])])
                st.markdown(f"""
<div class="dcr-root mcard dcr-animate" style="border-left:4px solid var(--accent-green); height:auto;">
    <div style="font-weight:700; color:var(--accent-green); margin-bottom:12px;">✅ Pros</div>
    {pros_html}
</div>""", unsafe_allow_html=True)
            with col_c:
                cons_html = "".join([f'<div class="insight-item" style="font-size:13px;"><span>{c}</span></div>' for c in target.get("cons", [])])
                st.markdown(f"""
<div class="dcr-root mcard dcr-animate" style="border-left:4px solid var(--accent-red); height:auto;">
    <div style="font-weight:700; color:var(--accent-red); margin-bottom:12px;">⚠️ Cons</div>
    {cons_html}
</div>""", unsafe_allow_html=True)

            st.markdown("<div class='dcr-root' style='margin-top:24px; font-weight:700;'>Why this score?</div>", unsafe_allow_html=True)
            for r in target.get("reasoning", []):
                st.markdown(
                    f'<div class="dcr-root insight-item dcr-animate"><span class="insight-icon">→</span><span style="font-size:14px;">{r}</span></div>',
                    unsafe_allow_html=True,
                )
        else:
            st.error("Could not score this domain. Ensure Flask API is running.")

# ---------------------------------------------------------------------------
# MAIN ENTRY POINT
# ---------------------------------------------------------------------------

def render_domain_confusion_resolver():
    _inject_styles()

    st.markdown("""
<div style="position: absolute; top: 20px; right: 30px; 
            background: #f59e0b; color: white; padding: 6px 14px; 
            border-radius: 20px; font-size: 13px; font-weight: 600; 
            box-shadow: 0 2px 8px rgba(245,158,11,0.3);">
    🛠 Beta Version • Analytics may not be 100% accurate
</div>
""", unsafe_allow_html=True)

    st.markdown("""<div class="dcr-root dcr-page-header dcr-animate" style="background:var(--dcr-gradient-primary); padding:60px 40px; border-radius:32px; color:white !important; text-align:center; margin-bottom:40px; box-shadow:0 20px 40px -15px rgba(79,70,229,0.3);">
<h1 style="color:white !important; font-size:42px; font-weight:800; margin:0;">🎯 Domain Confusion Resolver</h1>
<p style="font-size:18px; opacity:0.9; max-width:700px; margin:20px auto 0; line-height:1.6;">Stop the guesswork. Get a data-backed career path designed for the Indian job market. Analyze demand, competition, and growth in seconds.</p>
</div>""", unsafe_allow_html=True)

    # ── Phase 3: Path 2 killed — single first-class experience ──────────────
    # "I Know My Domain" redirects to Skill Gap Analyzer (already in project).
    # Path 1 is the only entry point here.
    st.markdown("""
<div class="dcr-root" style="display:flex; align-items:center; gap:12px; padding:10px 16px;
     background:rgba(79,70,229,0.06); border:1px solid rgba(79,70,229,0.18);
     border-radius:10px; margin-bottom:20px; font-size:14px;">
<span style="font-size:20px;">💡</span>
<span style="color:var(--color-text-secondary);">
Already know your domain?
<strong style="color:var(--accent-indigo);">Use the Skill Gap Analyzer</strong>
to see exactly what you're missing and get a learning roadmap.
</span>
</div>
""", unsafe_allow_html=True)

    render_path_1_flow()

# ---------------------------------------------------------------------------
# Standalone execution
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    st.set_page_config(
        page_title="Domain Confusion Resolver",
        page_icon="🎯",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    render_domain_confusion_resolver()