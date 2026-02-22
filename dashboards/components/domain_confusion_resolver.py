"""
domain_confusion_resolver.py
Streamlit UI component for the Domain Confusion Resolver feature.
Provides two user paths:
  Path 1 – Help Me Decide  : Form → AI Recommendations → Full Analysis
  Path 2 – I Know My Domain: Domain select → Market Reality → (Optional) Full Analysis
"""

import streamlit as st
import plotly.graph_objects as go
import uuid
from typing import Dict, Any, List
import pandas as pd

# --- Analytics imports ---
from src.analytics.market_analysis.average_salary_calculator import AverageSalaryRangeCalculator
from src.analytics.market_analysis.demand_score_calculator import MarketDemandEngine
from src.analytics.market_analysis.job_market_velocity_calculator import JobMarketVelocityCalculator
from src.analytics.market_analysis.competition_level_calculator import CompetitionLevelCalculator
from src.analytics.market_analysis.saturation_risk_indicator import SaturationRiskIndicator

from src.recommender.rule_based_recommendation_engine import DomainRecommendationEngine
from src.recommender.knowledge_base_store.knowledge_base import ALL_DOMAINS

from src.analytics.career_insights.career_path_engine import CareerPathEngine
from src.analytics.career_insights.role_evaluation_engine import RoleEvolutionEngine

from src.analytics.entry_barriers.project_complexity_evaluator import ProjectComplexityEvaluator
from src.analytics.entry_barriers.hidden_blocker_detector import HiddenBlockerDetector
from src.analytics.entry_barriers.interview_difficulty_engine import InterviewDifficultyEngine
from src.analytics.entry_barriers.prequisite_engine import PrerequisiteEngine

from src.analytics.domain_analysis.ai_replacement_risk_engine import AIReplacementRiskEngine
from src.analytics.domain_analysis.domain_stability_engine import DomainStabilityEngine
from src.analytics.domain_analysis.salary_growth_engine import SalaryGrowthEngine
from src.analytics.domain_analysis.skill_transferability_engine import SkillTransferabilityEngine

from src.analytics.real_talk.adaptive_real_talk_engine import AdaptiveRealTalkEngine

# ---------------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------------
DATA_PATH = r"D:\DATA SCIENCE AND ML\Project\job_trend_predictor\data\processed\cleaned\cleaned_job_data.csv"

DOMAIN_OPTIONS = ALL_DOMAINS
LOCATION_OPTIONS = ["Jaipur", "Bangalore", "Hyderabad", "Pune", "Delhi NCR"]

# ---------------------------------------------------------------------------
# GLOBAL STYLES
# ---------------------------------------------------------------------------

_GLOBAL_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=IBM+Plex+Mono:wght@400;600;700&family=Outfit:wght@300;400;500;600;700&display=swap');

