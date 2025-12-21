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
        .hero-section {
            background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #d946ef 100%);
            padding: 5rem 3rem;
            border-radius: 24px;
            margin: 2rem 0 3rem 0;
            text-align: center;
            position: relative;
            overflow: hidden;
            box-shadow: 0 25px 50px -12px rgba(139, 92, 246, 0.25);
        }
        
        .hero-section::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: 
                radial-gradient(circle at 20% 50%, rgba(255, 255, 255, 0.1) 0%, transparent 50%),
                radial-gradient(circle at 80% 80%, rgba(255, 255, 255, 0.1) 0%, transparent 50%);
            pointer-events: none;
        }
        
        .hero-content {
            position: relative;
            z-index: 1;
        }
        
        .hero-title {
            font-size: 4rem;
            font-weight: 900;
            color: white;
            margin-bottom: 1.5rem;
            line-height: 1.1;
            letter-spacing: -0.02em;
        }
        
        .hero-subtitle {
            font-size: 1.25rem;
            color: rgba(255, 255, 255, 0.95);
            margin-bottom: 3rem;
            max-width: 900px;
            margin-left: auto;
            margin-right: auto;
            line-height: 1.7;
            font-weight: 400;
        }
        
        .hero-buttons {
            display: flex;
            gap: 1.25rem;
            justify-content: center;
            flex-wrap: wrap;
            margin-top: 2rem;
        }
        
        .btn-primary, .btn-secondary {
            padding: 1rem 2.5rem;
            font-size: 1.1rem;
            font-weight: 600;
            border: none;
            border-radius: 12px;
            cursor: pointer;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
        }
        
        .btn-primary {
            background: white;
            color: #6366f1;
            box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.3);
        }
        
        .btn-primary:hover {
            transform: translateY(-2px);
            box-shadow: 0 15px 35px -5px rgba(0, 0, 0, 0.4);
        }
        
        .btn-secondary {
            background: rgba(255, 255, 255, 0.15);
            color: white;
            border: 2px solid rgba(255, 255, 255, 0.3);
            backdrop-filter: blur(10px);
        }
        
        .btn-secondary:hover {
            background: rgba(255, 255, 255, 0.25);
            border-color: rgba(255, 255, 255, 0.5);
        }
        
        /* Stats Section */
        div[data-testid="column"] {
            padding: 0 0.75rem;
        }
        
        .stat-card {
            background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
            border-radius: 20px;
            padding: 2.5rem 2rem;
            text-align: center;
            transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
            border: 1px solid rgba(99, 102, 241, 0.2);
            position: relative;
            overflow: hidden;
        }
        
        .stat-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
            background: linear-gradient(90deg, #6366f1, #8b5cf6, #d946ef);
        }
        
        .stat-card:hover {
            transform: translateY(-8px);
            border-color: rgba(99, 102, 241, 0.5);
            box-shadow: 0 20px 40px -10px rgba(99, 102, 241, 0.3);
        }
        
        .stat-number {
            font-size: 3.5rem;
            font-weight: 900;
            background: linear-gradient(135deg, #6366f1, #8b5cf6, #d946ef);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin-bottom: 0.75rem;
            letter-spacing: -0.02em;
        }
        
        .stat-label {
            font-size: 1.1rem;
            color: #94a3b8;
            font-weight: 500;
            margin-bottom: 0.75rem;
        }
        
        .stat-change {
            font-size: 0.95rem;
            font-weight: 600;
            padding: 0.4rem 1rem;
            border-radius: 50px;
            display: inline-block;
            margin-top: 0.5rem;
        }
        
        .stat-change.positive {
            color: #10b981;
            background: rgba(16, 185, 129, 0.15);
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
        
        /* Feature Cards */
        .feature-card {
            background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
            border-radius: 20px;
            padding: 2.5rem;
            margin-bottom: 1.5rem;
            transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
            border: 1px solid rgba(99, 102, 241, 0.15);
            height: 100%;
            position: relative;
            overflow: hidden;
        }
        
        .feature-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 3px;
            background: linear-gradient(90deg, transparent, #6366f1, transparent);
            opacity: 0;
            transition: opacity 0.4s;
        }
        
        .feature-card:hover::before {
            opacity: 1;
        }
        
        .feature-card:hover {
            transform: translateY(-10px);
            border-color: rgba(99, 102, 241, 0.4);
            box-shadow: 0 25px 50px -12px rgba(99, 102, 241, 0.25);
        }
        
        .feature-icon {
            width: 80px;
            height: 80px;
            border-radius: 18px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 2.5rem;
            margin-bottom: 2rem;
            box-shadow: 0 8px 20px rgba(0, 0, 0, 0.3);
            transition: transform 0.4s;
        }
        
        .feature-card:hover .feature-icon {
            transform: scale(1.1) rotate(5deg);
        }
        
        .feature-icon.purple { background: linear-gradient(135deg, #6366f1, #8b5cf6); }
        .feature-icon.blue { background: linear-gradient(135deg, #3b82f6, #06b6d4); }
        .feature-icon.pink { background: linear-gradient(135deg, #ec4899, #f43f5e); }
        .feature-icon.green { background: linear-gradient(135deg, #10b981, #059669); }
        .feature-icon.orange { background: linear-gradient(135deg, #f97316, #fb923c); }
        .feature-icon.teal { background: linear-gradient(135deg, #14b8a6, #06b6d4); }
        
        .feature-title {
            font-size: 1.5rem;
            font-weight: 700;
            color: #f8fafc;
            margin-bottom: 1.25rem;
            letter-spacing: -0.01em;
        }
        
        .feature-description {
            font-size: 1.05rem;
            color: #94a3b8;
            line-height: 1.7;
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
        /* Profile Page Styles */
.profile-header {
    text-align: center;
    padding: 2rem 0 3rem 0;
}

.profile-header h1 {
    font-size: 3rem;
    font-weight: 900;
    color: #f8fafc;
    margin-bottom: 1rem;
}

.profile-header p {
    font-size: 1.2rem;
    color: #94a3b8;
}

/* Make role selection buttons taller and more visual */
div[data-testid="column"] button {
    height: 120px !important;
    white-space: pre-line !important;
    line-height: 1.6 !important;
}
    </style>
    """, unsafe_allow_html=True)

    