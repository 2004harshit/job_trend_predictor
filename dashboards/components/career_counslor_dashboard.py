"""
Career Counselor Dashboard
===========================
Streamlit frontend for the Career Counselor API.

Run:
    streamlit run career_counselor_dashboard.py

Environment:
    API_BASE_URL=http://localhost:5000   (default)
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import plotly.figure_factory as ff
import pandas as pd
from typing import Optional, List

import sys
import os

# 1. Get the path to the 'dashboards' folder (which contains 'utils' and 'components')
# This script is in 'dashboards/components/'
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir) # This is the 'dashboards' folder

# 2. Add the 'dashboards' folder to the Python path
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# 3. Import the 'api_client' FILE from the 'utils' FOLDER
# This makes 'api' the module that contains cc_health()
# from utils import api_client as api

# --- FULLY COMPATIBLE MOCK API ---
class MockApi:
    def cc_health(self, *args, **kwargs): return True
    
    def cc_filter_options(self, *args, **kwargs):
        return {
            "domains": ["Data Science", "Web Development", "DevOps", "Data Engineering"],
            "locations": ["Jaipur", "Bangalore", "Remote", "Pune"],
            "companies": ["TCS", "Meta", "Google", "Infosys", "Zomato"],
            "total_jobs": 4500
        }

    def cc_market_snapshot(self, *args, **kwargs):
        return {
            "total_jobs": 1200, "active_domains": 10, "top_skill": "Python", 
            "salary_snapshot": {"median": "8.5 LPA"}
        }

    def cc_top_domains(self, *args, **kwargs):
        return {"domains": [
            {"domain": "Data Science", "job_count": 450, "fresher_eligible_pct": 70, "avg_salary": 9.2},
            {"domain": "Web Dev", "job_count": 380, "fresher_eligible_pct": 85, "avg_salary": 6.5}
        ]}

    def cc_skill_frequency(self, *args, **kwargs):
        return {"skills": [
            {"skill": "Python", "job_count": 800, "frequency_pct": 80},
            {"skill": "SQL", "job_count": 600, "frequency_pct": 60},
            {"skill": "Pandas", "job_count": 500, "frequency_pct": 50},
            {"skill": "Excel", "job_count": 450, "frequency_pct": 45},
            {"skill": "Tableau", "job_count": 300, "frequency_pct": 30}
        ]}

    def cc_momentum_badges(self, *args, **kwargs):
        return {"badges": [{"skill": "GenAI", "current_count": 100, "change_pct": 45, "trend": "rising", "arrow": "↑"}]}

    def cc_saturation(self, *args, **kwargs):
        return {"indicators": [
            {"domain": "Data Science", "job_count": 450, "unique_companies": 45, "saturation_score": 0.42},
            {"domain": "Web Dev", "job_count": 380, "unique_companies": 30, "saturation_score": 0.55},
            {"domain": "Data Eng", "job_count": 290, "unique_companies": 20, "saturation_score": 0.68},
            {"domain": "DevOps", "job_count": 210, "unique_companies": 15, "saturation_score": 0.35}
        ]}

    def cc_compare_domains(self, *args, **kwargs):
        return {"domains": [{"domain": "Data Science", "job_count": 100, "fresher_eligible_pct": 70, "salary": 8.0}], "skill_overlap_matrix": {}}

    def cc_domain_skill_matrix(self, *args, **kwargs):
        return {"skills": ["Python", "SQL"], "domains": ["Data Science"], "matrix": {"Python": {"Data Science": 90}}}

    def cc_skill_matrix(self, domains, *args, **kwargs):
        """Alias for cc_domain_skill_matrix — used in the skill overlap section."""
        return self.cc_domain_skill_matrix(domains, *args, **kwargs)

    def cc_popular_skills(self, *args, **kwargs):
        return [{"skill": "Python", "frequency_pct": 90}, {"skill": "SQL", "frequency_pct": 70}]

    def cc_skill_gap_analyze(self, *args, **kwargs):
        return {
            "match_percentage": 75, "jobs_accessible_now": 20, "total_domain_jobs": 100,
            "matched_skills": ["Python"], "missing_skills": [{"skill": "Docker", "frequency_pct": 30, "extra_jobs_if_added": 15}],
            "impact_summary": "Strong start!", "top_benchmark_roles": []
        }

    def cc_salary_ranges(self, *args, **kwargs):
        return {"salary": {"available": True, "p10": 4, "p25": 5, "p50": 8, "p75": 12, "p90": 18}}

    def cc_jaipur_vs_national(self, *args, **kwargs):
        return {"jaipur": {"p50": 6}, "national": {"p50": 8}, "comparison": {"jaipur_lower_by_pct": 25}}

    def cc_salary_top_skills(self, *args, **kwargs):
        return [{"skill": "AWS", "premium_signal": 1.2, "overall_frequency": 30}]

    def cc_salary_by_experience(self, *args, **kwargs):
        return [{"band_label": "0-2y", "salary": {"p50": 6}}]

    def cc_top_companies(self, *args, **kwargs):
        return {"companies": [{"company": "Google", "job_count": 50, "estimated_type": "Product", "fresher_pct": 10}]}

    def cc_company_type_split(self, *args, **kwargs):
        return {"type_split": {"Product": {"job_count": 100, "pct": 50}, "Service": {"job_count": 100, "pct": 50}}}

    def cc_jaipur_companies(self, *args, **kwargs):
        return {"companies": [{"company": "GirnarSoft", "job_count": 20}]}

    def cc_hiring_frequency(self, *args, **kwargs):
        return {"total_jobs": 10, "avg_jobs_per_week": 2, "weekly_buckets": [{"week_start": "2024-01-01", "job_count": 2}]}

    def cc_fresher_analysis(self, domain, days=30, location="All"):
        return {
            "total_domain_jobs": 1200, "fresher_jobs": 480, "fresher_pct": 40.0,
            "top_fresher_skills": ["Python", "SQL", "Basic Statistics", "Excel"],
            "top_fresher_companies": [
                {"company": "TCS", "job_count": 50}, {"company": "Infosys", "job_count": 40},
                {"company": "Wipro", "job_count": 35}, {"company": "Zomato", "job_count": 20}
            ]
        }

# Initialize the fake API
api = MockApi()

# ─────────────────────────────────────────────────────────────────────────────
# Page config
# ─────────────────────────────────────────────────────────────────────────────
# NOTE:
# `dashboards/app.py` is responsible for calling `st.set_page_config()` once
# for the entire Streamlit app. This component is imported by pages, so we
# must not call `st.set_page_config()` here (it can trigger Streamlit errors
# like "set_page_config must be called as the first Streamlit command").

# ─────────────────────────────────────────────────────────────────────────────
# Minimal custom CSS
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
.metric-card {
    background: #f8f9fa;
    border-radius: 10px;
    padding: 16px 20px;
    border-left: 4px solid #4f46e5;
    margin-bottom: 8px;
}
.metric-card h3 { margin: 0 0 4px 0; font-size: 13px; color: #6b7280; font-weight: 500; }
.metric-card p  { margin: 0; font-size: 26px; font-weight: 700; color: #111827; }
.metric-card { min-height: 105px; display: flex; flex-direction: column; justify-content: center; }

.impact-card {
    background: #f0fdf4;
    border: 1px solid #bbf7d0;
    border-radius: 8px;
    padding: 12px 16px;
    margin-bottom: 8px;
    font-size: 14px;
    color: #166534;
}
.badge-up   { color: #15803d; font-weight: 600; }
.badge-down { color: #dc2626; font-weight: 600; }
.badge-stable { color: #92400e; font-weight: 600; }
.warn-box {
    background: #fffbeb;
    border: 1px solid #fcd34d;
    border-radius: 6px;
    padding: 8px 12px;
    font-size: 12px;
    color: #78350f;
    margin-top: 4px;
}
.salary-note {
    background: #eff6ff;
    border: 1px solid #bfdbfe;
    border-radius: 6px;
    padding: 8px 12px;
    font-size: 12px;
    color: #1e40af;
    margin-top: 4px;
}
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _metric_card(label: str, value: str, border_color: str = "#4f46e5") -> None:
    st.markdown(
        f'<div class="metric-card" style="border-left-color:{border_color}">'
        f'<h3>{label}</h3><p>{value}</p></div>',
        unsafe_allow_html=True,
    )


def _warn(msgs: list) -> None:
    for m in msgs:
        st.markdown(f'<div class="warn-box">⚠ {m}</div>', unsafe_allow_html=True)


def _salary_note(note: str) -> None:
    st.markdown(f'<div class="salary-note">ℹ {note}</div>', unsafe_allow_html=True)


def _api_error(feature: str) -> None:
    st.error(f"Could not load {feature} — API unavailable or returned no data.")


@st.cache_data(ttl=300)
def _get_filter_options():
    return api.cc_filter_options()


@st.cache_data(ttl=60)
def _cached_snapshot(days, location, fresher_only):
    return api.cc_market_snapshot(days, location, fresher_only)


@st.cache_data(ttl=60)
def _cached_top_domains(days, limit, location, fresher_only):
    return api.cc_top_domains(days, limit, location, fresher_only)


@st.cache_data(ttl=60)
def _cached_skill_freq(days, top_n, location, fresher_only, domain):
    return api.cc_skill_frequency(days, top_n, location, fresher_only, domain)


@st.cache_data(ttl=120)
def _cached_momentum(days, location):
    return api.cc_momentum_badges(days=days, location=location)


@st.cache_data(ttl=120)
def _cached_saturation(days, location):
    return api.cc_saturation(days=days, location=location)


@st.cache_data(ttl=120)
def _cached_popular_skills(domain, fresher_only):
    return api.cc_popular_skills(domain=domain, fresher_only=fresher_only)


@st.cache_data(ttl=120)
def _cached_compare(domains_key, fresher_only, days, location):
    domains = list(domains_key)
    return api.cc_compare_domains(domains, fresher_only, days, location)


@st.cache_data(ttl=120)
def _cached_skill_matrix(domains_key, days, fresher_only):
    return api.cc_domain_skill_matrix(list(domains_key), days=days, fresher_only=fresher_only)


@st.cache_data(ttl=300)
def _cached_salary_ranges(domain, location, fresher_only):
    return api.cc_salary_ranges(domain, location, fresher_only)


@st.cache_data(ttl=300)
def _cached_jaipur_vs_national(domain, fresher_only):
    return api.cc_jaipur_vs_national(domain, fresher_only)


@st.cache_data(ttl=300)
def _cached_salary_top_skills(domain, location):
    return api.cc_salary_top_skills(domain=domain, location=location)


@st.cache_data(ttl=300)
def _cached_salary_by_exp(domain, location):
    return api.cc_salary_by_experience(domain=domain, location=location)


@st.cache_data(ttl=60)
def _cached_top_companies(domain, days, location, fresher_only, limit):
    return api.cc_top_companies(domain, days, location, fresher_only, limit)


@st.cache_data(ttl=60)
def _cached_type_split(domain, days, location, fresher_only):
    return api.cc_company_type_split(domain, days, location, fresher_only)


@st.cache_data(ttl=120)
def _cached_jaipur_companies(domain, days, fresher_only):
    return api.cc_jaipur_companies(domain, days, fresher_only)


# ─────────────────────────────────────────────────────────────────────────────
# Sidebar
# ─────────────────────────────────────────────────────────────────────────────

with st.sidebar:
    st.title("🎯 Career Counselor")
    st.caption("Powered by Naukri job data")

    st.divider()

    # API health check
    if api.cc_health():
        st.success("API connected", icon="✅")
    else:
        st.error("API unreachable", icon="❌")
        st.stop()

    st.subheader("Filters")

    # Location
    filter_opts = _get_filter_options()
    locations = ["All (National)"]
    if filter_opts and "locations" in filter_opts:
        locations += sorted(set(filter_opts["locations"]))

    location_sel = st.selectbox("Location", locations)
    sidebar_location: Optional[str] = None if location_sel == "All (National)" else location_sel

    # Days window
    days_sel = st.slider("Data window (days)", min_value=7, max_value=180, value=30, step=7)

    # Fresher toggle
    fresher_toggle = st.toggle("Fresher only (0–1 yr exp)", value=False)

    st.divider()
    st.caption("Salary note: ~80% of Naukri postings don't disclose salary. "
               "All salary figures are estimates from the disclosed subset.")


# ─────────────────────────────────────────────────────────────────────────────
# Tab layout
# ─────────────────────────────────────────────────────────────────────────────

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Market Pulse",
    "⚖ Domain Comparison",
    "🔍 Skill Gap Analyzer",
    "💰 Salary Intelligence",
    "🏢 Company Intelligence",
])


# ═════════════════════════════════════════════════════════════════════════════
# TAB 1 — MARKET PULSE
# ═════════════════════════════════════════════════════════════════════════════

with tab1:
    try:
        st.header("Live Market Pulse")
        st.markdown("""
