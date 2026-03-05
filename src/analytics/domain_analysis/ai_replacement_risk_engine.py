import re
import logging
from typing import Dict, Tuple
import pandas as pd
import numpy as np 

class AIReplacementRiskEngine:
    
    MIN_SAMPLES = 5
    
    # ── Task-Nature Keyword Banks ─────────────────────────────────────
    # Expanded from 7 → 40+ keywords per dimension
    
    ROUTINE_KEYWORDS = [
        # Data handling
        'data entry', 'manual entry', 'copy paste', 'data cleaning',
        'daily report', 'weekly report', 'monthly report',
        # Process execution
        'repetitive', 'maintenance', 'standard procedure', 'template',
        'batch processing', 'rule based', 'checklist', 'monitoring',
        # Volume tasks
        'high volume', 'bulk', 'pipeline execution', 'scheduled',
        'automated workflow', 'logging', 'tracking', 'updating records'
    ]
    
    CODIFIED_KEYWORDS = [
        # Procedure-following
        'standard operating procedure', 'sop', 'fixed protocol',
        'compliance', 'regulatory', 'audit', 'policy enforcement',
        # Script/rule-based
        'script', 'template', 'predefined', 'rule engine',
        'decision tree', 'flowchart', 'playbook',
        # Structured outputs
        'fill in', 'complete form', 'submit report', 'generate invoice',
        'ticket resolution', 'level 1 support', 'faq'
    ]
    
    CREATIVE_KEYWORDS = [
        # Strategic thinking
        'strategic', 'strategy', 'vision', 'roadmap', 'innovation',
        'novel approach', 'original', 'creative solution',
        # Judgment & ambiguity
        'ambiguous', 'complex problem', 'trade-off', 'judgment',
        'critical thinking', 'ethical', 'nuanced',
        # Human connection
        'empathy', 'negotiation', 'stakeholder', 'client relationship',
        'mentoring', 'coaching', 'cultural', 'emotional intelligence',
        # Research
        'research', 'hypothesis', 'experiment', 'discover',
        'architect', 'design from scratch', 'exploratory'
    ]
    
    HUMAN_FACTOR_KEYWORDS = [
        # Physical presence
        'onsite', 'on-site', 'physical', 'hardware', 'lab',
        'field work', 'site visit', 'in person',
        # Leadership & social
        'leadership', 'team lead', 'manage team', 'mentor',
        'client facing', 'customer success', 'presentation',
        # High-stakes judgment
        'crisis', 'incident response', 'escalation', 'board',
        'c-suite', 'executive', 'legal', 'medical', 'compliance officer'
    ]
    
    # ── Skill-Level AI Risk Scores ────────────────────────────────────
    SKILL_AI_RISK = {
        # Very high risk (>0.75)
        'data entry':        0.92, 'excel reporting':   0.85,
        'copy editing':      0.80, 'manual testing':    0.78,
        'basic sql':         0.70, 'report generation': 0.75,
        # High risk (0.50-0.75)
        'html css':          0.55, 'wordpress':         0.65,
        'tableau':           0.50, 'power bi':          0.48,
        'qa testing':        0.60, 'selenium':          0.55,
        # Medium risk (0.25-0.50)
        'python':            0.30, 'java':              0.35,
        'javascript':        0.32, 'sql':               0.40,
        'react':             0.30, 'node.js':           0.28,
        'devops':            0.25, 'docker':            0.22,
        # Low risk (0.10-0.25)
        'machine learning':  0.15, 'deep learning':     0.12,
        'system design':     0.10, 'cloud architecture':0.10,
        'data science':      0.15, 'nlp':               0.12,
        'computer vision':   0.10, 'reinforcement learning':0.08,
        # Very low risk (<0.10)
        'ai research':       0.05, 'llm fine-tuning':   0.06,
        'ethics ai':         0.04, 'product strategy':  0.07,
        'cybersecurity':     0.08, 'penetration testing':0.07,
    }
    
    def __init__(self, weights: Dict = None):
        default_weights = {
            "routine_exposure":    0.30,  # Reduced from 0.7 — less dominant
            "codified_knowledge":  0.20,
            "creativity_gap":      0.20,  # Increased — creativity is the key differentiator
            "skill_automation":    0.20,  # NEW: skill-level risk
            "human_factor":        0.10,  # Protective factor
        }
        self.weights = weights or default_weights
        self._validate_weights()
        self.logger = logging.getLogger(__name__)
    
    def _validate_weights(self):
        total = sum(self.weights.values())
        if not (0.98 <= total <= 1.02):
            raise ValueError(f"Weights must sum to 1.0, got {total:.3f}")

    def _filter_domain(self, df: pd.DataFrame,
                        target_domain: str,
                        experience_band: Tuple = None) -> pd.DataFrame:
        """Job_Type first, Title fallback. Never mutates input."""
        df = df.copy()

        if 'TItle_Cleaned' in df.columns and 'Title_Cleaned' not in df.columns:
            df = df.rename(columns={'TItle_Cleaned': 'Title_Cleaned'})

        # Priority 1: Job_Type exact
        if 'Job_Type' in df.columns:
            exact = df[df['Job_Type'].str.lower() == target_domain.lower()]
            if len(exact) >= self.MIN_SAMPLES:
                domain_df = exact
            else:
                domain_df = pd.DataFrame()
        else:
            domain_df = pd.DataFrame()

        # Priority 2: Title word-boundary
        if domain_df.empty:
            title_col = 'Title_Cleaned' if 'Title_Cleaned' in df.columns else None
            if title_col:
                pattern = r'\b' + re.escape(target_domain) + r'\b'
                domain_df = df[df[title_col].str.contains(
                    pattern, case=False, na=False, regex=True
                )]

        if domain_df.empty:
            return pd.DataFrame()

        # Optional experience filter
        if experience_band and 'Min_Experience' in domain_df.columns:
            min_e, max_e = experience_band
            domain_df = domain_df[
                (domain_df['Min_Experience'] >= min_e) &
                (domain_df['Min_Experience'] <= max_e)
            ]

        return domain_df.copy()

    def _safe_keyword_score(self, series: pd.Series, 
                              keywords: list) -> Tuple[float, int]:
        """
        Safe keyword matching with:
        1. NaN handling (don't silently skip — track coverage)
        2. Word-boundary matching (avoid 'art' matching 'artificial')
        3. Returns (score, n_valid) for confidence weighting
        """
        if series.empty:
            return 0.5, 0  # Neutral when no data

        valid = series.dropna()
        n_valid = len(valid)

        if n_valid == 0:
            return 0.5, 0

        # Build combined pattern with word boundaries
        pattern = r'\b(?:' + '|'.join(
            re.escape(kw) for kw in keywords
        ) + r')\b'

        # Count matching rows (not just presence — frequency matters)
        matches = valid.str.contains(pattern, case=False, na=False)

        return float(matches.mean()), n_valid

    def _analyze_task_nature(self, domain_df):
        """
        Scans JDs for keywords that signal the nature of work.
        """
        if domain_df.empty:
            return 0.5, 0.5, 0.5 # Default middle ground
        
        # 1. Routine Detection (Keywords signaling repetitive, manual, or high-volume data tasks)
        routine_kw = 'manual|repetitive|entry|maintenance|standard|daily reports|cleaning'
        routine_score = domain_df['Description_Cleaned'].str.contains(routine_kw, case=False).mean()
        
        # 2. Codified Knowledge (Tasks that follow fixed protocols or scripts)
        codified_kw = 'standard operating procedure|compliance|fixed protocols|template|scripts'
        codified_score = domain_df['Description_Cleaned'].str.contains(codified_kw, case=False).mean()
        
        # 3. Creative/High Judgment (Reverse keyword search)
        creative_kw = 'strategic|original|innovation|ambiguous|complex problem|empathy|negotiation'
        creative_presence = domain_df['Description_Cleaned'].str.contains(creative_kw, case=False).mean()
        low_creativity_score = 1 - creative_presence
        
        return routine_score, codified_score, low_creativity_score
    
    def _analyze_skill_risk(self, domain_df: pd.DataFrame) -> dict:
        """
        Skill-based AI risk: more reliable than description keywords.
        Skills are structured data — less noisy than free-text descriptions.

        Priority: Star_Skills (must-have) > Combined_Skills > Normal_Skills
        """
        skill_col = None
        for col in ['Star_Skills', 'Combined_Skills', 'Normal_Skills']:
            if col in domain_df.columns:
                skill_col = col
                break
            
        if skill_col is None:
            return {"score": 0.4, "top_risky_skills": [], 
                    "top_safe_skills": [], "source": "unavailable"}

        # Aggregate all skills from postings
        all_skills_text = ' '.join(
            domain_df[skill_col].dropna().str.lower().tolist()
        )

        if not all_skills_text.strip():
            return {"score": 0.4, "top_risky_skills": [], 
                    "top_safe_skills": [], "source": skill_col}

        # Score each known skill
        skill_scores = {}
        for skill, risk in self.SKILL_AI_RISK.items():
            pattern = r'\b' + re.escape(skill) + r'\b'
            count = len(re.findall(pattern, all_skills_text, re.IGNORECASE))
            if count > 0:
                skill_scores[skill] = {"risk": risk, "frequency": count}

        if not skill_scores:
            # No known skills found — use Skill_Count as structural proxy
            if 'Skill_Count' in domain_df.columns:
                median_skills = pd.to_numeric(
                    domain_df['Skill_Count'], errors='coerce'
                ).median()
                # More skills = lower automation risk (requires breadth)
                proxy_risk = max(0.05, 0.70 - (median_skills * 0.04)) if not pd.isna(median_skills) else 0.40
                return {
                    "score":           round(1 - proxy_risk, 3),
                    "top_risky_skills": [],
                    "top_safe_skills":  [],
                    "source":           f"{skill_col}_count_proxy"
                }
            return {"score": 0.5, "top_risky_skills": [], 
                    "top_safe_skills": [], "source": "no_match"}

        # Frequency-weighted average risk
        total_freq  = sum(v["frequency"] for v in skill_scores.values())
        weighted_risk = sum(
            v["risk"] * v["frequency"] for v in skill_scores.values()
        ) / total_freq

        # Sort by risk level
        sorted_skills = sorted(
            skill_scores.items(), key=lambda x: x[1]["risk"], reverse=True
        )
        top_risky = [s[0] for s in sorted_skills if s[1]["risk"] >= 0.50][:5]
        top_safe  = [s[0] for s in sorted_skills if s[1]["risk"] <= 0.20][:5]

        return {
            "score":            round(1 - weighted_risk, 3),  # Higher = more AI-resistant
            "weighted_risk_pct": round(weighted_risk * 100, 1),
            "top_risky_skills": top_risky,
            "top_safe_skills":  top_safe,
            "skills_analyzed":  len(skill_scores),
            "source":           skill_col
        }

    def _analyze_risk_trend(self, domain_df: pd.DataFrame) -> dict:
        """
        Is AI risk increasing over time in this domain?
        Signal: Are routine/codified keywords appearing MORE in recent postings?
        Opposite: Are creative/strategic keywords appearing MORE? (domain evolving safely)
        """
        date_col = 'Posted_Date' if 'Posted_Date' in domain_df.columns else 'Scraped_At_Cleaned'

        if date_col not in domain_df.columns or 'Description_Cleaned' not in domain_df.columns:
            return {"trend": "Unknown", "direction_score": 0.0}

        df = domain_df.copy()
        df['_date'] = pd.to_datetime(df[date_col], errors='coerce')
        df = df.sort_values('_date').dropna(subset=['_date', 'Description_Cleaned'])

        if len(df) < 20:
            return {"trend": "Insufficient data", "direction_score": 0.0}

        # Split into old half vs new half
        mid = len(df) // 2
        old_df, new_df = df.iloc[:mid], df.iloc[mid:]

        # Routine exposure: old vs new
        old_routine, _ = self._safe_keyword_score(old_df['Description_Cleaned'], self.ROUTINE_KEYWORDS)
        new_routine, _ = self._safe_keyword_score(new_df['Description_Cleaned'], self.ROUTINE_KEYWORDS)

        # Creative exposure: old vs new
        old_creative, _ = self._safe_keyword_score(old_df['Description_Cleaned'], self.CREATIVE_KEYWORDS)
        new_creative, _ = self._safe_keyword_score(new_df['Description_Cleaned'], self.CREATIVE_KEYWORDS)

        routine_delta  = new_routine  - old_routine    # Positive = more routine over time = BAD
        creative_delta = new_creative - old_creative   # Positive = more creative over time = GOOD

        direction_score = creative_delta - routine_delta  # Combined signal

        if direction_score > 0.05:
            trend = "Evolving Safely — Role becoming more strategic over time"
        elif direction_score < -0.05:
            trend = "Increasing Automation Risk — Role becoming more routine over time"
        else:
            trend = "Stable — No significant shift in task nature"

        return {
            "trend":            trend,
            "direction_score":  round(direction_score, 3),
            "routine_delta":    round(routine_delta, 3),
            "creative_delta":   round(creative_delta, 3)
        }

    def _compute_human_factor_protection(self, human_score: float) -> float:
        """
        Previous: risk * (1 - human_factor * 0.3)
        Problem: multiplicative reduces high-risk roles more than low-risk ones
                 in absolute terms — backwards logic.

        Fix: Additive reduction capped at 0.15 (max 15% protection boost).
        Human presence reduces risk score, not multiplies it.
        """
        # Max 15% reduction for strong human factor presence
        # human_score ∈ [0, 1] → protection ∈ [0, 0.15]
        return float(np.clip(human_score * 0.15, 0.0, 0.15))

    def calculate_ai_risk(self, df, target_domain):
        # 1. Filter Domain
        domain_df = self._filter_domain(df, target_domain)
        
        # 2. Assess Task Automation Probability
        routine_p, codified_p, low_creative_p = self._analyze_task_nature(domain_df)
        
        # 3. Math Logic: Risk Score Calculation
        # Risk_Score = (Routine_tasks% * routine_weight) + (Codified_knowledge% * codified_weight) + (Low_creativity% * creativity_weight)
        risk_score = (routine_p * self.weights.get('routine_exposure', 0.30)) + \
                     (codified_p * self.weights.get('codified_knowledge', 0.20)) + \
                     (low_creative_p * self.weights.get('creativity_gap', 0.20))
        
        # 4. Human Factor Adjustment (Physical presence / High Judgment)
        # If the JD mentions 'onsite', 'physical', 'hardware', or 'team leadership', we reduce risk.
        human_factor_kw = 'physical|hardware|onsite|leadership|mentoring|client facing'
        human_factor_presence = domain_df['Description_Cleaned'].str.contains(human_factor_kw, case=False).mean()
        
        final_risk = risk_score * (1 - (human_factor_presence * 0.3)) # Physical/Human roles get a 30% safety boost

        # 5. Risk Categorization
        if final_risk < 0.3:
            category = "AI-Resilient (Human-Centric)"
        elif 0.3 <= final_risk <= 0.6:
            category = "AI-Augmented (Requires AI Synergy)"
        else:
            category = "High Exposure (Vulnerable to Automation)"

        return {
            "Domain": target_domain,
            "AI_Risk_Score": round(final_risk, 2),
            "Risk_Category": category,
            "Vulnerability_Breakdown": {
                "Routine_Exposure": f"{round(routine_p * 100)}%",
                "Rule_Based_Exposure": f"{round(codified_p * 100)}%",
                "Creativity_Gap": f"{round(low_creative_p * 100)}%"
            },
            "Actionable_Advice": "Focus on high-judgment and strategic tasks." if final_risk > 0.5 else "Stay updated with AI tools to enhance productivity."
        }
    
    def _classify_risk(self, risk: float) -> Tuple[str, str]:
        """5-tier classification replacing 3-tier."""
        if risk < 0.20:
            return ("🟢 AI-Resilient", "Strong creative/strategic core — minimal automation threat")
        elif risk < 0.35:
            return ("🟡 Low Risk — AI-Augmented", "Some automatable tasks — master AI tools to amplify output")
        elif risk < 0.50:
            return ("🟠 Moderate Risk", "Significant routine exposure — upskill toward judgment-heavy tasks")
        elif risk < 0.70:
            return ("🔴 High Risk", "Core tasks increasingly automatable — urgent reskilling advised")
        else:
            return ("🚨 Critical Risk", "Role likely disrupted within 3-5 years — serious career pivot needed")

    def _generate_advice(self, task: dict, skill: dict, 
                          final_risk: float) -> list:
        """
        Granular, factor-specific advice replacing single generic message.
        Identifies the DOMINANT risk driver and targets advice there.
        """
        advice = []

        # Identify dominant risk factor
        if task["routine"] > 0.4:
            advice.append(
                f"🔄 High routine exposure ({task['routine']*100:.0f}% of JDs) — "
                f"automate these tasks yourself before AI does. "
                f"Learn scripting, workflow automation, and LLM-assisted pipelines."
            )

        if task["codified"] > 0.3:
            advice.append(
                f"📋 Rule-based tasks dominate ({task['codified']*100:.0f}% of JDs) — "
                f"move toward policy design and exception handling rather than policy execution."
            )

        if task["creativity_gap"] > 0.6:
            advice.append(
                f"💡 Low creative signal in JDs — deliberately pursue projects requiring "
                f"original problem-solving, stakeholder alignment, and ambiguous problem spaces."
            )

        if skill["top_risky_skills"]:
            risky = ', '.join(skill["top_risky_skills"][:3])
            advice.append(
                f"⚠️  High-automation skills dominating your domain: {risky}. "
                f"Pair these with system design, architecture, or AI orchestration skills."
            )

        if skill["top_safe_skills"]:
            safe = ', '.join(skill["top_safe_skills"][:3])
            advice.append(f"✅ AI-resistant skills in demand: {safe}. Deepen these.")

        if task["human_factor"] > 0.3:
            advice.append(
                "🤝 Strong human-factor signal — leadership, client, and mentoring "
                "responsibilities provide natural protection from automation."
            )

        if final_risk > 0.5:
            advice.append(
                "🎯 Priority action: Shift from execution to orchestration. "
                "Learn to use AI tools as force multipliers — become the person "
                "who directs AI, not the one who does what AI can do."
            )
        elif final_risk < 0.25:
            advice.append(
                "🚀 Strong position — stay current with AI tooling in your domain "
                "to amplify productivity. Your core role is safe but AI fluency "
                "will separate top performers."
            )

        return advice if advice else [
            "📊 Insufficient description data for specific advice. "
            "Ensure job descriptions are populated in your dataset."
        ]
    

# Example usage
if __name__ == "__main__":
    
    # Load sample data
    data_path = r"D:\DATA SCIENCE AND ML\Project\job_trend_predictor\data\processed\cleaned\cleaned_job_data.csv"
    
    df = pd.read_csv(data_path)
    
    engine = AIReplacementRiskEngine()
    
    # Analyze specific domain
    target_domain = "Data Scientist"  # Change this to analyze different domains
    
    risk_result = engine.calculate_ai_risk(df, target_domain)
    print(risk_result)
        
      