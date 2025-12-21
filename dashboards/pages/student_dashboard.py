import streamlit as st



def render(navigate_to):
   if  st.session_state.profile_data['persona'] =='Fresher':
        st.title("Welcome to the Student Dashboard")
        st.write("Here you can access your courses, track your progress, and connect with mentors.")
        st.markdown("""
        <style>.student-dashboard-header {
            text-align: center;
            margin-bottom: 20px;
               }
            .Student-dashboard-features {
               font-size: 18px;
               line-height: 1.6;
               }
                    </style>
        <div class="student-dashboard-header">
            <h1>🎓 Student Dashboard</h1>
        </div>
        <div class = "Student-dashboard-features">
               <ul>
                    <li>📚 Access your courses and learning materials</li>
                    <li>📈 Track your learning progress and achievements</li>
                    <li>🤝 Connect with mentors and peers</li>
                    <li>🗓️ Manage your study schedule and deadlines</li>
               </ul>
            </div>
        """, unsafe_allow_html=True)
   else:
          st.title("Welcome to the Professional Dashboard")
          st.write("Here you can manage your projects, enhance your skills, and network with peers.")       
     
render("")