<div style="text-align: right; margin-bottom: 10px;">
    <span style="background: #f59e0b; color: white; padding: 5px 12px; 
                 border-radius: 9999px; font-size: 12.5px; font-weight: 600;">
        🛠 In Development • Data is approximate
    </span>
</div>
""", unsafe_allow_html=True)
        st.caption(f"Last {days_sel} days · {location_sel} · {'Freshers only' if fresher_toggle else 'All experience'}")

        # ── Snapshot cards ──────────────────────────────────────────────────────
        snap = _cached_snapshot(days_sel, sidebar_location, fresher_toggle)

        if snap:
            _warn(snap.get("metadata", {}).get("data_quality_warnings", []))
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                _metric_card("Total Jobs", f"{snap.get('total_jobs', 0):,}", "#4f46e5")
            with c2:
                _metric_card("Active Domains", str(snap.get("active_domains", 0)), "#0891b2")
            with c3:
                _metric_card("Top Skill", str(snap.get("top_skill") or "—"), "#7c3aed")
            with c4:
                sal = snap.get("salary_snapshot", {})
                if not isinstance(sal, dict):
                    sal = {}
                val = f"₹{sal['median']:.1f}L" if sal.get("available") else "₹7.5 - 12.0 LPA (est)"
                _metric_card("Median Salary", val, "#059669")
                if sal.get("available"):
                    _salary_note(f"{sal.get('coverage_pct', 0):.0f}% of jobs disclosed salary")
        else:
            _api_error("market snapshot")

        st.divider()

        col_left, col_right = st.columns(2, gap="large")

        # ── Top Domains ──────────────────────────────────────────────────────────
        with col_left:
            st.subheader("Top Domains by Job Volume")
            try:
                domains_data = _cached_top_domains(days_sel, 10, sidebar_location, fresher_toggle)

                if domains_data and domains_data.get("domains"):
                    df_dom = pd.DataFrame(domains_data["domains"])
                    fig = px.bar(
                        df_dom.head(10),
                        x="job_count", y="domain", orientation="h",
                        text="job_count",
                        color="fresher_eligible_pct",
                        color_continuous_scale="Blues",
                        labels={"job_count": "Job Count", "domain": "",
                                "fresher_eligible_pct": "Fresher %"},
                        height=400,
                    )
                    fig.update_layout(
                        margin=dict(l=0, r=20, t=10, b=10),
                        yaxis={"categoryorder": "total ascending"},
                        coloraxis_colorbar=dict(title="Fresher %", thickness=12),
                    )
                    fig.update_traces(textposition="outside")
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No domain volume data found for these filters.")
            except Exception as e:
                st.error(f"Error loading domain chart: {str(e)}")

        # ── Skill Frequency ──────────────────────────────────────────────────────
        with col_right:
            st.subheader("Most Demanded Skills")
            try:
                skills_data = _cached_skill_freq(days_sel, 20, sidebar_location, fresher_toggle, None)

                if skills_data and skills_data.get("skills"):
                    df_sk = pd.DataFrame(skills_data["skills"])
                    fig2 = px.bar(
                        df_sk.head(20),
                        x="frequency_pct", y="skill", orientation="h",
                        text=df_sk.head(20)["frequency_pct"].apply(lambda x: f"{x:.1f}%"),
                        color="frequency_pct",
                        color_continuous_scale="Purples",
                        labels={"frequency_pct": "% of Jobs", "skill": ""},
                        height=400,
                    )
                    fig2.update_layout(
                        margin=dict(l=0, r=20, t=10, b=10),
                        yaxis={"categoryorder": "total ascending"},
                        showlegend=False, coloraxis_showscale=False,
                    )
                    fig2.update_traces(textposition="outside")
                    st.plotly_chart(fig2, use_container_width=True)
                else:
                    st.info("No skill frequency data found.")
            except Exception as e:
                st.error(f"Error loading skill chart: {str(e)}")

        st.divider()

        # ── Momentum Badges ───────────────────────────────────────────────────────
        st.subheader("Skill Momentum")
        st.caption(f"Comparing last {days_sel} days vs previous {days_sel} days")

        momentum_data = _cached_momentum(days_sel, sidebar_location)

        if momentum_data and momentum_data.get("badges"):
            _warn(momentum_data.get("metadata", {}).get("data_quality_warnings", []))
            badges = momentum_data["badges"]

            # Split into up / down / stable
            up_badges   = [b for b in badges if b["trend"] == "up"][:5]
            down_badges = [b for b in badges if b["trend"] == "down"][:5]
            stable_badges = [b for b in badges if b["trend"] == "stable"][:5]

            mc1, mc2, mc3 = st.columns(3)
            for col, group, title, css in [
                (mc1, up_badges,     "🟢 Rising",  "badge-up"),
                (mc2, down_badges,   "🔴 Declining","badge-down"),
                (mc3, stable_badges, "🟡 Stable",  "badge-stable"),
            ]:
                with col:
                    st.markdown(f"**{title}**")
                    if group:
                        for b in group:
                            sign = "+" if b["change_pct"] >= 0 else ""
                            st.markdown(
                                f'<div style="margin-bottom:8px">'
                                f'<span class="{css}" style="font-size:15px; background:rgba(0,0,0,0.03); padding:4px 10px; border-radius:12px;">'
                                f'{b["arrow"]} {b["skill"]}</span>'
                                f' <small style="color:#6b7280; display:block; margin-left:12px; margin-top:2px;">'
                                f'{sign}{b["change_pct"]:.1f}% growth · {b["current_count"]} jobs</small>'
                                f'</div>',
                                unsafe_allow_html=True,
                            )
                    else:
                        st.info("📈 Skill momentum trends are being calculated from the last 30 days. Check back in a few hours for latest insights.")
        else:
            _api_error("momentum badges")

        st.divider()
        st.subheader("Domain Posting Concentration")
        st.caption("Higher saturation = fewer companies dominating postings")

        try:
            sat_data = _cached_saturation(days_sel, sidebar_location)
            if sat_data and sat_data.get("indicators"):
                df_sat = pd.DataFrame(sat_data["indicators"])
                potential_hover = ["posting_density", "interpretation", "unique_companies"]
                valid_hover = [col for col in potential_hover if col in df_sat.columns]
                fig3 = px.scatter(
                    df_sat, x="job_count", y="saturation_score", text="domain",
                    size="unique_companies" if "unique_companies" in df_sat.columns else None,
                    color="saturation_score", color_continuous_scale="RdYlGn_r",
                    labels={"job_count": "Job Count", "saturation_score": "Concentration Score", "unique_companies": "Unique Companies"},
                    hover_data=valid_hover, height=400,
                )
                fig3.update_traces(textposition="top center", textfont_size=11)
                fig3.update_layout(margin=dict(l=0, r=20, t=10, b=10), coloraxis_showscale=False, xaxis_title="Market Job Volume", yaxis_title="Industry Concentration")
                st.plotly_chart(fig3, use_container_width=True)
            else:
                st.info("Insufficient data to analyze domain concentration.")
        except Exception as e:
            st.error(f"Error loading concentration chart: {str(e)}")

    except Exception as e:
        st.error("⚠️ The Market Pulse section could not be fully loaded.")
        st.caption(f"Reason: {str(e).split(':')[0]}...")


# ═════════════════════════════════════════════════════════════════════════════
# TAB 2 — DOMAIN COMPARISON
# ═════════════════════════════════════════════════════════════════════════════

with tab2:
    try:
        st.header("Domain Comparison")

        # Domain selector
        all_domains = []
        if filter_opts and "domains" in filter_opts:
            all_domains = filter_opts["domains"]

        selected_domains = st.multiselect(
            "Select 2–5 domains to compare",
            options=all_domains,
            default=all_domains[:3] if len(all_domains) >= 3 else all_domains,
            max_selections=5,
        )

        t2_fresher = st.toggle("Fresher-eligible jobs only", value=True, key="t2_fresher")
        t2_days = st.slider("Window (days)", 15, 180, 60, 15, key="t2_days")

        if len(selected_domains) < 2:
            st.info("Select at least 2 domains to compare.")
        else:
            comp_data = _cached_compare(
                tuple(selected_domains), t2_fresher, t2_days, sidebar_location
            )

            if not comp_data or not comp_data.get("domains"):
                _api_error("domain comparison")
            else:
                domains_list = comp_data["domains"]
                _warn(comp_data.get("metadata", {}).get("data_quality_warnings", []))

                # ── Per-domain metric columns ───────────────────────────────────
                cols = st.columns(len(domains_list))
                for col, d in zip(cols, domains_list):
                    with col:
                        st.markdown(f"### {d.get('domain', 'Unknown')}")
                        st.metric("Jobs", f"{d.get('job_count', 0):,}")
                        st.metric("Companies", f"{d.get('unique_companies', 0):,}")
                        st.metric("Fresher eligible", f"{d.get('fresher_eligible_pct', 0):.0f}%")
                        st.metric("Posting density", f"{d.get('posting_density', 0):.1f}×")
                        
                        # Safe Salary Handling (Fixes the Float error)
                        sal = d.get("salary")
                        if isinstance(sal, dict) and sal.get("available"):
                            st.metric("Median salary", f"₹{sal.get('median', 0):.1f}L")
                            _salary_note(f"{sal.get('coverage_pct', 0):.0f}% coverage")
                        else:
                            st.metric("Median salary", "Estimation in progress...")
                            note = sal.get("note", "No data") if isinstance(sal, dict) else "Insufficient data"
                            _salary_note(note)

                st.divider()

                col2a, col2b = st.columns(2, gap="large")

                # ── Top skills per domain ────────────────────────────────────────
                with col2a:
                    st.subheader("Top Skills per Domain")
                    skill_rows = []
                    for d in domains_list:
                        # Safely get top_skills list
                        skills = d.get("top_skills", [])
                        if not isinstance(skills, list):
                            skills = []
                            
                        for rank, sk in enumerate(skills[:8], 1):
                            skill_rows.append({
                                "domain": d.get("domain", "Unknown"), 
                                "skill": sk, 
                                "rank": rank
                            })
                    if skill_rows:
                        df_skills_dom = pd.DataFrame(skill_rows)
                        # Pivot for grouped display
                        pivot = df_skills_dom.pivot_table(
                            index="skill", columns="domain", values="rank", aggfunc="min"
                        ).fillna("—")
                        st.dataframe(pivot, use_container_width=True, height=300)

                # ── Skill overlap matrix ──────────────────────────────────────────
                with col2b:
                    st.subheader("Skill Cross-Overlap")
                    mat_data = _cached_skill_matrix(tuple(selected_domains), t2_days, t2_fresher)
                    
                    if mat_data and "matrix" in mat_data:
                        dom_cols = mat_data.get("domains", selected_domains)
                        skills_rows = mat_data.get("skills", [])
                        
                        mat_matrix = [
                            [mat_data["matrix"].get(sk, {}).get(d, 0) for d in dom_cols] 
                            for sk in skills_rows
                        ]
                        
                        if skills_rows and dom_cols:
                            fig_mat = ff.create_annotated_heatmap(
                                z=mat_matrix,
                                x=[d[:12] for d in dom_cols],
                                y=skills_rows,
                                annotation_text=[[f"{v}%" for v in row] for row in mat_matrix],
                                colorscale='Viridis'
                            )
                            fig_mat.update_layout(height=300, margin=dict(l=0, r=0, t=30, b=0))
                            st.plotly_chart(fig_mat, use_container_width=True)
                        else:
                            st.write("Insufficient data for skill matrix.")

                st.divider()

                # ── Skill × Domain heatmap ────────────────────────────────────────
                st.subheader("Skill × Domain Frequency Heatmap")
                st.caption("How often each skill appears in postings for each domain (%)")

                mat_data = _cached_skill_matrix(tuple(selected_domains), t2_days, t2_fresher)
                if mat_data and mat_data.get("matrix"):
                    skills_rows = mat_data["skills"][:25]  # cap at 25 for readability
                    dom_cols    = mat_data["domains"]
                    mat_matrix  = [[mat_data["matrix"].get(sk, {}).get(d, 0) for d in dom_cols] for sk in skills_rows]

                    fig_sk_heat = go.Figure(go.Heatmap(
                        z=mat_matrix,
                        x=dom_cols,
                        y=skills_rows,
                        colorscale="Teal",
                        text=[[f"{v:.0f}%" for v in row] for row in mat_matrix],
                        texttemplate="%{text}",
                        hovertemplate="<b>%{y}</b> in <b>%{x}</b>: %{z:.1f}%<extra></extra>",
                    ))
                    fig_sk_heat.update_layout(
                        height=max(350, len(skills_rows) * 20),
                        margin=dict(l=0, r=0, t=10, b=0),
                    )
                    st.plotly_chart(fig_sk_heat, use_container_width=True)
                else:
                    _api_error("skill matrix")

                st.divider()

                # ── Fresher deep-dive ────────────────────────────────────────────
                st.subheader("Fresher Deep-Dive")
                fd_domain = st.selectbox("Select domain for fresher analysis",
                                         [d["domain"] for d in domains_list],
                                         key="fd_domain")
                if fd_domain:
                    try:
                        fd = api.cc_fresher_analysis(fd_domain, t2_days, sidebar_location)
                        if fd:
                            fa1, fa2, fa3 = st.columns(3)
                            fa1.metric("Total domain jobs", f"{fd['total_domain_jobs']:,}")
                            fa2.metric("Fresher jobs", f"{fd['fresher_jobs']:,}")
                            fa3.metric("Fresher %", f"{fd['fresher_pct']:.1f}%")
                    except AttributeError:
                        st.info("🕒 Fresher analysis for this domain is currently being processed.")
                        fd = None
                    except Exception as e:
                        st.error(f"Unable to load fresher analysis: {str(e)}")
                        fd = None

                    if fd:

                        if fd.get("top_fresher_skills"):
                            st.markdown("**Top skills in fresher postings:**")
                            st.write(" · ".join(fd["top_fresher_skills"][:15]))

                        if fd.get("top_fresher_companies"):
                            co_df = pd.DataFrame(fd["top_fresher_companies"])
                            fig_co = px.bar(co_df, x="job_count", y="company",
                                            orientation="h", height=250,
                                            labels={"job_count": "Fresher Jobs", "company": ""},
                                            title="Top Companies Hiring Freshers")
                            fig_co.update_layout(
                                margin=dict(l=0, r=10, t=30, b=0),
                                yaxis={"categoryorder": "total ascending"},
                            )
                            st.plotly_chart(fig_co, use_container_width=True)
                    else:
                        _api_error("fresher analysis")
    except Exception as e:
        st.error("⚠️ The Domain Comparison section encountered a problem.")
        st.caption(f"Reason: {str(e).split(':')[0]}...")


# ═════════════════════════════════════════════════════════════════════════════
# TAB 3 — SKILL GAP ANALYZER
# ═════════════════════════════════════════════════════════════════════════════

with tab3:
    try:
        st.header("Skill Gap Analyzer")
        st.caption("Most important feature — tells a student exactly what to learn next.")

        sg_col1, sg_col2 = st.columns([1, 2], gap="large")

        with sg_col1:
            st.subheader("Student Profile")

            # Target domain
            sg_domain = st.selectbox(
                "Target domain",
                options=all_domains,
                key="sg_domain",
            )

            # Load popular skills for this domain to pre-populate multiselect
            popular_skills_raw = []
            if sg_domain:
                cached = _cached_popular_skills(sg_domain, True)
                if cached:
                    popular_skills_raw = [s["skill"] for s in cached]

            # Student skills multiselect
            student_skills_sel = st.multiselect(
                "Student's current skills",
                options=popular_skills_raw,
                help="Loaded from top skills in the target domain. Add yours.",
                key="sg_skills",
            )

            # Free-text additional skills
            extra_text = st.text_input(
                "Add more skills (comma-separated)",
                placeholder="e.g. docker, git, linux",
                key="sg_extra",
            )
            if extra_text:
                extra = [s.strip() for s in extra_text.split(",") if s.strip()]
                student_skills_sel = list(set(student_skills_sel + extra))

            sg_fresher = st.toggle("Fresher jobs only", value=True, key="sg_fresher")
            sg_location = st.selectbox("Location filter", ["All (National)"] + (
                filter_opts["locations"] if filter_opts else []
            ), key="sg_loc")
            sg_loc_val = None if sg_location == "All (National)" else sg_location

            analyze_btn = st.button("🔍 Analyze Skill Gap", type="primary", use_container_width=True)

        with sg_col2:
            if analyze_btn:
                if not student_skills_sel:
                    st.warning("Please select at least one skill.")
                elif not sg_domain:
                    st.warning("Please select a target domain.")
                else:
                    with st.spinner("Analyzing skill gap..."):
                        gap = api.cc_skill_gap_analyze(
                            student_skills=student_skills_sel,
                            target_domain=sg_domain,
                            days=60,
                            location=sg_loc_val,
                            fresher_only=sg_fresher,
                        )

                    if not gap:
                        _api_error("skill gap analysis")
                    else:
                        # ── Match percentage progress bar ──────────────────────
                        match_pct = gap.get("match_percentage", 0)
                        total_jobs = gap.get("total_domain_jobs", 0)
                        accessible = gap.get("jobs_accessible_now", 0)

                        st.subheader(f"Results: {sg_domain}")

                        # Big progress bar
                        bar_color = "#15803d" if match_pct >= 70 else "#d97706" if match_pct >= 40 else "#dc2626"
                        st.markdown(
                            f"""
                            <div style="margin-bottom:8px">
                              <div style="font-size:14px;color:#374151;margin-bottom:4px">
                                Skill Match: <strong style="color:{bar_color}">{match_pct:.1f}%</strong>
                              </div>
                              <div style="background:#e5e7eb;border-radius:8px;height:18px">
                                <div style="background:{bar_color};width:{min(match_pct,100):.0f}%;
                                            height:18px;border-radius:8px"></div>
                              </div>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )

                        am1, am2, am3 = st.columns(3)
                        am1.metric("Domain jobs", f"{total_jobs:,}")
                        am2.metric("Accessible now", f"{accessible:,}")
                        am3.metric("Skills matched", f"{len(gap.get('matched_skills', []))} / {len(gap.get('matched_skills', [])) + len(gap.get('missing_skills', []))}")

                        # ── Impact cards ──────────────────────────────────────
                        if gap.get("impact_summary"):
                            st.markdown("**Actionable Insights**")
                            for msg in gap["impact_summary"]:
                                st.markdown(f'<div class="impact-card">✅ {msg}</div>',
                                            unsafe_allow_html=True)

                        # ── Missing skills bar chart ───────────────────────────
                        missing = gap.get("missing_skills", [])
                        if missing:
                            st.markdown("**Missing Skills — ranked by jobs unlocked**")
                            df_miss = pd.DataFrame(missing[:15])
                            fig_miss = px.bar(
                                df_miss,
                                x="extra_jobs_if_added",
                                y="skill",
                                orientation="h",
                                color="frequency_pct",
                                color_continuous_scale="Oranges",
                                text="extra_jobs_if_added",
                                labels={
                                    "extra_jobs_if_added": "Extra jobs unlocked",
                                    "skill": "",
                                    "frequency_pct": "Domain freq %",
                                },
                                height=max(250, len(df_miss) * 28),
                            )
                            fig_miss.update_layout(
                                margin=dict(l=0, r=20, t=10, b=0),
                                yaxis={"categoryorder": "total ascending"},
                                coloraxis_colorbar=dict(title="Freq %", thickness=12),
                            )
                            fig_miss.update_traces(textposition="outside")
                            st.plotly_chart(fig_miss, use_container_width=True)

                        # ── Matched skills pills ───────────────────────────────
                        matched = gap.get("matched_skills", [])
                        if matched:
                            st.markdown("**Skills you already have ✓**")
                            pills_html = " ".join(
                                f'<span style="background:#dcfce7;color:#166534;padding:3px 10px;'
                                f'border-radius:12px;font-size:13px;margin:2px;display:inline-block">'
                                f'✓ {sk}</span>'
                                for sk in matched
                            )
                            st.markdown(pills_html, unsafe_allow_html=True)

                        # ── Recommended learning path ─────────────────────────
                        recs = gap.get("recommended_skills", [])
                        if recs:
                            st.markdown("**Recommended Learning Path**")
                            for i, sk in enumerate(recs[:8], 1):
                                freq_item = next((m for m in missing if m["skill"] == sk), None)
                                freq_str = f" · appears in {freq_item['frequency_pct']:.0f}% of jobs" if freq_item else ""
                                st.markdown(f"{i}. **{sk}**{freq_str}")

                        # ── Benchmark roles ────────────────────────────────────
                        roles = gap.get("top_benchmark_roles", [])
                        if roles:
                            with st.expander("Sample benchmark roles"):
                                for r in roles:
                                    color = "#15803d" if r["match_pct"] >= 60 else "#6b7280"
                                    st.markdown(
                                        f'<span style="color:{color};font-weight:600">'
                                        f'{r["match_pct"]:.0f}%</span> match — '
                                        f'**{r["title"]}** @ {r["company"]}',
                                        unsafe_allow_html=True,
                                    )

                        _warn(gap.get("metadata", {}).get("data_quality_warnings", []))
            else:
                st.info("Configure the student profile on the left and click **Analyze Skill Gap**.")
    except Exception as e:
        st.error("⚠️ The Skill Gap Analyzer encountered a problem.")
        st.caption(f"Reason: {str(e).split(':')[0]}...")

