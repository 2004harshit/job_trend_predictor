import pandas as pd
import numpy as np
from datetime import datetime, timedelta

class JobMarketVelocityCalculator:
    def __init__(self, nearby_cities=None):
        # Example: For Jaipur, nearby might be ['Ajmer', 'Sanganer', 'Amer']
        self.nearby_cities = nearby_cities if nearby_cities else []

    def _filter_by_domain(self, df, domain_keywords):
        """Filters by keywords in Title or Description."""
        pattern = '|'.join(domain_keywords)
        return df[
            df['TItle_Cleaned'].str.contains(pattern, case=False, na=False) |
            df['Description_Cleaned'].str.contains(pattern, case=False, na=False)
        ].copy()

    def calculate_openings_stats(self, df, domain_keywords, target_location):
        # 1. Setup Dates
        df['Scraped_At_Cleaned'] = pd.to_datetime(df['Scraped_At_Cleaned'])
        today = df['Scraped_At_Cleaned'].max()
        thirty_days_ago = today - timedelta(days=30)
        sixty_days_ago = today - timedelta(days=60)

        # 2. Filter Domain
        domain_df = self._filter_by_domain(df, domain_keywords)

        # 3. National Counts
        national_current = domain_df[domain_df['Scraped_At_Cleaned'] > thirty_days_ago]
        national_previous = domain_df[
            (domain_df['Scraped_At_Cleaned'] <= thirty_days_ago) & 
            (domain_df['Scraped_At_Cleaned'] > sixty_days_ago)
        ]

        # 4. Local Counts (Exact match + Nearby)
        location_list = [target_location] + self.nearby_cities
        loc_pattern = '|'.join(location_list)
        
        local_current = national_current[national_current['Location'].str.contains(loc_pattern, case=False, na=False)]
        local_previous = national_previous[national_previous['Location'].str.contains(loc_pattern, case=False, na=False)]

        # 5. Math Logic: Growth Rate
        def get_growth(curr, prev):
            if len(prev) == 0: return 0.0
            return ((len(curr) - len(prev)) / len(prev)) * 100

        national_growth = get_growth(national_current, national_previous)
        local_growth = get_growth(local_current, local_previous)

        # 6. Local Market Share
        local_share = (len(local_current) / len(national_current) * 100) if len(national_current) > 0 else 0

        return {
            "Domain_Keywords": domain_keywords,
            "Location": target_location,
            "Counts": {
                "National_Openings_30d": len(national_current),
                "Local_Openings_30d": len(local_current)
            },
            "Growth_Metrics": {
                "National_Growth_Pct": round(national_growth, 2),
                "Local_Growth_Pct": round(local_growth, 2)
            },
            "Market_Context": {
                "Local_Market_Share_Pct": round(local_share, 2),
                "Status": "Expanding" if local_growth > 0 else "Contracting"
            }
        }

if __name__ == "__main__":
    path = r"D:\DATA SCIENCE AND ML\Project\job_trend_predictor\data\processed\cleaned\cleaned_job_data.csv"
    df = pd.read_csv(path)
    
    # Example for Jaipur with nearby radius
    jvc = JobMarketVelocityCalculator(nearby_cities=['Sanganer', 'Amer'])
    result = jvc.calculate_openings_stats(df, ['Data Scientist', 'Machine Learning'], 'Jaipur')
    
    print(result)