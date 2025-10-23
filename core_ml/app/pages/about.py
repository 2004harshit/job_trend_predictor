import streamlit as st

def render():
    """Render the about page"""
    st.markdown('<div class="fade-in">', unsafe_allow_html=True)
    st.markdown('<div class="content-title">ℹ️ About Job Trend Predictor</div>', 
                unsafe_allow_html=True)
    
    # Project Overview Section
    st.markdown("""
    <div class="about-section">
        <div class="about-title">🎯 Project Overview</div>
        <p style="font-size: 1.1rem; line-height: 1.6; color: #555;">
            The <strong>Job Trend Predictor</strong> provides data-driven insights 
            for students and counselors using a modern Streamlit interface and 
            interactive analytics.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Technologies Section
    st.markdown("""
    <div class="about-section">
        <div class="about-title">🔧 Technologies Used</div>
        <ul class="feature-list">
            <li>Python, Streamlit, Plotly</li>
            <li>Scikit-learn, XGBoost (for modeling)</li>
            <li>Pandas, NumPy for data processing</li>
            <li>Power BI (embedded dashboards)</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    # Key Features Section
    st.markdown("""
    <div class="about-section">
        <div class="about-title">✨ Key Features & Benefits</div>
        <ul class="feature-list">
            <li>Student Dashboard with sidebar inputs and real-time results</li>
            <li>Career Counselor Dashboard with analytics and Power BI placeholder</li>
            <li>Modern, responsive UI with smooth transitions</li>
            <li>Consistent theme and typography</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    # Footer Section
    st.markdown("""
    <div class="about-section" style="text-align:center; background:#f8f9fa;">
        <p style="color:#666; margin:0;">
            © 2024 Job Trend Predictor. Built with ❤️ using Python, Streamlit, and ML
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)