import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

class CompetitionLevelCalculator:
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def _filter_data(self, data, target_domain):
        """Filters data based on the cleaned title."""
        if 'TItle_Cleaned' not in data.columns:
            self.logger.error("Column 'TItle_Cleaned' not found in DataFrame.")
            return pd.DataFrame()
        return data[data['TItle_Cleaned'].str.contains(target_domain, case=False, na=False)].copy()

    def calculate_competition_level(self, df, target_domain, user_skill_count=None):
        """
        Implements: Competition_Index = (Active_Job_Seekers * Skill_Overlap_Factor) / Available_Positions
        """
        # 1. Filter for Domain
        domain_df = self._filter_data(df, target_domain)
        
        if domain_df.empty:
            self.logger.warning(f"No postings found for domain: {target_domain}")
            return {"error": "Domain not found"}

        # 2. Identify Variables (Demand)
        available_positions = len(domain_df)
        
        # 3. Supply Logic (Current Proxy vs. Future Actuals)
        if 'Applicants' in domain_df.columns:
            active_job_seekers = domain_df['Applicants'].sum()
        else:
            # Domain-specific proxy mapping
            proxies = {'data scientist': 12, 'ml engineer': 8, 'web development': 25}
            multiplier = proxies.get(target_domain.lower(), 15)
            active_job_seekers = available_positions * multiplier

        # 4. Calculate Skill Overlap Factor
        avg_req_skills = domain_df['Skill_Count'].mean()
        
        if user_skill_count is not None:
            # How well the USER fits the market
            skill_overlap_factor = min(1.0, user_skill_count / avg_req_skills) if avg_req_skills > 0 else 0.5
        else:
            # How well the AVERAGE SEEKER fits the market
            skill_overlap_factor = max(0.1, min(1.0, 5 / avg_req_skills)) if avg_req_skills > 0 else 0.5

        # 5. Math Formulas
        # Raw Ratio for categorization
        raw_ratio = active_job_seekers / max(available_positions, 1)
        
        # Competition Index (Your Required Formula)
        competition_index = (active_job_seekers * skill_overlap_factor) / max(available_positions, 1)

        # 6. Mapping Levels
        if raw_ratio < 5:
            level = "Low"
        elif 5 <= raw_ratio <= 15:
            level = "Medium"
        else:
            level = "High"

        return {
            "Domain": target_domain,
            "Metrics": {
                "Competition_Level": level,
                "Competition_Index": round(competition_index, 2),
                "Raw_Supply_Demand_Ratio": round(raw_ratio, 2),
                "Skill_Overlap_Factor": round(skill_overlap_factor, 2)
            },
            "Actual_Numbers": {
                "Active_Job_Seekers": int(active_job_seekers),
                "Available_Positions": available_positions
            }
        }

if __name__ == "__main__":
    # Load your data
    try:
        path = r"D:\DATA SCIENCE AND ML\Project\job_trend_predictor\data\processed\cleaned\cleaned_job_data.csv"
        job_data = pd.read_csv(path)

        clc = CompetitionLevelCalculator()
        
        # Example: Calculate for 'Data Scientist' with user having 8 skills
        result = clc.calculate_competition_level(job_data, "Data Scientist", user_skill_count=8)

        if "error" not in result:
            print(f"\n--- Competition Report: {result['Domain']} ---")
            print(f"Level: {result['Metrics']['Competition_Level']}")
            print(f"Competition Index: {result['Metrics']['Competition_Index']}")
            print(f"Candidates per Job: {result['Metrics']['Raw_Supply_Demand_Ratio']}")
            print(f"Your Skill Match: {result['Metrics']['Skill_Overlap_Factor'] * 100}%")
    except Exception as e:
        print(f"Error loading data or calculating: {e}")