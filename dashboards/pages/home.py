# import streamlit as st

# def render(navigate_to):
#     """Render the home page"""
#     st.markdown('<div class="fade-in">', unsafe_allow_html=True)
    
#     st.markdown("""
#     <div class="content-title">Navigate Your Tech Career
# With Confidence</div>
#     <p style="text-align: center; color: #666; font-size: 1.1rem; margin-bottom: 3rem;">
#         Make informed career decisions backed by real-time market data, AI predictions, and comprehensive trend analysis across 350K+ job opportunities
#     </p>
#     """, unsafe_allow_html=True)
    
#     col1, col2, col3 = st.columns(3)

#     with col1:
#         st.metric(label="Prediction Accuracy", value="85%", delta="120")
    
#     with col2:
#         st.metric(label="Job Opening tracked", value="$12,405", delta="-15%", delta_color="normal")
    
#     with col3:
#         st.metric(label="Tech Skill Monitored", value="50+", delta="8%", delta_color="normal")

#     st.markdown(""" 
#             <span>Powerful Feature</span>
#                 <p>Everything You Need to</p>
#                 <p>Make Smart Career Moves</p>
#                 <p>Comprehensive tools and insights designed for every stage of your career journey</p>
#     """,unsafe_allow_html=True)
#     with st.container():
#         st.markdown("""
#                     <h4>Domain Confusion Resolver</h4>
#                     <p>Compare multiple tech domains with AI-powered recommendations. Know exactly which path suits you best.</p>
#                     """,unsafe_allow_html=True)
#     with st.container():
#         st.markdown("""
#                     <h4>AI-Powered Insights</h4>
#                     <p>Machine learning models analyze market trends and predict future demands with 85%+ accuracy.</p>
#                     """,unsafe_allow_html=True)
#     with st.container():
#         st.markdown("""
#                     <h4>Career Path Generator</h4>
#                     <p>Get personalized learning roadmaps with skill requirements, timelines, and salary projections.</p>
#                     """,unsafe_allow_html=True)
#     with st.container():
#         st.markdown("""
#                     <h4>Real-Time Market Data</h4>
#                     <p>Access live hiring trends, salary insights, and job openings across 350K+ opportunities.</p>
#                     """, unsafe_allow_html=True)
#     with st.container():
#         st.markdown("""
#                     <h4>Skill Gap Analysis</h4>
#                     <p>Identify missing skills and get priority learning paths to become industry-ready faster.</p>
#                     """,unsafe_allow_html=True)
#     with st.container():
#         st.markdown("""
#                     <h4>Future Trend Forecasting</h4>
#                     <p>ARIMA & Prophet models predict 6-12 month market trends for strategic career planning.</p>
#                     """, unsafe_allow_html=True)
    
#     st.markdown(""" 
# Simple Process<br>
# How It Works<br>
# Three simple steps to career clarity
#                 Select Your Profile
# Choose whether you're a fresher, intermediate learner, professional, or counselo
#                 Explore Insights
# Access personalized dashboards with real-time market data and AI predictions
#                 Make Decisions
# Use data-driven recommendations to plan your career moves strategically""", unsafe_allow_html=True)
#     with st.container():
#         st.markdown("""
# For Everyone
# Tailored for Your Journey
# Personalized dashboards for every career stage

# 👨‍🎓 Freshers
# Navigate career choices with data-driven domain comparisons and skill roadmaps

# Domain Selection Guide
# Learning Roadmaps
# Company Insights
# Salary Expectations
# 📚 Intermediate Learners
# Analyze skill gaps and discover high-value upskilling opportunities

# Skill Gap Analysis
# Upskilling Advisor
# Role Predictions
# Salary Projections
# 💼 Professionals
# Find growth opportunities and optimal switch timing with market intelligence

# Career Growth Path
# Switch Opportunities
# Salary Comparison
# Domain Switch Analysis
# 🎯 Counselors
# Access comprehensive market insights for curriculum design and career guidance

# Market Overview
# Trend Forecasting
# Emerging Skills
# Policy Recommendations

