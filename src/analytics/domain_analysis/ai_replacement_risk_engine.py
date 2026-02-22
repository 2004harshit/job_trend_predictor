import pandas as pd
import numpy as np

class AIReplacementRiskEngine:
    def __init__(self):
        # Weights based on your logic
        self.w_routine = 0.7       # Routine/Repetitive tasks
        self.w_codified = 0.2      # Knowledge that follows strict rules/if-then logic
        self.w_low_creativity = 0.1 # Lack of original problem-solving

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

    def calculate_ai_risk(self, df, target_domain):
        # 1. Filter Domain
        domain_df = df[df['TItle_Cleaned'].str.contains(target_domain, case=False, na=False)]
        
        # 2. Assess Task Automation Probability
        routine_p, codified_p, low_creative_p = self._analyze_task_nature(domain_df)
        
        # 3. Math Logic: Risk Score Calculation
        # Risk_Score = (Routine_tasks% * 0.7) + (Codified_knowledge% * 0.2) + (Low_creativity% * 0.1)
        risk_score = (routine_p * self.w_routine) + \
                     (codified_p * self.w_codified) + \
                     (low_creative_p * self.w_low_creativity)
        
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

if __name__ == "__main__":
    # Example usage
    path = r"D:\DATA SCIENCE AND ML\Project\job_trend_predictor\data\processed\cleaned\cleaned_job_data.csv"
    df = pd.read_csv(path)
    ai_engine = AIReplacementRiskEngine()
    report = ai_engine.calculate_ai_risk(df, "Data Scientist")
    # report = ai_engine.calculate_ai_risk(df, "Web Developer")
    print(report)