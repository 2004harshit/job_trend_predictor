import sys
import os


# Get the project root directory (parent of current file's directory)
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)

# Add project root to Python path
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import streamlit as st
from dashboards.components.career_profiler import render_profiling_flow
from dashboards.pages import fresher_dashboard, home, counselor_dashboard, about, set_profile
from dashboards.utils.styles import apply_custom_styles

# 1. set_page_config FIRST — before any other st.* call
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

def render_sidebar() -> None:
    """Render sidebar navigation"""
    with st.sidebar:
        st.markdown("## 📊 Job Trend Predictor")
        st.markdown("---")
        if st.button("🏠 Home", key="nav_home", use_container_width=True):
            st.session_state.current_page = "Home"
            st.rerun()
        if st.button("👤 Profile Selection", key="nav_profile", use_container_width=True):
            st.session_state.current_page = "Profile"
            st.rerun()
        if st.button("📈 Fresher Dashboard", key="nav_fresher", use_container_width=True):
            st.session_state.current_page = "Fresher Dashboard"
            st.rerun()
        if st.button("ℹ️ About", key="nav_about", use_container_width=True):
            st.session_state.current_page = "About"
            st.rerun()
        st.markdown("---")
        if st.button("🎯 Counselor Dashboard", key="nav_counselor", use_container_width=True):
            st.session_state.current_page = "Career Counselor Dashboard"
            st.rerun()

def main() -> None:
    """Main application logic"""
    render_sidebar()

    page = st.session_state.current_page

    if page == "Home":
        home.render(navigate_to)
    elif page in ("Profile", "profile", "Profile Selection"):
        set_profile.render(navigate_to)
    elif page in ("Fresher Dashboard", "Student Dashboard"):
        fresher_dashboard.render(navigate_to)
    elif page == "Career Counselor Dashboard":
        counselor_dashboard.render(navigate_to)
    elif page == "About":
        about.render(navigate_to)
    elif page == "profiling_flow":
        render_profiling_flow(navigate_to)
    else:
        home.render(navigate_to)

if __name__ == "__main__":
    main()