# """
# Domain Confusion Resolver - Complete Streamlit Implementation
# Complete working code with all visualizations and interactions
# """

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import numpy as np

# # ============================================
# # PAGE CONFIGURATION
# # ============================================
# st.set_page_config(
#     page_title="Domain Confusion Resolver | Job Trend Platform",
#     page_icon="🎯",
#     layout="wide",
#     initial_sidebar_state="expanded"
# )

# # Custom CSS for better styling
# st.markdown("""
# <style>
#     .main-header {
#         font-size: 3rem;
#         font-weight: bold;
#         color: #1f77b4;
#         text-align: center;
#         margin-bottom: 0;
#     }
#     .sub-header {
#         font-size: 1.2rem;
#         color: #666;
#         text-align: center;
#         margin-top: 0;
#     }
#     .metric-card {
#         background-color: #f0f2f6;
#         padding: 20px;
#         border-radius: 10px;
#         border-left: 5px solid #1f77b4;
#     }
#     .recommendation-box {
#         background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
#         color: white;
#         padding: 30px;
#         border-radius: 15px;
#         margin: 20px 0;
#     }
#     .stTabs [data-baseweb="tab-list"] {
#         gap: 10px;
#     }
#     .stTabs [data-baseweb="tab"] {
#         height: 50px;
#         padding: 10px 20px;
#         background-color: #f0f2f6;
#         border-radius: 5px;
#     }
#     .stTabs [aria-selected="true"] {
#         background-color: #1f77b4;
#         color: white;
#     }
# </style>
# """, unsafe_allow_html=True)

# # ============================================
# # SESSION STATE INITIALIZATION
# # ============================================
# if 'analyzed' not in st.session_state:
#     st.session_state.analyzed = False
# if 'selected_domain' not in st.session_state:
#     st.session_state.selected_domain = None
# if 'comparison_domains' not in st.session_state:
#     st.session_state.comparison_domains = []

# # ============================================
# # SAMPLE DATA GENERATION (Replace with your actual data)
# # ============================================
# @st.cache_data
# def load_sample_data():
#     """Generate sample data - replace with your actual data loading"""
    
#     domains_data = {
#         'Web Development': {
#             'demand_score': 82,
#             'job_count': 8450,
#             'trend_yoy': 15.3,
#             'avg_salary': 8,
#             'salary': {'min': 5, 'p25': 6, 'median': 8, 'p75': 10, 'max': 15},
#             'growth_score': 78,
#             'ease_of_entry': 7.5,
#             'time_to_job_ready': 6,
#             'job_security_score': 72,
#             'remote_percent': 65,
#             'top_skills': ['React', 'JavaScript', 'Node.js', 'CSS', 'HTML'],
#             'saturation': 'Balanced'
#         },
#         'Data Science': {
#             'demand_score': 76,
#             'job_count': 6200,
#             'trend_yoy': 22.1,
#             'avg_salary': 12,
#             'salary': {'min': 7, 'p25': 9, 'median': 12, 'p75': 15, 'max': 25},
#             'growth_score': 88,
#             'ease_of_entry': 5.5,
#             'time_to_job_ready': 10,
#             'job_security_score': 85,
#             'remote_percent': 70,
#             'top_skills': ['Python', 'SQL', 'Machine Learning', 'Statistics', 'Pandas'],
#             'saturation': 'Undersupplied'
#         },
#         'Cloud Computing': {
#             'demand_score': 71,
#             'job_count': 5800,
#             'trend_yoy': 18.5,
#             'avg_salary': 10,
#             'salary': {'min': 6, 'p25': 8, 'median': 10, 'p75': 13, 'max': 20},
#             'growth_score': 82,
#             'ease_of_entry': 6.0,
#             'time_to_job_ready': 8,
#             'job_security_score': 80,
#             'remote_percent': 75,
#             'top_skills': ['AWS', 'Azure', 'Docker', 'Kubernetes', 'DevOps'],
#             'saturation': 'Undersupplied'
#         },
#         'Cybersecurity': {
#             'demand_score': 58,
#             'job_count': 3100,
#             'trend_yoy': 12.3,
#             'avg_salary': 9,
#             'salary': {'min': 6, 'p25': 7, 'median': 9, 'p75': 12, 'max': 18},
#             'growth_score': 75,
#             'ease_of_entry': 5.0,
#             'time_to_job_ready': 12,
#             'job_security_score': 88,
#             'remote_percent': 50,
#             'top_skills': ['Network Security', 'Penetration Testing', 'SIEM', 'Cryptography', 'Linux'],
#             'saturation': 'Balanced'
#         },
#         'DevOps': {
#             'demand_score': 62,
#             'job_count': 4200,
#             'trend_yoy': 16.7,
#             'avg_salary': 11,
#             'salary': {'min': 7, 'p25': 9, 'median': 11, 'p75': 14, 'max': 22},
#             'growth_score': 80,
#             'ease_of_entry': 5.5,
#             'time_to_job_ready': 9,
#             'job_security_score': 78,
#             'remote_percent': 68,
#             'top_skills': ['CI/CD', 'Docker', 'Jenkins', 'Terraform', 'Git'],
#             'saturation': 'Balanced'
#         }
#     }
    
