"""
fresher_dashboard.py
Unified dashboard for freshers and intermediate learners.
Domain Confusion Resolver + skill path, salary, market, gap, and upskilling sections.
All calculations go through Flask API (dashboards.utils.api_client).
"""

from __future__ import annotations

from typing import Any, Dict, Optional

import streamlit as st

from dashboards.components.domain_confusion_resolver import render_path_1_flow
from dashboards.utils import api_client


def render_path() -> None:
    """
    Path selection for the Domain Confusion Resolver tab.
    Path 2 ('I Know My Domain') is retired — clicking it now redirects
    the user to the Skill Gap Analyzer tab with an inline prompt.
    """
    if "path_choice" not in st.session_state:
        st.session_state.path_choice = None

    col1, col2 = st.columns(2)

    with col1:
        is_p1 = st.session_state.path_choice == "help_me_decide"
        if st.button(
            "🤔 Help Me Decide",
            use_container_width=True,
            type="primary" if is_p1 else "secondary",
            key="fd_btn_p1",
        ):
            st.session_state.path_choice = "help_me_decide"
            st.rerun()

    with col2:
        if st.button(
            "🚀 I Know My Domain → Skill Gap Analyzer",
            use_container_width=True,
            type="secondary",
            key="fd_btn_p2",
            help="Takes you to the Skill Gap Analyzer",
        ):
            st.session_state.path_choice = "know_my_domain"
            st.rerun()

    st.divider()


def _is_fresher_profile_ready() -> bool:
    """
    Tabs 2–6 require a profile: either explicit ``st.session_state['user_profile']``
    (non-empty dict) OR Profile Selection with persona **Fresher**.
    Tab 1 (Domain Confusion) is always available.
    """
    up = st.session_state.get("user_profile")
    if isinstance(up, dict) and len(up) > 0:
        return True
    pd: Dict[str, Any] = st.session_state.get("profile_data") or {}
    return pd.get("persona") == "Fresher"


def _user_profile_for_api() -> Dict[str, Any]:
    """
    Merge explicit st.session_state['user_profile'] with safe defaults for API calls.
    """
    defaults: Dict[str, Any] = {
        "experience": "Fresher",
        "skills": ["Python"],
        "location": "Jaipur",
        "math_comfort": "Moderate",
    }
    raw = st.session_state.get("user_profile")
    if isinstance(raw, dict) and raw:
        out = {**defaults, **raw}
        if not out.get("skills"):
            out["skills"] = ["Python"]
        return out
    return defaults


def _profile_gate_message() -> None:
    st.warning(
        "Please complete profile first — set **Profile Selection → Fresher**, "
        "or define **user_profile** in session (skills, experience, location)."
    )


def _render_tab_skill_path() -> None:
    st.subheader("🛤️ Skill Path Generator")
    st.caption("Personalised learning direction from the API (freshers & intermediate learners).")

    col_a, col_b = st.columns(2)
    with col_a:
        exp = st.selectbox(
            "Experience band",
            ["Fresher", "1-2 years", "3-5 years", "5+ years"],
            key="fd_skill_exp",
        )
    with col_b:
        loc = st.selectbox(
            "Preferred location",
            ["Jaipur", "Bangalore", "Hyderabad", "Pune", "Delhi NCR"],
            key="fd_skill_loc",
        )
    skills = st.multiselect(
        "Skills you already have",
        [
            "Python", "SQL", "Machine Learning", "Statistics", "Pandas",
            "HTML", "CSS", "JavaScript", "React", "Node.js",
            "Docker", "AWS", "Java", "APIs", "LLMs",
        ],
        key="fd_skill_skills",
    )

    if st.button("Get skill-path hints from API", key="fd_skill_fetch", type="primary"):
        profile = _user_profile_for_api()
        profile["experience"] = exp
        profile["location"] = loc
        profile["skills"] = skills if skills else ["Python"]
        with st.spinner("Fetching recommendations from server…"):
            recs = api_client.get_recommendations(profile, top_n=3)
        if recs:
            st.session_state["fd_skill_path_recs"] = recs
            st.session_state["user_profile"] = profile
        else:
            st.error("Could not load data from API. Is the Flask server running?")
            st.session_state["fd_skill_path_recs"] = None

    recs = st.session_state.get("fd_skill_path_recs")
    if recs:
        st.success("Top domains to focus your learning (API)")
        for r in recs:
            with st.expander(f"{r.get('domain', 'Domain')} — {r.get('match_percentage', 0)}% match"):
                st.write("**Timeline:**", r.get("timeline", "—"))
                st.write("**Salary hint:**", r.get("market_metrics", {}).get("avg_starting_salary", "—"))
                for line in r.get("reasoning", []) or []:
                    st.markdown(f"- {line}")
    else:
        st.info("Submit your skills above to fetch API-driven path suggestions.")


