import pandas as pd
import numpy as np

class HiddenBlockerDetector:
    def __init__(self):
        # Impact weights for different blocker types
        # These determine how much a blocker affects the "Success Probability"
        self.impact_weights = {
            "Math-heavy": 0.7,
            "Requires internship": 0.9,
            "Portfolio-dependent": 0.8,
            "Seniority-Bias": 0.85
        }

    def scan_for_blockers(self, df, target_domain):
        # 1. Filter for Domain
        domain_df = df[df['TItle_Cleaned'].str.contains(target_domain, case=False, na=False)].copy()
        if domain_df.empty:
            return {"error": "Domain data missing"}

        total_posts = len(domain_df)
        blockers = []

        # --- Rule 1: Math-heavy (Specific to AI/ML) ---
        math_keywords = 'math|statistics|probability|calculus|linear algebra'
        math_mention_pct = (domain_df['Description_Cleaned'].str.contains(math_keywords, case=False, na=False).sum() / total_posts) * 100
        
        if "ML" in target_domain.upper() and math_mention_pct > 60:
            severity = (math_mention_pct / 100) * self.impact_weights["Math-heavy"]
            blockers.append({
                "type": "Math-heavy",
                "severity": round(severity, 2),
                "message": "Heavy theoretical math focus in interviews detected."
            })

        # --- Rule 2: Requires Internship (Entry-level scarcity) ---
        fresher_jobs = domain_df[domain_df['Min_Experience'] <= 1]
        fresher_pct = (len(fresher_jobs) / total_posts) * 100
        
        if fresher_pct < 30:
            severity = ((100 - fresher_pct) / 100) * self.impact_weights["Requires internship"]
            blockers.append({
                "type": "Requires internship",
                "severity": round(severity, 2),
                "message": "Fresher roles are scarce (<30%). You likely need a prior internship."
            })

        # --- Rule 3: Portfolio-dependent (Project mentions) ---
        project_keywords = 'portfolio|personal project|github|live link|demo'
        project_mention_pct = (domain_df['Description_Cleaned'].str.contains(project_keywords, case=False, na=False).sum() / total_posts) * 100

        if project_mention_pct > 80:
            severity = (project_mention_pct / 100) * self.impact_weights["Portfolio-dependent"]
            blockers.append({
                "type": "Portfolio-dependent",
                "severity": round(severity, 2),
                "message": "Standard applications won't work. High emphasis on proof-of-work/GitHub."
            })

        return {
            "Domain": target_domain,
            "Detected_Blockers": blockers,
            "Overall_Risk_Score": round(sum(b['severity'] for b in blockers), 2)
        }
    
if __name__ == "__main__":
    path = r"D:\DATA SCIENCE AND ML\Project\job_trend_predictor\data\processed\cleaned\cleaned_job_data.csv"
    df = pd.read_csv(path)
    hbd = HiddenBlockerDetector()
    # report = hbd.scan_for_blockers(df, "Machine Learning Engineer")
    report = hbd.scan_for_blockers(df, "Web Developer")
    print(report)