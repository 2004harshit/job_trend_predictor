# import streamlit as st

# def render():
#     """Render the about page"""
#     st.markdown('<div class="fade-in">', unsafe_allow_html=True)
#     st.markdown('<div class="content-title">ℹ️ About Job Trend Predictor</div>', 
#                 unsafe_allow_html=True)
    
#     # Project Overview Section
#     st.markdown("""
#     <div class="about-section">
#         <div class="about-title">🎯 Project Overview</div>
#         <p style="font-size: 1.1rem; line-height: 1.6; color: #555;">
#             The <strong>Job Trend Predictor</strong> provides data-driven insights 
#             for students and counselors using a modern Streamlit interface and 
#             interactive analytics.
#         </p>
#     </div>
#     """, unsafe_allow_html=True)
    
#     # Technologies Section
#     st.markdown("""
#     <div class="about-section">
#         <div class="about-title">🔧 Technologies Used</div>
#         <ul class="feature-list">
#             <li>Python, Streamlit, Plotly</li>
#             <li>Scikit-learn, XGBoost (for modeling)</li>
#             <li>Pandas, NumPy for data processing</li>
#             <li>Power BI (embedded dashboards)</li>
#         </ul>
#     </div>
#     """, unsafe_allow_html=True)
    
#     # Key Features Section
#     st.markdown("""
#     <div class="about-section">
#         <div class="about-title">✨ Key Features & Benefits</div>
#         <ul class="feature-list">
#             <li>Student Dashboard with sidebar inputs and real-time results</li>
#             <li>Career Counselor Dashboard with analytics and Power BI placeholder</li>
#             <li>Modern, responsive UI with smooth transitions</li>
#             <li>Consistent theme and typography</li>
#         </ul>
#     </div>
#     """, unsafe_allow_html=True)
    
#     # Footer Section
#     st.markdown("""
#     <div class="about-section" style="text-align:center; background:#f8f9fa;">
#         <p style="color:#666; margin:0;">
#             © 2024 Job Trend Predictor. Built with ❤️ using Python, Streamlit, and ML
#         </p>
#     </div>
#     """, unsafe_allow_html=True)
    
#     st.markdown('</div>', unsafe_allow_html=True)


import streamlit as st

