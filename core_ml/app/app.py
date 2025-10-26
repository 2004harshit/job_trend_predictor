import sys
import os

# Get the project root directory (parent of current file's directory)
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)

# Add project root to Python path
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import streamlit as st
from app.pages import home, student_dashboard, counselor_dashboard, about
from app.utils.styles import apply_custom_styles

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
    """Render the top navigation bar"""
    st.markdown("""
    <div class="nav-container">
        <h1 class="nav-title">📊 Job Trend Predictor</h1>
        <div class="nav-tabs"></div>
    </div>
    """, unsafe_allow_html=True)
    
    c1, c2 = st.columns([1, 1])
    with c1:
        if st.button("🏠 Home", key="nav_home", use_container_width=True):
            navigate_to('Home')
    with c2:
        if st.button("ℹ️ About", key="nav_about", use_container_width=True):
            navigate_to('About')

def main() -> None:
    """Main application logic"""
    render_navigation()
    
    # Route to appropriate page
    if st.session_state.current_page == 'Home':
        home.render(navigate_to)
    elif st.session_state.current_page == 'Student Dashboard':
        student_dashboard.render()
    elif st.session_state.current_page == 'Career Counselor Dashboard':
        counselor_dashboard.render()
    elif st.session_state.current_page == 'About':
        about.render()

if __name__ == "__main__":
    main()