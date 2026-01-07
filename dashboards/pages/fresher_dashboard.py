import streamlit as st
from ..components.career_profiler import render_profiling_flow

def render(navigate_to):
    # Step 1: Check karo ki user ne submit button click kiya hai ya nahi
    # Hum 'profiling_complete' naam ka ek flag use karenge
    if 'profiling_complete' not in st.session_state:
        st.session_state.profiling_complete = False

    # Step 2: Conditional Rendering
    if not st.session_state.profiling_complete:
        # User ko profiling QNA dikhao
        render_profiling_flow(navigate_to)
    elif st.session_state.profile_results.get("comfort") == "Comfortable":
        render_actual_intermediate_dashboard()
    else:
        # User profiling kar chuka hai, ab asli dashboard dikhao
        render_actual_fresher_dashboard()

def render_actual_fresher_dashboard():
    st.title("👨‍🎓 Your Personalized Insights")
    st.write("Welcome to the actual functionality!")
    
    # Yahan aap apna graphs, data aur analysis dikha sakte hain
    user_data = st.session_state.get('profile_results', {})
    st.success(f"Showing trends for {user_data.get('branch', 'your branch')}...")

def render_actual_intermediate_dashboard():
    st.title("👨‍🎓 Your Personalized Insights for Intermediate")
    st.write("Welcome to the actual functionality!")
    
    # Yahan aap apna graphs, data aur analysis dikha sakte hain
    user_data = st.session_state.get('profile_results', {})
    st.success(f"Showing trends for {user_data.get('branch', 'your branch')}...")