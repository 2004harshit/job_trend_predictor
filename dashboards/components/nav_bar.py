import streamlit as st
def render_navigation() -> None:
    """Render the top navigation bar in a single line"""
    
    # Ek hi row mein columns create karein
    # [3, 1, 1, 1] ka matlab hai Brand name zyada space lega, buttons kam
    col_brand, col_home, col_profile, col_login = st.columns([3, 1, 1, 1], vertical_alignment="center")

    with col_brand:
        # Markdown ko yahan render karein
        st.markdown("""
        <div style="display: flex; align-items: center;">
            <span style="font-size: 24px; margin-right: 10px;">📊</span>
            <span style="font-size: 20px; font-weight: bold; white-space: nowrap;">Job Trend Predictor</span>
        </div>
        """, unsafe_allow_html=True)