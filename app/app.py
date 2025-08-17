import streamlit as st
import pandas as pd
import numpy as np
import logging

# Configure logging
logging.basicConfig(
    filename='app.log',
    level=logging.INFO,
    format='%(asctime)s %(levelname)s:%(message)s'
)

st.title("Job Trend Predictor")

# Project Description
st.markdown(
    """
    ### Welcome to the Job Trend Predictor!
    This application helps you predict job market trends based on your skills, experience, and location. 
    Enter your details below to see the predicted demand for your profile and explore job trends with interactive graphs. 
    
    **How it works:**
    - Enter your skills (comma separated)
    - Select your years of experience
    - Enter your preferred job location
    - Click 'Predict' to see the results!
    """
)

# Sidebar for user input
st.sidebar.header("Input Your Details")
skills = st.sidebar.text_input(
    "Skills",
    help="Enter your primary skills, separated by commas (e.g., Python, Machine Learning, SQL)"
)
experience = st.sidebar.selectbox(
    "Years of Experience",
    list(range(0, 21)),
    help="Select your total years of professional experience"
)
location = st.sidebar.text_input(
    "Preferred Job Location",
    help="Enter the city or region where you want to work (e.g., Delhi, Bangalore)"
)

if st.sidebar.button("Predict"):
    # Input validation
    if not skills.strip():
        st.warning("Please enter at least one skill.")
    elif not location.strip():
        st.warning("Please enter your preferred job location.")
    else:
        # Log user input
        logging.info(f"User input - Skills: {skills}, Experience: {experience}, Location: {location}")
        st.subheader("Prediction Result")
        st.info("🔧 The prediction model is currently under construction. Please check back soon for real predictions!")
        # Log model under construction
        logging.info("Prediction attempted, but model is under construction.")
else:
    st.info("Please enter your details in the sidebar and click Predict.")
