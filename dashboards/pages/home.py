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
    st.markdown("""
    <div class="stats-grid">
        <div class="stat-card">
            <div class="stat-number">355K+</div>
            <div class="stat-label">Job Openings Tracked</div>
        </div>
        <div class="stat-card">
            <div class="stat-number">1500+</div>
            <div class="stat-label">Companies Analyzed</div>
        </div>
        <div class="stat-card">
            <div class="stat-number">50+</div>
            <div class="stat-label">Tech Skills Monitored</div>
        </div>
        <div class="stat-card">
            <div class="stat-number">85%</div>
            <div class="stat-label">Prediction Accuracy</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<br/>", unsafe_allow_html=True)
    
    # Features Section - modern landing style (single-line SVGs to avoid raw HTML showing)
    ICON_TARGET = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M22 12H18"/><path d="M6 12H2"/><path d="M12 2v4"/><path d="M12 18v4"/><path d="m15 9-3 3 3 3"/><path d="m9 9 3 3-3 3"/></svg>'
    ICON_BRAIN = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 9a3 3 0 0 1 6 0c0 1-.5 1.5-1 2-.5.5-1 1-1 2"/><path d="M12 17h.01"/><path d="M5.5 8A6.5 6.5 0 0 1 18 6.5"/><path d="M8 20h8"/><path d="M7 20a4 4 0 0 1-.88-7.9"/><path d="M17.88 12.1A4 4 0 0 1 17 20"/></svg>'
    ICON_ROCKET = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4.5 21 9 3l4 9 4-6 2.5 15"/><path d="M4.5 21h15"/></svg>'
    ICON_CHART = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 3v18h18"/><rect x="7" y="10" width="3" height="7" rx="1"/><rect x="12" y="6" width="3" height="11" rx="1"/><rect x="17" y="8" width="3" height="9" rx="1"/></svg>'
    ICON_ZAP = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 12h6l3-9 3 18 3-9h3"/></svg>'
    ICON_TREND = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 3v18h18"/><path d="m19 9-5 5-4-4-3 3"/></svg>'

    features = [
        {"title": "Domain Confusion Resolver", "description": "Compare multiple tech domains with AI-powered recommendations. Know exactly which path suits you best.", "gradient_class": "gradient-blue-cyan", "icon_svg": ICON_TARGET},
        {"title": "AI-Powered Insights", "description": "Machine learning models analyze market trends and predict future demands with 85%+ accuracy.", "gradient_class": "gradient-purple-pink", "icon_svg": ICON_BRAIN},
        {"title": "Career Path Generator", "description": "Get personalized learning roadmaps with skill requirements, timelines, and salary projections.", "gradient_class": "gradient-green-emerald", "icon_svg": ICON_ROCKET},
        {"title": "Real-Time Market Data", "description": "Access live hiring trends, salary insights, and job openings across 350K+ opportunities.", "gradient_class": "gradient-orange-red", "icon_svg": ICON_CHART},
        {"title": "Skill Gap Analysis", "description": "Identify missing skills and get priority learning paths to become industry-ready faster.", "gradient_class": "gradient-yellow-orange", "icon_svg": ICON_ZAP},
        {"title": "Future Trend Forecasting", "description": "ARIMA & Prophet models predict 6-12 month market trends for strategic career planning.", "gradient_class": "gradient-indigo-purple", "icon_svg": ICON_TREND},
    ]

    cards_html = "".join(
        f'<div class="feature-card"><div class="feature-icon-wrapper {f["gradient_class"]}">{f["icon_svg"]}</div><h3 class="feature-title">{f["title"]}</h3><p class="feature-description">{f["description"]}</p></div>'
        for f in features
    )

    hero_heading_svg = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>'

    st.markdown(
        f'<section class="features-section"><div class="features-inner"><div class="features-heading"><div class="pill-badge"><span class="pill-badge-icon">{hero_heading_svg}</span><span>Powerful Features</span></div><h2 class="features-heading-title">Everything You Need to<br/><span class="gradient-title">Make Smart Career Moves</span></h2><p class="features-heading-subtitle">Comprehensive tools and insights designed for every stage of your career journey.</p></div><div class="feature-grid">{cards_html}</div></div></section>',
        unsafe_allow_html=True,
    )
    
    # How It Works Section
    st.markdown("""
    <div class="how-it-works-container">
        <div class="how-it-works-badge">
            <span class="how-it-works-badge-icon">🚀</span>
            <span>Simple Process</span>
        </div>
        <h2 class="how-it-works-title">How It Works</h2>
        <p class="how-it-works-subtitle">Three simple steps to career clarity</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="process-wrapper">
            <div class="process-card">
                <div class="process-number-wrapper">
                    <div class="process-number">01</div>
                </div>
                <div class="process-icon-wrapper">
                    <svg class="process-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/>
                        <circle cx="9" cy="7" r="4"/>
                        <path d="m22 21-3-3 3-3"/>
                        <path d="M16 21v-2a4 4 0 0 0-4-4H6"/>
                    </svg>
                </div>
                <h3 class="process-title">Select Your Profile</h3>
                <p class="process-description">Choose whether you're a fresher, intermediate learner, professional, or counselor</p>
            </div>
            <div class="process-arrow">
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="width: 32px; height: 32px; color: #2563eb;">
                    <path d="M5 12h14"/>
                    <path d="m12 5 7 7-7 7"/>
                </svg>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="process-wrapper">
            <div class="process-card">
                <div class="process-number-wrapper">
                    <div class="process-number">02</div>
                </div>
                <div class="process-icon-wrapper">
                    <svg class="process-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
                        <line x1="9" y1="9" x2="15" y2="9"/>
                        <line x1="9" y1="15" x2="15" y2="15"/>
                    </svg>
                </div>
                <h3 class="process-title">Explore Insights</h3>
                <p class="process-description">Access personalized dashboards with real-time market data and AI predictions</p>
            </div>
            <div class="process-arrow">
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="width: 32px; height: 32px; color: #2563eb;">
                    <path d="M5 12h14"/>
                    <path d="m12 5 7 7-7 7"/>
                </svg>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="process-wrapper">
            <div class="process-card">
                <div class="process-number-wrapper">
                    <div class="process-number">03</div>
                </div>
                <div class="process-icon-wrapper">
                    <svg class="process-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
                        <polyline points="22 4 12 14.01 9 11.01"/>
                    </svg>
                </div>
                <h3 class="process-title">Make Decisions</h3>
                <p class="process-description">Use data-driven recommendations to plan your career moves strategically</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
    

    # Personas Section
    st.markdown("""
    <section class="personas-section">
        <div class="personas-inner">
            <div class="personas-heading">
                <div class="personas-badge">
                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"></path>
                        <circle cx="9" cy="7" r="4"></circle>
                        <path d="M22 21v-2a4 4 0 0 0-3-3.87"></path>
                        <path d="M16 3.13a4 4 0 0 1 0 7.75"></path>
                    </svg>
                    <span>For Everyone</span>
                </div>
                <h2 class="personas-title">Tailored for Your Journey</h2>
                <p class="personas-subtitle">Personalized dashboards and insights built for every stage of your tech career</p>
            </div>
            <div class="persona-grid">
    """, unsafe_allow_html=True)
    
    # Persona data
    personas = [
        {"emoji": "👨‍🎓", "title": "Freshers", "desc": "Navigate career choices with data-driven domain comparisons and skill roadmaps",
         "features": ["Domain Selection Guide", "Learning Roadmaps", "Company Insights", "Salary Expectations"]},
        {"emoji": "📚", "title": "Intermediate Learners", "desc": "Analyze skill gaps and discover high-value upskilling opportunities",
         "features": ["Skill Gap Analysis", "Upskilling Advisor", "Role Predictions", "Salary Projections"]},
        {"emoji": "💼", "title": "Professionals", "desc": "Find growth opportunities and optimal switch timing with market intelligence",
         "features": ["Career Growth Path", "Switch Opportunities", "Salary Comparison", "Domain Switch Analysis"]},
        {"emoji": "🎯", "title": "Counselors", "desc": "Access comprehensive market insights for curriculum design and career guidance",
         "features": ["Market Overview", "Trend Forecasting", "Emerging Skills", "Policy Recommendations"]}
    ]
    
    # Create 2x2 grid using Streamlit columns
    col1, col2 = st.columns(2)
    
    # First row - Freshers and Intermediate Learners
    with col1:
        features_html = "".join(
            f'<div class="persona-feature-item"><div class="persona-feature-icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M20 6 9 17l-5-5"/></svg></div><span>{f}</span></div>'
            for f in personas[0]["features"]
        )
        st.markdown(f"""
        <div class="persona-card">
            <div class="persona-emoji">{personas[0]["emoji"]} {personas[0]["title"]}</div>
            <p class="persona-description">{personas[0]["desc"]}</p>
            <div class="persona-features">{features_html}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        features_html = "".join(
            f'<div class="persona-feature-item"><div class="persona-feature-icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M20 6 9 17l-5-5"/></svg></div><span>{f}</span></div>'
            for f in personas[1]["features"]
        )
        st.markdown(f"""
        <div class="persona-card">
            <div class="persona-emoji">{personas[1]["emoji"]} {personas[1]["title"]}</div>
            <p class="persona-description">{personas[1]["desc"]}</p>
            <div class="persona-features">{features_html}</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Second row - Professionals and Counselors
    col3, col4 = st.columns(2)
    
    with col3:
        features_html = "".join(
            f'<div class="persona-feature-item"><div class="persona-feature-icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M20 6 9 17l-5-5"/></svg></div><span>{f}</span></div>'
            for f in personas[2]["features"]
        )
        st.markdown(f"""
        <div class="persona-card">
            <div class="persona-emoji">{personas[2]["emoji"]} {personas[2]["title"]}</div>
            <p class="persona-description">{personas[2]["desc"]}</p>
            <div class="persona-features">{features_html}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        features_html = "".join(
            f'<div class="persona-feature-item"><div class="persona-feature-icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M20 6 9 17l-5-5"/></svg></div><span>{f}</span></div>'
            for f in personas[3]["features"]
        )
        st.markdown(f"""
        <div class="persona-card">
            <div class="persona-emoji">{personas[3]["emoji"]} {personas[3]["title"]}</div>
            <p class="persona-description">{personas[3]["desc"]}</p>
            <div class="persona-features">{features_html}</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Close the section containers
    st.markdown("""
        </div>      <!-- personas-inner -->
    </section>      <!-- personas-section -->
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