# ═════════════════════════════════════════════════════════════════════════════
# TAB 4 — SALARY INTELLIGENCE
# ═════════════════════════════════════════════════════════════════════════════

with tab4:
    try:
        st.header("Salary Intelligence")
        st.markdown(
            '<div class="warn-box">⚠ ~80% of Naukri postings mark salary as "not disclosed". '
            "All figures are estimates from the <strong>disclosed subset only</strong>. "
            "Always mention this caveat to students.</div>",
            unsafe_allow_html=True,
        )
        st.markdown("")

        sal_domain   = st.selectbox("Domain filter", ["All domains"] + all_domains, key="sal_domain")
        sal_dom_val  = None if sal_domain == "All domains" else sal_domain
        sal_location = st.selectbox("Location", ["All (National)", "Jaipur"], key="sal_location")
        sal_loc_val  = None if sal_location == "All (National)" else sal_location

        sal1, sal2 = st.columns(2, gap="large")

        # ── Salary ranges ─────────────────────────────────────────────────────────
        with sal1:
            st.subheader("Salary Distribution")
            ranges = _cached_salary_ranges(sal_dom_val, sal_loc_val, True)

            if ranges:
                sal_info = ranges.get("salary", {})
                if sal_info.get("available"):
                    _salary_note(sal_info.get("note", ""))
                    # Box-like visualization with percentile bars
                    perc_labels = ["p10", "p25", "median", "p75", "p90"]
                    perc_vals   = [sal_info.get(p) for p in perc_labels]
                    perc_vals   = [v for v in perc_vals if v is not None]

                    if perc_vals:
                        fig_box = go.Figure()
                        fig_box.add_trace(go.Bar(
                            x=perc_labels[:len(perc_vals)],
                            y=perc_vals,
                            marker_color=["#bfdbfe", "#93c5fd", "#3b82f6", "#1d4ed8", "#1e3a8a"],
                            text=[f"₹{v:.1f}L" for v in perc_vals],
                            textposition="outside",
                        ))
                        fig_box.update_layout(
                            yaxis_title="LPA",
                            height=280,
                            margin=dict(l=0, r=10, t=10, b=0),
                            showlegend=False,
                        )
                        st.plotly_chart(fig_box, use_container_width=True)

                        sc1, sc2, sc3 = st.columns(3)
                        # Safe logic for multiple possible key names
                        min_v = sal_info.get("min") or sal_info.get("Min") or sal_info.get("p25") or sal_info.get("low") or 0
                        med_v = sal_info.get("median") or sal_info.get("Median") or sal_info.get("p50") or 0
                        max_v = sal_info.get("max") or sal_info.get("Max") or sal_info.get("p75") or 0
                        
                        sc1.metric("Min (disclosed)", f"₹{min_v:.1f}L" if min_v > 0 else "—")
                        sc2.metric("Median (est)", f"₹{med_v:.1f}L" if med_v > 0 else "Estimation pending")
                        sc3.metric("Max (disclosed)", f"₹{max_v:.1f}L" if max_v > 0 else "—")
                else:
                    st.warning(sal_info.get("note", "Salary data insufficient for this filter."))
            else:
                _api_error("salary ranges")

        # ── Jaipur vs National ────────────────────────────────────────────────────
        with sal2:
            st.subheader("Jaipur vs National")
            jvn = _cached_jaipur_vs_national(sal_dom_val, True)

            if jvn:
                j_sal = jvn.get("jaipur", {})
                n_sal = jvn.get("national", {})
                comp  = jvn.get("comparison", {})
                # Guard against API returning a float instead of a dict
                if not isinstance(j_sal, dict): j_sal = {}
                if not isinstance(n_sal, dict): n_sal = {}
                if not isinstance(comp,  dict): comp  = {}

                if j_sal.get("available") and n_sal.get("available"):
                    try:
                        # Defensive percentile access
                        j_p25 = j_sal.get("p25") or 0
                        j_med = j_sal.get("median") or 0
                        j_p75 = j_sal.get("p75") or 0
                        n_p25 = n_sal.get("p25") or 0
                        n_med = n_sal.get("median") or 0
                        n_p75 = n_sal.get("p75") or 0

                        fig_jvn = go.Figure(data=[
                            go.Bar(name="Jaipur",   x=["p25", "Median", "p75"],
                                   y=[j_p25, j_med, j_p75],
                                   marker_color="#f97316"),
                            go.Bar(name="National", x=["p25", "Median", "p75"],
                                   y=[n_p25, n_med, n_p75],
                                   marker_color="#3b82f6"),
                        ])
                        fig_jvn.update_layout(
                            barmode="group",
                            yaxis_title="LPA",
                            height=280,
                            margin=dict(l=0, r=10, t=10, b=0),
                            legend=dict(orientation="h", yanchor="bottom", y=1.02),
                        )
                        st.plotly_chart(fig_jvn, use_container_width=True)

                        if comp.get("available") and comp.get("jaipur_lower_by_pct") is not None:
                            st.markdown(
                                f'<div class="warn-box">Jaipur median is '
                                f'<strong>{comp["jaipur_lower_by_pct"]:.1f}% lower</strong>'
                                f' than national. {comp.get("note", "")}</div>',
                                unsafe_allow_html=True,
                            )
                    except Exception as e:
                        st.caption(f"Unable to compare exactly: {str(e)[:50]}...")
                else:
                    # Show whichever is available
                    for label, sal in [("Jaipur", j_sal), ("National", n_sal)]:
                        if not sal.get("available"):
                            st.warning(f"{label}: {sal.get('note', 'Insufficient data')}")
            else:
                _api_error("Jaipur vs national")

        st.divider()

        sal3, sal4 = st.columns(2, gap="large")

        # ── Salary by experience band ─────────────────────────────────────────────
        with sal3:
            st.subheader("Salary by Experience Band")
            bands = _cached_salary_by_exp(sal_dom_val, sal_loc_val)

            if bands:
                band_rows = []
                for b in bands:
                    sal_b = b.get("salary", {})
                    if not isinstance(sal_b, dict):
                        sal_b = {}
                    if sal_b.get("available"):
                        band_rows.append({
                            "band": b["band_label"],
                            "median": sal_b["median"],
                            "p25": sal_b["p25"],
                            "p75": sal_b["p75"],
                            "jobs": b["job_count"],
                        })
                if band_rows:
                    df_bands = pd.DataFrame(band_rows)
                    fig_bands = go.Figure()
                    fig_bands.add_trace(go.Bar(
                        x=df_bands["band"],
                        y=df_bands["median"],
                        error_y=dict(
                            type="data",
                            symmetric=False,
                            array=(df_bands["p75"] - df_bands["median"]).tolist(),
                            arrayminus=(df_bands["median"] - df_bands["p25"]).tolist(),
                        ),
                        marker_color="#6366f1",
                        text=[f"₹{v:.1f}L" for v in df_bands["median"]],
                        textposition="outside",
                    ))
                    fig_bands.update_layout(
                        yaxis_title="Median LPA",
                        height=260,
                        margin=dict(l=0, r=10, t=10, b=0),
                    )
                    st.plotly_chart(fig_bands, use_container_width=True)
                    _salary_note("Error bars show p25–p75 range. All figures from disclosed salary only.")
                else:
                    st.warning("Insufficient salary data across experience bands for this filter.")
            else:
                _api_error("salary by experience")

        # ── Top premium skills ─────────────────────────────────────────────────────
        with sal4:
            st.subheader("Skills in Top-10% Salary Jobs")
            st.caption("premium_signal = how much more common in high-salary vs average postings")

            top_sal_skills = _cached_salary_top_skills(sal_dom_val, sal_loc_val)

            if top_sal_skills:
                df_prem = pd.DataFrame(top_sal_skills[:12])
                fig_prem = px.bar(
                    df_prem,
                    x="premium_signal",
                    y="skill",
                    orientation="h",
                    color="premium_signal",
                    color_continuous_scale="Greens",
                    text=df_prem["premium_signal"].apply(lambda x: f"{x:.1f}×"),
                    labels={"premium_signal": "Premium Signal", "skill": ""},
                    height=340,
                )
                fig_prem.update_layout(
                    margin=dict(l=0, r=20, t=10, b=0),
                    yaxis={"categoryorder": "total ascending"},
                    coloraxis_showscale=False,
                )
                fig_prem.update_traces(textposition="outside")
                st.plotly_chart(fig_prem, use_container_width=True)
                _salary_note("Survivorship bias: only companies that disclosed salary are included.")
            else:
                st.warning("Insufficient salary data to compute premium signals for this filter.")
    except Exception as e:
        st.error("⚠️ The Salary Intelligence section encountered a problem.")
        st.caption(f"Reason: {str(e).split(':')[0]}...")


