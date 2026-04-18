import re
import ast
import logging
from typing import Dict, List, Tuple
import pandas as pd
import numpy as np


# ── Central Skills Parser ─────────────────────────────────────────────────────
def parse_skills_column(raw) -> List[str]:
    """
    Handles both storage formats for the 'skills' column:
      Format A (old list repr): "['python', 'machine learning', 'sql']"
      Format B (new plain str):  "python, machine learning, sql"
    Always returns a clean List[str] — never crashes.
    """
    if raw is None or (isinstance(raw, float) and pd.isna(raw)):
        return []

    raw = str(raw).strip()
    if not raw:
        return []

    # Format A: Python list literal
    if raw.startswith('['):
        try:
            parsed = ast.literal_eval(raw)
            if isinstance(parsed, list):
                return [
                    re.sub(r'\s+', ' ', str(s).strip().lower())
                    for s in parsed
                    if str(s).strip()
                ]
        except (ValueError, SyntaxError):
            pass  # Fall through to Format B

    # Format B: plain comma-separated (new schema)
    return [
        re.sub(r"['\"\\[\\]]", '', s).strip().lower()
        for s in raw.split(',')
        if re.sub(r"['\"\\[\\]]", '', s).strip()
    ]


def skills_to_text(series: pd.Series) -> str:
    """
    Convert an entire 'skills' Series to a single flat text string
    for keyword matching. Works for both old list-repr and new string format.
    """
    tokens = []
    for raw in series.dropna():
        tokens.extend(parse_skills_column(raw))
    return ' '.join(tokens)
# ─────────────────────────────────────────────────────────────────────────────


