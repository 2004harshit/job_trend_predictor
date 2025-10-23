# import streamlit as st
# import pandas as pd
# import numpy as np
# import logging

# # Configure logging
# logging.basicConfig(
#     filename='app.log',
#     level=logging.INFO,
#     format='%(asctime)s %(levelname)s:%(message)s'
# )

# st.title("Job Trend Predictor")

# # Project Description
# st.markdown(
#     """
#     ### Welcome to the Job Trend Predictor!
#     This application helps you predict job market trends based on your skills, experience, and location. 
#     Enter your details below to see the predicted demand for your profile and explore job trends with interactive graphs. 
    
#     **How it works:**
#     - Enter your skills (comma separated)
#     - Select your years of experience
#     - Enter your preferred job location
#     - Click 'Predict' to see the results!
#     """
# )

# # Sidebar for user input
# st.sidebar.header("Input Your Details")
# skills = st.sidebar.text_input(
#     "Skills",
#     help="Enter your primary skills, separated by commas (e.g., Python, Machine Learning, SQL)"
# )
# experience = st.sidebar.selectbox(
#     "Years of Experience",
#     list(range(0, 21)),
#     help="Select your total years of professional experience"
# )
# location = st.sidebar.text_input(
#     "Preferred Job Location",
#     help="Enter the city or region where you want to work (e.g., Delhi, Bangalore)"
# )

# if st.sidebar.button("Predict"):
#     # Input validation
#     if not skills.strip():
#         st.warning("Please enter at least one skill.")
#     elif not location.strip():
#         st.warning("Please enter your preferred job location.")
#     else:
#         # Log user input
#         logging.info(f"User input - Skills: {skills}, Experience: {experience}, Location: {location}")
#         st.subheader("Prediction Result")
#         st.info("🔧 The prediction model is currently under construction. Please check back soon for real predictions!")
#         # Log model under construction
#         logging.info("Prediction attempted, but model is under construction.")
# else:
#     st.info("Please enter your details in the sidebar and click Predict.")

import streamlit as st
import joblib
import pandas as pd
import plotly.express as px
from PIL import Image

# ============ PAGE CONFIG ============
st.set_page_config(
    page_title="Job Trend Predictor",
    page_icon="💼",
    layout="wide"
)

# ============ LOAD MODELS ============
@st.cache_resource
def load_models():
    try:
        clf = joblib.load("models/job_title_classifier.pkl")
        vectorizer = joblib.load("models/tfidf_vectorizer.pkl")
        return clf, vectorizer
    except:
        return None, None

model, vectorizer = load_models()

# ============ SIDEBAR NAVIGATION ============
st.sidebar.title("🔍 Navigation")
page = st.sidebar.radio("Go to", ["🏠 Home", "💼 Job Predictor", "📊 Future Trends", "ℹ️ About"])

# ============ 1. HOME PAGE ============
if page == "🏠 Home":
    st.title("💼 Job Trend Predictor")
    st.write("Welcome to the **Job Trend Predictor** — an intelligent platform that helps you explore job market patterns, predict future demand, and make informed career decisions.")

    st.markdown("### Select Your Role")
    col1, col2, col3 = st.columns(3)

    with col1:
        st.subheader("🎓 Student")
        st.markdown("""
        - Discover trending job roles.
        - Compare skills required in your field.
        - Plan your learning path smartly.
        """)
        if st.button("Explore as Student"):
            st.session_state.page = "💼 Job Predictor"

    with col2:
        st.subheader("🧭 Career Counselor")
        st.markdown("""
        - Analyze hiring trends by skill or domain.
        - Provide data-backed advice to students.
        - Explore growth clusters.
        """)
        if st.button("Explore as Counselor"):
            st.session_state.page = "📊 Future Trends"

    with col3:
        st.subheader("📈 Future Trend Prediction")
        st.markdown("""
        - Forecast top-demand technologies.
        - Analyze skill evolution.
        - Predict industry shifts.
        """)
        if st.button("Explore Trends"):
            st.session_state.page = "📊 Future Trends"

    st.markdown("---")
    st.write("Use the sidebar to navigate or click any card above.")

# ============ 2. JOB PREDICTOR ============
elif page == "💼 Job Predictor":
    st.title("💡 Job Category Predictor")

    st.write("Enter your current **skills** and **location** to find the most probable job category based on market data.")

    col1, col2 = st.columns(2)
    with col1:
        skills_input = st.text_area("Enter your skills (comma-separated):", "python, machine learning, sql")
    with col2:
        location_input = st.text_input("Enter location:", "Bangalore")

    if st.button("🔮 Predict Job Category"):
        if model is not None and vectorizer is not None:
            skills_list = [s.strip().lower() for s in skills_input.split(",")]
            text_input = " ".join(skills_list)
            vec_input = vectorizer.transform([text_input])
            pred = model.predict(vec_input)[0]

            st.success(f"### 🧭 Predicted Job Category: {pred}")

            st.markdown("#### 📌 Suggested Career Actions")
            st.write("- Explore advanced courses in this domain.")
            st.write("- Connect with professionals in your predicted role.")
            st.write("- Build portfolio projects aligned with this job cluster.")
        else:
            st.error("Model files not found. Please train and save models first.")

# ============ 3. FUTURE TRENDS ============
elif page == "📊 Future Trends":
    st.title("📊 Future Skill & Job Trends")

    st.write("Explore emerging technologies, top job clusters, and salary trends from your dataset.")

    # Example simulated data (replace with your EDA output)
    trends_df = pd.DataFrame({
        "Skill": ["Python", "Machine Learning", "SQL", "AWS", "Data Analysis"],
        "Demand_Index": [89, 82, 74, 68, 71]
    })
    fig = px.bar(trends_df, x="Skill", y="Demand_Index", color="Skill", title="Top Trending Skills (Demand Index)")
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("#### 💬 Insights")
    st.write("- **Python** and **ML** remain top in-demand skills across 2024–25.")
    st.write("- Cloud and Data-related skills show rising trends.")
    st.write("- Skills like **GenAI** and **MLOps** are emerging for 2025.")

# ============ 4. ABOUT PAGE ============
elif page == "ℹ️ About":
    st.title("ℹ️ About This Project")
    st.write("""
    The **Job Trend Predictor** is a final-year Machine Learning project built by **Harshit**, 
    aimed at analyzing job market data to identify key skills, job demand, and future employment trends.

    ### 📚 Project Overview
    - **Data Source:** Scraped job listings from multiple portals.
    - **Tech Stack:** Python, Pandas, Scikit-learn, Plotly, Streamlit.
    - **Core Modules:**
        1. Data cleaning, EDA, and feature engineering.
        2. Salary prediction (regression) and job classification (classification).
        3. Interactive visualization and prediction through Streamlit.
    - **Key Insight:** Top-demand skills such as *Python*, *SQL*, and *Machine Learning* are consistently associated with higher job postings.

    ### 🧠 Future Scope
    - Integrate real-time job APIs for live trend updates.
    - Add advanced forecasting using Time-Series models (ARIMA, Prophet).
    - Include salary clustering and regional demand maps.

    ---
    Built with ❤️ by **Harshit** | Guided by faith, discipline, and continuous learning.
    """)

