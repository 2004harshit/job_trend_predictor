import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime

# Page configuration
st.set_page_config(
	page_title="Job Trend Predictor",
	page_icon="📊",
	layout="wide",
	initial_sidebar_state="expanded"
)

# Custom CSS for modern design
st.markdown("""
<style>
	/* Global Styles */
	.main { padding-top: 2rem; }

	/* Navigation Styles */
	.nav-container { background: linear-gradient(90deg, #667eea 0%, #764ba2 100%); padding: 1rem 0; margin-bottom: 2rem; border-radius: 10px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1); }
	.nav-title { color: white; font-size: 2rem; font-weight: bold; text-align: center; margin: 0; text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3); }
	.nav-tabs { display: flex; justify-content: center; gap: 2rem; margin-top: 1rem; }
	.nav-tab { background: rgba(255, 255, 255, 0.2); color: white; padding: 0.5rem 1.5rem; border-radius: 25px; text-decoration: none; font-weight: 500; transition: all 0.3s ease; border: 2px solid transparent; }
	.nav-tab:hover { background: rgba(255, 255, 255, 0.3); transform: translateY(-2px); box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2); }
	.nav-tab.active { background: white; color: #667eea; border: 2px solid white; }

	/* Card Styles */
	.dashboard-card { background: white; border-radius: 15px; padding: 2rem; box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1); transition: all 0.3s ease; border: 1px solid #e0e0e0; height: 300px; display: flex; flex-direction: column; justify-content: center; align-items: center; text-align: center; }
	.dashboard-card:hover { transform: translateY(-5px); box-shadow: 0 15px 35px rgba(0, 0, 0, 0.15); }
	.card-icon { font-size: 4rem; margin-bottom: 1rem; }
	.card-title { font-size: 1.5rem; font-weight: bold; color: #333; margin-bottom: 1rem; }
	.card-description { color: #666; font-size: 1rem; line-height: 1.5; margin-bottom: 1.5rem; }

	/* Sidebar */
	.sidebar-content { background: #f8f9fa; padding: 1.5rem; border-radius: 10px; margin-bottom: 1rem; }
	.sidebar-title { color: #333; font-size: 1.2rem; font-weight: bold; margin-bottom: 1rem; border-bottom: 2px solid #667eea; padding-bottom: 0.5rem; }

	/* Main Content */
	.main-content { background: white; padding: 2rem; border-radius: 10px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1); min-height: 500px; }
	.content-title { color: #333; font-size: 2rem; font-weight: bold; margin-bottom: 1.5rem; text-align: center; }

	/* Power BI */
	.powerbi-container { background: #f8f9fa; border: 2px dashed #667eea; border-radius: 10px; padding: 3rem; text-align: center; margin: 2rem 0; }
	.powerbi-placeholder { color: #667eea; font-size: 1.2rem; font-weight: 500; }

	/* About */
	.about-section { background: white; padding: 2rem; border-radius: 10px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1); margin-bottom: 2rem; }
	.about-title { color: #333; font-size: 1.8rem; font-weight: bold; margin-bottom: 1rem; border-bottom: 3px solid #667eea; padding-bottom: 0.5rem; }
	.feature-list { list-style: none; padding: 0; }
	.feature-list li { padding: 0.5rem 0; border-bottom: 1px solid #eee; }
	.feature-list li:before { content: "✨ "; color: #667eea; font-weight: bold; }

	/* Responsive */
	@media (max-width: 768px) { .nav-tabs { flex-direction: column; gap: 1rem; } .dashboard-card { height: auto; margin-bottom: 1rem; } }

	/* Animation */
	.fade-in { animation: fadeIn 0.5s ease-in; }
	@keyframes fadeIn { from { opacity: 0; transform: translateY(20px);} to { opacity: 1; transform: translateY(0);} }
</style>
""", unsafe_allow_html=True)

# Session state
if 'current_page' not in st.session_state:
	st.session_state.current_page = 'Home'
if 'show_prediction' not in st.session_state:
	st.session_state.show_prediction = False

# Navigation

def navigate_to(page: str) -> None:
	st.session_state.current_page = page
	st.rerun()


def render_navigation() -> None:
	st.markdown("""
	<div class="nav-container">
		<h1 class="nav-title">📊 Job Trend Predictor</h1>
		<div class="nav-tabs"></div>
	</div>
	""", unsafe_allow_html=True)
	c1, c2 = st.columns([1, 1])
	with c1:
		if st.button("🏠 Home", key="nav_home", use_container_width=True):
			navigate_to('Home')
	with c2:
		if st.button("ℹ️ About", key="nav_about", use_container_width=True):
			navigate_to('About')

# Pages

