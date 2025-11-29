# import streamlit as st
# import pandas as pd
# import plotly.express as px
# import sys
# import os

# # Add parent directory to path for imports
# CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
# PARENT_DIR = os.path.abspath(os.path.join(CURRENT_DIR, "..", ".."))
# if PARENT_DIR not in sys.path:
#     sys.path.insert(0, PARENT_DIR)

# from app.utils.model_predictor import get_predictor

# def render_sidebar():
#     """Render sidebar with user input fields"""
#     with st.sidebar:
#         st.markdown("""
#         <div class="sidebar-content">
#             <div class="sidebar-title">📝 Your Profile</div>
#         </div>
#         """, unsafe_allow_html=True)
        
#         st.subheader("Basic Information")
#         experience = st.slider("Years of Experience", 0, 20, 2)
#         location = st.selectbox("Location", ["Tier 1", "Tier 2", "Tier 3"])
#         education = st.selectbox("Education Level", ["Graduate", "Postgraduate", "Other"])
        
#         st.subheader("🛠️ Skills")
#         programming_skills = st.slider("Programming Skills", 0, 10, 2)
#         ml_skills = st.slider("ML/AI Skills", 0, 10, 1)
#         data_skills = st.slider("Data Analysis Skills", 0, 10, 1)
#         cloud_skills = st.slider("Cloud Skills", 0, 10, 1)
#         skills_input = st.text_area("Additional Skills (comma-separated)", 
#                                      placeholder="python, machine learning, sql, etc.")
        
#         st.subheader("🏢 Company Preferences")
#         company_size = st.selectbox("Preferred Company Size", ["Small", "Medium", "Large"])
#         industry = st.selectbox("Industry Type", 
#                                 ["IT Services & Consulting", "Internet", "Software Product", 
#                                  "Banking", "Financial Services", "E-Learning", "Other"])
        
#         predict_button = st.button("🔮 Predict My Salary", key="predict_salary", use_container_width=True)
    
#     return {
#         'experience': experience,
#         'location': location,
#         'education': education,
#         'programming_skills': programming_skills,
#         'ml_skills': ml_skills,
#         'data_skills': data_skills,
#         'cloud_skills': cloud_skills,
#         'skills_input': skills_input,
#         'company_size': company_size,
#         'industry': industry,
#         'predict_button': predict_button
#     }

# def calculate_salary(user_data):
#     """Calculate predicted salary based on user inputs using ML model"""
#     try:
#         # Get predictor instance
#         predictor = get_predictor()
        
#         # Make prediction
#         result = predictor.predict_salary(user_data)
        
#         predicted_salary = result['predicted_salary']
#         confidence = result['confidence']
#         model_used = result.get('model_used', 'ML Model')
        
#     except Exception as e:
#         # Fallback to heuristic if model fails
#         st.warning(f"Using fallback prediction. Error: {e}")
#         base_salary = (3.5 + (user_data['experience'] * 0.8) + 
#                        (user_data['programming_skills'] * 0.3) + 
#                        (user_data['ml_skills'] * 0.4))
        
#         location_multiplier = {"Tier 1": 1.2, "Tier 2": 1.0, "Tier 3": 0.8}[user_data['location']]
#         education_multiplier = {"Graduate": 1.0, "Postgraduate": 1.2, "Other": 0.9}[user_data['education']]
        
#         predicted_salary = base_salary * location_multiplier * education_multiplier
#         confidence = min(95, 60 + (user_data['experience'] * 2) + 
#                         (user_data['programming_skills'] + user_data['ml_skills'] + user_data['data_skills']) * 3)
#         model_used = 'Heuristic Fallback'
    
#     # Determine market demand
#     market_demand = ("High" if (user_data['ml_skills'] + user_data['data_skills']) > 3 
#                      else ("Medium" if (user_data['programming_skills'] + user_data['ml_skills']) > 2 
#                      else "Low"))
    
#     return predicted_salary, confidence, market_demand, model_used

# def render_predictions(user_data):
#     """Render salary predictions and recommendations"""
#     result = calculate_salary(user_data)
#     predicted_salary, confidence, market_demand, model_used = result
    
