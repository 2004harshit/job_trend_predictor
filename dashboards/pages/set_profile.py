import streamlit as st

def render(navigate_to):
    """Render enhanced profile selection page with modern styling."""

    # Apply custom CSS for this page
    st.markdown("""
    <style>
        /* Profile Selection Specific Styles */
        .profile-hero {         
            background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #d946ef 100%);
            padding: 5rem 3rem;
            border-radius: 24px;
            margin: 2rem 0 3rem 0;
    
            /* Flexbox for even vertical distribution */
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            gap: 1.5rem; /* This controls the uniform space between ALL elements */
    
            text-align: center;
            position: relative;
            overflow: hidden;
            min-height: 400px; /* Ensures enough room for even spacing */
        }

        .profile-hero-badge {
            display: inline-block;
            padding: 0.6rem 1.4rem;
            background: rgba(255, 255, 255, 0.12);
            color: #ffffff;
            border-radius: 100px;
            font-size: 0.75rem;
            font-weight: 800;
            text-transform: uppercase;
            letter-spacing: 0.15em;
            border: 1px solid rgba(255, 255, 255, 0.3);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);

            /* Removed margin-bottom/top because 'gap' handles it now */
            margin: 0; 
        }

        .profile-hero-title {
            font-size: 4rem;
            font-weight: 900;
            color: white;
            line-height: 1.1;
            letter-spacing: -0.02em;
            margin: 0; /* Let the parent gap handle spacing */
        }

        .profile-hero-subtitle {
            font-size: 1.25rem;
            color: rgba(255, 255, 255, 0.95);
            max-width: 800px;
            line-height: 1.7;
            font-weight: 400;
            margin: 0; /* Let the parent gap handle spacing */
        }
        
        /* Profile Card Container Styles */
        .user_profile_fresher_persona_container,
        .user_profile_working_professional_persona_container,
        .user_profile_career_counselor_persona_container {
            background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
            border-radius: 20px;
            padding: 2rem;
            margin-bottom: 1.5rem;
            border: 2px solid rgba(99, 102, 241, 0.2);
            transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
            position: relative;
            overflow: hidden;
        }
        
        .user_profile_fresher_persona_container::before,
        .user_profile_working_professional_persona_container::before,
        .user_profile_career_counselor_persona_container::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
            background: linear-gradient(90deg, #6366f1, #8b5cf6, #d946ef);
            opacity: 0;
            transition: opacity 0.3s;
        }
        
        .user_profile_fresher_persona_container:hover,
        .user_profile_working_professional_persona_container:hover,
        .user_profile_career_counselor_persona_container:hover {
            transform: translateY(-8px);
            border-color: rgba(99, 102, 241, 0.5);
            box-shadow: 0 20px 40px rgba(99, 102, 241, 0.15);
        }
        
        .user_profile_fresher_persona_container:hover::before,
        .user_profile_working_professional_persona_container:hover::before,
        .user_profile_career_counselor_persona_container:hover::before {
            opacity: 1;
        }
        
        /* List items inside profile cards */
        .user_profile_fresher_persona_container ls,
        .user_profile_working_professional_persona_container ls,
        .user_profile_career_counselor_persona_container ls {
            display: block;
            padding: 0.75rem 0;
            color: #cbd5e1;
            font-size: 1rem;
            line-height: 1.6;
            border-bottom: 1px solid rgba(148, 163, 184, 0.1);
            transition: all 0.3s;
        }
        
        .user_profile_fresher_persona_container ls:first-child,
        .user_profile_working_professional_persona_container ls:first-child,
        .user_profile_career_counselor_persona_container ls:first-child {
            font-size: 1.4rem;
            font-weight: 700;
            color: #f8fafc;
            padding-bottom: 1rem;
            margin-bottom: 0.5rem;
            border-bottom: 2px solid rgba(99, 102, 241, 0.3);
        }
        
        .user_profile_fresher_persona_container ls:last-child,
        .user_profile_working_professional_persona_container ls:last-child,
        .user_profile_career_counselor_persona_container ls:last-child {
            border-bottom: none;
            padding-bottom: 0;
        }
        
        .user_profile_fresher_persona_container:hover ls,
        .user_profile_working_professional_persona_container:hover ls,
        .user_profile_career_counselor_persona_container:hover ls {
            color: #e2e8f0;
            padding-left: 0.5rem;
        }
        
        /* Add icons/bullets to list items */
        .user_profile_fresher_persona_container ls:not(:first-child)::before,
        .user_profile_working_professional_persona_container ls:not(:first-child)::before,
        .user_profile_career_counselor_persona_container ls:not(:first-child)::before {
            content: '✓';
            display: inline-block;
            margin-right: 0.75rem;
            color: #6366f1;
            font-weight: bold;
            font-size: 1.1rem;
        }
        
        /* Different gradient accents for each profile */
        .user_profile_fresher_persona_container::after {
            content: '👨‍🎓';
            position: absolute;
            top: 1.5rem;
            right: 1.5rem;
            font-size: 2.5rem;
            opacity: 0.2;
            transition: all 0.3s;
        }
        
        .user_profile_working_professional_persona_container::after {
            content: '💼';
            position: absolute;
            top: 1.5rem;
            right: 1.5rem;
            font-size: 2.5rem;
            opacity: 0.2;
            transition: all 0.3s;
        }
        
        .user_profile_career_counselor_persona_container::after {
            content: '🎯';
            position: absolute;
            top: 1.5rem;
            right: 1.5rem;
            font-size: 2.5rem;
            opacity: 0.2;
            transition: all 0.3s;
        }
        
        .user_profile_fresher_persona_container:hover::after,
        .user_profile_working_professional_persona_container:hover::after,
        .user_profile_career_counselor_persona_container:hover::after {
            opacity: 0.4;
            transform: scale(1.1) rotate(5deg);
        }
        
        /* Button styling to match cards */
        div.stButton > button {
            width: 100%;
            background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%) !important;
            color: white !important;
            border: none !important;
            border-radius: 12px !important;
            padding: 1rem 2rem !important;
            font-size: 1.1rem !important;
            font-weight: 600 !important;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
            box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3) !important;
        }
        
        div.stButton > button:hover {
            transform: translateY(-2px) !important;
            box-shadow: 0 8px 20px rgba(99, 102, 241, 0.4) !important;
            background: linear-gradient(135deg, #7c3aed 0%, #a855f7 100%) !important;
        }
        
        div.stButton > button:active {
            transform: translateY(0px) !important;
        }
        
        /* Feature List Styling */
        .profile-features {
            background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
            border-radius: 20px;
            padding: 2.5rem;
            margin-top: 4rem;
            border: 1px solid rgba(99, 102, 241, 0.15);
        }
        
        .profile-features h3 {
            font-size: 1.75rem;
            font-weight: 800;
            color: #f8fafc;
            margin-bottom: 1.5rem;
            text-align: center;
        }
        
        .profile-features ul {
            list-style: none;
            padding: 0;
            margin: 0;
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 1rem;
        }
        
        .profile-features li {
            padding: 1rem;
            background: rgba(99, 102, 241, 0.05);
            border-radius: 12px;
            color: #cbd5e1;
            font-size: 1rem;
            border-left: 3px solid #6366f1;
            transition: all 0.3s;
        }
        
        .profile-features li:hover {
            background: rgba(99, 102, 241, 0.1);
            transform: translateX(5px);
        }
        
        @media (max-width: 768px) {
            .profile-hero-title {
                font-size: 2.5rem;
            }
            
            .profile-hero-subtitle {
                font-size: 1.1rem;
            }
            
            .user_profile_fresher_persona_container,
            .user_profile_working_professional_persona_container,
            .user_profile_career_counselor_persona_container {
                padding: 1.5rem;
            }
            
            .user_profile_fresher_persona_container ls:first-child,
            .user_profile_working_professional_persona_container ls:first-child,
            .user_profile_career_counselor_persona_container ls:first-child {
                font-size: 1.2rem;
            }
        }
    </style>
    """, unsafe_allow_html=True)

    # Initialize profile_data if it doesn't exist
    if 'profile_data' not in st.session_state:
        st.session_state.profile_data = {}
    
    # Hero Section
    st.markdown("""
    <div class="profile-hero">
        <h1 class="profile-hero-title">Choose Your Journey 🚀</h1>
        <p class="profile-hero-subtitle">
            Select your profile to get personalized career insights, tailored recommendations, 
            and industry trends designed specifically for your path.
        </p>
        <div class="profile-hero-badge">
            ✨ Powered by AI-driven analytics
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Profile Selection Cards
    col1, col2, col3 = st.columns(3, gap="large")
    
    with col1:
        st.markdown("""<div class="user_profile_fresher_persona_container">
                    <ls>Fresher / Student</ls>
                    <ls>Skill Gap Analysis</ls>
                    <ls>Learning Roadmaps</ls>
                    <ls>Entry-level Insights</ls>
            </div>""", unsafe_allow_html=True)
        if st.button(
            "👨‍🎓 Go to Fresher Dashboard",
            use_container_width=True,
            key="fresher"
        ):
            st.session_state.profile_data['persona'] = 'Fresher'
            st.success("✅ Profile created successfully! Welcome aboard!")
            st.balloons()
            navigate_to('Student Dashboard')
    
    with col2:
        st.markdown("""<div class="user_profile_working_professional_persona_container">
                    <ls>Professional Working with experience</ls>
                    <ls>Career Growth Path</ls>
                    <ls>Upskilling Advice</ls>
                    <ls>Market Positioning</ls>
            </div>""", unsafe_allow_html=True)
        if st.button(
            "💼 Go to Professional Dashboard",
            use_container_width=True,
            key="professional"
        ):
            st.session_state.profile_data['persona'] = 'Professional'
            st.success("✅ Profile created successfully! Let's accelerate your growth!")
            st.balloons()
            navigate_to('Student Dashboard')
    
    with col3:
        st.markdown("""<div class="user_profile_career_counselor_persona_container">
                    <ls>Career Counselor</ls>
                    <ls>Guiding Students & Professionals</ls>
                    <ls>Market Insights</ls>
                    <ls>Trend Forecasting</ls>
            </div>""", unsafe_allow_html=True)
        if st.button(
            "🎯 Go to Career Counselor Dashboard",
            use_container_width=True,
            key="counselor"
        ):
            st.session_state.profile_data['persona'] = 'Career Counselor'
            st.success("✅ Profile created successfully! Ready to empower others!")
            st.balloons()
            navigate_to('Career Counselor Dashboard')
    
    # What You'll Get Section
    st.markdown("""
    <div class="profile-features">
        <h3>🎁 What You'll Get</h3>
        <ul>
            <li>📊 Real-time job market analytics</li>
            <li>🎯 Personalized skill recommendations</li>
            <li>📈 Industry trend forecasts</li>
            <li>💡 AI-powered career guidance</li>
            <li>🔍 Salary benchmarking tools</li>
            <li>🌟 Domain comparison insights</li>
            <li>📚 Learning resource suggestions</li>
            <li>🚀 Career path visualization</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    # Additional spacing
    st.markdown("<div style='margin-bottom: 3rem;'></div>", unsafe_allow_html=True)