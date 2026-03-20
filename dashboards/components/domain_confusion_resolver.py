import streamlit as st
import plotly.graph_objects as go
from typing import Dict, Any, List
import pandas as pd

# --- Analytics imports ---
from src.recommender.rule_based_recommendation_engine import DomainRecommendationEngine
from src.recommender.knowledge_base_store.knowledge_base import ALL_DOMAINS

from dashboards.utils.pipeline_loader import (
    run_domain_analytics,
    run_profile_analytics,
)

# ---------------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------------
DATA_PATH = r"D:\DATA SCIENCE AND ML\Project\job_trend_predictor\data\processed\cleaned\cleaned_job_data.csv"

DOMAIN_OPTIONS   = ALL_DOMAINS
LOCATION_OPTIONS = ["Jaipur", "Bangalore", "Hyderabad", "Pune", "Delhi NCR"]

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
        "Low":    ("🟢", "var(--accent-green)", "green"),
        "Medium": ("🟡", "var(--accent-amber)", "amber"),
        "High":   ("🔴", "var(--accent-red)",   "red"),
    }
    return badges.get(level, ("⚪", "var(--text-muted)", "indigo"))

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

@st.cache_data(show_spinner=False)
def _load_dataframe(path: str) -> pd.DataFrame:
    return pd.read_csv(path)



