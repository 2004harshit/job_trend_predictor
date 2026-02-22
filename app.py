import sys
import os


# Get the project root directory (parent of current file's directory)
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)

# Add project root to Python path
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import streamlit as st
# from dashboards.components.career_profiler import render_profiling_flow
from dashboards.pages import fresher_dashboard, home, counselor_dashboard, about,set_profile
from dashboards.utils.styles import apply_custom_styles

# Page configuration
st.set_page_config(
    page_title="Job Trend Predictor",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply custom styles
apply_custom_styles()

# Initialize session state
if 'current_page' not in st.session_state:
    st.session_state.current_page = 'Home'
if 'show_prediction' not in st.session_state:
    st.session_state.show_prediction = False

def navigate_to(page: str) -> None:
    """Navigate to a different page"""
    st.session_state.current_page = page
    st.rerun()

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

    with col_home:
        if st.button("🏠 Home", key="nav_home", use_container_width=True, type="primary"):
            st.session_state.current_page = 'Home'
            st.rerun()

    with col_profile:
        if st.button("👤 Profile", key="nav_profile", use_container_width=True):
            st.session_state.current_page = 'Profile'
            st.rerun()

    with col_login:
        if st.button("🔐 Login", key="nav_login", use_container_width=True):
            st.session_state.current_page = 'Login'
            st.rerun()
    
    st.markdown("---") # Optional: Divider line for clean look

def main() -> None:
    """Main application logic"""
    render_navigation()
    
    # Use a local variable to make the code cleaner
    page = st.session_state.current_page
    
    # Route to appropriate page
    if page == 'Home':
        home.render(navigate_to)
    elif page == 'Student Dashboard':
        fresher_dashboard.render(navigate_to)
    elif page == 'Career Counselor Dashboard':
        counselor_dashboard.render(navigate_to)
    elif page == 'About':
        about.render(navigate_to)
    elif page == 'profile':
        set_profile.render(navigate_to)
    elif page =="profiling_flow":
        render_profiling_flow(navigate_to)

if __name__ == "__main__":
    main()