#     # Trend data (last 12 months)
#     months = pd.date_range(start='2024-01-01', periods=12, freq='MS')
#     trend_data = {}
#     for domain in domains_data.keys():
#         base = domains_data[domain]['job_count'] / 12
#         trend = base + np.random.normal(0, base * 0.1, 12)
#         trend = np.cumsum(np.random.normal(base/12, base/20, 12))
#         trend_data[domain] = pd.DataFrame({
#             'month': months.strftime('%b %Y'),
#             'job_count': trend.astype(int)
#         })
    
#     # Regional data
#     cities = ['Bangalore', 'Delhi NCR', 'Mumbai', 'Pune', 'Hyderabad', 
#               'Chennai', 'Kolkata', 'Jaipur']
#     regional_data = {}
#     for domain in domains_data.keys():
#         regional_data[domain] = pd.DataFrame({
#             'city': cities,
#             'job_count': np.random.randint(100, 3000, len(cities)),
#             'avg_salary': np.random.uniform(6, 15, len(cities)),
#             'demand_level': np.random.choice(['Low', 'Medium', 'High'], len(cities))
#         })
    
#     return domains_data, trend_data, regional_data

# domains_data, trend_data, regional_data = load_sample_data()

# # ============================================
# # HELPER FUNCTIONS
# # ============================================
# def calculate_match_score(user_profile, domain_data):
#     """Calculate personalized match score based on user preferences"""
    
#     weights = {
#         'Highest Salary': {'salary': 0.5, 'demand': 0.2, 'growth': 0.3},
#         'Job Security': {'demand': 0.3, 'job_security': 0.4, 'saturation': 0.3},
#         'Easy Entry': {'ease_of_entry': 0.5, 'demand': 0.3, 'time': 0.2},
#         'Growth Potential': {'growth': 0.5, 'demand': 0.3, 'salary': 0.2},
#         'Balanced': {'demand': 0.25, 'salary': 0.25, 'growth': 0.25, 'ease_of_entry': 0.25}
#     }
    
#     priority = user_profile['priority']
#     w = weights[priority]
    
#     score = 0
#     if 'salary' in w:
#         score += (domain_data['avg_salary'] / 15) * 100 * w['salary']
#     if 'demand' in w:
#         score += domain_data['demand_score'] * w['demand']
#     if 'growth' in w:
#         score += domain_data['growth_score'] * w['growth']
#     if 'ease_of_entry' in w:
#         score += (domain_data['ease_of_entry'] / 10) * 100 * w['ease_of_entry']
#     if 'job_security' in w:
#         score += domain_data['job_security_score'] * w.get('job_security', 0)
    
#     return min(int(score), 100)

# def get_recommendations(user_profile, domains_data):
#     """Get top 2 recommendations based on user profile"""
    
#     scores = {}
#     for domain, data in domains_data.items():
#         scores[domain] = calculate_match_score(user_profile, data)
    
#     # Sort by score
#     sorted_domains = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    
#     # Get reasons
#     primary_domain = sorted_domains[0][0]
#     primary_data = domains_data[primary_domain]
    
#     primary_reasons = []
#     if primary_data['demand_score'] >= 70:
#         primary_reasons.append("High market demand")
#     if primary_data['ease_of_entry'] >= 7:
#         primary_reasons.append("Beginner-friendly entry path")
#     if primary_data['growth_score'] >= 75:
#         primary_reasons.append("Strong career growth potential")
#     if primary_data['avg_salary'] >= 10:
#         primary_reasons.append("Above-average salary prospects")
    
#     return {
#         'primary': {
#             'domain': primary_domain,
#             'match_score': sorted_domains[0][1],
#             'reasons': primary_reasons[:3],
#             'data': primary_data
#         },
#         'alternative': {
#             'domain': sorted_domains[1][0],
#             'match_score': sorted_domains[1][1],
#             'reasons': ["Alternative with different strengths", "Consider if primary doesn't fit"],
#             'data': domains_data[sorted_domains[1][0]]
#         }
#     }

# # ============================================
# # UI COMPONENTS
# # ============================================
# def render_header():
#     """Render page header"""
#     st.markdown('<p class="main-header">🎯 Domain Confusion Resolver</p>', unsafe_allow_html=True)
#     st.markdown('<p class="sub-header">Find Your Perfect Tech Career Path with Data-Driven Insights</p>', 
#                 unsafe_allow_html=True)
    
#     col1, col2, col3 = st.columns([1, 2, 1])
#     with col2:
#         st.caption(f"📅 Data updated: {datetime.now().strftime('%B %d, %Y')} | "
#                    f"Based on 27,750 job postings across India")
    
