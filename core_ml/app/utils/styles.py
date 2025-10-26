import streamlit as st

def apply_custom_styles():
    """Apply custom CSS styles to the application"""
    st.markdown("""
    <style>
        /* Global Styles */
        .main { padding-top: 2rem; }

        /* Navigation Styles */
        .nav-container { 
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%); 
            padding: 1rem 0; 
            margin-bottom: 2rem; 
            border-radius: 10px; 
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1); 
        }
        .nav-title { 
            color: white; 
            font-size: 2rem; 
            font-weight: bold; 
            text-align: center; 
            margin: 0; 
            text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3); 
        }
        .nav-tabs { 
            display: flex; 
            justify-content: center; 
            gap: 2rem; 
            margin-top: 1rem; 
        }

        /* Card Styles */
        .dashboard-card { 
            background: white; 
            border-radius: 15px; 
            padding: 2rem; 
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1); 
            transition: all 0.3s ease; 
            border: 1px solid #e0e0e0; 
            height: 300px; 
            display: flex; 
            flex-direction: column; 
            justify-content: center; 
            align-items: center; 
            text-align: center; 
        }
        .dashboard-card:hover { 
            transform: translateY(-5px); 
            box-shadow: 0 15px 35px rgba(0, 0, 0, 0.15); 
        }
        .card-icon { font-size: 4rem; margin-bottom: 1rem; }
        .card-title { 
            font-size: 1.5rem; 
            font-weight: bold; 
            color: #333; 
            margin-bottom: 1rem; 
        }
        .card-description { 
            color: #666; 
            font-size: 1rem; 
            line-height: 1.5; 
            margin-bottom: 1.5rem; 
        }

        /* Sidebar */
        .sidebar-content { 
            background: #f8f9fa; 
            padding: 1.5rem; 
            border-radius: 10px; 
            margin-bottom: 1rem; 
        }
        .sidebar-title { 
            color: #333; 
            font-size: 1.2rem; 
            font-weight: bold; 
            margin-bottom: 1rem; 
            border-bottom: 2px solid #667eea; 
            padding-bottom: 0.5rem; 
        }

        /* Main Content */
        .main-content { 
            background: white; 
            padding: 2rem; 
            border-radius: 10px; 
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1); 
            min-height: 500px; 
        }
        .content-title { 
            color: #333; 
            font-size: 2rem; 
            font-weight: bold; 
            margin-bottom: 1.5rem; 
            text-align: center; 
        }

        /* Power BI */
        .powerbi-container { 
            background: #f8f9fa; 
            border: 2px dashed #667eea; 
            border-radius: 10px; 
            padding: 3rem; 
            text-align: center; 
            margin: 2rem 0; 
        }
        .powerbi-placeholder { 
            color: #667eea; 
            font-size: 1.2rem; 
            font-weight: 500; 
        }

        /* About */
        .about-section { 
            background: white; 
            padding: 2rem; 
            border-radius: 10px; 
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1); 
            margin-bottom: 2rem; 
        }
        .about-title { 
            color: #333; 
            font-size: 1.8rem; 
            font-weight: bold; 
            margin-bottom: 1rem; 
            border-bottom: 3px solid #667eea; 
            padding-bottom: 0.5rem; 
        }
        .feature-list { list-style: none; padding: 0; }
        .feature-list li { 
            padding: 0.5rem 0; 
            border-bottom: 1px solid #eee; 
        }
        .feature-list li:before { 
            content: "✨ "; 
            color: #667eea; 
            font-weight: bold; 
        }

        /* Responsive */
        @media (max-width: 768px) { 
            .nav-tabs { flex-direction: column; gap: 1rem; } 
            .dashboard-card { height: auto; margin-bottom: 1rem; } 
        }

        /* Animation */
        .fade-in { animation: fadeIn 0.5s ease-in; }
        @keyframes fadeIn { 
            from { opacity: 0; transform: translateY(20px); } 
            to { opacity: 1; transform: translateY(0); } 
        }
    </style>
    """, unsafe_allow_html=True)