#     st.subheader("💰 Salary Prediction")
#     m1, m2, m3 = st.columns(3)
#     with m1:
#         st.metric("Predicted Salary", f"₹{predicted_salary:.1f} LPA")
#     with m2:
#         st.metric("Confidence", f"{confidence:.0f}%")
#     with m3:
#         st.metric("Market Demand", market_demand)
    
#     # lower_bound = predicted_salary * 0.8
#     # upper_bound = predicted_salary * 1.2
#     # st.info(f"**Expected Range:** ₹{lower_bound:.1f} - ₹{upper_bound:.1f} LPA")
    
#     # Show model used
#     st.caption(f"Model: {model_used}")
    
#     st.subheader("💡 Career Recommendations")
#     recs = []
#     if user_data['experience'] < 2:
#         recs.append("Focus on foundational skills and internships")
#     if user_data['ml_skills'] < 3:
#         recs.append("Invest time in ML/AI projects and courses")
#     if user_data['cloud_skills'] < 2:
#         recs.append("Add a cloud provider (AWS/Azure/GCP)")
#     if user_data['location'] == "Tier 3":
#         recs.append("Consider opportunities in Tier 1 cities")
    
#     for i, r in enumerate(recs, 1):
#         st.write(f"{i}. {r}")

# def render_market_insights():
#     """Render market insights sidebar"""
#     st.subheader("📊 Market Insights")
    
#     skills_data = pd.DataFrame({
#         'Skill': ['Python', 'Machine Learning', 'SQL', 'AWS', 'JavaScript'],
#         'Demand': [85, 78, 72, 68, 65]
#     })
#     fig = px.bar(skills_data, x='Demand', y='Skill', orientation='h',
#                  title="Top Skills in Demand", color='Demand',
#                  color_continuous_scale='Blues')
#     fig.update_layout(height=300, showlegend=False)
#     st.plotly_chart(fig, use_container_width=True)
    
#     exp_data = pd.DataFrame({
#         'Experience': ['0-2', '2-5', '5-10', '10+'],
#         'Avg Salary': [3.5, 6.2, 9.8, 15.2]
#     })
#     fig2 = px.line(exp_data, x='Experience', y='Avg Salary',
#                    title="Experience vs Average Salary", markers=True)
#     fig2.update_layout(height=250)
#     st.plotly_chart(fig2, use_container_width=True)

# def render():
#     """Main render function for student dashboard"""
#     st.markdown('<div class="fade-in">', unsafe_allow_html=True)
#     st.markdown('<div class="content-title">🎓 Student Dashboard</div>', unsafe_allow_html=True)
    
#     # Get user inputs from sidebar
#     user_data = render_sidebar()
    
#     if user_data['predict_button']:
#         st.session_state.show_prediction = True
    
#     # Main content area
#     c_main, c_side = st.columns([2, 1])
    
#     with c_main:
#         st.markdown("<div class=\"main-content\">", unsafe_allow_html=True)
#         if st.session_state.get('show_prediction', False):
#             render_predictions(user_data)
#         else:
#             st.info("👈 Fill your details in the sidebar and click 'Predict My Salary' to begin")
#         st.markdown("</div>", unsafe_allow_html=True)
    
#     with c_side:
#         render_market_insights()
    
#     st.markdown('</div>', unsafe_allow_html=True)


import streamlit as st
import pandas as pd
import plotly.express as px
import sys
import os
from groq import Groq
import json

# Add parent directory to path for imports
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.abspath(os.path.join(CURRENT_DIR, "..", ".."))
if PARENT_DIR not in sys.path:
    sys.path.insert(0, PARENT_DIR)

from app.utils.model_predictor import get_predictor

# Initialize Groq client
@st.cache_resource
def get_groq_client():
    """Initialize Groq client"""

    # api_key = os.getenv("GROQ_API_KEY") or st.secrets.get("GROQ_API_KEY")
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return None
    return Groq(api_key=api_key)