def _render_tab_company_salary() -> None:
    st.subheader("🏢 Company & Salary Insight")
    st.caption("Salary and market context for a chosen domain (API).")

    domains = api_client.get_all_domains() or []
    if not domains:
        domains = ["Data Scientist", "Data Analyst", "Software Engineer"]

    dom = st.selectbox("Domain", domains, key="fd_cs_domain")
    loc = st.selectbox(
        "Location",
        ["Jaipur", "Bangalore", "Hyderabad", "Pune", "Delhi NCR"],
        key="fd_cs_loc",
    )

    if st.button("Load salary & market snapshot", key="fd_cs_btn", type="primary"):
        with st.spinner("Fetching domain analytics from server…"):
            bundle = api_client.get_domain_analytics(
                domain=dom,
                location=loc,
                experience_band=(0, 3),
                user_profile=None,
            )
        if bundle:
            st.session_state["fd_cs_bundle"] = bundle
        else:
            st.error("API request failed. Check Flask server.")
            st.session_state["fd_cs_bundle"] = None

    b = st.session_state.get("fd_cs_bundle")
    if not b:
        st.info("Pick a domain and load data from the API.")
        return

    da = b.get("domain_analytics") or {}
    sg = da.get("salary_growth") or {}
    ladder = sg.get("Experience_Ladder") or {}
    fresher = ladder.get("fresher") or {}

    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Fresher median (LPA)", f"{fresher.get('median', 0) or '—'}")
    with c2:
        st.metric("Fresher p25", f"{fresher.get('p25', 0) or '—'}")
    with c3:
        st.metric("Fresher p75", f"{fresher.get('p75', 0) or '—'}")

    st.markdown("---")
    st.markdown("**Raw bundle** (debug)")
    with st.expander("View JSON"):
        st.json(b)


def _render_tab_market_comparison() -> None:
    st.subheader("📊 Market Comparison Tool")
    st.caption("Compare two domains side by side via API demand signals.")

    dlist = api_client.get_all_domains() or ["Data Scientist", "Data Analyst", "Web Developer"]
    c1, c2 = st.columns(2)
    with c1:
        d_a = st.selectbox("Domain A", dlist, key="fd_mc_a")
    with c2:
        d_b = st.selectbox("Domain B", dlist, index=min(1, len(dlist) - 1), key="fd_mc_b")
    loc = st.selectbox("Location", ["Jaipur", "Bangalore", "Hyderabad"], key="fd_mc_loc")

    if st.button("Compare domains", key="fd_mc_btn", type="primary"):
        with st.spinner("Fetching analytics from server…"):
            a = api_client.get_domain_analytics(d_a, loc, (0, 3), None)
            b = api_client.get_domain_analytics(d_b, loc, (0, 3), None)
        st.session_state["fd_mc_pair"] = (d_a, d_b, a, b)

    quad = st.session_state.get("fd_mc_pair")
    if not quad or len(quad) != 4:
        st.info("Select two domains and run comparison.")
        return

    d_a_k, d_b_k, blob_a, blob_b = quad
    if not blob_a or not blob_b:
        st.error("One or both API calls failed.")
        return

    def _brief(blob: Dict[str, Any], domain_key: str) -> None:
        da = blob.get("domain_analytics") or {}
        sat = da.get("saturation") or {}
        md = (blob.get("global_analytics") or {}).get("market_demand") or {}
        stats: Dict[str, Any] = {}
        if isinstance(md, dict):
            stats = md.get(domain_key, {})
            if not stats:
                for k, v in md.items():
                    if str(k).lower() == str(domain_key).lower():
                        stats = v if isinstance(v, dict) else {}
                        break
        st.markdown(f"**{domain_key}**")
        st.write("Demand score:", stats.get("Overall_Demand_Score", "—"))
        st.write("Saturation risk:", sat.get("Risk_Level", "—"))

    colx, coly = st.columns(2)
    with colx:
        _brief(blob_a, d_a_k)
    with coly:
        _brief(blob_b, d_b_k)


def _render_tab_skill_gap() -> None:
    st.subheader("📉 Skill Gap Analyzer")
    st.caption("How well your profile fits one target domain (API).")

    dlist = api_client.get_all_domains() or ["Data Scientist", "Data Analyst"]
    target = st.selectbox("Target domain", dlist, key="fd_gap_dom")

    with st.form("fd_gap_form"):
        ex = st.selectbox("Experience", ["Fresher", "1-2 years", "3-5 years", "5+ years"])
        sk = st.multiselect(
            "Your skills",
            ["Python", "SQL", "Machine Learning", "React", "Java", "AWS"],
        )
        mc = st.select_slider("Math comfort", ["Weak", "Moderate", "Strong"])
        loc = st.selectbox("Location", ["Jaipur", "Bangalore", "Hyderabad"])
        submitted = st.form_submit_button("Analyse gap (API)")

    if submitted:
        prof = _user_profile_for_api()
        prof.update(
            {"experience": ex, "skills": sk or ["Python"], "math_comfort": mc, "location": loc}
        )
        with st.spinner("Fetching compatibility from server…"):
            fit = api_client.get_domain_compatibility(prof, target)
        st.session_state["fd_gap_result"] = fit

    fit = st.session_state.get("fd_gap_result")
    if fit:
        st.metric("Match %", f"{fit.get('match_percentage', 0)}")
        st.write("**Timeline:**", fit.get("timeline", "—"))
        for p in fit.get("pros", []) or []:
            st.success(p)
        for c in fit.get("cons", []) or []:
            st.warning(c)
    else:
        st.info("Submit the form to call the API.")


