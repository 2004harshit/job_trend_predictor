import streamlit as st

from app import navigate_to


def load_qna_based_profiler() -> None:
    """Load the Q&A based user profiler component"""
    st.header("User Profiler")
    st.write("This component collects user information through a series of questions to build a user profile.")
    # Add more interactive elements as needed


def render_profiling_flow(navigate_to):
    # 1. Reuse and Enhanced CSS
    st.markdown("""
    <style>
    /* 1. Centered Header & Badge */
    .blueprint-centered-header {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        gap: 0.8rem;
        margin: 1rem 0 2rem 0;
        width: 100%;
    }

    .blueprint-title-centered {
        font-size: 3.5rem;
        font-weight: 900;
        /* Gradient text still works beautifully on white */
        background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #d946ef 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0;
        line-height: 1.1;
        text-align: center;
    }

    .blueprint-step-badge-centered {
        padding: 0.4rem 1.2rem;
        /* Darker border and text for visibility on white */
        background: rgba(99, 102, 241, 0.05);
        color: #6366f1; 
        border: 1px solid rgba(99, 102, 241, 0.2);
        border-radius: 50px;
        font-size: 0.85rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.1em;
    }

    /* 2. Light Theme Form Container */
    [data-testid="stForm"] {
        background: #ffffff !important;
        border: 1px solid #e2e8f0 !important;
        border-radius: 20px !important;
        padding: 2.5rem !important;
        /* Soft blue-ish shadow instead of dark shadow */
        box-shadow: 0 10px 25px rgba(99, 102, 241, 0.1) !important;
        margin-bottom: 2rem;
    }

    /* 3. Visible Subheaders (H3) on White */
    h3 {
        color: #1e1b4b !important; /* Very dark Indigo (almost black) */
        font-weight: 800 !important;
        font-size: 1.5rem !important;
        margin-top: 0 !important;
        margin-bottom: 1rem !important;
        border-left: 4px solid #8b5cf6;
        padding-left: 15px;
    }

    /* 4. Labels and Paragraphs */
    .stMarkdown p { 
        color: #475569 !important; /* Medium Slate Grey */
        font-weight: 500;
    }
</style>
    """, unsafe_allow_html=True)

    # State management for stages
    if 'form_stage' not in st.session_state:
        st.session_state.form_stage = 1
    if 'profile_results' not in st.session_state:
        st.session_state.profile_results = {}

    # Hero Section Header
    st.markdown(f'<div class="blueprint-centered-header"><h1 class="blueprint-title-centered">Build Your Blueprint</h1><div class="blueprint-step-badge-centered">Step {st.session_state.form_stage} of 3</div></div>', unsafe_allow_html=True)


    # --- STAGE 1: BASIC PROFILE ---
    if st.session_state.form_stage == 1:
        with st.form("stage1"):
            st.subheader("🎓 Basic Profile")
            col1, col2 = st.columns(2)
            with col1:
                branch = st.text_input("Educational Branch (e.g. CS, IT, ECE)")
                cgpa = st.select_slider("CGPA Range", options=["< 6", "6-7", "7-8", "8-9", "9+"])
            with col2:
                year = st.selectbox("Current Year", ["1st Year", "2nd Year", "3rd Year", "Final Year", "Graduate"])
                exp = st.selectbox("Prior Experience", ["None", "Internship", "Freelance", "Open Source"])
            
            prog_level = st.select_slider("Programming Comfort Level", options=["Beginner", "Comfortable", "Advanced"])
            time_inv = st.radio("Time Available to Invest", ["3-6 months", "6-12 months", "1+ year"], horizontal=True)

            if st.form_submit_button("Next: Psychology & Priorities →"):
                st.session_state.profile_results.update({"branch": branch, "cgpa": cgpa, "year": year, "exp": exp, "comfort": prog_level, "time": time_inv})
                st.session_state.form_stage = 2
                st.rerun()

    # --- STAGE 2: PSYCHOLOGICAL MAPPING ---
    elif st.session_state.form_stage == 2:
        with st.form("stage2"):
            st.subheader("🧠 Psychology & Priority Mapping")
            
            anxiety_q = st.selectbox("How do you feel about your current preparation?", [
                "Confident and on track", 
                "Somewhat confused but learning", 
                "Completely lost and overwhelmed", 
                "Haven't started, feeling behind"
            ])
            
            fear_q = st.radio("What worries you most?", [
                "Not getting placed at all", 
                "Choosing wrong domain and wasting time", 
                "Low salary / financial insecurity", 
                "Falling behind peers", 
                "Domain becoming irrelevant"
            ])

            learn_style = st.multiselect("Learning Style Preference", ["Tutorial-heavy", "Project-based", "Theory-first", "Learn-by-doing"])
            
            st.markdown("---")
            st.write("**Real Priority Matrix (1 = Low, 5 = High)**")
            p_cols = st.columns(5)
            p1 = p_cols[0].number_input("Quick Job", 1, 5, 3)
            p2 = p_cols[1].number_input("High Salary", 1, 5, 3)
            p3 = p_cols[2].number_input("Growth", 1, 5, 3)
            p4 = p_cols[3].number_input("WLB", 1, 5, 3)
            p5 = p_cols[4].number_input("Innovation", 1, 5, 3)

            if st.form_submit_button("Next: Interest & Constraints →"):
                st.session_state.profile_results.update({"anxiety": anxiety_q, "fear": fear_q, "style": learn_style, "priorities": [p1,p2,p3,p4,p5]})
                st.session_state.form_stage = 3
                st.rerun()

    # --- STAGE 3: INTERESTS & CONSTRAINTS ---
    elif st.session_state.form_stage == 3:
        with st.form("stage3"):
            st.subheader("🎯 Interest & Constraint Discovery")
            
            # Variable ko yahan define karein (Outside if check)
            interests_selection = st.multiselect("What genuinely interests you?", [
                "Building user interfaces / visual design",
                "Problem-solving with data",
                "Understanding how systems work internally",
                "Creating intelligent applications"
            ])
    
            c1, c2 = st.columns(2)
            with c1:
                loc = st.radio("Location", ["Jaipur", "Remote", "Relocation"])
            with c2:
                math = st.select_slider("Math comfort", options=["Weak", "Average", "Strong"])
    
            # Ab button check karein
            if st.form_submit_button("🚀 Generate My Career Roadmap"):
                # Yahan interests_selection accessible hai
                st.session_state.profile_results.update({
                    "interests": interests_selection, 
                    "location": loc, 
                    "math": math
                })
                
                # State update for navigation
                st.session_state.profiling_complete = True
                st.rerun()