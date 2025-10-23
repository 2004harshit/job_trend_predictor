import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

def render_powerbi_section():
    """Render Power BI integration section"""
    st.markdown("""
    <div class="powerbi-container">
        <div class="powerbi-placeholder">📊 Power BI Report Integration</div>
        <p style="color: #666; margin-top: 1rem;">
            Embed your Power BI report iframe here for interactive insights.
        </p>
    </div>
    """, unsafe_allow_html=True)

def render_metrics():
    """Render key metrics cards"""
    st.markdown("### 📈 Market Analytics Dashboard")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Total Jobs Analyzed", "1,724", "↗️ 12%")
    with c2:
        st.metric("Active Companies", "792", "↗️ 8%")
    with c3:
        st.metric("Average Salary", "₹7.2L", "↗️ 15%")
    with c4:
        st.metric("Skill Categories", "2,918", "↗️ 5%")

def render_market_trends():
    """Render market trends tab"""
    st.subheader("Job Market Trends")
    
    trend_data = pd.DataFrame({
        'Month': ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
        'Job Postings': [120, 135, 142, 158, 165, 172],
        'Avg Salary': [6.8, 6.9, 7.0, 7.1, 7.2, 7.3]
    })
    
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(
        go.Scatter(x=trend_data['Month'], y=trend_data['Job Postings'], 
                   name="Job Postings"),
        secondary_y=False
    )
    fig.add_trace(
        go.Scatter(x=trend_data['Month'], y=trend_data['Avg Salary'], 
                   name="Avg Salary (LPA)"),
        secondary_y=True
    )
    fig.update_layout(title_text="Market Trends Over Time")
    st.plotly_chart(fig, use_container_width=True)

def render_industry_analysis():
    """Render industry analysis tab"""
    st.subheader("Industry Analysis")
    
    industry_data = pd.DataFrame({
        'Industry': ['IT Services', 'Software Product', 'Internet', 'Banking', 'E-Learning'],
        'Job Count': [450, 320, 280, 180, 120],
        'Avg Salary': [8.2, 9.5, 7.8, 6.5, 5.8]
    })
    
    fig = px.bar(industry_data, x='Industry', y='Job Count',
                 title="Job Distribution by Industry",
                 color='Avg Salary', color_continuous_scale='Viridis')
    st.plotly_chart(fig, use_container_width=True)

def render_geographic_distribution():
    """Render geographic distribution tab"""
    st.subheader("Geographic Distribution")
    
    geo_data = pd.DataFrame({
        'City Tier': ['Tier 1', 'Tier 2', 'Tier 3'],
        'Job Count': [850, 520, 354],
        'Avg Salary': [8.5, 6.2, 4.8]
    })
    
    fig = px.pie(geo_data, values='Job Count', names='City Tier',
                 title="Job Distribution by City Tier")
    st.plotly_chart(fig, use_container_width=True)

def render():
    """Main render function for counselor dashboard"""
    st.markdown('<div class="fade-in">', unsafe_allow_html=True)
    st.markdown('<div class="content-title">🧑‍🏫 Career Counselor Dashboard</div>', 
                unsafe_allow_html=True)
    
    render_powerbi_section()
    render_metrics()
    
    # Create tabs for different analytics
    t1, t2, t3 = st.tabs([
        "📊 Market Trends",
        "🏢 Industry Analysis",
        "🌍 Geographic Distribution"
    ])
    
    with t1:
        render_market_trends()
    
    with t2:
        render_industry_analysis()
    
    with t3:
        render_geographic_distribution()
    
    st.markdown('</div>', unsafe_allow_html=True)