# """, unsafe_allow_html=True)
#     with st.container():
#         st.markdown("""Powered by AI
# Advanced Machine Learning
# Our platform uses cutting-edge AI models including ARIMA, Prophet, and XGBoost to deliver accurate predictions with 85%+ confidence intervals

# 🔮
# ARIMA Models
# Time-series forecasting for trend prediction

# 📊
# Prophet Algorithm
# Seasonal trend decomposition & analysis

# 🚀
# XGBoost
# Advanced regression for salary prediction

# Ready to Transform Your Career?
# Join thousands who are making smarter career decisions with data-driven insights


# Get Started Now
# No credit card required • Free access • Updated daily

# CareerTrend AI
# AI-powered career intelligence platform for the modern tech professional

# Platform
# Features
# Pricing
# API Access
# Resources
# Documentation
# Blog
# Career Guides
# Company
# About Us
# Contact
# Privacy Policy
# © 2024 CareerTrend AI. All rights reserved.

# 📊 Data from LinkedIn, Naukri, Indeed
# •
# 🤖 85%+ Prediction Accuracy""",unsafe_allow_html=True)
#     # c1, c2 = st.columns(2)
#     # with c1:
#     #     st.markdown("""
#     #     <div class="dashboard-card">
#     #         <div class="card-icon">🎓</div>
#     #         <div class="card-title">Student Dashboard</div>
#     #         <div class="card-description">
#     #             Get personalized insights, salary estimates, and recommendations based on your profile.
#     #         </div>
#     #     </div>
#     #     """, unsafe_allow_html=True)
#     #     if st.button("Enter Student Dashboard", key="btn_student", use_container_width=True):
#     #         navigate_to('Student Dashboard')
    
#     # with c2:
#     #     st.markdown("""
#     #     <div class="dashboard-card">
#     #         <div class="card-icon">🧑‍🏫</div>
#     #         <div class="card-title">Career Counselor Dashboard</div>
#     #         <div class="card-description">
#     #             Access analytics and embedded Power BI reports to guide student careers.
#     #         </div>
#     #     </div>
#     #     """, unsafe_allow_html=True)
#     #     if st.button("Enter Counselor Dashboard", key="btn_counselor", use_container_width=True):
#     #         navigate_to('Career Counselor Dashboard')
    
#     # st.markdown('</div>', unsafe_allow_html=True)

import streamlit as st
import time

