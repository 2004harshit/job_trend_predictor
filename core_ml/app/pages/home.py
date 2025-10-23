import streamlit as st

def render(navigate_to):
    """Render the home page"""
    st.markdown('<div class="fade-in">', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="content-title">Welcome to Job Trend Predictor</div>
    <p style="text-align: center; color: #666; font-size: 1.1rem; margin-bottom: 3rem;">
        Empowering students and career counselors with data-driven insights for better career decisions
    </p>
    """, unsafe_allow_html=True)
    
    c1, c2 = st.columns(2)
    
    with c1:
        st.markdown("""
        <div class="dashboard-card">
            <div class="card-icon">🎓</div>
            <div class="card-title">Student Dashboard</div>
            <div class="card-description">
                Get personalized insights, salary estimates, and recommendations based on your profile.
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Enter Student Dashboard", key="btn_student", use_container_width=True):
            navigate_to('Student Dashboard')
    
    with c2:
        st.markdown("""
        <div class="dashboard-card">
            <div class="card-icon">🧑‍🏫</div>
            <div class="card-title">Career Counselor Dashboard</div>
            <div class="card-description">
                Access analytics and embedded Power BI reports to guide student careers.
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Enter Counselor Dashboard", key="btn_counselor", use_container_width=True):
            navigate_to('Career Counselor Dashboard')
    
    st.markdown('</div>', unsafe_allow_html=True)