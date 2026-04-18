import streamlit as st

def render(navigate_to):
    """Render the enhanced home page"""

    # Common Icons Setup (Clean, emoji-free)
    ICON_TARGET = '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M22 12H18"/><path d="M6 12H2"/><path d="M12 2v4"/><path d="M12 18v4"/><path d="m15 9-3 3 3 3"/><path d="m9 9 3 3-3 3"/></svg>'
    ICON_BRAIN = '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 9a3 3 0 0 1 6 0c0 1-.5 1.5-1 2-.5.5-1 1-1 2"/><path d="M12 17h.01"/><path d="M5.5 8A6.5 6.5 0 0 1 18 6.5"/><path d="M8 20h8"/><path d="M7 20a4 4 0 0 1-.88-7.9"/><path d="M17.88 12.1A4 4 0 0 1 17 20"/></svg>'
    ICON_ROCKET = '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4.5 21 9 3l4 9 4-6 2.5 15"/><path d="M4.5 21h15"/></svg>'
    ICON_CHART = '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 3v18h18"/><rect x="7" y="10" width="3" height="7" rx="1"/><rect x="12" y="6" width="3" height="11" rx="1"/><rect x="17" y="8" width="3" height="9" rx="1"/></svg>'
    ICON_ZAP = '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 12h6l3-9 3 18 3-9h3"/></svg>'
    ICON_TREND = '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 3v18h18"/><path d="m19 9-5 5-4-4-3 3"/></svg>'
    ICON_USER = '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>'
    ICON_BOOK = '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H20v20H6.5a2.5 2.5 0 0 1 0-5H20"/></svg>'
    ICON_COMPASS = '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><polygon points="16.24 7.76 14.12 14.12 7.76 16.24 9.88 9.88 16.24 7.76"/></svg>'

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
                navigate_to("Profile Selection")
        with btn_col2:
            if st.button("▶ Watch Demo", use_container_width=True):
                st.info("Demo video coming soon!")
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Stats Section
    st.markdown("""
    <div class="stats-grid">
        <div class="stat-card">
            <div class="stat-number">355K+</div>
            <div class="stat-label card-bottom">Job Openings Tracked</div>
        </div>
        <div class="stat-card">
            <div class="stat-number">1500+</div>
            <div class="stat-label card-bottom">Companies Analyzed</div>
        </div>
        <div class="stat-card">
            <div class="stat-number">50+</div>
            <div class="stat-label card-bottom">Tech Skills Monitored</div>
        </div>
        <div class="stat-card">
            <div class="stat-number">85%</div>
            <div class="stat-label card-bottom">Prediction Accuracy</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Features Section - modern landing style (single-line SVGs to avoid raw HTML showing)
    features = [
        {"title": "Domain Confusion Resolver", "description": "Compare multiple tech domains with AI-powered recommendations. Know exactly which path suits you best.", "gradient_class": "gradient-blue-cyan", "icon_svg": ICON_TARGET},
        {"title": "AI-Powered Insights", "description": "Machine learning models analyze market trends and predict future demands with 85%+ accuracy.", "gradient_class": "gradient-purple-pink", "icon_svg": ICON_BRAIN},
        {"title": "Career Path Generator", "description": "Get personalized learning roadmaps with skill requirements, timelines, and salary projections.", "gradient_class": "gradient-green-emerald", "icon_svg": ICON_ROCKET},
        {"title": "Real-Time Market Data", "description": "Access live hiring trends, salary insights, and job openings across 350K+ opportunities.", "gradient_class": "gradient-orange-red", "icon_svg": ICON_CHART},
        {"title": "Skill Gap Analysis", "description": "Identify missing skills and get priority learning paths to become industry-ready faster.", "gradient_class": "gradient-yellow-orange", "icon_svg": ICON_ZAP},
        {"title": "Future Trend Forecasting", "description": "ARIMA & Prophet models predict 6-12 month market trends for strategic career planning.", "gradient_class": "gradient-indigo-purple", "icon_svg": ICON_TREND},
    ]

    cards_html = "".join(
        f'<div class="feature-card"><div class="feature-icon-wrapper {f["gradient_class"]}">{f["icon_svg"]}</div><h3 class="feature-title">{f["title"]}</h3><p class="feature-description card-bottom">{f["description"]}</p></div>'
        for f in features
    )

    hero_heading_svg = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>'

    st.markdown(
        f'<section class="features-section"><div class="features-inner"><div class="features-heading"><div class="pill-badge"><span class="pill-badge-icon">{hero_heading_svg}</span><span>Powerful Features</span></div><h2 class="features-heading-title">Everything You Need to<br/><span class="gradient-title">Make Smart Career Moves</span></h2><p class="features-heading-subtitle">Comprehensive tools and insights designed for every stage of your career journey.</p></div><div class="feature-grid">{cards_html}</div></div></section>',
        unsafe_allow_html=True,
    )
    
    # How It Works Section
    st.markdown('<div class="section-spacing"></div>', unsafe_allow_html=True) # Spacer before How It Works
    
    st.markdown(f"""
<div class="how-it-works-container" style="margin-bottom: 3.5rem;">
    <div class="how-it-works-badge">
        <span class="how-it-works-badge-icon">{ICON_ROCKET}</span>
        <span>Simple Process</span>
    </div>
    <h2 class="how-it-works-title">How It Works</h2>
    <p class="how-it-works-subtitle">Three simple steps to career clarity</p>
</div>
""", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3, gap="large")
    
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
                <p class="process-description card-bottom">Open Profile Selection — choose Fresher to unlock the full dashboard</p>
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
                <p class="process-description card-bottom">Access personalized dashboards with real-time market data and AI predictions</p>
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
                <p class="process-description card-bottom">Use data-driven recommendations to plan your career moves strategically</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
    

    # Personas Section
    st.markdown('<div class="section-spacing"></div>', unsafe_allow_html=True) # Adding symmetric spacing
    
    # Persona data — Freshers, Intermediate, Counselors
    personas = [
        {"icon": ICON_USER, "title": "Freshers", "desc": "Navigate career choices with data-driven domain comparisons and skill roadmaps",
         "features": ["Domain Selection Guide", "Learning Roadmaps", "Company Insights", "Salary Expectations"]},
        {"icon": ICON_BOOK, "title": "Intermediate Learners", "desc": "Analyze skill gaps and discover high-value upskilling opportunities",
         "features": ["Skill Gap Analysis", "Upskilling Advisor", "Role Predictions", "Salary Projections"]},
        {"icon": ICON_COMPASS, "title": "Counselors", "desc": "Access comprehensive market insights for curriculum design and career guidance",
         "features": ["Market Overview", "Trend Forecasting", "Emerging Skills", "Policy Recommendations"]}
    ]

    persona_cards_html = ""
    for p in personas:
        features_html = "".join(
            f'<div class="persona-feature-item"><div class="persona-feature-icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M20 6 9 17l-5-5"/></svg></div><span>{f}</span></div>'
            for f in p["features"]
        )
        persona_cards_html += f"""
<div class="persona-card">
    <div class="persona-header">{p["icon"]} <h3>{p["title"]}</h3></div>
    <p class="persona-description">{p["desc"]}</p>
    <div class="persona-features card-bottom">{features_html}</div>
</div>
"""

    st.markdown(f"""
<section class="personas-section">
<div class="personas-inner">
<div class="personas-heading">
<div class="personas-badge">
{ICON_USER}
<span>For Learners</span>
</div>
<h2 class="personas-title">Tailored for Your Journey</h2>
<p class="personas-subtitle">Insights built for freshers and intermediate learners entering tech</p>
</div>
<div class="persona-grid">
{persona_cards_html}</div>
</div>
</section>
""", unsafe_allow_html=True)
    
    # Footer
    st.markdown("""
    <div class="footer">
        <div class="footer-content">
            <div class="footer-brand">
                <h3>Job Trend Predictor</h3>
                <p>AI-powered career intelligence for tech learners and job seekers</p>
            </div>
        </div>
        <div class="footer-bottom">
            <p>© 2026 Job Trend Predictor. All rights reserved.</p>
            <p class="footer-stats">Reliable Data from LinkedIn, Naukri, Indeed &bull; 85%+ Prediction Accuracy</p>
        </div>
    </div>
    """, unsafe_allow_html=True)