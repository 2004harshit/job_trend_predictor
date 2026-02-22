import pandas as pd
import numpy as np

class ProjectComplexityEvaluator:
    def __init__(self):
        # Weights for complexity scoring
        self.w1 = 0.4  # Number of features (Core logic)
        self.w2 = 0.2  # Tech stack size (Versatility)
        self.w3 = 0.25 # Integration points (API, DB, Webhooks)
        self.w4 = 0.15 # Deployment complexity (Docker, AWS, CI/CD)

    def _extract_market_complexity(self, domain_df):
        """
        Analyzes JDs to estimate required project complexity.
        In a real scenario, this uses NLP to count mentions of 
        integrations, cloud tools, and features.
        """
        if domain_df.empty:
            return 2.5 # Default medium complexity
        
        # Proxy Logic: Higher skill counts in JDs usually correlate with 
        # higher expected project complexity.
        avg_skills = domain_df['Skill_Count'].mean()
        
        # Calibration: Scale average skills to a 1-10 complexity score
        market_complexity_benchmark = min(10, avg_skills / 1.5)
        return market_complexity_benchmark

    def calculate_project_score(self, num_features, tech_stack_size, integrations, deployment_level):
        """
        Calculates the score of a user's existing project.
        deployment_level: 1 (Local), 2 (Cloud/Basic), 3 (Scalable/CI-CD)
        """
        score = (self.w1 * num_features) + \
                (self.w2 * tech_stack_size) + \
                (self.w3 * integrations) + \
                (self.w4 * deployment_level)
        return score

    def evaluate_portfolio_readiness(self, df, target_domain, user_project_stats=None):
        """
        user_project_stats: {'features': x, 'tech': y, 'ints': z, 'deploy': a}
        """
        # 1. Filter Domain
        domain_df = df[df['TItle_Cleaned'].str.contains(target_domain, case=False, na=False)]
        
        # 2. Get Market Benchmark (50th Percentile / Median)
        market_median_complexity = self._extract_market_complexity(domain_df)
        
        # 3. Define Thresholds for Labeling
        # Simple < 3 | Medium 3-6 | Advanced > 6
        if market_median_complexity < 3:
            market_label = "Simple CRUD"
        elif 3 <= market_median_complexity <= 6:
            market_label = "Medium Complexity"
        else:
            market_label = "Advanced / Scalable"

        # 4. Compare User Project if provided
        user_score = 0
        status = "Not Assessed"
        if user_skill_stats := user_project_stats:
            user_score = self.calculate_project_score(
                user_skill_stats['features'],
                user_skill_stats['tech'],
                user_skill_stats['ints'],
                user_skill_stats['deploy']
            )
            status = "Market Ready" if user_score >= market_median_complexity else "Complexity Gap Detected"

        return {
            "Domain": target_domain,
            "Market_Median_Expectation": round(market_median_complexity, 2),
            "Requirement_Tier": market_label,
            "User_Project_Score": round(user_score, 2),
            "Readiness_Status": status,
            "Target_Specs": {
                "Suggested_Features": "6+" if market_median_complexity > 6 else "3-5",
                "Suggested_Tech_Stack": "7+" if market_median_complexity > 6 else "4-6"
            }
        }
    

# --- Example Call ---
if __name__ == "__main__":
    path = r"D:\DATA SCIENCE AND ML\Project\job_trend_predictor\data\processed\cleaned\cleaned_job_data.csv"
    df = pd.read_csv(path)
    pce = ProjectComplexityEvaluator()
    my_project = {'features': 4, 'tech': 5, 'ints': 1, 'deploy': 2}
    report = pce.evaluate_portfolio_readiness(df, "Web Developer", my_project)
    print(report)