def generate_career_insights(user_data, predicted_salary, confidence, market_demand):
    """Generate personalized career insights using Groq"""
    client = get_groq_client()
    
    if not client:
        return {
            'summary': "Please configure GROQ_API_KEY to enable AI-powered insights.",
            'job_roles': [],
            'learning_path': [],
            'next_steps': []
        }
    
    # Prepare context
    profile_context = f"""
Student Profile:
- Experience: {user_data['experience']} years
- Location: {user_data['location']}
- Education: {user_data['education']}
- Programming Skills: {user_data['programming_skills']}/10
- ML/AI Skills: {user_data['ml_skills']}/10
- Data Analysis Skills: {user_data['data_skills']}/10
- Cloud Skills: {user_data['cloud_skills']}/10
- Additional Skills: {user_data['skills_input']}
- Preferred Company Size: {user_data['company_size']}
- Preferred Industry: {user_data['industry']}

Prediction Results:
- Predicted Salary: ₹{predicted_salary:.1f} LPA
- Confidence: {confidence:.0f}%
- Market Demand: {market_demand}
"""

    prompt = f"""Based on the following student profile, provide personalized career guidance for the Indian job market:

{profile_context}

Please provide:
1. A brief summary of their current position in the job market (2-3 sentences)
2. Top 3-5 suitable job roles with brief explanations (specific to Indian tech market)
3. A learning path with 3-4 concrete steps to advance their career
4. Immediate next steps they should take (2-3 action items)

Return ONLY a valid JSON object with these exact keys: summary, job_roles (array of objects with 'title' and 'description'), learning_path (array of strings), next_steps (array of strings).

Example format:
{{
  "summary": "Your summary here",
  "job_roles": [
    {{"title": "Software Engineer", "description": "Description here"}},
    {{"title": "Data Analyst", "description": "Description here"}}
  ],
  "learning_path": ["Step 1", "Step 2"],
  "next_steps": ["Action 1", "Action 2"]
}}
"""

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are a helpful career advisor for students in the Indian tech industry. Always respond with valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=1500
        )
        
        response_text = response.choices[0].message.content.strip()
        
        # Clean up response text
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()
        
        insights = json.loads(response_text)
        return insights
        
    except Exception as e:
        st.error(f"Error generating insights: {e}")
        return {
            'summary': "Unable to generate AI insights at this time. Please try again.",
            'job_roles': [],
            'learning_path': [],
            'next_steps': []
        }

def render_sidebar():
    """Render sidebar with user input fields"""
    with st.sidebar:
        st.markdown("""
        <div class="sidebar-content">
            <div class="sidebar-title">📝 Your Profile</div>
        </div>
        """, unsafe_allow_html=True)
        
        st.subheader("Basic Information")
        experience = st.slider("Years of Experience", 0, 20, 2)
        location = st.selectbox("Location", ["Tier 1", "Tier 2", "Tier 3"])
        education = st.selectbox("Education Level", ["Graduate", "Postgraduate", "Other"])
        
        st.subheader("🛠️ Skills")
        programming_skills = st.slider("Programming Skills", 0, 10, 2)
        ml_skills = st.slider("ML/AI Skills", 0, 10, 1)
        data_skills = st.slider("Data Analysis Skills", 0, 10, 1)
        cloud_skills = st.slider("Cloud Skills", 0, 10, 1)
        skills_input = st.text_area("Additional Skills (comma-separated)", 
                                     placeholder="python, machine learning, sql, etc.")
        
        st.subheader("🏢 Company Preferences")
        company_size = st.selectbox("Preferred Company Size", ["Small", "Medium", "Large"])
        industry = st.selectbox("Industry Type", 
                                ["IT Services & Consulting", "Internet", "Software Product", 
                                 "Banking", "Financial Services", "E-Learning", "Other"])
        
        predict_button = st.button("🔮 Predict My Salary", key="predict_salary", use_container_width=True)
    
    return {
        'experience': experience,
        'location': location,
        'education': education,
        'programming_skills': programming_skills,
        'ml_skills': ml_skills,
        'data_skills': data_skills,
        'cloud_skills': cloud_skills,
        'skills_input': skills_input,
        'company_size': company_size,
        'industry': industry,
        'predict_button': predict_button
    }