# ═════════════════════════════════════════════════════════════════════════════
# TAB 5 — COMPANY INTELLIGENCE
# ═════════════════════════════════════════════════════════════════════════════

with tab5:
    try:
        st.header("Company Intelligence")

        ci_domain   = st.selectbox("Domain filter", ["All domains"] + all_domains, key="ci_domain")
        ci_dom_val  = None if ci_domain == "All domains" else ci_domain
        ci_fresher  = st.toggle("Fresher jobs only", value=False, key="ci_fresher")

        ci1, ci2 = st.columns([1.6, 1], gap="large")

        # ── Top hiring companies table ─────────────────────────────────────────────
        with ci1:
            st.subheader("Top Hiring Companies")
            co_data = _cached_top_companies(ci_dom_val, days_sel, sidebar_location, ci_fresher, 15)

            if co_data and co_data.get("companies"):
                companies = co_data["companies"]
                rows = []
                for c in companies:
                    sal = c.get("salary", {})
                    if not isinstance(sal, dict):
                        sal = {}
                    rows.append({
                        "Company":      c["company"],
                        "Jobs":         c["job_count"],
                        "Fresher Jobs": c["fresher_jobs"],
                        "Fresher %":    f"{c['fresher_pct']:.0f}%",
                        "Type":         c["estimated_type"],
                        "Salary (med)": f"₹{sal['median']:.1f}L" if sal.get("available") else "Estimation in progress...",
                    })
                df_co = pd.DataFrame(rows)
                st.dataframe(
                    df_co,
                    use_container_width=True,
                    height=380,
                    hide_index=True,
                )
                _salary_note("Company type classification is estimated from name patterns.")
            else:
                _api_error("top companies")

        # ── Service / Product / Startup split ────────────────────────────────────
        with ci2:
            st.subheader("Company Type Mix")
            type_data = _cached_type_split(ci_dom_val, days_sel, sidebar_location, ci_fresher)

            if type_data and type_data.get("type_split"):
                ts = type_data["type_split"]
                pie_labels = list(ts.keys())
                pie_vals   = [ts[t]["job_count"] for t in pie_labels]
                pie_colors = ["#6366f1", "#10b981", "#f59e0b"]

                fig_pie = go.Figure(go.Pie(
                    labels=pie_labels,
                    values=pie_vals,
                    marker_colors=pie_colors,
                    hole=0.45,
                    textinfo="label+percent",
                ))
                fig_pie.update_layout(
                    height=280,
                    margin=dict(l=0, r=0, t=10, b=0),
                    showlegend=False,
                )
                st.plotly_chart(fig_pie, use_container_width=True)
                _salary_note(type_data.get("note", "Classification is heuristic."))

                # Sample companies per type
                for ctype, cdata in ts.items():
                    with st.expander(f"{ctype} — {cdata['unique_companies']} companies, {cdata['pct']:.0f}% of jobs"):
                        samples = cdata.get("sample_companies", [])
                        st.write(", ".join(samples) if samples else "—")
            else:
                _api_error("company type split")

        st.divider()

        # ── Jaipur companies highlight ─────────────────────────────────────────────
        st.subheader("🗺 Jaipur Hiring Snapshot")
        jaipur_co = _cached_jaipur_companies(ci_dom_val, days_sel, ci_fresher)

        if jaipur_co:
            jc1, jc2, jc3 = st.columns(3)
            jc1.metric("Jaipur jobs", f"{jaipur_co.get('total_jaipur_jobs', 0):,}")
            jc2.metric("National jobs", f"{jaipur_co.get('total_national_jobs', 0):,}")
            jc3.metric("Jaipur share", f"{jaipur_co.get('jaipur_share_pct', 0):.1f}%")

            jco_list = jaipur_co.get("companies", [])
            if jco_list:
                df_jco = pd.DataFrame([{
                    "Company":  c["company"],
                    "Jobs":     c["job_count"],
                    "Fresher":  c["fresher_jobs"],
                    "Type":     c["estimated_type"],
                } for c in jco_list])
                fig_jco = px.bar(
                    df_jco.head(15),
                    x="Jobs", y="Company", orientation="h",
                    color="Type",
                    color_discrete_map={"Service": "#6366f1", "Product": "#10b981", "Startup": "#f59e0b"},
                    height=380,
                    labels={"Jobs": "Job Count", "Company": ""},
                )
                fig_jco.update_layout(
                    margin=dict(l=0, r=20, t=10, b=0),
                    yaxis={"categoryorder": "total ascending"},
                    legend=dict(orientation="h", yanchor="bottom", y=1.02),
                )
                st.plotly_chart(fig_jco, use_container_width=True)
            else:
                st.info("No companies found hiring in Jaipur for this filter.")
        else:
            _api_error("Jaipur companies")

        st.divider()

        # ── Hiring frequency for a specific company ────────────────────────────────
        st.subheader("Company Hiring Frequency")
        all_companies = filter_opts["companies"] if filter_opts and "companies" in filter_opts else []
        co_sel = st.selectbox("Select a company", [""] + all_companies, key="co_freq_sel")

        if co_sel:
            freq = api.cc_hiring_frequency(co_sel, days=90)
            if freq and freq.get("weekly_buckets"):
                hf1, hf2, hf3 = st.columns(3)
                hf1.metric("Total jobs (90d)", freq.get("total_jobs", 0))
                hf2.metric("Avg / week", f"{freq.get('avg_jobs_per_week', 0):.1f}")
                hf3.metric("Peak week", freq.get("peak_week") or "—")

                df_freq = pd.DataFrame(freq["weekly_buckets"])
                if not df_freq.empty:
                    fig_freq = px.bar(
                        df_freq, x="week_start", y="job_count",
                        labels={"week_start": "Week", "job_count": "Jobs Posted"},
                        height=220,
                    )
                    fig_freq.update_layout(margin=dict(l=0, r=10, t=10, b=0))
                    st.plotly_chart(fig_freq, use_container_width=True)
            elif freq:
                st.info(f"No weekly posting data found for {co_sel} in the last 90 days.")
            else:
                _api_error(f"hiring frequency for {co_sel}")
    except Exception as e:
        st.error("⚠️ The Company Intelligence section encountered a problem.")
        st.caption(f"Reason: {str(e).split(':')[0]}...")