def render_home_page() -> None:
	st.markdown('<div class="fade-in">', unsafe_allow_html=True)
	st.markdown("""
	<div class="content-title">Welcome to Job Trend Predictor</div>
	<p style="text-align: center; color: #666; font-size: 1.1rem; margin-bottom: 3rem;">
		Empowering students and career counselors with data-driven insights for better career decisions
	</p>
	""", unsafe_allow_html=True)
	c1, c2 = st.columns(2)
	with c1:
		st.markdown("""
		<div class="dashboard-card">
			<div class="card-icon">🎓</div>
			<div class="card-title">Student Dashboard</div>
			<div class="card-description">Get personalized insights, salary estimates, and recommendations based on your profile.</div>
		</div>
		""", unsafe_allow_html=True)
		if st.button("Enter Student Dashboard", key="btn_student", use_container_width=True):
			navigate_to('Student Dashboard')
	with c2:
		st.markdown("""
		<div class="dashboard-card">
			<div class="card-icon">🧑‍🏫</div>
			<div class="card-title">Career Counselor Dashboard</div>
			<div class="card-description">Access analytics and embedded Power BI reports to guide student careers.</div>
		</div>
		""", unsafe_allow_html=True)
		if st.button("Enter Counselor Dashboard", key="btn_counselor", use_container_width=True):
			navigate_to('Career Counselor Dashboard')
	st.markdown('</div>', unsafe_allow_html=True)


