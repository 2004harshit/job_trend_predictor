
"""
fresher_dashboard.py
Entry-point page for the Fresher / Personalised Insights dashboard.
Handles global path selection and routes to the correct sub-components.
"""

import streamlit as st



# Domain Confusion Resolver sub-flows
from dashboards.components.domain_confusion_resolver import (
    render_path_1_flow,
    render_path_2_flow,
)

def render_path():
    # --- Global path selection (lives above the tabs) ---
    if "path_choice" not in st.session_state:
        st.session_state.path_choice = None

    col1, col2 = st.columns(2)

    with col1:
        is_p1 = st.session_state.path_choice == "help_me_decide"
        if st.button(
            "🤔 Help Me Decide (Path 1)",
            use_container_width=True,
            type="primary" if is_p1 else "secondary",
            key="fd_btn_p1",
        ):
            st.session_state.path_choice = "help_me_decide"
            st.rerun()

    with col2:
        is_p2 = st.session_state.path_choice == "know_my_domain"
        if st.button(
            "🚀 I Know My Domain (Path 2)",
            use_container_width=True,
            type="primary" if is_p2 else "secondary",
            key="fd_btn_p2",
        ):
            st.session_state.path_choice = "know_my_domain"
            st.rerun()

    st.divider()


def render():  
    st.title("👨‍🎓 Your Personalised Insights")

    # --- Tabs ---
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
    # Tab 1 – Domain Confusion Resolver                                    #
    # ------------------------------------------------------------------ #
    with tab_resolver:
      
        # render_path()
        
        path = st.session_state.get("path_choice")

        if path == "help_me_decide":
            render_path_1_flow()
        elif path == "know_my_domain":
            render_path_2_flow()
        else:
            st.info("👆 Please select a path above to begin your journey.")

    # ------------------------------------------------------------------ #
    # Tab 2 – Skill Path Generator (placeholder)                          #
    # ------------------------------------------------------------------ #
    with tab_path:
        st.info("🚧 Skill Path Generator coming soon.")

    # ------------------------------------------------------------------ #
    # Tab 3 – Company & Salary Insight (placeholder)                      #
    # ------------------------------------------------------------------ #
    with tab_company:
        st.info("🚧 Company & Salary Insight coming soon.")

    # ------------------------------------------------------------------ #
    # Tab 4 – Market Comparison Tool (placeholder)                        #
    # ------------------------------------------------------------------ #
    with tab_market:
        st.info("🚧 Market Comparison Tool coming soon.")

    # ------------------------------------------------------------------ #
    # Tab 5 – Skill Gap Analyzer (placeholder)                            #
    # ------------------------------------------------------------------ #
    with tab_gap:
        st.info("🚧 Skill Gap Analyzer coming soon.")

    # ------------------------------------------------------------------ #
    # Tab 6 – Upskilling Advisor (placeholder)                            #
    # ------------------------------------------------------------------ #
    with tab_upskilling:
        st.info("🚧 Upskilling Advisor coming soon.")