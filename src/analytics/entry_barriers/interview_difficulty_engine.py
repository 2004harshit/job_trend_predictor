import pandas as pd
import numpy as np

class InterviewDifficultyEngine:
    def __init__(self):
        # Domain-specific weights (Alpha: DSA, Beta: Domain, Gamma: System Design)
        # Weights must sum to 1.0
        self.weights = {
            'software engineer': {'a': 0.50, 'b': 0.30, 'g': 0.20},
            'ml engineer':       {'a': 0.25, 'b': 0.40, 'g': 0.35},
            'data scientist':    {'a': 0.15, 'b': 0.65, 'g': 0.20},
            'frontend dev':      {'a': 0.40, 'b': 0.50, 'g': 0.10}
        }

    def _calculate_dsa_score(self, easy_p, med_p, hard_p):
        """Math: (Easy*0.3) + (Medium*0.5) + (Hard*0.2)"""
        return (easy_p * 0.3) + (med_p * 0.5) + (hard_p * 0.2)

    def calculate_interview_difficulty(self, df, target_domain):
        # 1. Standardize domain name
        domain_key = target_domain.lower()
        w = self.weights.get(domain_key, {'a': 0.33, 'b': 0.33, 'g': 0.34}) # Default equal split

        # 2. Extract Domain Score (Frequency of specific keywords in JDs)
        # We proxy 'Difficulty' by looking at the density of advanced requirements
        domain_df = df[df['TItle_Cleaned'].str.contains(target_domain, case=False, na=False)]
        if domain_df.empty: return {"error": "Domain not found"}

        # Logic: High mention of 'Architecture' or 'Scalability' increases System Design Score
        sys_design_mentions = domain_df['Description_Cleaned'].str.contains('architecture|scalable|cloud', case=False).mean()
        
        # 3. Mock/Aggregate DSA Distribution for the Domain 
        # (In a production system, this would be scraped from Glassdoor/LeetCode interview reports)
        if "ml" in domain_key or "data" in domain_key:
            dsa_dist = (0.5, 0.4, 0.1) # Mostly Easy/Med for ML
        else:
            dsa_dist = (0.2, 0.6, 0.2) # Med/Hard focus for SWE

        dsa_score = self._calculate_dsa_score(*dsa_dist)
        domain_score = min(1.0, domain_df['Skill_Count'].mean() / 15) # Normalized by 15 skills avg

        # 4. Math Logic: Composite Difficulty
        # Composite = alpha*DSA + beta*Domain + gamma*SysDesign
        difficulty_index = (w['a'] * dsa_score) + (w['b'] * domain_score) + (w['g'] * sys_design_mentions)

        return {
            "Domain": target_domain,
            "Difficulty_Index": round(difficulty_index * 10, 1), # Scale 1-10
            "Pillar_Breakdown": {
                "DSA_Weight": f"{w['a']*100}%",
                "Domain_Weight": f"{w['b']*100}%",
                "System_Design_Weight": f"{w['g']*100}%"
            },
            "Preparation_Focus": "Algorithms" if w['a'] > 0.4 else "Subject Matter/System Design"
        }

if __name__ == "__main__":
    # Example usage
    path = r"D:\DATA SCIENCE AND ML\Project\job_trend_predictor\data\processed\cleaned\cleaned_job_data.csv"
    df = pd.read_csv(path)
    ide = InterviewDifficultyEngine()
    report = ide.calculate_interview_difficulty(df, "Machine Learning Engineer")
    print(report)