#     st.markdown("---")

# def render_sidebar():
#     """Render sidebar with user input"""
#     with st.sidebar:
#         st.title("👤 Your Profile")
#         st.markdown("Tell us about yourself to get personalized recommendations")
#         st.markdown("---")
        
#         # Experience Level
#         experience = st.radio(
#             "🎓 What's your current level?",
#             ["Complete Beginner", 
#              "Basic Programming Knowledge", 
#              "Intermediate (1-2 years learning)"],
#             help="This helps us tailor recommendations to your learning stage"
#         )
        
#         # Interest
#         interest = st.selectbox(
#             "💡 What's your area of interest?",
#             ["Web Development", "Data Science", "Cloud Computing", "Cybersecurity", "DevOps"],
#             help="Choose the tech domain you are most interested in"
#         )
#         # Priority
#         priority = st.selectbox(
#             "🎯 What's your top priority?",
#             ["Salary", "Job Security", "Career Growth", "Ease of Entry"],
#             help="Choose what matters most to you in your career path"
#         )
#         priority_map = {
#             "Salary": "Highest Salary",
#             "Job Security": "Job Security",
#             "Career Growth": "Growth Potential",
#             "Ease of Entry": "Easy Entry"
#         }
#         priority_mapped = priority_map[priority]
#         st.markdown("---")
#     return {
#         'experience': experience,
#         'interest': interest,
#         'priority': priority_mapped
#     }

# if __name__ == "__main__":
#     render_header()
#     user_profile = render_sidebar()
    
#     if st.button("🔍 Analyze Domains"):
#         st.session_state.analyzed = True
#         st.session_state.selected_domain = user_profile['interest']
        
#     if st.session_state.analyzed:
#         recommendations = get_recommendations(user_profile, domains_data)
        
#         # Display Recommendations
#         st.markdown('<div class="recommendation-box">', unsafe_allow_html=True)
#         st.markdown(f"### 🌟 Top Recommendation: {recommendations['primary']['domain']}")
#         st.markdown(f"**Match Score:** {recommendations['primary']['match_score']} / 100")
#         st.markdown("**Why this domain?**")
#         for reason in recommendations['primary']['reasons']:
#             st.markdown(f"- {reason}")
#         st.markdown("</div>", unsafe_allow_html=True)
        
#         st.markdown('<div class="recommendation-box" style="background: linear-gradient(135deg, #ff9966 0%, #ff5e62 100%);">', unsafe_allow_html=True)
#         st.markdown(f"### 🔄 Alternative Option: {recommendations['alternative']['domain']}")
#         st.markdown(f"**Match Score:** {recommendations['alternative']['match_score']} / 100")
#         st.markdown("**Consider this domain because:**")
#         for reason in recommendations['alternative']['reasons']:
#             st.markdown(f"- {reason}")
#         st.markdown("</div>", unsafe_allow_html=True)


def render_user_input_expander():
    with st.expander("🎯 Quick Setup: Tell us about yourself", expanded=True):
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            experience = st.selectbox(
                "Experience Level",
                ["Beginner", "Intermediate", "Advanced"]
            )
        
        with col2:
            interest = st.selectbox(
                "Interest Area",
                ["Web Dev", "Data Science", "Cloud", "Other"]
            )
        
        with col3:
            priority = st.selectbox(
                "Priority",
                ["Salary", "Security", "Growth", "Easy Entry"]
            )
        
        with col4:
            location = st.selectbox(
                "Location",
                ["Jaipur", "Metro Cities", "Remote"]
            )
        
        analyze_btn = st.button("🔍 Analyze Domains", type="primary")
    
    return {...}

def render_overview_cards(domains_data):
    st.subheader("📊 Domain Overview at a Glance")
    st.markdown("---")
    
    # Create 5 columns for top domains
    cols = st.columns(5)
    
    domains = ['Web Dev', 'Data Science', 'Cloud', 'Cybersecurity', 'DevOps']
    
    for idx, domain in enumerate(domains):
        with cols[idx]:
            # Get domain data
            data = domains_data[domain]
            
            # Card styling using metrics
            st.metric(
                label=f"**{domain}**",
                value=f"{data['demand_score']}%",
                delta=f"+{data['trend_yoy']}% YoY",
                help=f"Market demand score"
            )
            
            # Salary info
            st.caption(f"💰 ₹{data['avg_salary']} LPA avg")
            
            # Job count
            st.caption(f"📌 {data['job_count']:,} jobs")
            
            # Ease of entry stars
            stars = "⭐" * int(data['ease_of_entry'] / 2)
            st.caption(f"Entry: {stars}")
            
            # Button to deep dive
            if st.button(f"Details", key=f"btn_{domain}"):
                st.session_state.selected_domain = domain

if __name__ == "__main__":
    render_user_input_expander()
    domains_data = {
        'Web Dev': {}
    }
    render_overview_cards(domains_data)