class AIReplacementRiskEngine:

    MIN_SAMPLES = 5

    ROUTINE_KEYWORDS = [
        'data entry', 'manual entry', 'copy paste', 'data cleaning',
        'daily report', 'weekly report', 'monthly report',
        'repetitive', 'maintenance', 'standard procedure', 'template',
        'batch processing', 'rule based', 'checklist', 'monitoring',
        'high volume', 'bulk', 'pipeline execution', 'scheduled',
        'automated workflow', 'logging', 'tracking', 'updating records'
    ]

    CODIFIED_KEYWORDS = [
        'standard operating procedure', 'sop', 'fixed protocol',
        'compliance', 'regulatory', 'audit', 'policy enforcement',
        'script', 'template', 'predefined', 'rule engine',
        'decision tree', 'flowchart', 'playbook',
        'fill in', 'complete form', 'submit report', 'generate invoice',
        'ticket resolution', 'level 1 support', 'faq'
    ]

    CREATIVE_KEYWORDS = [
        'strategic', 'strategy', 'vision', 'roadmap', 'innovation',
        'novel approach', 'original', 'creative solution',
        'ambiguous', 'complex problem', 'trade-off', 'judgment',
        'critical thinking', 'ethical', 'nuanced',
        'empathy', 'negotiation', 'stakeholder', 'client relationship',
        'mentoring', 'coaching', 'cultural', 'emotional intelligence',
        'research', 'hypothesis', 'experiment', 'discover',
        'architect', 'design from scratch', 'exploratory'
    ]

    HUMAN_FACTOR_KEYWORDS = [
        'onsite', 'on-site', 'physical', 'hardware', 'lab',
        'field work', 'site visit', 'in person',
        'leadership', 'team lead', 'manage team', 'mentor',
        'client facing', 'customer success', 'presentation',
        'crisis', 'incident response', 'escalation', 'board',
        'c-suite', 'executive', 'legal', 'medical', 'compliance officer'
    ]

    SKILL_AI_RISK = {
        'data entry':        0.92, 'excel reporting':   0.85,
        'copy editing':      0.80, 'manual testing':    0.78,
        'basic sql':         0.70, 'report generation': 0.75,
        'html css':          0.55, 'wordpress':         0.65,
        'tableau':           0.50, 'power bi':          0.48,
        'qa testing':        0.60, 'selenium':          0.55,
        'python':            0.30, 'java':              0.35,
        'javascript':        0.32, 'sql':               0.40,
        'react':             0.30, 'node.js':           0.28,
        'devops':            0.25, 'docker':            0.22,
        'machine learning':  0.15, 'deep learning':     0.12,
        'system design':     0.10, 'cloud architecture':0.10,
        'data science':      0.15, 'nlp':               0.12,
        'computer vision':   0.10, 'reinforcement learning': 0.08,
        'ai research':       0.05, 'llm fine-tuning':   0.06,
        'ethics ai':         0.04, 'product strategy':  0.07,
        'cybersecurity':     0.08, 'penetration testing': 0.07,
    }

    def __init__(self, weights: Dict = None):
        default_weights = {
            "routine_exposure":    0.30,
            "codified_knowledge":  0.20,
            "creativity_gap":      0.20,
            "skill_automation":    0.20,
            "human_factor":        0.10,
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
        df = df.copy()
        if 'title_cleaned' in df.columns and 'title' not in df.columns:
            df = df.rename(columns={'title_cleaned': 'title'})

        if 'title' in df.columns:
            exact = df[df['title'].str.lower() == target_domain.lower()]
            domain_df = exact if len(exact) >= self.MIN_SAMPLES else pd.DataFrame()
        else:
            domain_df = pd.DataFrame()

        if domain_df.empty:
            title_col = 'title' if 'title' in df.columns else None
            if title_col:
                pattern = r'\b' + re.escape(target_domain) + r'\b'
                domain_df = df[df[title_col].str.contains(
                    pattern, case=False, na=False, regex=True
                )]

        if domain_df.empty:
            return pd.DataFrame()

        if experience_band and 'min_experience' in domain_df.columns:
            min_e, max_e = experience_band
            domain_df = domain_df[
                (domain_df['min_experience'] >= min_e) &
                (domain_df['min_experience'] <= max_e)
            ]

        return domain_df.copy()

    def _safe_keyword_score(self, series: pd.Series,
                            keywords: list) -> Tuple[float, int]:
        if series.empty:
            return 0.5, 0
        valid = series.dropna()
        n_valid = len(valid)
        if n_valid == 0:
            return 0.5, 0
        pattern = r'\b(?:' + '|'.join(re.escape(kw) for kw in keywords) + r')\b'
        matches = valid.str.contains(pattern, case=False, na=False)
        return float(matches.mean()), n_valid

    def _analyze_task_nature(self, domain_df: pd.DataFrame):
        if domain_df.empty:
            return 0.5, 0.5, 0.5

        routine_kw = 'manual|repetitive|entry|maintenance|standard|daily reports|cleaning'
        routine_score = domain_df['description'].str.contains(routine_kw, case=False).mean()

        codified_kw = 'standard operating procedure|compliance|fixed protocols|template|scripts'
        codified_score = domain_df['description'].str.contains(codified_kw, case=False).mean()

        creative_kw = 'strategic|original|innovation|ambiguous|complex problem|empathy|negotiation'
        creative_presence = domain_df['description'].str.contains(creative_kw, case=False).mean()
        low_creativity_score = 1 - creative_presence

        return routine_score, codified_score, low_creativity_score

    def _analyze_skill_risk(self, domain_df: pd.DataFrame) -> dict:
        """
        Skill-based AI risk using the 'skills' column.
        Parses both old list-repr format and new plain-string format.
        Falls back to skill_count as structural proxy if no skill matches found.
        """
        # ── Use 'skills' column (new unified schema) ──────────────────
        if 'skills' not in domain_df.columns:
            return {"score": 0.4, "top_risky_skills": [],
                    "top_safe_skills": [], "source": "unavailable"}

        # Convert entire skills series → flat text for keyword matching
        all_skills_text = skills_to_text(domain_df['skills'])

        if not all_skills_text.strip():
            # Fallback: use skill_count as structural proxy
            if 'skill_count' in domain_df.columns:
                median_skills = pd.to_numeric(
                    domain_df['skill_count'], errors='coerce'
                ).median()
                proxy_risk = (
                    max(0.05, 0.70 - (median_skills * 0.04))
                    if not pd.isna(median_skills) else 0.40
                )
                return {
                    "score":            round(1 - proxy_risk, 3),
                    "top_risky_skills": [],
                    "top_safe_skills":  [],
                    "source":           "skill_count_proxy"
                }
            return {"score": 0.5, "top_risky_skills": [],
                    "top_safe_skills": [], "source": "no_match"}

        # Score each known skill
        skill_scores = {}
        for skill, risk in self.SKILL_AI_RISK.items():
            pattern = r'\b' + re.escape(skill) + r'\b'
            count = len(re.findall(pattern, all_skills_text, re.IGNORECASE))
            if count > 0:
                skill_scores[skill] = {"risk": risk, "frequency": count}

        if not skill_scores:
            if 'skill_count' in domain_df.columns:
                median_skills = pd.to_numeric(
                    domain_df['skill_count'], errors='coerce'
                ).median()
                proxy_risk = (
                    max(0.05, 0.70 - (median_skills * 0.04))
                    if not pd.isna(median_skills) else 0.40
                )
                return {
                    "score":            round(1 - proxy_risk, 3),
                    "top_risky_skills": [],
                    "top_safe_skills":  [],
                    "source":           "skill_count_proxy"
                }
            return {"score": 0.5, "top_risky_skills": [],
                    "top_safe_skills": [], "source": "no_match"}

        total_freq = sum(v["frequency"] for v in skill_scores.values())
        weighted_risk = sum(
            v["risk"] * v["frequency"] for v in skill_scores.values()
        ) / total_freq

        sorted_skills = sorted(
            skill_scores.items(), key=lambda x: x[1]["risk"], reverse=True
        )
        top_risky = [s[0] for s in sorted_skills if s[1]["risk"] >= 0.50][:5]
        top_safe  = [s[0] for s in sorted_skills if s[1]["risk"] <= 0.20][:5]

        return {
            "score":             round(1 - weighted_risk, 3),
            "weighted_risk_pct": round(weighted_risk * 100, 1),
            "top_risky_skills":  top_risky,
            "top_safe_skills":   top_safe,
            "skills_analyzed":   len(skill_scores),
            "source":            "skills_column"
        }

    def _analyze_risk_trend(self, domain_df: pd.DataFrame) -> dict:
        date_col = 'timestamp' if 'timestamp' in domain_df.columns else None
        if date_col is None or 'description' not in domain_df.columns:
            return {"trend": "Unknown", "direction_score": 0.0}

        df = domain_df.copy()
        df['_date'] = pd.to_datetime(df[date_col], errors='coerce')
        df = df.sort_values('_date').dropna(subset=['_date', 'description'])

        if len(df) < 20:
            return {"trend": "Insufficient data", "direction_score": 0.0}

        mid = len(df) // 2
        old_df, new_df = df.iloc[:mid], df.iloc[mid:]

        old_routine, _ = self._safe_keyword_score(old_df['description'], self.ROUTINE_KEYWORDS)
        new_routine, _ = self._safe_keyword_score(new_df['description'], self.ROUTINE_KEYWORDS)
        old_creative, _ = self._safe_keyword_score(old_df['description'], self.CREATIVE_KEYWORDS)
        new_creative, _ = self._safe_keyword_score(new_df['description'], self.CREATIVE_KEYWORDS)

        routine_delta  = new_routine  - old_routine
        creative_delta = new_creative - old_creative
        direction_score = creative_delta - routine_delta

        if direction_score > 0.05:
            trend = "Evolving Safely — Role becoming more strategic over time"
        elif direction_score < -0.05:
            trend = "Increasing Automation Risk — Role becoming more routine over time"
        else:
            trend = "Stable — No significant shift in task nature"

        return {
            "trend":           trend,
            "direction_score": round(direction_score, 3),
            "routine_delta":   round(routine_delta, 3),
            "creative_delta":  round(creative_delta, 3)
        }

    def _compute_human_factor_protection(self, human_score: float) -> float:
        return float(np.clip(human_score * 0.15, 0.0, 0.15))

    def calculate_ai_risk(self, df: pd.DataFrame, target_domain: str) -> dict:
        # 1. Filter domain
        domain_df = self._filter_domain(df, target_domain)

        if domain_df.empty:
            return {"error": f"No data found for domain: '{target_domain}'"}

        # 2. Task nature from descriptions
        routine_p, codified_p, low_creative_p = self._analyze_task_nature(domain_df)

        # 3. Skill-based risk (uses 'skills' column now)
        skill_risk = self._analyze_skill_risk(domain_df)
        skill_automation_score = 1 - skill_risk["score"]  # higher = more automatable

        # 4. Composite risk score
        risk_score = (
            routine_p          * self.weights.get('routine_exposure',   0.30) +
            codified_p         * self.weights.get('codified_knowledge', 0.20) +
            low_creative_p     * self.weights.get('creativity_gap',     0.20) +
            skill_automation_score * self.weights.get('skill_automation', 0.20)
        )

        # 5. Human factor adjustment
        human_factor_kw = 'physical|hardware|onsite|leadership|mentoring|client facing'
        human_factor_presence = domain_df['description'].str.contains(
            human_factor_kw, case=False
        ).mean()
        protection = self._compute_human_factor_protection(human_factor_presence)
        final_risk = float(np.clip(risk_score - protection, 0.0, 1.0))

        # 6. Classification
        label, explanation = self._classify_risk(final_risk)

        return {
            "Domain":         target_domain,
            "AI_Risk_Score":  round(final_risk, 2),
            "Risk_Category":  label,
            "Risk_Explanation": explanation,
            "Vulnerability_Breakdown": {
                "Routine_Exposure":    f"{round(routine_p * 100)}%",
                "Rule_Based_Exposure": f"{round(codified_p * 100)}%",
                "Creativity_Gap":      f"{round(low_creative_p * 100)}%",
                "Skill_Automation":    f"{round(skill_automation_score * 100)}%",
            },
            "Skill_Risk_Detail": skill_risk,
            "Actionable_Advice": (
                "Focus on high-judgment and strategic tasks."
                if final_risk > 0.5 else
                "Stay updated with AI tools to enhance productivity."
            )
        }

    def _classify_risk(self, risk: float) -> Tuple[str, str]:
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

    def _generate_advice(self, task: dict, skill: dict, final_risk: float) -> list:
        advice = []
        if task.get("routine", 0) > 0.4:
            advice.append(
                f"🔄 High routine exposure ({task['routine']*100:.0f}% of JDs) — "
                f"automate these tasks yourself before AI does."
            )
        if task.get("codified", 0) > 0.3:
            advice.append(
                f"📋 Rule-based tasks dominate ({task['codified']*100:.0f}% of JDs) — "
                f"move toward policy design and exception handling."
            )
        if task.get("creativity_gap", 0) > 0.6:
            advice.append(
                "💡 Low creative signal in JDs — deliberately pursue projects requiring "
                "original problem-solving and stakeholder alignment."
            )
        if skill.get("top_risky_skills"):
            risky = ', '.join(skill["top_risky_skills"][:3])
            advice.append(
                f"⚠️  High-automation skills dominating your domain: {risky}. "
                "Pair these with system design or AI orchestration skills."
            )
        if skill.get("top_safe_skills"):
            safe = ', '.join(skill["top_safe_skills"][:3])
            advice.append(f"✅ AI-resistant skills in demand: {safe}. Deepen these.")
        if final_risk > 0.5:
            advice.append(
                "🎯 Priority action: Shift from execution to orchestration. "
                "Become the person who directs AI, not the one it replaces."
            )
        return advice or [
            "📊 Insufficient description data for specific advice. "
            "Ensure job descriptions are populated in your dataset."
        ]


if __name__ == "__main__":
    data_path = r"D:\DATA SCIENCE AND ML\Project\job_trend_predictor\data\processed\cleaned\cleaned_job_data.csv"
    df = pd.read_csv(data_path)
    engine = AIReplacementRiskEngine()
    risk_result = engine.calculate_ai_risk(df, "Data Scientist")
    print(risk_result)