def render():
    """Render the about page"""
    st.markdown('<div class="fade-in">', unsafe_allow_html=True)
    st.markdown('<div class="content-title">ℹ️ About Job Market Intelligence System</div>', 
                unsafe_allow_html=True)
    
    # Project Overview Section
    st.markdown("""
    <div class="about-section">
        <div class="about-title">🌍 Project Overview</div>
        <p style="font-size: 1.1rem; line-height: 1.6; color: #555;">
            The <strong>Job Market Intelligence System</strong> is a Data + ML + LLM powered 
            platform designed to analyze and predict job market trends for students, policy-makers, 
            and career counsellors. This system not only predicts job types and salary ranges using 
            Machine Learning models, but also explains the "why" behind the patterns through 
            LLM-generated insights.
        </p>
        <p style="font-size: 1.1rem; line-height: 1.6; color: #555;">
            It acts as an AI-powered decision-support tool that provides real-time job posting 
            analysis, uncovers emerging patterns in hiring, salary, and skill demand, and visualizes 
            all findings in an interactive Business Intelligence dashboard.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Core Objectives Section
    st.markdown("""
    <div class="about-section">
        <div class="about-title">🎯 Core Objectives</div>
        <ul class="feature-list">
            <li>Identify current trends in the job market — demand, location, skill importance, and salary variations</li>
            <li>Predict salary and job type based on required skills and experience level</li>
            <li>Provide LLM-powered insights explaining why certain roles or skills are trending</li>
            <li>Visualize all findings in a dynamic BI dashboard for policy-makers and career counsellors</li>
            <li>Forecast future job trends using time-series and NLP techniques (planned)</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    # How It Works Section
    st.markdown("""
    <div class="about-section">
        <div class="about-title">⚙️ How It Works</div>
        <p style="font-size: 1rem; line-height: 1.6; color: #555; margin-bottom: 1rem;">
            <strong>🔹 Step 1: Data Collection</strong><br>
            Web scraping from job portals (Naukri, LinkedIn, etc.) to extract job titles, skills, 
            experience, salary, location, company, and post dates.
        </p>
        <p style="font-size: 1rem; line-height: 1.6; color: #555; margin-bottom: 1rem;">
            <strong>🔹 Step 2: Data Processing</strong><br>
            Cleaning, normalization, and feature engineering including skill extraction, experience 
            encoding, and NLP-based text insights.
        </p>
        <p style="font-size: 1rem; line-height: 1.6; color: #555; margin-bottom: 1rem;">
            <strong>🔹 Step 3: Machine Learning Layer</strong><br>
            Salary prediction using regression models and job type classification 
            (Full-time, Internship, Contract).
        </p>
        <p style="font-size: 1rem; line-height: 1.6; color: #555; margin-bottom: 1rem;">
            <strong>🔹 Step 4: LLM Insight Layer</strong><br>
            Large Language Models generate contextual insights and trend summaries to explain 
            hiring patterns and market dynamics.
        </p>
        <p style="font-size: 1rem; line-height: 1.6; color: #555;">
            <strong>🔹 Step 5: Visualization & BI Dashboard</strong><br>
            Interactive dashboards displaying skill vs salary, experience trends, fresher demand 
            ratios, and location-based hiring heatmaps.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Technologies Section
    st.markdown("""
    <div class="about-section">
        <div class="about-title">🔧 Technology Stack</div>
        <ul class="feature-list">
            <li><strong>Data Scraping:</strong> Requests, BeautifulSoup, Selenium</li>
            <li><strong>Data Processing:</strong> Pandas, NumPy, Regex</li>
            <li><strong>NLP & Text Features:</strong> spaCy, NLTK, TF-IDF, WordCloud</li>
            <li><strong>Machine Learning:</strong> Scikit-learn, XGBoost, Random Forest</li>
            <li><strong>LLM Integration:</strong> OpenAI API, LlamaIndex</li>
            <li><strong>Visualization:</strong> Streamlit, Plotly, Power BI</li>
            <li><strong>MLOps (Planned):</strong> MLflow, ZenML, Git</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    # Key Features Section
    st.markdown("""
    <div class="about-section">
        <div class="about-title">✨ Key Features & Benefits</div>
        <ul class="feature-list">
            <li><strong>For Students:</strong> Skill-based salary prediction, demand analysis, and personalized career insights</li>
            <li><strong>For Career Counsellors:</strong> BI Dashboard with skill-demand trends, hiring ratios, and salary statistics</li>
            <li><strong>For Policy-Makers:</strong> Aggregate hiring insights, fresher demand analysis, and regional/sectoral trends</li>
            <li>Real-time job market analysis with explainable AI insights</li>
            <li>Interactive visualizations with filtering by skill, city, and experience level</li>
            <li>Modern, responsive UI with smooth transitions and consistent design</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    # Target Audience Section
    st.markdown("""
    <div class="about-section">
        <div class="about-title">👥 Target Audience</div>
        <p style="font-size: 1rem; line-height: 1.6; color: #555;">
            <strong>🎓 Students & Freshers:</strong> Get insights on which skills and domains 
            offer better job opportunities and higher pay.<br><br>
            <strong>👨‍🏫 Career Counsellors & Placement Officers:</strong> Access data-driven 
            guidance to help students develop employable skillsets.<br><br>
            <strong>🏛️ Policy-Makers & Institutions:</strong> Receive evidence-based insights 
            to design curriculum and placement strategies aligned with market needs.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Expected Impact Section
    st.markdown("""
    <div class="about-section">
        <div class="about-title">🏁 Expected Impact</div>
        <ul class="feature-list">
            <li>Helps students choose realistic and high-demand skills for better career prospects</li>
            <li>Enables career counsellors to design evidence-based guidance programs</li>
            <li>Assists policy-makers in aligning curriculum with current market needs</li>
            <li>Acts as an early-stage Job Market Research System built using end-to-end ML and LLM technologies</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    # Team Section
    st.markdown("""
    <div class="about-section">
        <div class="about-title">👨‍💻 Team Members</div>
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1.5rem; margin-top: 1rem;">
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 1.5rem; border-radius: 10px; text-align: center; color: white; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                <div style="font-size: 2rem; margin-bottom: 0.5rem;">👤</div>
                <div style="font-size: 1.1rem; font-weight: 600;">Harshit Chauhan</div>
            </div>
            <div style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); padding: 1.5rem; border-radius: 10px; text-align: center; color: white; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                <div style="font-size: 2rem; margin-bottom: 0.5rem;">👤</div>
                <div style="font-size: 1.1rem; font-weight: 600;">Harsh Dhakad</div>
            </div>
            <div style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); padding: 1.5rem; border-radius: 10px; text-align: center; color: white; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                <div style="font-size: 2rem; margin-bottom: 0.5rem;">👤</div>
                <div style="font-size: 1.1rem; font-weight: 600;">Gulshan Kumar</div>
            </div>
            <div style="background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%); padding: 1.5rem; border-radius: 10px; text-align: center; color: white; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                <div style="font-size: 2rem; margin-bottom: 0.5rem;">👤</div>
                <div style="font-size: 1.1rem; font-weight: 600;">Harsh</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Future Roadmap Section
    st.markdown("""
    <div class="about-section">
        <div class="about-title">🔮 Future Roadmap (Next Semester)</div>
        <ul class="feature-list">
            <li>Trend forecasting using Time-Series ML models (ARIMA, Prophet, LSTM)</li>
            <li>Skill evolution tracker to monitor demand changes over months</li>
            <li>Enhanced LLM insights explaining "why demand is rising/falling"</li>
            <li>End-to-End MLOps integration with model versioning and retraining</li>
            <li>Public deployment of the Streamlit application</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    # Footer Section
    st.markdown("""
    <div class="about-section" style="text-align:center; background:#f8f9fa;">
        <p style="color:#666; margin:0;">
            © 2025 Job Market Intelligence System. Built with ❤️ using Python, Streamlit, Machine Learning & LLM
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)