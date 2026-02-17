import streamlit as st

def apply_custom_styles():
    """Apply enhanced custom CSS styles with dark theme"""
    st.markdown("""
    <style>
        /* Import Google Fonts */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');
        
        /* Global Reset & Base Styles */
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        html, body, [class*="css"] {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        }
                
        /* Main Container */
        .main {
            background: #0f1419;
            color: #e4e4e7;
            padding: 0 !important;
            max-width: 100% !important;
        }
        
        .block-container {
            padding: 2rem 4rem !important;
            max-width: 1400px !important;
            margin: 0 auto;
        }
        
        /* Hide Streamlit Branding */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        
        /* Hero Section */
        /* New premium hero (2025 SaaS style) */
        .hero-container {
            background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 50%, #c026d3 100%);
            padding: 6rem 2rem;
            border-radius: 24px;
            margin: 2rem 1rem 4rem 1rem;
            text-align: center;
            position: relative;
            overflow: hidden;
            box-shadow: 0 25px 50px -12px rgba(124, 58, 237, 0.4);
        }

        .hero-container::before {
            content: "";
            position: absolute;
            inset: 0;
            background:
                radial-gradient(circle at 18% 22%, rgba(255, 255, 255, 0.14) 0%, transparent 55%),
                radial-gradient(circle at 82% 78%, rgba(255, 255, 255, 0.12) 0%, transparent 55%);
            pointer-events: none;
        }

        .hero-content {
            max-width: 900px;
            margin: 0 auto;
            position: relative;
            z-index: 2;
        }

        .hero-headline {
            font-weight: 900;
            line-height: 1.1;
            color: #ffffff !important;
            letter-spacing: -0.025em;
            margin-bottom: 1.5rem;
            font-size: 3.5rem;
            animation: fadeInUp 0.9s ease-out both;
        }

        .hero-headline .hero-highlight {
            background: linear-gradient(to right, #fde047, #f97316);
            -webkit-background-clip: text;
            background-clip: text;
            -webkit-text-fill-color: transparent;
            color: transparent;
        }

        .hero-subtitle {
            font-size: clamp(1.35rem, 1.4vw + 0.95rem, 1.85rem);
            line-height: 1.7;
            color: rgba(255, 255, 255, 0.9);
            max-width: 48rem;
            margin: 0 auto 2.5rem auto;
            animation: fadeInUp 0.9s ease-out both;
            animation-delay: 0.2s;
            text-align  : centre;
        }

        /* Streamlit hero actions (real buttons outside hero) */
        .hero-streamlit-actions {
            margin: 0.25rem 0 0.75rem 0;
        }

        .hero-streamlit-actions .stButton > button,
        .hero-streamlit-actions .stButton button,
        .hero-streamlit-actions button {
            border: none !important;
            border-radius: 12px !important;
            padding: 1rem 2.5rem !important;
            font-size: 1.125rem !important;
            font-weight: 600 !important;
            transition: transform 0.2s ease, box-shadow 0.2s ease, background 0.2s ease, border-color 0.2s ease !important;
        }

        /* Primary (matches earlier hero primary: white background) */
        .hero-streamlit-actions .stButton > button[kind="primary"],
        .hero-streamlit-actions .stButton > button[data-testid="baseButton-primary"],
        .hero-streamlit-actions .stButton button[kind="primary"],
        .hero-streamlit-actions .stButton button[data-testid="baseButton-primary"] {
            background: #ffffff !important;
            color: #6d28d9 !important;
            box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.25) !important;
        }

        .hero-streamlit-actions .stButton > button[kind="primary"]:hover,
        .hero-streamlit-actions .stButton > button[data-testid="baseButton-primary"]:hover,
        .hero-streamlit-actions .stButton button[kind="primary"]:hover,
        .hero-streamlit-actions .stButton button[data-testid="baseButton-primary"]:hover {
            background: rgba(255, 255, 255, 0.96) !important;
            transform: translateY(-3px) scale(1.03) !important;
            box-shadow: 0 18px 35px -12px rgba(0, 0, 0, 0.35) !important;
        }

        /* Secondary (matches earlier hero secondary: glass background) */
        .hero-streamlit-actions .stButton > button[kind="secondary"],
        .hero-streamlit-actions .stButton > button[data-testid="baseButton-secondary"],
        .hero-streamlit-actions .stButton button[kind="secondary"],
        .hero-streamlit-actions .stButton button[data-testid="baseButton-secondary"] {
            background: rgba(255, 255, 255, 0.1) !important;
            color: #ffffff !important;
            border: 2px solid rgba(255, 255, 255, 0.3) !important;
            backdrop-filter: blur(8px) !important;
            -webkit-backdrop-filter: blur(8px) !important;
            box-shadow: 0 10px 25px -10px rgba(0, 0, 0, 0.25) !important;
        }

        .hero-streamlit-actions .stButton > button[kind="secondary"]:hover,
        .hero-streamlit-actions .stButton > button[data-testid="baseButton-secondary"]:hover,
        .hero-streamlit-actions .stButton button[kind="secondary"]:hover,
        .hero-streamlit-actions .stButton button[data-testid="baseButton-secondary"]:hover {
            background: rgba(255, 255, 255, 0.2) !important;
            border-color: rgba(255, 255, 255, 0.5) !important;
            transform: translateY(-3px) scale(1.02) !important;
            box-shadow: 0 18px 35px -14px rgba(0, 0, 0, 0.32) !important;
        }

        .features {
            display: flex;
            flex-wrap: wrap;
            justify-content: center;
            gap: 2rem;
            color: rgba(255, 255, 255, 0.85);
            font-size: 1rem;
            animation: fadeInUp 0.9s ease-out both;
            animation-delay: 0.5s;
        }

        .feature-item {
            display: inline-flex;
            align-items: center;
            gap: 0.75rem;
            background: rgba(255, 255, 255, 0.08);
            padding: 0.75rem 1.5rem;
            border-radius: 9999px;
            backdrop-filter: blur(4px);
            -webkit-backdrop-filter: blur(4px);
        }

        .feature-item svg {
            width: 24px;
            height: 24px;
            color: #86efac;
            flex: 0 0 auto;
        }

        @media (min-width: 768px) {
            .hero-headline {
                font-size: 5rem;
            }
        }

        @media (max-width: 768px) {
            .hero-container {
                padding: 4rem 1.25rem;
            }
        }
        
        /* Stats Section */
        div[data-testid="column"] {
            padding: 0 0.75rem;
        }

        .stats-grid {
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 1.5rem;
            margin: 2.25rem 0 3rem 0;
        }

        @media (min-width: 768px) {
            .stats-grid {
                grid-template-columns: repeat(4, minmax(0, 1fr));
            }
        }
        
        .stat-card {
            background: rgba(255, 255, 255, 0.96);
            border-radius: 20px;
            padding: 2rem 1.5rem;
            text-align: center;
            transition: transform 0.25s ease, box-shadow 0.25s ease;
            border: 1px solid rgba(99, 102, 241, 0.15);
            position: relative;
            overflow: hidden;
            box-shadow: 0 10px 25px -12px rgba(15, 23, 42, 0.35);
        }
        
        .stat-card:hover {
            transform: translateY(-6px);
            box-shadow: 0 18px 40px -18px rgba(15, 23, 42, 0.45);
        }
        
        .stat-number {
            font-size: 2.25rem;
            font-weight: 900;
            background: linear-gradient(to right, #2563eb, #7c3aed);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin-bottom: 0.5rem;
            letter-spacing: -0.02em;
        }

        @media (min-width: 768px) {
            .stat-number {
                font-size: 3rem;
            }
        }
        
        .stat-label {
            font-size: 0.875rem;
            color: #4b5563;
            font-weight: 600;
        }
        
        /* Section Headers */
        .section-header {
            text-align: center;
            margin: 5rem 0 4rem 0;
        }
        
        .section-badge {
            display: inline-block;
            padding: 0.6rem 1.75rem;
            background: linear-gradient(135deg, #6366f1, #8b5cf6);
            color: white;
            border-radius: 50px;
            font-size: 0.85rem;
            font-weight: 700;
            margin-bottom: 1.5rem;
            text-transform: uppercase;
            letter-spacing: 1.5px;
            box-shadow: 0 4px 15px rgba(99, 102, 241, 0.3);
        }
        
        .section-title {
            font-size: 3rem;
            font-weight: 900;
            color: #f8fafc;
            margin-bottom: 1.5rem;
            line-height: 1.2;
            letter-spacing: -0.02em;
        }
        
        .section-subtitle {
            font-size: 1.2rem;
            color: #94a3b8;
            max-width: 800px;
            margin: 0 auto;
            line-height: 1.7;
            font-weight: 400;
        }
        
        /* Features Section - modern cards */
        .features-section {
            padding: 5rem 1.5rem;
            background: #ffffff;
            border-radius: 24px;
            margin: 4rem 0;
        }

        .features-inner {
            max-width: 1280px;
            margin: 0 auto;
        }

        .features-heading {
            text-align: center;
            margin-bottom: 3rem;
        }

        .pill-badge {
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            padding: 0.5rem 1rem;
            border-radius: 9999px;
            background: #eff6ff;
            color: #2563eb;
            font-size: 0.875rem;
            font-weight: 600;
            margin-bottom: 1rem;
        }

        .pill-badge-icon {
            width: 1rem;
            height: 1rem;
            display: inline-flex;
            align-items: center;
            justify-content: center;
        }

        .features-heading-title {
            font-size: 2.25rem;
            line-height: 1.1;
            font-weight: 800;
            color: #111827;
            margin-bottom: 1rem;
        }

        @media (min-width: 768px) {
            .features-heading-title {
                font-size: 3rem;
            }
        }

        .features-heading-title .gradient-title {
            background: linear-gradient(to right, #2563eb, #7c3aed);
            -webkit-background-clip: text;
            background-clip: text;
            -webkit-text-fill-color: transparent;
            color: transparent;
        }

        .features-heading-subtitle {
            font-size: 1.125rem;
            color: #4b5563;
            max-width: 40rem;
            margin: 0.5rem auto 0 auto;
        }

        .feature-grid {
            display: grid;
            grid-template-columns: minmax(0, 1fr);
            gap: 2rem;
        }

        @media (min-width: 768px) {
            .feature-grid {
                grid-template-columns: repeat(3, minmax(0, 1fr));
            }
        }

        .feature-card {
            padding: 1.5rem;
            border-radius: 1rem;
            border: 2px solid #e5e7eb;
            background: #ffffff;
            transition: all 0.3s ease;
            box-shadow: 0 0 0 rgba(15, 23, 42, 0);
        }

        .feature-card:hover {
            border-color: transparent;
            box-shadow: 0 25px 50px -12px rgba(15, 23, 42, 0.25);
            transform: scale(1.05);
        }

        .feature-icon-wrapper {
            width: 3.5rem;
            height: 3.5rem;
            border-radius: 0.9rem;
            display: flex;
            align-items: center;
            justify-content: center;
            margin-bottom: 1rem;
            transition: transform 0.3s ease;
        }

        .feature-card:hover .feature-icon-wrapper {
            transform: scale(1.1);
        }

        .feature-icon-wrapper svg {
            width: 1.75rem;
            height: 1.75rem;
            color: #ffffff;
        }

        .gradient-blue-cyan {
            background: linear-gradient(135deg, #3b82f6, #06b6d4);
        }

        .gradient-purple-pink {
            background: linear-gradient(135deg, #8b5cf6, #ec4899);
        }

        .gradient-green-emerald {
            background: linear-gradient(135deg, #22c55e, #10b981);
        }

        .gradient-orange-red {
            background: linear-gradient(135deg, #f97316, #ef4444);
        }

        .gradient-yellow-orange {
            background: linear-gradient(135deg, #facc15, #fb923c);
        }

        .gradient-indigo-purple {
            background: linear-gradient(135deg, #4f46e5, #7c3aed);
        }

        .feature-title {
            font-size: 1.25rem;
            font-weight: 700;
            color: #111827;
            margin-bottom: 0.5rem;
        }

        .feature-description {
            font-size: 0.975rem;
            color: #4b5563;
            line-height: 1.6;
        }
        
        /* Process Cards */
        .process-card {
            background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
            border-radius: 20px;
            padding: 3rem 2rem;
            text-align: center;
            transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
            position: relative;
            border: 2px solid transparent;
            height: 100%;
        }
        
        .process-card:hover {
            border-color: #6366f1;
            transform: translateY(-8px);
            box-shadow: 0 20px 40px -10px rgba(99, 102, 241, 0.3);
        }
        
        .process-number {
            width: 70px;
            height: 70px;
            background: linear-gradient(135deg, #6366f1, #8b5cf6);
            color: white;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 2rem;
            font-weight: 900;
            margin: 0 auto 2rem auto;
            box-shadow: 0 8px 25px rgba(99, 102, 241, 0.4);
        }
        
        .process-title {
            font-size: 1.5rem;
            font-weight: 700;
            color: #f8fafc;
            margin-bottom: 1.25rem;
            letter-spacing: -0.01em;
        }
        
        .process-description {
            font-size: 1.05rem;
            color: #94a3b8;
            line-height: 1.7;
        }
        
        /* Persona Cards */
        .persona-card {
            background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
            border-radius: 20px;
            padding: 2.5rem;
            margin-bottom: 1.5rem;
            transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
            border-left: 5px solid #6366f1;
            position: relative;
            overflow: hidden;
        }
        
        .persona-card::after {
            content: '';
            position: absolute;
            top: 0;
            right: 0;
            width: 200px;
            height: 200px;
            background: radial-gradient(circle, rgba(99, 102, 241, 0.1) 0%, transparent 70%);
            pointer-events: none;
        }
        
        .persona-card:hover {
            transform: translateX(8px);
            box-shadow: -8px 0 30px rgba(99, 102, 241, 0.2);
            border-left-color: #8b5cf6;
        }
        
        .persona-header {
            display: flex;
            align-items: center;
            gap: 1.5rem;
            margin-bottom: 1.5rem;
            position: relative;
            z-index: 1;
        }
        
        .persona-icon {
            font-size: 3.5rem;
            filter: drop-shadow(0 4px 8px rgba(0, 0, 0, 0.3));
        }
        
        .persona-title {
            font-size: 1.75rem;
            font-weight: 800;
            color: #f8fafc;
            margin: 0;
            letter-spacing: -0.01em;
        }
        
        .persona-description {
            font-size: 1.05rem;
            color: #94a3b8;
            margin-bottom: 2rem;
            line-height: 1.7;
            position: relative;
            z-index: 1;
        }
        
        .persona-features {
            list-style: none;
            padding: 0;
            margin: 0;
            position: relative;
            z-index: 1;
        }
        
        .persona-features li {
            padding: 1rem 0;
            color: #cbd5e1;
            font-size: 1rem;
            border-bottom: 1px solid rgba(99, 102, 241, 0.1);
            transition: all 0.3s;
        }
        
        .persona-features li:hover {
            color: #f8fafc;
            padding-left: 0.5rem;
        }
        
        .persona-features li:last-child {
            border-bottom: none;
        }
        
        /* AI Model Cards */
        .ai-model-card {
            background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
            border-radius: 20px;
            padding: 3rem 2rem;
            text-align: center;
            transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
            border: 1px solid rgba(99, 102, 241, 0.15);
            position: relative;
            overflow: hidden;
        }
        
        .ai-model-card::before {
            content: '';
            position: absolute;
            top: 50%;
            left: 50%;
            width: 200%;
            height: 200%;
            background: radial-gradient(circle, rgba(99, 102, 241, 0.1) 0%, transparent 70%);
            transform: translate(-50%, -50%);
            opacity: 0;
            transition: opacity 0.4s;
        }
        
        .ai-model-card:hover::before {
            opacity: 1;
        }
        
        .ai-model-card:hover {
            transform: translateY(-10px) scale(1.02);
            box-shadow: 0 25px 50px -12px rgba(99, 102, 241, 0.3);
            border-color: rgba(99, 102, 241, 0.4);
        }
        
        .ai-icon {
            font-size: 4rem;
            margin-bottom: 1.5rem;
            filter: drop-shadow(0 4px 12px rgba(99, 102, 241, 0.5));
            position: relative;
            z-index: 1;
        }
        
        .ai-title {
            font-size: 1.5rem;
            font-weight: 700;
            color: #f8fafc;
            margin-bottom: 1rem;
            position: relative;
            z-index: 1;
        }
        
        .ai-description {
            font-size: 1.05rem;
            color: #94a3b8;
            line-height: 1.6;
            position: relative;
            z-index: 1;
        }
        
        /* CTA Section */
        .cta-section {
            background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #d946ef 100%);
            border-radius: 24px;
            padding: 5rem 3rem;
            text-align: center;
            margin: 5rem 0;
            box-shadow: 0 25px 50px -12px rgba(139, 92, 246, 0.4);
            position: relative;
            overflow: hidden;
        }
        
        .cta-section::before {
            content: '';
            position: absolute;
            top: -50%;
            left: -50%;
            width: 200%;
            height: 200%;
            background: radial-gradient(circle, rgba(255, 255, 255, 0.1) 0%, transparent 70%);
            animation: rotate 20s linear infinite;
        }
        
        @keyframes rotate {
            from { transform: rotate(0deg); }
            to { transform: rotate(360deg); }
        }
        
        .cta-title {
            font-size: 3rem;
            font-weight: 900;
            color: white;
            margin-bottom: 1.5rem;
            position: relative;
            z-index: 1;
            letter-spacing: -0.02em;
        }
        
        .cta-subtitle {
            font-size: 1.3rem;
            color: rgba(255, 255, 255, 0.95);
            margin-bottom: 3rem;
            max-width: 700px;
            margin-left: auto;
            margin-right: auto;
            position: relative;
            z-index: 1;
            line-height: 1.6;
        }
        
        .cta-button {
            background: white;
            color: #6366f1;
            padding: 1.3rem 3.5rem;
            font-size: 1.2rem;
            font-weight: 700;
            border: none;
            border-radius: 12px;
            cursor: pointer;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
            position: relative;
            z-index: 1;
        }
        
        .cta-button:hover {
            transform: translateY(-3px);
            box-shadow: 0 15px 40px rgba(0, 0, 0, 0.4);
        }
        
        .cta-note {
            margin-top: 2rem;
            color: rgba(255, 255, 255, 0.85);
            font-size: 1rem;
            position: relative;
            z-index: 1;
        }
        
        /* Footer */
        .footer {
            background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
            border-radius: 24px;
            padding: 4rem 3rem 2rem 3rem;
            margin-top: 5rem;
            color: #e2e8f0;
            border: 1px solid rgba(99, 102, 241, 0.1);
        }
        
        .footer-content {
            display: grid;
            grid-template-columns: 2fr 1fr 1fr 1fr;
            gap: 3rem;
            margin-bottom: 3rem;
        }
        
        .footer-brand h3 {
            font-size: 1.75rem;
            margin-bottom: 1rem;
            font-weight: 800;
            background: linear-gradient(135deg, #6366f1, #8b5cf6, #d946ef);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        
        .footer-brand p {
            color: #94a3b8;
            line-height: 1.7;
            font-size: 1.05rem;
        }
        
        .footer-column h4 {
            font-size: 1.15rem;
            margin-bottom: 1.5rem;
            color: #f8fafc;
            font-weight: 700;
        }
        
        .footer-column ul {
            list-style: none;
            padding: 0;
        }
        
        .footer-column li {
            margin-bottom: 1rem;
            color: #94a3b8;
            cursor: pointer;
            transition: all 0.3s;
            font-size: 1rem;
        }
        
        .footer-column li:hover {
            color: #f8fafc;
            padding-left: 0.5rem;
        }
        
        .footer-bottom {
            border-top: 1px solid rgba(99, 102, 241, 0.2);
            padding-top: 2rem;
            text-align: center;
            color: #64748b;
            font-size: 0.95rem;
        }
        
        .footer-stats {
            margin-top: 1rem;
            color: #94a3b8;
            font-size: 1rem;
        }
        
        /* Responsive Design */
        @media (max-width: 1024px) {
            .block-container {
                padding: 2rem !important;
            }
            
            .hero-title {
                font-size: 3rem;
            }
            
            .section-title {
                font-size: 2.5rem;
            }
            
            .footer-content {
                grid-template-columns: 1fr 1fr;
                gap: 2rem;
            }
        }
        
        @media (max-width: 768px) {
            .hero-title {
                font-size: 2.25rem;
            }
            
            .hero-subtitle {
                font-size: 1.1rem;
            }
            
            .section-title {
                font-size: 2rem;
            }
            
            .stat-number {
                font-size: 2.5rem;
            }
            
            .footer-content {
                grid-template-columns: 1fr;
            }
            
            .cta-title {
                font-size: 2rem;
            }
        }
        
        /* Smooth Animations */
        @keyframes fadeInUp {
            from {
                opacity: 0;
                transform: translateY(30px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        .fade-in {
            animation: fadeInUp 0.6s ease-out;
        }
    </style>
    """, unsafe_allow_html=True)

    