def _render_tab_upskilling() -> None:
    st.subheader("🚀 Upskilling Advisor")
    st.caption("API-driven next steps — aligned with fresher & intermediate journeys.")

    st.markdown(
        """
        **Suggested flow**
        1. Use **Domain Confusion Resolver** to shortlist domains.
        2. Run **Skill Gap** for your target role.
        3. Refresh recommendations here after you update skills.
        """
    )

    if st.button("Refresh upskilling recommendations", key="fd_up_btn"):
        with st.spinner("Fetching from server…"):
            recs = api_client.get_recommendations(_user_profile_for_api(), top_n=5)
        st.session_state["fd_up_recs"] = recs

    recs = st.session_state.get("fd_up_recs")
    if recs:
        for i, r in enumerate(recs):
            st.markdown(f"**{i + 1}. {r.get('domain')}** — {r.get('match_percentage')}%")
            st.caption(r.get("timeline", ""))
    else:
        st.info("Click the button above to load upskilling-oriented recommendations from the API.")


def render(navigate_to: Any = None) -> None:
    """
    Main entry for the Fresher dashboard.
    `navigate_to` is kept for compatibility with app.py routing.
    """
    _ = navigate_to

    st.title("👨‍🎓 Fresher & Intermediate Hub")
    st.caption("Personalised insights for freshers and intermediate learners — powered by the Flask API.")

    if "profile_data" not in st.session_state:
        st.session_state.profile_data = {}

    tabs = st.tabs(
        [
            "Domain Confusion Resolver",
            "Skill Path Generator",
            "Company & Salary Insight",
            "Market Comparison Tool",
            "Skill Gap Analyzer",
            "Upskilling Advisor",
        ]
    )

    (
        tab_resolver,
        tab_path,
        tab_company,
        tab_market,
        tab_gap,
        tab_upskilling,
    ) = tabs

    # ------------------------------------------------------------------ #
    # Tab 1 – Domain Confusion Resolver                                  #
    # ------------------------------------------------------------------ #
    with tab_resolver:
        st.markdown("### 🎯 Domain Confusion Resolver")
        st.markdown(
            "Compare domains, see market reality, and get recommendations — "
            "all data comes from the API via `domain_confusion_resolver`."
        )
        render_path()
        path = st.session_state.get("path_choice")
        if path == "help_me_decide":
            render_path_1_flow()
        elif path == "know_my_domain":
            st.markdown("""
<div style="padding:20px 24px; border-radius:12px;
     border:1px solid rgba(79,70,229,0.25);
     background:linear-gradient(135deg,rgba(79,70,229,0.06) 0%,rgba(99,102,241,0.03) 100%);
     margin-top:8px;">
  <div style="font-size:20px; font-weight:700; margin-bottom:8px;">
    🚀 You already know your domain — let's find your gaps
  </div>
  <div style="font-size:15px; color:var(--color-text-secondary); line-height:1.6; margin-bottom:16px;">
    The <strong>Skill Gap Analyzer</strong> is built exactly for this.
    Pick your target domain, add your current skills, and get a clear
    picture of what's missing and how long it'll take to close the gap.
  </div>
  <div style="font-size:13px; color:var(--color-text-tertiary);">
    👉 Click the <strong>Skill Gap Analyzer</strong> tab above to get started.
  </div>
</div>
""", unsafe_allow_html=True)
        else:
            st.info("👆 Choose **Help Me Decide** or **I Know My Domain** above to begin.")

    # ------------------------------------------------------------------ #
    # Tabs 2–6 – require Fresher profile                                 #
    # ------------------------------------------------------------------ #
    gated = not _is_fresher_profile_ready()

    with tab_path:
        if gated:
            _profile_gate_message()
        else:
            _render_tab_skill_path()

    with tab_company:
        if gated:
            _profile_gate_message()
        else:
            _render_tab_company_salary()

    with tab_market:
        if gated:
            _profile_gate_message()
        else:
            _render_tab_market_comparison()

    with tab_gap:
        if gated:
            _profile_gate_message()
        else:
            _render_tab_skill_gap()

    with tab_upskilling:
        if gated:
            _profile_gate_message()
        else:
            _render_tab_upskilling()