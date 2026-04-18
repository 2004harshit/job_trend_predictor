import streamlit as st
def render_navigation() -> None:
    """Render the top navigation bar in a single line"""
    
    # Ek hi row mein columns create karein
    # [3, 1, 1, 1] ka matlab hai Brand name zyada space lega, buttons kam
    col_brand, col_home, col_profile, col_login = st.columns([3, 1, 1, 1], vertical_alignment="center")

    with col_brand:
        # Replaced emoji with SVG icon and updated typography to inherit premium fonts
        st.markdown("""
<div style="display: flex; align-items: center;">
    <svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="var(--accent-indigo, #6366f1)" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" style="margin-right: 12px; filter: drop-shadow(0 2px 4px rgba(99,102,241,0.2));">
        <path d="M3 3v18h18" />
        <path d="m19 9-5 5-4-4-3 3" />
        <circle cx="19" cy="9" r="2" fill="var(--accent-indigo, #6366f1)" stroke="none" />
    </svg>
    <span style="font-family: 'DM Serif Display', serif; font-size: 25px; color: var(--text-primary, #1e293b); letter-spacing: -0.5px; white-space: nowrap;">Job Trend Predictor</span>
</div>
""", unsafe_allow_html=True)