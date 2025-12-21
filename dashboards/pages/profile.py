import streamlit as st

def render(navigate_to):
    """Render profile selection page with Q&A format"""
    
    # Initialize session state for profile data
    if 'profile_step' not in st.session_state:
        st.session_state.profile_step = 1
    if 'profile_data' not in st.session_state:
        st.session_state.profile_data = {}
    
    st.markdown("""
    <div class="profile-header">
        <h1>👋 Let's Get to Know You</h1>
        <p>Answer a few questions to personalize your experience</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Progress bar
    progress = st.session_state.profile_step / 4
    st.progress(progress)
    st.markdown(f"**Step {st.session_state.profile_step} of 4**")
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Question 1: Name
    if st.session_state.profile_step == 1:
        st.markdown("### 📝 What's your name?")
        name = st.text_input("", placeholder="Enter your full name", key="name_input")
        
        if st.button("Next →", disabled=not name, type="primary"):
            st.session_state.profile_data['name'] = name
            st.session_state.profile_step = 2
            st.rerun()
    
    # Question 2: Role/Persona
    elif st.session_state.profile_step == 2:
        st.markdown(f"### 👤 Great, {st.session_state.profile_data.get('name')}! What best describes you?")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("👨‍🎓 Fresher\n\nJust starting my career", use_container_width=True, key="fresher"):
                st.session_state.profile_data['persona'] = 'Fresher'
                st.session_state.profile_step = 3
                st.rerun()
            
            if st.button("💼 Professional\n\nWorking with experience", use_container_width=True, key="professional"):
                st.session_state.profile_data['persona'] = 'Professional'
                st.session_state.profile_step = 3
                st.rerun()
        
        with col2:
            if st.button("📚 Intermediate Learner\n\nBuilding my skills", use_container_width=True, key="intermediate"):
                st.session_state.profile_data['persona'] = 'Intermediate Learner'
                st.session_state.profile_step = 3
                st.rerun()
            
            if st.button("🎯 Career Counselor\n\nGuiding others", use_container_width=True, key="counselor"):
                st.session_state.profile_data['persona'] = 'Career Counselor'
                st.session_state.profile_step = 3
                st.rerun()
        
        if st.button("← Back", key="back_2"):
            st.session_state.profile_step = 1
            st.rerun()
    
    # Question 3: Experience Level
    elif st.session_state.profile_step == 3:
        persona = st.session_state.profile_data.get('persona')
        
        if persona == 'Professional':
            st.markdown("### 📊 How much working experience do you have?")
            experience = st.slider("Years of Experience", 0, 20, 0, key="exp_slider")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("← Back", key="back_3"):
                    st.session_state.profile_step = 2
                    st.rerun()
            with col2:
                if st.button("Next →", type="primary", key="next_3"):
                    st.session_state.profile_data['experience'] = experience

        elif persona in ['Fresher', 'Intermediate Learner']:
            st.markdown("### 📊 Intrested Domains?")

            col1 , col2 = st.columns(2)
            with col1:
                domain_interest = st.multiselect("Select Domains of Interest", [
                    "Data Science", "Web Development", "Mobile Development",
                    "Cloud Computing", "Cybersecurity", "AI & Machine Learning",
                    "DevOps", "Game Development", "UI/UX Design"
                ], key="domain_interest")
            with col2:
                st.markdown("#### Educational Background")
                education = st.selectbox("Highest Qualification", [
                    "High School", "Bachelor's Degree", "Master's Degree",
                    "PhD", "Diploma", "Other"
                ], key="education_select")

            st.markdown("<br>", unsafe_allow_html=True) 

            col1, col2 = st.columns(2)
            with col1:
                if st.button("← Back", key="back_3"):
                    st.session_state.profile_step = 2
                    st.rerun()
            with col2:
                if st.button("Next →", type="primary", key="next_3"):
                    st.session_state.profile_data['domain_interest'] = domain_interest
                    st.session_state.profile_data['education'] = education
                    st.session_state.profile_step = 4
                    st.rerun()       
        else:
            # Skip for counselors
            st.session_state.profile_data['experience'] = None
            st.session_state.profile_step = 4
            navigate_to('Career Counselor Dashboard')
    
    # Question 4: Skills
    elif st.session_state.profile_step == 4:
        st.markdown("### 💡 What skills do you have or want to learn?")
        
        col1, col2 = st.columns(2)
        with col1:
            tech_skills = st.multiselect("Technical Skills", [
                "Python", "Java", "JavaScript", "C++", "SQL",
                "React", "Node.js", "Django", "Flask",
                "Machine Learning", "Data Analysis", "AI",
                "Cloud Computing", "DevOps", "Docker"
            ], key="tech_skills")
        
        with col2:
            location = st.text_input("Preferred Work Location", placeholder="e.g., Remote, New York, San Francisco", key="location_input")
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("← Back", key="back_4"):
                st.session_state.profile_step = 3
                st.rerun()
        with col2:
            if st.button("Complete Profile 🎉", type="primary", disabled=not (tech_skills or location)):
                st.session_state.profile_data['tech_skills'] = tech_skills
                st.session_state.profile_data['location'] = location
                
                # Show success and navigate to dashboard
                st.success(f"✅ Profile created successfully!")
                st.balloons()
                
                # Navigate based on persona
                persona = st.session_state.profile_data.get('persona')
                if persona == 'Career Counselor':
                    navigate_to('Career Counselor Dashboard')
                else:
                    navigate_to('Student Dashboard')