/* ── Light-mode tokens ── */
:root {
    --bg-card:         rgba(255,255,255,0.75);
    --bg-card-alt:     rgba(245,247,255,0.82);
    --border-card:     rgba(99,102,241,0.18);
    --shadow-card:     0 4px 24px rgba(79,70,229,0.09), 0 1px 4px rgba(0,0,0,0.05);
    --shadow-hover:    0 12px 36px rgba(79,70,229,0.18), 0 2px 8px rgba(0,0,0,0.07);
    --text-primary:    #0f172a;
    --text-secondary:  #475569;
    --text-muted:      #94a3b8;
    --accent-indigo:   #4f46e5;
    --accent-teal:     #0d9488;
    --accent-amber:    #d97706;
    --accent-red:      #dc2626;
    --accent-green:    #059669;
    --divider:         rgba(99,102,241,0.12);
    --tag-bg:          rgba(79,70,229,0.07);
    --header-grad:     linear-gradient(135deg,#1e1b4b 0%,#312e81 50%,#1e40af 100%);
}

/* ── Dark-mode tokens ── */
[data-theme="dark"],
.stApp[data-theme="dark"] {
    --bg-card:         rgba(22,20,60,0.60) !important;
    --bg-card-alt:     rgba(10,15,35,0.68) !important;
    --border-card:     rgba(129,140,248,0.22) !important;
    --shadow-card:     0 4px 24px rgba(0,0,0,0.42), 0 1px 4px rgba(0,0,0,0.30) !important;
    --shadow-hover:    0 12px 40px rgba(99,102,241,0.35), 0 2px 8px rgba(0,0,0,0.40) !important;
    --text-primary:    #f1f5f9 !important;
    --text-secondary:  #94a3b8 !important;
    --text-muted:      #64748b !important;
    --accent-indigo:   #818cf8 !important;
    --accent-teal:     #2dd4bf !important;
    --accent-amber:    #fbbf24 !important;
    --accent-red:      #f87171 !important;
    --accent-green:    #34d399 !important;
    --divider:         rgba(129,140,248,0.15) !important;
    --tag-bg:          rgba(129,140,248,0.10) !important;
    --header-grad:     linear-gradient(135deg,#0f172a 0%,#1e1b4b 50%,#162440 100%) !important;
}

/* OS dark mode fallback */
@media (prefers-color-scheme: dark) {
    :root {
        --bg-card:         rgba(22,20,60,0.60);
        --bg-card-alt:     rgba(10,15,35,0.68);
        --border-card:     rgba(129,140,248,0.22);
        --shadow-card:     0 4px 24px rgba(0,0,0,0.42), 0 1px 4px rgba(0,0,0,0.30);
        --shadow-hover:    0 12px 40px rgba(99,102,241,0.35), 0 2px 8px rgba(0,0,0,0.40);
        --text-primary:    #f1f5f9;
        --text-secondary:  #94a3b8;
        --text-muted:      #64748b;
        --accent-indigo:   #818cf8;
        --accent-teal:     #2dd4bf;
        --accent-amber:    #fbbf24;
        --accent-red:      #f87171;
        --accent-green:    #34d399;
        --divider:         rgba(129,140,248,0.15);
        --tag-bg:          rgba(129,140,248,0.10);
        --header-grad:     linear-gradient(135deg,#0f172a 0%,#1e1b4b 50%,#162440 100%);
    }
}

/* ── Page header ── */
.dcr-page-header {
    padding: 36px 32px 28px;
    background: var(--header-grad);
    border-radius: 20px;
    margin-bottom: 28px;
    position: relative;
    overflow: hidden;
}
.dcr-page-header::before {
    content:'';
    position:absolute; top:-50px; right:-50px;
    width:220px; height:220px;
    background:radial-gradient(circle,rgba(165,180,252,0.22) 0%,transparent 70%);
    border-radius:50%; pointer-events:none;
}
.dcr-page-header h1 {
    font-family:'DM Serif Display',serif;
    font-size: 40px;
    color: #ffffff;
    margin: 0 0 10px;
    line-height: 1.15;
    letter-spacing: -0.4px;
}
.dcr-page-header p {
    font-family:'Outfit',sans-serif;
    font-size: 18px;
    color: rgba(199,210,254,0.90);
    margin: 0;
    font-weight: 300;
    max-width: 600px;
    line-height: 1.65;
}

/* ── Section titles ── */
.dcr-section-title {
    font-family:'DM Serif Display',serif;
    font-size: 26px;
    color: var(--text-primary);
    margin: 28px 0 18px;
    letter-spacing: -0.2px;
    display: flex;
    align-items: center;
    gap: 12px;
}
.step-badge {
    font-family:'IBM Plex Mono',monospace;
    font-size: 12px;
    font-weight: 700;
    color: var(--accent-indigo);
    background: var(--tag-bg);
    padding: 4px 11px;
    border-radius: 20px;
    letter-spacing: 0.6px;
    border: 1px solid var(--border-card);
}

/* ── Glass metric card ── */
.mcard {
    background: var(--bg-card);
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
    border: 1px solid var(--border-card);
    border-radius: 18px;
    padding: 24px 26px;
    margin: 10px 0;
    box-shadow: var(--shadow-card);
    transition: transform 0.22s ease, box-shadow 0.22s ease;
    position: relative;
    overflow: hidden;
}
.mcard::before {
    content:'';
    position:absolute; top:0; left:0; right:0;
    height: 3px;
    background: linear-gradient(90deg,var(--accent-indigo),var(--accent-teal));
    border-radius: 18px 18px 0 0;
    opacity: 0;
    transition: opacity 0.22s ease;
}
.mcard:hover { transform:translateY(-3px); box-shadow:var(--shadow-hover); }
.mcard:hover::before { opacity:1; }

.mcard-title {
    font-family:'Outfit',sans-serif;
    font-size: 13px;
    font-weight: 700;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.9px;
    margin-bottom: 14px;
}
.mcard-value {
    font-family:'IBM Plex Mono',monospace;
    font-size: 48px;
    font-weight: 700;
    color: var(--text-primary);
    line-height: 1;
    display: flex;
    align-items: baseline;
    gap: 6px;
}
.mcard-value .unit {
    font-size: 20px;
    color: var(--text-muted);
    font-weight: 400;
}
.mcard-value.sm { font-size: 36px; }
.mcard-label {
    font-family:'Outfit',sans-serif;
    font-size: 16px;
    font-weight: 500;
    color: var(--text-secondary);
    margin-top: 8px;
}
.mcard-sub {
    font-family:'Outfit',sans-serif;
    font-size: 14px;
    color: var(--text-muted);
    margin-top: 10px;
    line-height: 1.6;
}
.trend-arrow {
    font-size: 26px;
    margin-left: 8px;
    vertical-align: middle;
}

/* ── Status pill ── */
.pill {
    display: inline-block;
    padding: 5px 14px;
    border-radius: 50px;
    font-family:'Outfit',sans-serif;
    font-size: 13px;
    font-weight: 600;
    letter-spacing: 0.3px;
}
.pill-green  { background:rgba(5,150,105,0.12);  color:var(--accent-green);  border:1px solid rgba(5,150,105,0.25); }
.pill-amber  { background:rgba(217,119,6,0.12);  color:var(--accent-amber);  border:1px solid rgba(217,119,6,0.25); }
.pill-red    { background:rgba(220,38,38,0.12);  color:var(--accent-red);    border:1px solid rgba(220,38,38,0.25); }
.pill-indigo { background:var(--tag-bg);          color:var(--accent-indigo); border:1px solid var(--border-card); }

/* ── Salary bar ── */
.salary-bar-track {
    height: 8px;
    background: var(--divider);
    border-radius: 8px;
    position: relative;
    overflow: hidden;
    margin: 14px 0 6px;
}
.salary-bar-fill {
    position:absolute; left:0; top:0; bottom:0;
    background: linear-gradient(90deg,var(--accent-teal),var(--accent-indigo));
    border-radius: 8px;
    transition: width 0.7s cubic-bezier(0.4,0,0.2,1);
}
.salary-labels {
    display: flex;
    justify-content: space-between;
    font-family:'IBM Plex Mono',monospace;
    font-size: 13px;
    color: var(--text-muted);
}

/* ── Location chip ── */
.loc-chip {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 8px 18px;
    background: linear-gradient(135deg,rgba(13,148,136,0.12) 0%,rgba(79,70,229,0.07) 100%);
    border: 1px solid rgba(13,148,136,0.28);
    border-radius: 50px;
    font-family:'IBM Plex Mono',monospace;
    font-size: 15px;
    font-weight: 600;
    color: var(--accent-teal);
    margin-top: 14px;
}

/* ── Market header band ── */
.market-header {
    background: var(--header-grad);
    padding: 26px 30px 22px;
    border-radius: 20px 20px 0 0;
    margin-top: 26px;
    position: relative;
    overflow: hidden;
}
.market-header::after {
    content:'';
    position:absolute; bottom:-20px; right:-20px;
    width:150px; height:150px;
    background:radial-gradient(circle,rgba(99,102,241,0.28) 0%,transparent 70%);
    border-radius:50%; pointer-events:none;
}
.market-header h2 {
    font-family:'DM Serif Display',serif;
    font-size: 30px;
    color: #fff;
    margin: 0 0 8px;
    letter-spacing: -0.2px;
}
.market-header .loc {
    font-family:'Outfit',sans-serif;
    font-size: 16px;
    color: rgba(199,210,254,0.85);
    display: flex;
    align-items: center;
    gap: 5px;
}

/* ── Divider with label ── */
.dcr-divider {
    display: flex;
    align-items: center;
    gap: 14px;
    margin: 34px 0 24px;
}
.dcr-divider span {
    font-family:'Outfit',sans-serif;
    font-size: 12px;
    font-weight: 700;
    color: var(--text-muted);
    white-space: nowrap;
    text-transform: uppercase;
    letter-spacing: 1px;
}
.dcr-divider hr { flex:1; border:none; border-top:1px solid var(--divider); margin:0; }

/* ── Insights ── */
.insight-item {
    display: flex;
    align-items: flex-start;
    gap: 12px;
    padding: 15px 18px;
    background: var(--bg-card-alt);
    backdrop-filter: blur(10px);
    border: 1px solid var(--border-card);
    border-radius: 13px;
    margin: 8px 0;
    font-family:'Outfit',sans-serif;
    font-size: 15px;
    color: var(--text-secondary);
    line-height: 1.55;
    transition: transform 0.18s ease;
}
.insight-item:hover { transform:translateX(4px); }
.insight-icon { font-size:21px; flex-shrink:0; margin-top:1px; }

/* ── Rec card ── */
.rec-card {
    background: var(--bg-card);
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
    border: 2px solid var(--border-card);
    border-radius: 18px;
    padding: 24px 20px;
    text-align: center;
    box-shadow: var(--shadow-card);
    transition: all 0.25s ease;
    margin-bottom: 10px;
}
.rec-card:hover { transform:translateY(-4px); box-shadow:var(--shadow-hover); }
.rec-card .domain-name {
    font-family:'DM Serif Display',serif;
    font-size: 21px;
    color: var(--text-primary);
    margin-bottom: 10px;
    line-height: 1.2;
}
.rec-card .match-pct {
    font-family:'IBM Plex Mono',monospace;
    font-size: 52px;
    font-weight: 700;
    line-height: 1;
}
.rec-card .match-label {
    font-family:'Outfit',sans-serif;
    font-size: 12px;
    font-weight: 700;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.7px;
    margin-top: 4px;
}
.rec-card .timeline {
    font-family:'Outfit',sans-serif;
    font-size: 14px;
    color: var(--text-secondary);
    margin-top: 10px;
}
.rec-card .salary-tag {
    font-family:'IBM Plex Mono',monospace;
    font-size: 14px;
    color: var(--accent-teal);
    margin-top: 7px;
    font-weight: 600;
}
.rec-card .reason-list {
    text-align: left;
    margin-top: 14px;
    padding: 12px 14px;
    background: var(--tag-bg);
    border-radius: 10px;
    border: 1px solid var(--border-card);
    list-style: none;
}
.rec-card .reason-list li {
    font-family:'Outfit',sans-serif;
    font-size: 13px;
    color: var(--text-secondary);
    line-height: 1.65;
    padding: 2px 0;
}
.rec-card .reason-list li::before { content:'→ '; color:var(--accent-indigo); font-weight:700; }

/* ── Saturation card ── */
.sat-card {
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
    border-radius: 18px;
    padding: 26px;
    margin: 10px 0;
    box-shadow: var(--shadow-card);
}
.sat-risk-header { display:flex; align-items:center; gap:14px; margin-bottom:16px; }
.sat-risk-header .icon { font-size:46px; }
.sat-risk-header .risk-name {
    font-family:'DM Serif Display',serif;
    font-size: 34px;
    line-height: 1;
}
.sat-risk-header .risk-score {
    font-family:'Outfit',sans-serif;
    font-size: 15px;
    color: var(--text-muted);
    margin-top: 5px;
}
.sat-breakdown {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 12px;
    margin-top: 14px;
}
.sat-bd-item {
    background: var(--bg-card);
    border-radius: 11px;
    padding: 14px 16px;
    border: 1px solid var(--border-card);
}
.sat-bd-item .bd-label {
    font-family:'Outfit',sans-serif;
    font-size: 12px;
    font-weight: 700;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.7px;
    margin-bottom: 5px;
}
.sat-bd-item .bd-value {
    font-family:'Outfit',sans-serif;
    font-size: 17px;
    font-weight: 600;
    color: var(--text-primary);
}

/* ── Compat result ── */
.compat-result {
    background: var(--bg-card);
    backdrop-filter: blur(16px);
    border-radius: 20px;
    padding: 34px 30px;
    text-align: center;
    max-width: 480px;
    margin: 0 auto;
    box-shadow: var(--shadow-card);
    border: 1px solid var(--border-card);
}
.compat-result .cr-label {
    font-family:'Outfit',sans-serif;
    font-size: 15px;
    color: var(--text-muted);
    margin-bottom: 4px;
}
.compat-result .cr-domain {
    font-family:'DM Serif Display',serif;
    font-size: 28px;
    color: var(--text-primary);
    margin-bottom: 12px;
}
.compat-result .cr-pct {
    font-family:'IBM Plex Mono',monospace;
    font-size: 76px;
    font-weight: 700;
    line-height: 1;
}

/* ── Market share bar ── */
.mshare-bar {
    padding: 13px 20px;
    background: var(--bg-card-alt);
    border-radius: 11px;
    margin: 10px 0;
    font-family:'Outfit',sans-serif;
    font-size: 15px;
    color: var(--text-secondary);
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 7px;
    border: 1px solid var(--divider);
}
.mshare-bar strong {
    font-family:'IBM Plex Mono',monospace;
    font-size: 17px;
    color: var(--text-primary);
    font-weight: 700;
}

/* ── Fade-in animation ── */
@keyframes dcr-fadein {
    from { opacity:0; transform:translateY(14px); }
    to   { opacity:1; transform:translateY(0); }
}
.dcr-animate { animation: dcr-fadein 0.42s ease both; }
.dcr-animate:nth-child(2) { animation-delay:0.08s; }
.dcr-animate:nth-child(3) { animation-delay:0.16s; }
.dcr-animate:nth-child(4) { animation-delay:0.24s; }
.dcr-animate:nth-child(5) { animation-delay:0.32s; }
</style>
"""

def _inject_styles():
    st.markdown(_GLOBAL_CSS, unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# UTILITY HELPERS
# ---------------------------------------------------------------------------

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

# ---------------------------------------------------------------------------
# ENTRY BARRIER CARD
# ---------------------------------------------------------------------------

def render_entry_barrier_card(domain: str, user_profile: Dict[str, Any] = None):
    _inject_styles()

    # Placeholder values — replace with real engine later
    timeline_display = "5–9 months"
    prerequisites    = "Basic Python + Linear Algebra & Statistics"
    project_level    = "Medium to Advanced (2–3 portfolio-grade projects)"
    interview_dsa    = 7
    interview_domain = 6
    overall_difficulty = {"level": "Medium-High", "score": 7.2, "color": "amber"}
    hidden_blockers = [
        {"type": "warning", "text": "Math-heavy — discomfort with calculus/probability will hurt"},
        {"type": "critical", "text": "Most good roles expect at least one strong internship or open-source contribution"},
        {"type": "warning", "text": "Portfolio is extremely important — generic GitHub repos won't cut it"}
    ]

    st.markdown(f"""
    <div class="market-header dcr-animate" style="margin-top:32px;">
        <h2>⚡ Entry Barrier — {domain}</h2>
        <div class="loc">How hard is it to actually break in?</div>
    </div>
    """, unsafe_allow_html=True)

    cols = st.columns(3)
    with cols[0]:
        st.markdown(f"""
        <div class="mcard">
            <div class="mcard-title">⏱️ Time to Job-Ready</div>
            <div class="mcard-value sm" style="color:var(--accent-amber);">
                {timeline_display}
            </div>
            <div class="mcard-sub">realistic estimate (15–25 hrs/week focused effort)</div>
        </div>
        """, unsafe_allow_html=True)

    with cols[1]:
        st.markdown(f"""
        <div class="mcard">
            <div class="mcard-title">📋 Prerequisites</div>
            <div style="font-size:16px; line-height:1.5; margin:12px 0;">
                {prerequisites}
            </div>
        </div>
        """, unsafe_allow_html=True)

    with cols[2]:
        st.markdown(f"""
        <div class="mcard">
            <div class="mcard-title">📚 Project Complexity</div>
            <div style="font-size:20px; font-weight:700; color:var(--accent-red); margin:12px 0;">
                {project_level}
            </div>
        </div>
        """, unsafe_allow_html=True)

    col_dsa, col_dom = st.columns(2)
    with col_dsa:
        st.markdown(f"""
        <div class="mcard">
            <div class="mcard-title">💻 DSA / LeetCode Level</div>
            <div class="mcard-value sm" style="color:var(--accent-red);">
                {interview_dsa}/10
            </div>
            <div class="mcard-sub">≈ LeetCode Medium–Hard frequency</div>
        </div>
        """, unsafe_allow_html=True)

    with col_dom:
        st.markdown(f"""
        <div class="mcard">
            <div class="mcard-title">🎯 Domain Knowledge Depth</div>
            <div class="mcard-value sm" style="color:var(--accent-amber);">
                {interview_domain}/10
            </div>
            <div class="mcard-sub">system design + domain concepts matter</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="mcard" style="text-align:center;">
        <div class="mcard-title">Overall Entry Difficulty</div>
        <div class="mcard-value" style="color:var(--accent-{overall_difficulty['color']}); font-size:42px;">
            {overall_difficulty['level']}
        </div>
        <div class="mcard-sub">Difficulty score ≈ {overall_difficulty['score']}/10</div>
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

    # Placeholder values — replace with real calculations later
    salary_0_2y  = {"from": "6–9", "to": "14–22"}
    salary_3_5y  = {"from": "18–28", "to": "35–55"}
    role_path    = [
        ("0–2", "Junior / Associate", "core skills + clean code"),
        ("2–5", "Mid / Senior", "ownership + mentoring"),
        ("5–9", "Lead / Staff", "architecture + cross-team impact"),
        ("9+",  "Principal / Architect", "org-wide strategy")
    ]
    stability    = {"score": 7.8, "rating": "Good", "text": "Strong demand expected till 2030+"}
    transfer     = {"score": 8.1, "rating": "High", "targets": ["Data Eng", "Backend", "Full-Stack", "AI-adjacent roles"]}
    ai_risk      = {"level": "Medium", "score": 5.2, "text": "Routine tasks automated, creative/system thinking remains valuable"}

    st.markdown(f"""
    <div class="market-header dcr-animate" style="margin-top:32px;">
        <h2>📈 Growth Trajectory — {domain}</h2>
        <div class="loc">What your career could look like in 5–10 years</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="mcard">
        <div class="mcard-title">Salary Progression (India — realistic percentiles)</div>
        <div style="display:grid; grid-template-columns:1fr 1fr; gap:16px; text-align:center; margin:20px 0;">
            <div>
                <div style="color:var(--text-muted);">0–2 years</div>
                <div style="font-size:28px; font-weight:700; color:var(--accent-teal);">
                    ₹{salary_0_2y['from']} – {salary_0_2y['to']} LPA
                </div>
            </div>
            <div>
                <div style="color:var(--text-muted);">3–5 years</div>
                <div style="font-size:28px; font-weight:700; color:var(--accent-indigo);">
                    ₹{salary_3_5y['from']} – {salary_3_5y['to']} LPA
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""<div class="dcr-divider"><hr/><span>🎯 Typical Role Evolution</span><hr/></div>""", unsafe_allow_html=True)

    for i, (years, title, desc) in enumerate(role_path):
        st.markdown(f"""
        <div class="mcard" style="margin-bottom:8px;">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <div>
                    <div style="font-size:20px; font-weight:600;">{title}</div>
                    <div style="color:var(--text-muted);">{desc}</div>
                </div>
                <div style="font-family:'IBM Plex Mono'; color:var(--accent-indigo);">
                    {years} years
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        if i < len(role_path)-1:
            st.markdown("<div style='text-align:center; font-size:28px; color:var(--accent-indigo);'>↓</div>", unsafe_allow_html=True)

    cols = st.columns(3)
    with cols[0]:
        st.markdown(f"""
        <div class="mcard" style="text-align:center;">
            <div class="mcard-title">Domain Stability</div>
            <div class="mcard-value" style="color:var(--accent-green);">{stability['score']}/10</div>
            <div class="pill pill-green" style="margin:12px auto; display:inline-block;">{stability['rating']}</div>
            <div class="mcard-sub">{stability['text']}</div>
        </div>
        """, unsafe_allow_html=True)

    with cols[1]:
        st.markdown(f"""
        <div class="mcard" style="text-align:center;">
            <div class="mcard-title">Skill Transferability</div>
            <div class="mcard-value" style="color:var(--accent-teal);">{transfer['score']}/10</div>
            <div class="pill pill-green" style="margin:12px auto; display:inline-block;">{transfer['rating']}</div>
            <div class="mcard-sub">→ {', '.join(transfer['targets'])}</div>
        </div>
        """, unsafe_allow_html=True)

    with cols[2]:
        color = "var(--accent-amber)" if ai_risk["level"] == "Medium" else "var(--accent-red)"
        pill_cls = "amber" if ai_risk["level"] == "Medium" else "red"
        st.markdown(f"""
        <div class="mcard" style="text-align:center;">
            <div class="mcard-title">AI Replacement Risk</div>
            <div class="mcard-value sm" style="color:{color};">{ai_risk['level']}</div>
            <div class="pill pill-{pill_cls}" style="margin:12px auto; display:inline-block;">
                Score: {ai_risk['score']}/10
            </div>
            <div class="mcard-sub">{ai_risk['text']}</div>
        </div>
        """, unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# REAL TALK SECTION
# ---------------------------------------------------------------------------

def render_real_talk_section(domain: str):
    _inject_styles()

    harsh = "Very high competition at entry level — 70–80% of beginners never land a proper role in this domain."
    silver = "Once you cross the 1.5–2 year mark with good projects, salary and opportunity curve becomes steep."
    traps = [
        "Stuck in tutorial hell — watching 200+ videos without building anything meaningful",
        "Copy-pasting projects from YouTube / GitHub without understanding → interviewers spot it instantly",
        "Expecting job after doing only basic courses — market now demands deployed + documented work"
    ]
    patterns = [
        "Build 2–3 non-trivial projects → deploy them → write clear READMEs + architecture diagrams",
        "Contribute to open source or create public tools → gets noticed more than certificates",
        "Network + share progress on LinkedIn / Twitter → many offers come from visibility"
    ]
    timeline = "6–18 months of serious effort separates the 10–20% who succeed from the rest"

    st.markdown(f"""
    <div class="market-header dcr-animate" style="margin-top:32px; background:linear-gradient(135deg,#7f1d1d 0%,#991b1b 100%);">
        <h2>🎯 Real Talk — {domain}</h2>
        <div class="loc">No motivational fluff. Just reality.</div>
    </div>
    """, unsafe_allow_html=True)

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
        st.markdown(f"""<div class="insight-item"><span class="insight-icon">⚠️</span><span>{t}</span></div>""", unsafe_allow_html=True)

    st.markdown("""<div class="dcr-divider"><hr/><span>✅ Patterns of People Who Actually Make It</span><hr/></div>""", unsafe_allow_html=True)
    for p in patterns:
        st.markdown(f"""<div class="insight-item"><span class="insight-icon">→</span><span>{p}</span></div>""", unsafe_allow_html=True)

    st.markdown(f"""
    <div class="mcard" style="margin-top:24px; text-align:center;">
        <div class="mcard-title">⏳ Realistic Success Timeline</div>
        <div style="font-size:20px; color:var(--accent-indigo); margin:16px 0; font-weight:600;">
            {timeline}
        </div>
    </div>
    """, unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# FETCH ANALYTICS
# ---------------------------------------------------------------------------

def fetch_domain_analytics(domain: str, location: str = "Jaipur") -> Dict[str, Any] | None:
    try:
        df = _load_dataframe(DATA_PATH)
        custom_weights = {
            "Job_Posting_Frequency":  0.35,
            "Trend_Direction":        0.40,
            "Skill_Diversity":        0.15,
            "Experience_Flexibility": 0.10,
        }
        engine = MarketDemandEngine(data=df, weights=custom_weights)
        demand_results = engine.calculate_metrics(domains=[domain])
        domain_stats = demand_results.get(domain, {})
        salary_data = AverageSalaryRangeCalculator().calculate_salary_metrics(df, domain, location)
        velocity_data = JobMarketVelocityCalculator().calculate_openings_stats(df, domain, location)
        comp_data = CompetitionLevelCalculator().calculate_competition_level(df, domain)
        sat_data = SaturationRiskIndicator().get_saturation_risk(df, domain)

        return {
            "domain": domain,
            "location": location,
            "demand_score": domain_stats.get("Overall_Demand_Score", 0),
            "trend_score": domain_stats.get("Breakdown", {}).get("Growth_Trend", 5.0),
            "breakdown": domain_stats.get("Breakdown", {}),
            "competition": {
                "level": comp_data.get("Level", "Medium"),
                "index": comp_data.get("Competition Index", 0),
                "candidates_per_job": int(comp_data.get("Candidates per Job", 0)),
            },
            "salary": {
                "low": salary_data.get("Market_Range", {}).get("Low_End_25th", 0),
                "median": salary_data.get("Market_Range", {}).get("Median_50th", 0),
                "high": salary_data.get("Market_Range", {}).get("High_End_75th", 0),
                "location_adjusted": salary_data.get("Location_Adjusted_Median", 0),
            },
            "job_openings": {
                "local_30d": velocity_data.get("Counts", {}).get("Local_Openings_30d", 0),
                "national_30d": velocity_data.get("Counts", {}).get("National_Openings_30d", 0),
                "local_growth_pct": velocity_data.get("Growth_Metrics", {}).get("Local_Growth_Pct", 0),
                "national_growth_pct": velocity_data.get("Growth_Metrics", {}).get("National_Growth_Pct", 0),
            },
            "saturation": {
                "score": sat_data.get("Saturation_Score", 0),
                "risk_level": sat_data.get("Risk_Level", "Safe"),
                "color_code": sat_data.get("Color_Code", "Green"),
                "signals": sat_data.get("Signals", {}),
            },
        }
    except Exception as e:
        st.error(f"Error fetching analytics for **{domain}**: {e}")
        return None

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
                       script run (e.g. standalone card + full analysis) each
                       get a unique widget key.  Pass a short label like
                       "_standalone" or "_full" at each call-site.
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
        trend_icon = get_trend_indicator(domain_data.get("trend_score", 5.0))
        if demand_score >= 7:
            d_color, d_pill, d_label = "var(--accent-green)", "pill-green", "High Demand"
        elif demand_score >= 4:
            d_color, d_pill, d_label = "var(--accent-amber)", "pill-amber", "Moderate Demand"
        else:
            d_color, d_pill, d_label = "var(--accent-red)", "pill-red", "Low Demand"

        vol = domain_data.get("breakdown", {}).get("Volume", 0)
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
        comp = domain_data.get("competition", {})
        level = comp.get("level", "Medium")
        emoji, color, pill_cls = get_competition_badge(level)
        cands = comp.get("candidates_per_job", 0)
        c_idx = comp.get("index", 0)

        st.markdown(f"""
        <div class="mcard dcr-animate">
            <div class="mcard-title">Competition Level</div>
            <div class="mcard-value sm" style="color:{color};">
                {emoji} {level}
            </div>
            <div style="margin-top:12px;">
                <span class="pill pill-{pill_cls}">Index: {c_idx:.2f}</span>
            </div>
            <div class="mcard-sub">
                ~<strong>{cands}</strong> candidates per open position
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ── Row 2: Salary ────────────────────────────────────────────────────────
    sal = domain_data.get("salary", {})
    low = sal.get("low", 0)
    median = sal.get("median", 0)
    high = sal.get("high", 0)
    loc_adj = sal.get("location_adjusted", median)
    bar_pct = min(100, round((loc_adj / high * 100) if high > 0 else 50))

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
    o = domain_data.get("job_openings", {})
    local = o.get("local_30d", 0)
    national = o.get("national_30d", 0)
    local_growth = o.get("local_growth_pct", 0)
    national_growth = o.get("national_growth_pct", 0)

    col3, col4 = st.columns(2)
    with col3:
        lt = "↗" if local_growth > 0 else "↘" if local_growth < 0 else "→"
        lgc = "var(--accent-green)" if local_growth > 0 else "var(--accent-red)" if local_growth < 0 else "var(--text-muted)"
        st.markdown(f"""
        <div class="mcard dcr-animate">
            <div class="mcard-title">📍 {location} Job Openings</div>
            <div class="mcard-value" style="color:var(--accent-indigo);">{local}</div>
            <div class="mcard-label">listings — last 30 days</div>
            <div class="mcard-sub" style="font-family:'IBM Plex Mono'; font-size:16px; font-weight:700; color:{lgc}; margin-top:12px;">
                {lt} {abs(local_growth):.1f}% MoM
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        nt = "↗" if national_growth > 0 else "↘" if national_growth < 0 else "→"
        ngc = "var(--accent-green)" if national_growth > 0 else "var(--accent-red)" if national_growth < 0 else "var(--text-muted)"
        st.markdown(f"""
        <div class="mcard dcr-animate">
            <div class="mcard-title">🇮🇳 National Job Openings</div>
            <div class="mcard-value" style="color:#8b5cf6;">{national}</div>
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
    sat = domain_data.get("saturation", {})
    risk_level = sat.get("risk_level", "Safe")
    sat_score = sat.get("score", 0)
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
                {"range": [0, 33], "color": "rgba(5,150,105,0.10)"},
                {"range": [33, 66], "color": "rgba(217,119,6,0.10)"},
                {"range": [66, 100], "color": "rgba(220,38,38,0.10)"},
            ],
            "threshold": {"line": {"color": "#dc2626", "width": 3}, "thickness": 0.8, "value": 70},
        },
    ))

    fig.update_layout(
        height=295,
        margin=dict(l=20, r=20, t=65, b=20),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"family": "Outfit", "size": 14}
    )

    # Build a unique, stable key from domain + location + caller-supplied suffix.
    # Sanitise by replacing anything that isn't alphanumeric or underscore.
    raw_key = f"gauge_{domain_data['domain']}_{domain_data.get('location', 'default')}{gauge_key_suffix}"
    gauge_key = "".join(c if c.isalnum() or c == "_" else "_" for c in raw_key)

    st.plotly_chart(
        fig,
        use_container_width=True,
        key=gauge_key,
        config={"displayModeBar": False},
    )

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

    if loc_adj > median:
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
                       rendered in the same script run (e.g. in Path 2 before
                       the user clicks "Show Complete Analysis").  This prevents
                       the duplicate-widget-key error caused by rendering the
                       Plotly gauge twice with the same key.
    """
    with st.spinner(f"Loading comprehensive analysis for {domain}..."):
        market_data = fetch_domain_analytics(domain, location)

    if market_data:
        if not skip_market_card:
            # Standalone call (e.g. Path 1) — render the market card here.
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
    _inject_styles()

    st.markdown("""
    <div class="dcr-section-title">
        <span class="step-badge">STEP 01</span> Tell us about yourself
    </div>
    """, unsafe_allow_html=True)

    if "p1_recommendations" not in st.session_state:
        st.session_state.p1_recommendations = None
    if "p1_selected_domain" not in st.session_state:
        st.session_state.p1_selected_domain = None
    if "p1_location" not in st.session_state:
        st.session_state.p1_location = "Jaipur"

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
            math_comfort = st.select_slider(
                "Math Comfort Level",
                options=["Weak", "Moderate", "Strong"],
                value="Moderate",
                key="p1_math",
            )
        submitted = st.form_submit_button("Get My Recommendations →", use_container_width=True)

    if submitted:
        st.session_state.p1_location = location_pref
        st.session_state.p1_selected_domain = None
        user_profile = {
            "experience": experience,
            "skills": interest,
            "location": location_pref,
            "math_comfort": math_comfort,
        }
        with st.spinner("Analysing your profile against live market signals…"):
            try:
                df = _load_dataframe(DATA_PATH)
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

        recs = st.session_state.p1_recommendations
        cols = st.columns(len(recs))

        for i, rec in enumerate(recs):
            with cols[i]:
                match_pct = rec.get("match_percentage", 0)
                color = (
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
            "experience": st.session_state.get("p1_exp", "Fresher"),
            "skills": st.session_state.get("p1_int", []),
            "location": st.session_state.p1_location,
            "math_comfort": st.session_state.get("p1_math", "Moderate"),
        }

        # Path 1: market card has NOT been shown yet → skip_market_card=False
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
            st.session_state.p2_market_data = data
            # Reset the full-analysis flag whenever new data is loaded
            st.session_state.p2_show_full_analysis = False
        else:
            st.session_state.pop("p2_market_data", None)

    if "p2_market_data" in st.session_state:
        # Render the standalone market card with a unique suffix so its gauge
        # key never collides with the one inside render_complete_domain_analysis.
        render_market_reality_card(
            st.session_state.p2_market_data,
            gauge_key_suffix="_standalone",
        )

        st.markdown("""
        <div class="dcr-section-title" style="margin-top:40px;">
            📈 Want the Full Picture?
        </div>
        """, unsafe_allow_html=True)

        if st.button(
            "Show Complete Domain Analysis (Barriers + Growth + Real Talk)",
            type="primary",
            use_container_width=True,
            key="p2_full_analysis_btn",
        ):
            st.session_state.p2_show_full_analysis = True

        # Render the full analysis below the button if it has been requested.
        # We pass skip_market_card=True because the market card (including its
        # gauge) was already rendered just above in this same script run.
        if st.session_state.get("p2_show_full_analysis", False):
            render_complete_domain_analysis(
                domain=st.session_state.p2_market_data["domain"],
                location=st.session_state.p2_market_data["location"],
                user_profile=None,
                skip_market_card=True,   # ← market card already shown above
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
            skills = st.multiselect(
                "Skills you already have",
                ["Python", "SQL", "Machine Learning", "Statistics", "Pandas", "HTML", "CSS", "JavaScript", "React", "Node.js",
                 "Docker", "AWS", "Terraform", "Linux", "Kubernetes", "TensorFlow", "PyTorch", "Java", "APIs", "LLMs"],
                key="ic_skills",
            )
        with c2:
            math_comfort = st.select_slider("Math Comfort Level", ["Weak", "Moderate", "Strong"], value="Moderate", key="ic_math")

        submitted = st.form_submit_button("Check My Compatibility →", use_container_width=True)

    if submitted:
        user_profile = {
            "experience": experience,
            "skills": skills,
            "location": location,
            "math_comfort": math_comfort,
        }
        with st.spinner("Calculating compatibility…"):
            try:
                df = _load_dataframe(DATA_PATH)
                engine = DomainRecommendationEngine(df)
                all_recs = engine.get_recommendations(user_profile, top_n=len(engine.domains))
                target = next((r for r in all_recs if r["domain"] == selected_domain), None)

                if target:
                    match_pct = target["match_percentage"]
                    color = "#059669" if match_pct >= 65 else "#d97706" if match_pct >= 40 else "#dc2626"

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