def render_student_dashboard() -> None:
	st.markdown('<div class="fade-in">', unsafe_allow_html=True)
	st.markdown("""
	<div class="content-title">🎓 Student Dashboard</div>
	""", unsafe_allow_html=True)
	with st.sidebar:
		st.markdown("""
		<div class="sidebar-content"><div class="sidebar-title">📝 Your Profile</div></div>
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
		skills_input = st.text_area("Additional Skills (comma-separated)", placeholder="python, machine learning, sql, etc.")
		st.subheader("🏢 Company Preferences")
		company_size = st.selectbox("Preferred Company Size", ["Small", "Medium", "Large"])
		industry = st.selectbox("Industry Type", ["IT Services & Consulting", "Internet", "Software Product", "Banking", "Financial Services", "E-Learning", "Other"])
		if st.button("🔮 Predict My Salary", key="predict_salary", use_container_width=True):
			st.session_state.show_prediction = True
	c_main, c_side = st.columns([2, 1])
	with c_main:
		st.markdown("<div class=\"main-content\">", unsafe_allow_html=True)
		if st.session_state.get('show_prediction', False):
			st.subheader("💰 Salary Prediction")
			base_salary = 3.5 + (experience * 0.8) + (programming_skills * 0.3) + (ml_skills * 0.4)
			location_multiplier = {"Tier 1": 1.2, "Tier 2": 1.0, "Tier 3": 0.8}[location]
			education_multiplier = {"Graduate": 1.0, "Postgraduate": 1.2, "Other": 0.9}[education]
			predicted_salary = base_salary * location_multiplier * education_multiplier
			m1, m2, m3 = st.columns(3)
			with m1: st.metric("Predicted Salary", f"₹{predicted_salary:.1f} LPA")
			with m2: st.metric("Confidence", f"{min(95, 60 + (experience * 2) + (programming_skills + ml_skills + data_skills) * 3):.0f}%")
			with m3:
				market_demand = "High" if (ml_skills + data_skills) > 3 else ("Medium" if (programming_skills + ml_skills) > 2 else "Low")
				st.metric("Market Demand", market_demand)
			lower_bound = predicted_salary * 0.8
			upper_bound = predicted_salary * 1.2
			st.info(f"**Expected Range:** ₹{lower_bound:.1f} - ₹{upper_bound:.1f} LPA")
			st.subheader("💡 Career Recommendations")
			recs = []
			if experience < 2: recs.append("Focus on foundational skills and internships")
			if ml_skills < 3: recs.append("Invest time in ML/AI projects and courses")
			if cloud_skills < 2: recs.append("Add a cloud provider (AWS/Azure/GCP)")
			if location == "Tier 3": recs.append("Consider opportunities in Tier 1 cities")
			for i, r in enumerate(recs, 1): st.write(f"{i}. {r}")
		else:
			st.info("👈 Fill your details in the sidebar and click 'Predict My Salary' to begin")
		st.markdown("</div>", unsafe_allow_html=True)
	with c_side:
		st.subheader("📊 Market Insights")
		skills_data = pd.DataFrame({'Skill': ['Python', 'Machine Learning', 'SQL', 'AWS', 'JavaScript'], 'Demand': [85, 78, 72, 68, 65]})
		fig = px.bar(skills_data, x='Demand', y='Skill', orientation='h', title="Top Skills in Demand", color='Demand', color_continuous_scale='Blues')
		fig.update_layout(height=300, showlegend=False)
		st.plotly_chart(fig, use_container_width=True)
		exp_data = pd.DataFrame({'Experience': ['0-2', '2-5', '5-10', '10+'], 'Avg Salary': [3.5, 6.2, 9.8, 15.2]})
		fig2 = px.line(exp_data, x='Experience', y='Avg Salary', title="Experience vs Average Salary", markers=True)
		fig2.update_layout(height=250)
		st.plotly_chart(fig2, use_container_width=True)
	st.markdown('</div>', unsafe_allow_html=True)


def render_counselor_dashboard() -> None:
	st.markdown('<div class="fade-in">', unsafe_allow_html=True)
	st.markdown("""
	<div class="content-title">🧑‍🏫 Career Counselor Dashboard</div>
	""", unsafe_allow_html=True)
	st.markdown("""
	<div class="powerbi-container">
		<div class="powerbi-placeholder">📊 Power BI Report Integration</div>
		<p style=\"color: #666; margin-top: 1rem;\">Embed your Power BI report iframe here for interactive insights.</p>
	</div>
	""", unsafe_allow_html=True)
	st.markdown("### 📈 Market Analytics Dashboard")
	c1, c2, c3, c4 = st.columns(4)
	with c1: st.metric("Total Jobs Analyzed", "1,724", "↗️ 12%")
	with c2: st.metric("Active Companies", "792", "↗️ 8%")
	with c3: st.metric("Average Salary", "₹7.2L", "↗️ 15%")
	with c4: st.metric("Skill Categories", "2,918", "↗️ 5%")
	t1, t2, t3 = st.tabs(["📊 Market Trends", "🏢 Industry Analysis", "🌍 Geographic Distribution"])
	with t1:
		st.subheader("Job Market Trends")
		trend_data = pd.DataFrame({'Month': ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'], 'Job Postings': [120, 135, 142, 158, 165, 172], 'Avg Salary': [6.8, 6.9, 7.0, 7.1, 7.2, 7.3]})
		fig = make_subplots(specs=[[{"secondary_y": True}]])
		fig.add_trace(go.Scatter(x=trend_data['Month'], y=trend_data['Job Postings'], name="Job Postings"), secondary_y=False)
		fig.add_trace(go.Scatter(x=trend_data['Month'], y=trend_data['Avg Salary'], name="Avg Salary (LPA)"), secondary_y=True)
		fig.update_layout(title_text="Market Trends Over Time")
		st.plotly_chart(fig, use_container_width=True)
	with t2:
		st.subheader("Industry Analysis")
		industry_data = pd.DataFrame({'Industry': ['IT Services', 'Software Product', 'Internet', 'Banking', 'E-Learning'], 'Job Count': [450, 320, 280, 180, 120], 'Avg Salary': [8.2, 9.5, 7.8, 6.5, 5.8]})
		fig = px.bar(industry_data, x='Industry', y='Job Count', title="Job Distribution by Industry", color='Avg Salary', color_continuous_scale='Viridis')
		st.plotly_chart(fig, use_container_width=True)
	with t3:
		st.subheader("Geographic Distribution")
		geo_data = pd.DataFrame({'City Tier': ['Tier 1', 'Tier 2', 'Tier 3'], 'Job Count': [850, 520, 354], 'Avg Salary': [8.5, 6.2, 4.8]})
		fig = px.pie(geo_data, values='Job Count', names='City Tier', title="Job Distribution by City Tier")
		st.plotly_chart(fig, use_container_width=True)
	st.markdown('</div>', unsafe_allow_html=True)


def render_about_page() -> None:
	st.markdown('<div class="fade-in">', unsafe_allow_html=True)
	st.markdown("""
	<div class="content-title">ℹ️ About Job Trend Predictor</div>
	""", unsafe_allow_html=True)
	st.markdown("""
	<div class="about-section">
		<div class="about-title">🎯 Project Overview</div>
		<p style="font-size: 1.1rem; line-height: 1.6; color: #555;">The <strong>Job Trend Predictor</strong> provides data-driven insights for students and counselors using a modern Streamlit interface and interactive analytics.</p>
	</div>
	""", unsafe_allow_html=True)
	st.markdown("""
	<div class="about-section">
		<div class="about-title">🔧 Technologies Used</div>
		<ul class="feature-list">
			<li>Python, Streamlit, Plotly</li>
			<li>Scikit-learn, XGBoost (for modeling)</li>
			<li>Pandas, NumPy for data processing</li>
			<li>Power BI (embedded dashboards)</li>
		</ul>
	</div>
	""", unsafe_allow_html=True)
	st.markdown("""
	<div class="about-section">
		<div class="about-title">✨ Key Features & Benefits</div>
		<ul class="feature-list">
			<li>Student Dashboard with sidebar inputs and real-time results</li>
			<li>Career Counselor Dashboard with analytics and Power BI placeholder</li>
			<li>Modern, responsive UI with smooth transitions</li>
			<li>Consistent theme and typography</li>
		</ul>
	</div>
	""", unsafe_allow_html=True)
	st.markdown("""
	<div class="about-section" style="text-align:center; background:#f8f9fa;">
		<p style="color:#666; margin:0;">© 2024 Job Trend Predictor. Built with ❤️ using Python, Streamlit, and ML</p>
	</div>
	""", unsafe_allow_html=True)
	st.markdown('</div>', unsafe_allow_html=True)

# Main

def main() -> None:
	render_navigation()
	if st.session_state.current_page == 'Home':
		render_home_page()
	elif st.session_state.current_page == 'Student Dashboard':
		render_student_dashboard()
	elif st.session_state.current_page == 'Career Counselor Dashboard':
		render_counselor_dashboard()
	elif st.session_state.current_page == 'About':
		render_about_page()

if __name__ == "__main__":
	main()