def calculate_salary(user_data):
    """Calculate predicted salary based on user inputs using ML model"""
    try:
        # Get predictor instance
        predictor = get_predictor()
        
        # Make prediction
        result = predictor.predict_salary(user_data)
        
        predicted_salary = result['predicted_salary']
        confidence = result['confidence']
        model_used = result.get('model_used', 'ML Model')
        
    except Exception as e:
        # Fallback to heuristic if model fails
        st.warning(f"Using fallback prediction. Error: {e}")
        base_salary = (3.5 + (user_data['experience'] * 0.8) + 
                       (user_data['programming_skills'] * 0.3) + 
                       (user_data['ml_skills'] * 0.4))
        
        location_multiplier = {"Tier 1": 1.2, "Tier 2": 1.0, "Tier 3": 0.8}[user_data['location']]
        education_multiplier = {"Graduate": 1.0, "Postgraduate": 1.2, "Other": 0.9}[user_data['education']]
        
        predicted_salary = base_salary * location_multiplier * education_multiplier
        confidence = min(95, 60 + (user_data['experience'] * 2) + 
                        (user_data['programming_skills'] + user_data['ml_skills'] + user_data['data_skills']) * 3)
        model_used = 'Heuristic Fallback'
    
    # Determine market demand
    market_demand = ("High" if (user_data['ml_skills'] + user_data['data_skills']) > 3 
                     else ("Medium" if (user_data['programming_skills'] + user_data['ml_skills']) > 2 
                     else "Low"))
    
    return predicted_salary, confidence, market_demand, model_used

def render_ai_insights(insights):
    """Render AI-generated career insights"""
    st.markdown("### 🤖 AI Career Advisor")
    
    # Summary
    if insights.get('summary'):
        st.info(insights['summary'])
    
    # Job Roles
    if insights.get('job_roles'):
        st.markdown("#### 💼 Recommended Job Roles")
        for role in insights['job_roles']:
            with st.expander(f"**{role.get('title', 'Role')}**"):
                st.write(role.get('description', ''))
    
    # Learning Path
    if insights.get('learning_path'):
        st.markdown("#### 📚 Your Learning Path")
        for i, step in enumerate(insights['learning_path'], 1):
            st.markdown(f"{i}. {step}")
    
    # Next Steps
    if insights.get('next_steps'):
        st.markdown("#### 🎯 Immediate Next Steps")
        for step in insights['next_steps']:
            st.markdown(f"- {step}")

def render_chat_interface(user_data, predicted_salary, confidence, market_demand):
    """Render interactive chat interface with Groq"""
    st.markdown("### 💬 Ask Career Questions")
    
    # Initialize chat history
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    
    # Display chat history
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Ask me anything about your career..."):
        # Add user message
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Generate response
        client = get_groq_client()
        if client:
            profile_context = f"""
Context about the student:
- Experience: {user_data['experience']} years
- Skills: Programming {user_data['programming_skills']}/10, ML {user_data['ml_skills']}/10, Data {user_data['data_skills']}/10, Cloud {user_data['cloud_skills']}/10
- Predicted Salary: ₹{predicted_salary:.1f} LPA
- Market Demand: {market_demand}
- Location: {user_data['location']}
- Education: {user_data['education']}

You are a helpful career advisor for students in the Indian tech industry. Use the context above to provide personalized advice.
"""
            
            try:
                messages = [
                    {"role": "system", "content": profile_context}
                ] + [{"role": msg["role"], "content": msg["content"]} 
                     for msg in st.session_state.chat_history[-10:]]  # Last 10 messages
                
                response = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=messages,
                    temperature=0.7,
                    max_tokens=800
                )
                
                assistant_message = response.choices[0].message.content
                st.session_state.chat_history.append({"role": "assistant", "content": assistant_message})
                
                with st.chat_message("assistant"):
                    st.markdown(assistant_message)
                    
            except Exception as e:
                error_msg = f"Sorry, I couldn't process your question: {str(e)}"
                st.session_state.chat_history.append({"role": "assistant", "content": error_msg})
                with st.chat_message("assistant"):
                    st.error(error_msg)
        else:
            error_msg = "AI chat is not available. Please configure GROQ_API_KEY."
            st.session_state.chat_history.append({"role": "assistant", "content": error_msg})
            with st.chat_message("assistant"):
                st.error(error_msg)