def render(navigate_to):
    """Render the enhanced home page"""
    
    # Hero Section
    st.markdown("""
    <div class="hero-container">
        <div class="hero-content">
            <h1 class="hero-headline">
                Navigate Your Tech Career<br/>
                <span class="hero-highlight">With Confidence</span>
            </h1>
            <p class="hero-subtitle">
                Make informed career decisions backed by real-time market data, AI predictions, and comprehensive trend analysis across 350K+ job opportunities
            </p>
            <div class="features">
                <div class="feature-item">
                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
                        <path d="M20 6 9 17l-5-5"></path>
                    </svg>
                    <span>Real-time job market intel</span>
                </div>
                <div class="feature-item">
                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
                        <path d="M20 6 9 17l-5-5"></path>
                    </svg>
                    <span>AI-driven career predictions</span>
                </div>
                <div class="feature-item">
                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
                        <path d="M20 6 9 17l-5-5"></path>
                    </svg>
                    <span>350K+ opportunities analyzed</span>
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Real interactive buttons (kept outside the hero HTML by design)
    left_spacer, center, right_spacer = st.columns([1, 2, 1])
    with center:
        st.markdown('<div class="hero-streamlit-actions">', unsafe_allow_html=True)
        btn_col1, btn_col2 = st.columns(2)
        with btn_col1:
            if st.button("🚀 Get Started Now", use_container_width=True, type="primary"):
                navigate_to('profile')  # or wherever you want
        with btn_col2:
            if st.button("▶ Watch Demo", use_container_width=True):
                st.info("Demo video coming soon!")
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Stats Section
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="stat-card">
            <div class="stat-number">85%</div>
            <div class="stat-label">Prediction Accuracy</div>
            <div class="stat-change positive">↑ 12% from last month</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="stat-card">
            <div class="stat-number">350K+</div>
            <div class="stat-label">Job Openings Tracked</div>
            <div class="stat-change positive">↑ Updated Daily</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="stat-card">
            <div class="stat-number">50+</div>
            <div class="stat-label">Tech Skills Monitored</div>
            <div class="stat-change positive">↑ 8% growth</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br/>", unsafe_allow_html=True)
    
    # Features Section Header
    st.markdown("""
    <div class="section-header">
        <span class="section-badge">Powerful Features</span>
        <h2 class="section-title">Everything You Need to<br/>Make Smart Career Moves</h2>
        <p class="section-subtitle">Comprehensive tools and insights designed for every stage of your career journey</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Features Grid
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="feature-card">
            <div class="feature-icon purple">🎯</div>
            <h3 class="feature-title">Domain Confusion Resolver</h3>
            <p class="feature-description">Compare multiple tech domains with AI-powered recommendations. Know exactly which path suits you best.</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="feature-card">
            <div class="feature-icon blue">📊</div>
            <h3 class="feature-title">Real-Time Market Data</h3>
            <p class="feature-description">Access live hiring trends, salary insights, and job openings across 350K+ opportunities.</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="feature-card">
            <div class="feature-icon pink">🧠</div>
            <h3 class="feature-title">AI-Powered Insights</h3>
            <p class="feature-description">Machine learning models analyze market trends and predict future demands with 85%+ accuracy.</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="feature-card">
            <div class="feature-icon green">🔍</div>
            <h3 class="feature-title">Skill Gap Analysis</h3>
            <p class="feature-description">Identify missing skills and get priority learning paths to become industry-ready faster.</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="feature-card">
            <div class="feature-icon orange">🗺️</div>
            <h3 class="feature-title">Career Path Generator</h3>
            <p class="feature-description">Get personalized learning roadmaps with skill requirements, timelines, and salary projections.</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="feature-card">
            <div class="feature-icon teal">🔮</div>
            <h3 class="feature-title">Future Trend Forecasting</h3>
            <p class="feature-description">ARIMA & Prophet models predict 6-12 month market trends for strategic career planning.</p>
        </div>
        """, unsafe_allow_html=True)
    
    # How It Works Section
    st.markdown("""
    <div class="section-header" style="margin-top: 4rem;">
        <span class="section-badge">Simple Process</span>
        <h2 class="section-title">How It Works</h2>
        <p class="section-subtitle">Three simple steps to career clarity</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="process-card">
            <div class="process-number">1</div>
            <h3 class="process-title">Select Your Profile</h3>
            <p class="process-description">Choose whether you're a fresher, intermediate learner, professional, or counselor</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="process-card">
            <div class="process-number">2</div>
            <h3 class="process-title">Explore Insights</h3>
            <p class="process-description">Access personalized dashboards with real-time market data and AI predictions</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="process-card">
            <div class="process-number">3</div>
            <h3 class="process-title">Make Decisions</h3>
            <p class="process-description">Use data-driven recommendations to plan your career moves strategically</p>
        </div>
        """, unsafe_allow_html=True)
    
    # User Personas Section
    st.markdown("""
    <div class="section-header" style="margin-top: 4rem;">
        <span class="section-badge">For Everyone</span>
        <h2 class="section-title">Tailored for Your Journey</h2>
        <p class="section-subtitle">Personalized dashboards for every career stage</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div class="persona-card">
            <div class="persona-header">
                <span class="persona-icon">👨‍🎓</span>
                <h3 class="persona-title">Freshers</h3>
            </div>
            <p class="persona-description">Navigate career choices with data-driven domain comparisons and skill roadmaps</p>
            <ul class="persona-features">
                <li>✓ Domain Selection Guide</li>
                <li>✓ Learning Roadmaps</li>
                <li>✓ Company Insights</li>
                <li>✓ Salary Expectations</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="persona-card">
            <div class="persona-header">
                <span class="persona-icon">💼</span>
                <h3 class="persona-title">Professionals</h3>
            </div>
            <p class="persona-description">Find growth opportunities and optimal switch timing with market intelligence</p>
            <ul class="persona-features">
                <li>✓ Career Growth Path</li>
                <li>✓ Switch Opportunities</li>
                <li>✓ Salary Comparison</li>
                <li>✓ Domain Switch Analysis</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="persona-card">
            <div class="persona-header">
                <span class="persona-icon">📚</span>
                <h3 class="persona-title">Intermediate Learners</h3>
            </div>
            <p class="persona-description">Analyze skill gaps and discover high-value upskilling opportunities</p>
            <ul class="persona-features">
                <li>✓ Skill Gap Analysis</li>
                <li>✓ Upskilling Advisor</li>
                <li>✓ Role Predictions</li>
                <li>✓ Salary Projections</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="persona-card">
            <div class="persona-header">
                <span class="persona-icon">🎯</span>
                <h3 class="persona-title">Counselors</h3>
            </div>
            <p class="persona-description">Access comprehensive market insights for curriculum design and career guidance</p>
            <ul class="persona-features">
                <li>✓ Market Overview</li>
                <li>✓ Trend Forecasting</li>
                <li>✓ Emerging Skills</li>
                <li>✓ Policy Recommendations</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    # AI Models Section
    st.markdown("""
    <div class="section-header" style="margin-top: 4rem;">
        <span class="section-badge">Powered by AI</span>
        <h2 class="section-title">Advanced Machine Learning</h2>
        <p class="section-subtitle">Our platform uses cutting-edge AI models to deliver accurate predictions with 85%+ confidence</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="ai-model-card">
            <div class="ai-icon">🔮</div>
            <h3 class="ai-title">ARIMA Models</h3>
            <p class="ai-description">Time-series forecasting for accurate trend prediction</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="ai-model-card">
            <div class="ai-icon">📊</div>
            <h3 class="ai-title">Prophet Algorithm</h3>
            <p class="ai-description">Seasonal trend decomposition & analysis</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="ai-model-card">
            <div class="ai-icon">🚀</div>
            <h3 class="ai-title">XGBoost</h3>
            <p class="ai-description">Advanced regression for salary prediction</p>
        </div>
        """, unsafe_allow_html=True)
    
    # CTA Section
    st.markdown("""
    <div class="cta-section">
        <h2 class="cta-title">Ready to Transform Your Career?</h2>
        <p class="cta-subtitle">Join thousands who are making smarter career decisions with data-driven insights</p>
        <button class="cta-button">Get Started Now →</button>
        <p class="cta-note">No credit card required • Free access • Updated daily</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Footer
    st.markdown("""
    <div class="footer">
        <div class="footer-content">
            <div class="footer-brand">
                <h3>CareerTrend AI</h3>
                <p>AI-powered career intelligence platform for the modern tech professional</p>
            </div>
            <div class="footer-links">
                <div class="footer-column">
                    <h4>Platform</h4>
                    <ul>
                        <li>Features</li>
                        <li>Pricing</li>
                        <li>API Access</li>
                    </ul>
                </div>
                <div class="footer-column">
                    <h4>Resources</h4>
                    <ul>
                        <li>Documentation</li>
                        <li>Blog</li>
                        <li>Career Guides</li>
                    </ul>
                </div>
                <div class="footer-column">
                    <h4>Company</h4>
                    <ul>
                        <li>About Us</li>
                        <li>Contact</li>
                        <li>Privacy Policy</li>
                    </ul>
                </div>
            </div>
        </div>
        <div class="footer-bottom">
            <p>© 2024 CareerTrend AI. All rights reserved.</p>
            <p class="footer-stats">📊 Data from LinkedIn, Naukri, Indeed • 🤖 85%+ Prediction Accuracy</p>
        </div>
    </div>
    """, unsafe_allow_html=True)