def fetch_domain_analytics(domain: str, location: str = "Jaipur") -> dict | None:
    """
    Calls the analytics pipeline and maps raw engine output to the exact shape
    that render_market_reality_card() expects.

    """
    df = st.session_state.get("df")
    if df is None:
        st.error("Data not loaded. Please refresh the page.")
        return None

    experience_band = (0, 3)

    try:
        results = run_domain_analytics(
            df=df,
            domain=domain,
            experience_band=experience_band,
            location=location,
            global_results=st.session_state.get("global_analytics"),
        )
        # ROOT-FIX: store raw Phase-2 results so render_growth_trajectory_card()
        # and render_real_talk_section() can read role_evolution, salary_growth,
        # ai_risk, stability from session_state["domain_analytics"] — without this
        # those functions always fall back to hardcoded static content.
        st.session_state["domain_analytics"] = results
    except Exception as e:
        st.error(f"Error fetching analytics for **{domain}**: {e}")
        return None

    # ── Global market demand (Phase 1 cache) ────────────────────────────────
    global_md    = st.session_state.get("global_analytics", {}).get("market_demand", {})
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

    # ── Assemble final payload ───────────────────────────────────────────────
    return {
        "domain":       domain,
        "location":     location,
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

# ---------------------------------------------------------------------------
# MARKET REALITY CARD
# ---------------------------------------------------------------------------

def render_market_reality_card(domain_data: Dict[str, Any], gauge_key_suffix: str = ""):
    """
    Renders the full market reality card for a domain.

    Parameters
    ----------
    domain_data      : dict returned by fetch_domain_analytics()
    gauge_key_suffix : extra string appended to the plotly chart key so that
                       callers rendering the same domain+location twice in one
                       script run each get a unique widget key.
    """
    _inject_styles()
    location = domain_data.get("location", "Jaipur")

    # ── Header ──────────────────────────────────────────────────────────────
    st.markdown(f"""
    <div class="market-header dcr-animate">
        <h2>📊 Market Reality: {domain_data['domain']}</h2>
        <div class="loc">📍 {location}</div>
    </div>
    """, unsafe_allow_html=True)

    # ── Row 1: Demand & Competition ─────────────────────────────────────────
    col1, col2 = st.columns(2)
    with col1:
        demand_score = domain_data.get("demand_score", 0)
        trend_icon   = get_trend_indicator(domain_data.get("trend_score", 5.0))
        if demand_score >= 7:
            d_color, d_pill, d_label = "var(--accent-green)", "pill-green", "High Demand"
        elif demand_score >= 4:
            d_color, d_pill, d_label = "var(--accent-amber)", "pill-amber", "Moderate Demand"
        else:
            d_color, d_pill, d_label = "var(--accent-red)", "pill-red", "Low Demand"

        vol        = domain_data.get("breakdown", {}).get("Volume", 0)
        entry_flex = domain_data.get("breakdown", {}).get("Entry_Flexibility", 0)

        st.markdown(f"""
        <div class="mcard dcr-animate">
            <div class="mcard-title">Market Demand Score</div>
            <div class="mcard-value" style="color:{d_color};">
                {demand_score:.1f}
                <span class="unit">/10</span>
                <span class="trend-arrow">{trend_icon}</span>
            </div>
            <div style="margin-top:12px;">
                <span class="pill {d_pill}">{d_label}</span>
            </div>
            <div class="mcard-sub">
                Volume: <strong>{vol:.1f}</strong> · Entry flexibility: <strong>{entry_flex:.1f}</strong>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        comp       = domain_data.get("competition", {})
        level      = comp.get("level", "Medium")
        emoji, color, pill_cls = get_competition_badge(level)
        cands      = comp.get("candidates_per_job", 0)
        c_idx      = comp.get("index", 0)

        st.markdown(f"""
        <div class="mcard dcr-animate">
            <div class="mcard-title">Competition Level</div>
            <div class="mcard-value sm" style="color:{color};">
                {emoji} {level}
            </div>
            <div style="margin-top:12px;">
                <span class="pill pill-{pill_cls}">Index: {c_idx:.3f}</span>
            </div>
            <div class="mcard-sub">
                ~<strong>{cands:,}</strong> candidates per open position
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ── Row 2: Salary ────────────────────────────────────────────────────────
    sal      = domain_data.get("salary", {})
    low      = sal.get("low",    0)
    median   = sal.get("median", 0)
    high     = sal.get("high",   0)
    loc_adj  = sal.get("location_adjusted", median)
    bar_pct  = min(100, round((loc_adj / high * 100) if high > 0 else 50))

    st.markdown(f"""
    <div class="mcard dcr-animate">
        <div class="mcard-title">💰 Average Fresher Salary Range</div>
        <div class="mcard-value sm" style="color:var(--accent-teal);">
            ₹{low:.1f} – ₹{high:.1f}
            <span class="unit" style="font-family:'Outfit',sans-serif;">LPA</span>
        </div>
        <div class="salary-bar-track">
            <div class="salary-bar-fill" style="width:{bar_pct}%;"></div>
        </div>
        <div class="salary-labels">
            <span>₹{low:.1f}L</span>
            <span>₹{median:.1f}L (national median)</span>
            <span>₹{high:.1f}L</span>
        </div>
        <div class="loc-chip">
            📍 {location} median: ₹{loc_adj:.2f} LPA
        </div>
    </div>
    """, unsafe_allow_html=True)

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
                '<div class="mcard dcr-animate">'
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
                '<div class="mcard dcr-animate">'
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
            <div class="mcard dcr-animate">
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
            <div class="mcard dcr-animate">
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
            <div class="mshare-bar dcr-animate">
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
    <div class="sat-card dcr-animate" style="border:{s_border}; background:{s_bg};">
        <div class="mcard-title">⚠️ Market Saturation Risk</div>
        <div class="sat-risk-header">
            <span class="icon">{s_emoji}</span>
            <div>
                <div class="risk-name" style="color:{s_color};">{risk_level}</div>
                <div class="risk-score">
                    Saturation score: <span style="font-family:'IBM Plex Mono';font-weight:700;font-size:17px;color:{s_color};">{sat_score:.2f}</span> / 1.0
                </div>
            </div>
        </div>
        <div class="sat-breakdown">
            <div class="sat-bd-item">
                <div class="bd-label">Demand Trend</div>
                <div class="bd-value">{sat.get('signals', {}).get('Demand_Trend', 'N/A')}</div>
            </div>
            <div class="sat-bd-item">
                <div class="bd-label">Experience Barrier</div>
                <div class="bd-value">{sat.get('signals', {}).get('Experience_Barrier', 'N/A')}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Plotly Gauge ─────────────────────────────────────────────────────────
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=sat_score * 100,
        title={"text": "Market Saturation Level", "font": {"size": 17, "family": "Outfit"}},
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
    <div class="dcr-divider">
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
        <div class="insight-item dcr-animate">
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
    elif r_score >= 20:
        diff_level, diff_score, diff_color = "Medium-High", round((100 - r_score) / 10, 1), "amber"
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
    <div class="market-header dcr-animate" style="margin-top:32px;">
        <h2>⚡ Entry Barrier — {domain}</h2>
        <div class="loc">How hard is it to actually break in?</div>
    </div>
    """, unsafe_allow_html=True)

    cols = st.columns(3)
    with cols[0]:
        timeline_card = (
            '<div class="mcard">'
            '<div class="mcard-title">⏱️ Time to Job-Ready (core skills only)</div>'

            # 20h/wk row — highlighted as the realistic primary
            '<div style="display:flex; justify-content:space-between; align-items:center; '
            'padding:10px 14px; background:rgba(79,70,229,0.07); border-radius:10px; '
            'border:1px solid rgba(79,70,229,0.18); margin:10px 0;">'
            '<div>'
            '<div style="font-size:13px; font-weight:700; color:var(--accent-indigo);">20 hrs/week</div>'
            '<div style="font-size:11px; color:var(--text-muted);">Realistic student pace</div>'
            '</div>'
            f'<div style="font-family:\'IBM Plex Mono\'; font-weight:700; font-size:26px; '
            f'color:var(--accent-indigo);">{pace_20_display}</div>'
            '</div>'

            # 30h/wk row
            '<div style="display:flex; justify-content:space-between; align-items:center; '
            'padding:8px 14px; background:rgba(5,150,105,0.07); border-radius:10px; '
            'border:1px solid rgba(5,150,105,0.15); margin-bottom:8px;">'
            '<div>'
            '<div style="font-size:13px; font-weight:700; color:var(--accent-green);">30 hrs/week</div>'
            '<div style="font-size:11px; color:var(--text-muted);">Dedicated / bootcamp pace</div>'
            '</div>'
            f'<div style="font-family:\'IBM Plex Mono\'; font-weight:700; font-size:22px; '
            f'color:var(--accent-green);">{pace_30_display}</div>'
            '</div>'

            # 10h/wk reference (dimmed — just for reference)
            '<div style="display:flex; justify-content:space-between; padding:4px 14px; '
            'opacity:0.55;">'
            '<span style="font-size:12px; color:var(--text-muted);">10 hrs/week (reference only)</span>'
            f'<span style="font-family:\'IBM Plex Mono\'; font-size:13px; '
            f'color:var(--text-muted);">{pace_10_display}</span>'
            '</div>'

            f'<div class="mcard-sub" style="margin-top:10px; font-size:12px;">{timeline_sub}</div>'
            '</div>'
        )
        st.markdown(timeline_card, unsafe_allow_html=True)

    with cols[1]:
        st.markdown(f"""
        <div class="mcard">
            <div class="mcard-title">📋 Prerequisites</div>
            <div style="font-size:15px; line-height:1.55; margin:12px 0; color:var(--text-secondary);">
                {prereq_text}
            </div>
        </div>
        """, unsafe_allow_html=True)

    with cols[2]:
        st.markdown(f"""
        <div class="mcard">
            <div class="mcard-title">📚 Project Complexity</div>
            <div style="font-size:17px; font-weight:700; color:var(--accent-red); margin:12px 0;">
                {project_display}
            </div>
        </div>
        """, unsafe_allow_html=True)

    col_dsa, col_dom = st.columns(2)
    with col_dsa:
        st.markdown(f"""
        <div class="mcard">
            <div class="mcard-title">💻 Interview Difficulty Index</div>
            <div class="mcard-value sm" style="color:var(--accent-red);">
                {interview_score}/10
            </div>
            <div class="mcard-sub">{interview_label}</div>
        </div>
        """, unsafe_allow_html=True)

    with col_dom:
        st.markdown(f"""
        <div class="mcard">
            <div class="mcard-title">🎯 Domain Knowledge Depth</div>
            <div class="mcard-value sm" style="color:var(--accent-amber);">
                {domain_score}/10
            </div>
            <div class="mcard-sub">system design + domain concepts matter</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="mcard" style="text-align:center;">
        <div class="mcard-title">Overall Entry Difficulty</div>
        <div class="mcard-value" style="color:var(--accent-{diff_color}); font-size:42px;">
            {diff_level}
        </div>
        <div class="mcard-sub">Difficulty score ≈ {diff_score}/10</div>
    </div>
    """, unsafe_allow_html=True)

    if hidden_blockers:
        st.markdown("""
        <div class="dcr-divider"><hr/><span>🚨 Hidden Blocker Alerts</span><hr/></div>
        """, unsafe_allow_html=True)
        for b in hidden_blockers:
            icon = "🟡" if b["type"] == "warning" else "🔴" if b["type"] == "critical" else "ℹ️"
            st.markdown(f"""
            <div class="insight-item">
                <span class="insight-icon">{icon}</span>
                <span>{b['text']}</span>
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
    <div class="market-header dcr-animate" style="margin-top:32px;">
        <h2>📈 Growth Trajectory — {domain}</h2>
        <div class="loc">What your career could look like in 5–10 years</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="mcard">
        <div class="mcard-title">Salary Progression (India — realistic percentiles from dataset)</div>
        <div style="display:grid; grid-template-columns:1fr 1fr; gap:16px; text-align:center; margin:20px 0;">
            <div>
                <div style="color:var(--text-muted);">0–2 years (Fresher → Junior)</div>
                <div style="font-size:24px; font-weight:700; color:var(--accent-teal);">
                    {sal_0_2_display}
                </div>
            </div>
            <div>
                <div style="color:var(--text-muted);">3–5 years (Mid-level)</div>
                <div style="font-size:24px; font-weight:700; color:var(--accent-indigo);">
                    {sal_3_5_display}
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""<div class="dcr-divider"><hr/><span>🎯 Typical Role Evolution</span><hr/></div>""", unsafe_allow_html=True)

    for i, (years_label, title, desc) in enumerate(role_path):
        # Build alternative paths line from live engine data
        # FIX: do NOT use single-quoted CSS inside an f-string — causes raw HTML to render
        alt_line = ""
        if evo_steps and i < len(evo_steps):
            alts = evo_steps[i].get("alternative_paths", [])
            if alts:
                parts = []
                for a in alts[:3]:
                    role_name = a.get("role", "").title()
                    prob      = a.get("probability", "")
                    parts.append(f"{role_name} ({prob})")
                alt_line = "↔ Alt paths: " + " · ".join(parts)

        # Build card HTML using a plain string (no nested quotes issue)
        alt_html = ""
        if alt_line:
            alt_html = (
                '<div style="font-size:12px; color:var(--text-muted); '
                'margin-top:6px; font-style:italic;">'
                + alt_line + "</div>"
            )

        card_html = (
            '<div class="mcard" style="margin-bottom:8px;">'
            '<div style="display:flex; justify-content:space-between; align-items:flex-start;">'
            '<div style="flex:1;">'
            f'<div style="font-size:20px; font-weight:600;">{title}</div>'
            f'<div style="color:var(--text-muted); font-size:14px;">{desc}</div>'
            + alt_html +
            "</div>"
            '<div style="font-family:\'IBM Plex Mono\'; color:var(--accent-indigo); '
            f'white-space:nowrap; margin-left:16px;">{years_label} yrs</div>'
            "</div></div>"
        )
        st.markdown(card_html, unsafe_allow_html=True)

        if i < len(role_path) - 1:
            st.markdown(
                "<div style='text-align:center; font-size:28px; "
                "color:var(--accent-indigo);'>↓</div>",
                unsafe_allow_html=True,
            )

    cols = st.columns(3)
    with cols[0]:
        st.markdown(f"""
        <div class="mcard" style="text-align:center;">
            <div class="mcard-title">Domain Stability</div>
            <div class="mcard-value" style="color:var(--accent-green);">{stab_score}/10</div>
            <div class="pill pill-green" style="margin:12px auto; display:inline-block;">{stab_rating}</div>
            <div class="mcard-sub">{stab_text}</div>
        </div>
        """, unsafe_allow_html=True)

    with cols[1]:
        st.markdown(f"""
        <div class="mcard" style="text-align:center;">
            <div class="mcard-title">Skill Transferability</div>
            <div class="mcard-value" style="color:var(--accent-teal);">{trans_score}/10</div>
            <div class="pill pill-green" style="margin:12px auto; display:inline-block;">{trans_label}</div>
            <div class="mcard-sub">{trans_path}</div>
        </div>
        """, unsafe_allow_html=True)

    with cols[2]:
        ai_color    = "var(--accent-amber)" if ai_risk_level == "Medium" else ("var(--accent-red)" if ai_risk_level == "High" else "var(--accent-green)")
        ai_pill_cls = "amber" if ai_risk_level == "Medium" else ("red" if ai_risk_level == "High" else "green")
        st.markdown(f"""
        <div class="mcard" style="text-align:center;">
            <div class="mcard-title">AI Replacement Risk</div>
            <div class="mcard-value sm" style="color:{ai_color};">{ai_risk_level}</div>
            <div class="pill pill-{ai_pill_cls}" style="margin:12px auto; display:inline-block;">
                Score: {ai_risk_score}/10
            </div>
            <div class="mcard-sub">{ai_risk_adv}</div>
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

    st.markdown(f"""
    <div class="market-header dcr-animate" style="margin-top:32px; background:linear-gradient(135deg,#7f1d1d 0%,#991b1b 100%);">
        <h2>🎯 Real Talk — {domain}</h2>
        <div class="loc">No motivational fluff. Just reality.</div>
    </div>
    """, unsafe_allow_html=True)

    if persona_name:
        persona_card = (
            '<div class="mcard" style="text-align:center; margin-bottom:4px;">'
            '<div class="mcard-title">Your Persona</div>'
            f'<div style="font-size:22px; font-weight:700; color:var(--accent-indigo);">'
            f'{persona_emoji} {persona_name}</div>'
            f'<div class="mcard-sub">{persona_tag}</div>'
            '</div>'
        )
        st.markdown(persona_card, unsafe_allow_html=True)

    if salary_ctx:
        st.markdown(
            f'<div class="mshare-bar dcr-animate" style="margin-bottom:12px;">'
            f'<span>{salary_ctx}</span></div>',
            unsafe_allow_html=True,
        )

    st.markdown(f"""
    <div class="sat-card" style="border:2px solid rgba(220,38,38,0.4); background:rgba(30,10,10,0.3);">
        <div style="color:var(--accent-red); font-size:18px; font-weight:700; margin-bottom:12px;">
            ⚠️ HARSH TRUTH
        </div>
        <div style="line-height:1.6;">{harsh}</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="sat-card" style="border:2px solid rgba(5,150,105,0.4); background:rgba(10,30,20,0.3); margin-top:16px;">
        <div style="color:var(--accent-green); font-size:18px; font-weight:700; margin-bottom:12px;">
            ✨ SILVER LINING
        </div>
        <div style="line-height:1.6;">{silver}</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""<div class="dcr-divider"><hr/><span>🚨 Common Beginner Traps</span><hr/></div>""", unsafe_allow_html=True)
    for t in traps:
        st.markdown(
            f'<div class="insight-item"><span class="insight-icon">⚠️</span>'
            f'<span>{t}</span></div>',
            unsafe_allow_html=True,
        )

    st.markdown("""<div class="dcr-divider"><hr/><span>✅ Patterns of People Who Actually Make It</span><hr/></div>""", unsafe_allow_html=True)
    for p in patterns:
        st.markdown(
            f'<div class="insight-item"><span class="insight-icon">→</span>'
            f'<span>{p}</span></div>',
            unsafe_allow_html=True,
        )

    st.markdown(f"""
    <div class="mcard" style="margin-top:24px; text-align:center;">
        <div class="mcard-title">⏳ Realistic Success Timeline</div>
        <div style="font-size:18px; color:var(--accent-indigo); margin:16px 0; font-weight:600; line-height:1.5;">
            {timeline}
        </div>
    </div>
    """, unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# COMPLETE ANALYSIS
# ---------------------------------------------------------------------------

def render_complete_domain_analysis(
    domain: str,
    location: str,
    user_profile: Dict[str, Any] = None,
    skip_market_card: bool = False,
):
    """
    Renders the full domain breakdown.

    Parameters
    ----------
    skip_market_card : set True when the market reality card has already been
                       rendered in the same script run.  Prevents duplicate widget
                       key error from the Plotly gauge.
    """
    with st.spinner(f"Loading comprehensive analysis for {domain}..."):
        market_data = fetch_domain_analytics(domain, location)
        # Also run Phase 3 (profile analytics) so entry_barrier / growth /
        # real_talk sections have live data instead of static fallbacks.
        # Only run if profile_analytics isn't already set for this domain.
        existing_profile = st.session_state.get("profile_analytics") or {}
        existing_domain  = existing_profile.get("career_path", {}).get("Target_Domain", "")

        if existing_domain.lower() != domain.lower():
            df = st.session_state.get("df")
            if df is not None:
                try:
                    skills = (user_profile or {}).get("skills", [])

                    # FIX: normalise math_comfort ("Weak"/"Moderate"/"Strong") →
                    # prior_knowledge ("none"/"basic"/"intermediate"/"advanced")
                    # Phase 3 engines only recognise the second set of values.
                    _MATH_TO_PRIOR = {
                        "weak":         "none",
                        "moderate":     "basic",
                        "strong":       "intermediate",
                        "none":         "none",
                        "basic":        "basic",
                        "intermediate": "intermediate",
                        "advanced":     "advanced",
                    }
                    raw_math = str((user_profile or {}).get("math_comfort", "basic")).lower()
                    prior    = _MATH_TO_PRIOR.get(raw_math, "basic")

                    profile_results = run_profile_analytics(
                        df=df,
                        domain=domain,
                        experience_band=(0, 3),
                        location=location,
                        user_skills=skills,
                        prior_knowledge=prior,
                        user_project_stats={},
                        domain_results=st.session_state.get("domain_analytics", {}),
                    )
                    st.session_state["profile_analytics"] = profile_results
                except Exception:
                    pass  # silently fall back — render functions handle missing data

    if market_data:
        if not skip_market_card:
            render_market_reality_card(market_data, gauge_key_suffix="_full")
        render_entry_barrier_card(domain, user_profile)
        render_growth_trajectory_card(domain)
        render_real_talk_section(domain)
    else:
        st.error(f"Could not load data for {domain}")

# ---------------------------------------------------------------------------
# PATH 1 – Help Me Decide
# ---------------------------------------------------------------------------

def render_path_1_flow():
    
    st.markdown("""
    <div class="dcr-section-title">
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
        with st.spinner("Analysing your profile against live market signals…"):
            try:
                df = st.session_state.get("df")
                if df is None:
                    st.error("Data not loaded. Please refresh the page.")
                    st.stop()
                engine = DomainRecommendationEngine(df)
                st.session_state.p1_recommendations = engine.get_recommendations(user_profile, top_n=3)
            except Exception as e:
                st.error(f"Recommendation engine error: {e}")
                st.session_state.p1_recommendations = None

    if st.session_state.p1_recommendations:
        st.markdown("""
        <div class="dcr-section-title">
            <span class="step-badge">STEP 02</span> Your Top Domain Matches
        </div>
        """, unsafe_allow_html=True)

        recs  = st.session_state.p1_recommendations
        cols  = st.columns(len(recs))

        for i, rec in enumerate(recs):
            with cols[i]:
                match_pct    = rec.get("match_percentage", 0)
                color        = (
                    "var(--accent-green)" if match_pct >= 65
                    else "var(--accent-amber)" if match_pct >= 40
                    else "var(--accent-red)"
                )
                reasons_html = "".join(f"<li>{r}</li>" for r in rec.get("reasoning", []))

                st.markdown(f"""
                <div class="rec-card dcr-animate">
                    <div class="domain-name">{rec['domain']}</div>
                    <div class="match-pct" style="color:{color};">{match_pct}%</div>
                    <div class="match-label">Match Score</div>
                    <div class="timeline">⏱ {rec.get('timeline', 'N/A')}</div>
                    <div class="salary-tag">
                        {rec.get('market_metrics', {}).get('avg_starting_salary', '')}
                    </div>
                    <ul class="reason-list">{reasons_html}</ul>
                </div>
                """, unsafe_allow_html=True)

                if st.button(f"📊 Analyse {rec['domain']}", key=f"p1_btn_{i}", use_container_width=True):
                    st.session_state.p1_selected_domain = rec["domain"]
                    st.rerun()

    if st.session_state.p1_selected_domain:
        st.markdown(f"""
        <div class="dcr-section-title">
            <span class="step-badge">STEP 03</span>
            Deep Analysis — {st.session_state.p1_selected_domain}
        </div>
        """, unsafe_allow_html=True)

        user_profile = {
            "experience":   st.session_state.get("p1_exp",  "Fresher"),
            "skills":       st.session_state.get("p1_int",  []),
            "location":     st.session_state.p1_location,
            "math_comfort": st.session_state.get("p1_math", "Moderate"),
        }

        render_complete_domain_analysis(
            domain=st.session_state.p1_selected_domain,
            location=st.session_state.p1_location,
            user_profile=user_profile,
            skip_market_card=False,
        )

# ---------------------------------------------------------------------------
# PATH 2 – I Know My Domain
# ---------------------------------------------------------------------------

def render_path_2_flow():
    _inject_styles()

    st.markdown("""
    <div class="dcr-section-title">
        <span class="step-badge">STEP 01</span> Explore Market Reality
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([2, 1])
    with col1:
        selected_domain = st.selectbox("Choose Domain", DOMAIN_OPTIONS, key="p2_dom")
    with col2:
        location = st.selectbox("Location", LOCATION_OPTIONS, key="p2_loc")

    if st.button("📊 Load Analytics", type="primary", key="p2_load_btn", use_container_width=True):
        with st.spinner(f"Fetching market data for {selected_domain} in {location}…"):
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
        <div class="dcr-section-title" style="margin-top:40px;">
            📈 Want the Full Picture?
        </div>
        """, unsafe_allow_html=True)

        # ── Inline profile form — needed so Phase 3 has real user data ──────
        # Without this, Entry Barrier / Real Talk / Growth all show generic
        # content because they have no skills to compare against.
        st.markdown("""
        <div class="mcard" style="margin-bottom:16px;">
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
        <div class="dcr-section-title" style="margin-top:32px;">
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
        <div class="mcard-title" style="margin-bottom:12px; font-size:15px; text-transform:none; letter-spacing:0; color:var(--text-secondary);">
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
        with st.spinner("Calculating compatibility…"):
            try:
                df     = _load_dataframe(DATA_PATH)
                engine = DomainRecommendationEngine(df)
                all_recs = engine.get_recommendations(user_profile, top_n=len(engine.domains))
                target   = next((r for r in all_recs if r["domain"] == selected_domain), None)

                if target:
                    match_pct = target["match_percentage"]
                    color     = "#059669" if match_pct >= 65 else "#d97706" if match_pct >= 40 else "#dc2626"

                    st.markdown(f"""
                    <div class="compat-result dcr-animate">
                        <div class="cr-label">Your compatibility with</div>
                        <div class="cr-domain">{selected_domain}</div>
                        <div class="cr-pct" style="color:{color};">{match_pct}%</div>
                        <div style="margin-top:14px;">
                            <span class="pill" style="background:rgba(0,0,0,0.05); color:{color}; font-size:15px;">
                                ⏱ {target.get('timeline','N/A')} to job-ready
                            </span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                    col_p, col_c = st.columns(2)
                    with col_p:
                        st.markdown("**✅ Pros**")
                        for p in target.get("pros", []):
                            st.markdown(f'<div class="insight-item"><span class="insight-icon">✅</span><span>{p}</span></div>', unsafe_allow_html=True)
                    with col_c:
                        st.markdown("**⚠️ Cons**")
                        for c in target.get("cons", []):
                            st.markdown(f'<div class="insight-item"><span class="insight-icon">⚠️</span><span>{c}</span></div>', unsafe_allow_html=True)

                    st.markdown("**Why this score:**")
                    for r in target.get("reasoning", []):
                        st.markdown(f'<div class="insight-item dcr-animate"><span class="insight-icon">→</span><span>{r}</span></div>', unsafe_allow_html=True)
                else:
                    st.warning(f"Could not score {selected_domain} for your profile.")
            except Exception as e:
                st.error(f"Compatibility engine error: {e}")

# ---------------------------------------------------------------------------
# MAIN ENTRY POINT
# ---------------------------------------------------------------------------

def render_domain_confusion_resolver():
    _inject_styles()

    st.markdown("""
    <div class="dcr-page-header dcr-animate">
        <h1>🎯 Domain Confusion Resolver</h1>
        <p>Get clarity on which domain suits you best — based on real market data, competition levels, and salary expectations.</p>
    </div>
    """, unsafe_allow_html=True)

    if "path_choice" not in st.session_state:
        st.session_state.path_choice = None

    is_p1 = st.session_state.path_choice == "help_me_decide"
    is_p2 = st.session_state.path_choice == "know_my_domain"

    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("🤔 Help Me Decide", use_container_width=True, type="primary" if is_p1 else "secondary", key="btn_p1"):
            st.session_state.path_choice = "help_me_decide"
            st.rerun()

    with col_b:
        if st.button("🚀 I Know My Domain", use_container_width=True, type="primary" if is_p2 else "secondary", key="btn_p2"):
            st.session_state.path_choice = "know_my_domain"
            st.rerun()

    st.divider()

    if is_p1:
        render_path_1_flow()
    elif is_p2:
        render_path_2_flow()
    else:
        st.markdown("""
        <div class="insight-item dcr-animate" style="justify-content:center; text-align:center; padding:30px; font-size:17px; margin-top:12px;">
            <span class="insight-icon">👆</span>
            <span>Select a path above to begin your career analysis.</span>
        </div>
        """, unsafe_allow_html=True)

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