def render_predictions(user_data):
    """Render salary predictions and recommendations"""
    result = calculate_salary(user_data)
    predicted_salary, confidence, market_demand, model_used = result
    
    st.subheader("💰 Salary Prediction")
    m1, m2, m3 = st.columns(3)
    with m1:
        st.metric("Predicted Salary", f"₹{predicted_salary:.1f} LPA")
    with m2:
        st.metric("Confidence", f"{confidence:.0f}%")
    with m3:
        st.metric("Market Demand", market_demand)
    
    st.caption(f"Model: {model_used}")
    
    # Tabs for different sections
    tab1, tab2, tab3 = st.tabs(["🤖 AI Insights", "💡 Basic Recommendations", "💬 Ask Questions"])
    
    with tab1:
        # Generate and display AI insights
        if st.button("Generate AI Career Insights", key="generate_insights"):
            with st.spinner("Analyzing your profile with AI..."):
                insights = generate_career_insights(user_data, predicted_salary, confidence, market_demand)
                st.session_state.ai_insights = insights
        
        if 'ai_insights' in st.session_state:
            render_ai_insights(st.session_state.ai_insights)
        else:
            st.info("Click 'Generate AI Career Insights' to get personalized recommendations powered by Groq AI (Llama 3.3)")
    
    with tab2:
        st.subheader("💡 Quick Recommendations")
        recs = []
        if user_data['experience'] < 2:
            recs.append("Focus on foundational skills and internships")
        if user_data['ml_skills'] < 3:
            recs.append("Invest time in ML/AI projects and courses")
        if user_data['cloud_skills'] < 2:
            recs.append("Add a cloud provider (AWS/Azure/GCP)")
        if user_data['location'] == "Tier 3":
            recs.append("Consider opportunities in Tier 1 cities")
        
        for i, r in enumerate(recs, 1):
            st.write(f"{i}. {r}")
    
    with tab3:
        render_chat_interface(user_data, predicted_salary, confidence, market_demand)

def render_market_insights():
    """Render market insights sidebar"""
    st.subheader("📊 Market Insights")
    
    skills_data = pd.DataFrame({
        'Skill': ['Python', 'Machine Learning', 'SQL', 'AWS', 'JavaScript'],
        'Demand': [85, 78, 72, 68, 65]
    })
    fig = px.bar(skills_data, x='Demand', y='Skill', orientation='h',
                 title="Top Skills in Demand", color='Demand',
                 color_continuous_scale='Blues')
    fig.update_layout(height=300, showlegend=False)
    st.plotly_chart(fig, use_container_width=True)
    
    exp_data = pd.DataFrame({
        'Experience': ['0-2', '2-5', '5-10', '10+'],
        'Avg Salary': [3.5, 6.2, 9.8, 15.2]
    })
    fig2 = px.line(exp_data, x='Experience', y='Avg Salary',
                   title="Experience vs Average Salary", markers=True)
    fig2.update_layout(height=250)
    st.plotly_chart(fig2, use_container_width=True)

def render():
    """Main render function for student dashboard"""
    st.markdown('<div class="fade-in">', unsafe_allow_html=True)
    st.markdown('<div class="content-title">🎓 Student Dashboard</div>', unsafe_allow_html=True)
    
    # Get user inputs from sidebar
    user_data = render_sidebar()
    
    if user_data['predict_button']:
        st.session_state.show_prediction = True
    
    # Main content area
    c_main, c_side = st.columns([2, 1])
    
    with c_main:
        # st.markdown("<div class=\"main-content\">", unsafe_allow_html=True)
        if st.session_state.get('show_prediction', False):
            render_predictions(user_data)
        else:
            st.info("👈 Fill your details in the sidebar and click 'Predict My Salary' to begin")
        st.markdown("</div>", unsafe_allow_html=True)
    
    with c_side:
        render_market_insights()
    
    st.markdown('</div>', unsafe_allow_html=True)