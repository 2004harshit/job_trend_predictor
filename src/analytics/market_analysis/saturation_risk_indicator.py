import pandas as pd
import numpy as np
import logging
from sklearn.linear_model import LinearRegression

class SaturationRiskIndicator:
    def __init__(self):
        # Define weights based on your logic (Sum = 1.0)
        self.w1 = 0.4  # Supply/Demand Ratio
        self.w2 = 0.3  # Growth/Decline
        self.w3 = 0.15 # Experience Pressure
        self.w4 = 0.15 # Salary Stagnation

    def _calculate_slope(self, df):
        """Calculates the trend of job postings using Linear Regression."""
        if len(df) < 2: return 0
        
        # Group by month and count postings
        df['Month_Year'] = df['Scraped_At_Cleaned'].dt.to_period('M')
        monthly_counts = df.groupby('Month_Year').size().reset_index(name='counts')
        
        if len(monthly_counts) < 2: return 0
        
        # Linear Regression: X = months, Y = counts
        x = np.arange(len(monthly_counts)).reshape(-1, 1)
        y = monthly_counts['counts'].values
        
        model = LinearRegression().fit(x, y)
        return model.coef_[0] # The Slope

    def get_saturation_risk(self, df, target_domain):
        # 1. Domain Filter
        domain_df = df[df['TItle_Cleaned'].str.contains(target_domain, case=False, na=False)].copy()
        domain_df['Scraped_At_Cleaned'] = pd.to_datetime(domain_df['Scraped_At_Cleaned'])
        
        if domain_df.empty: return {"error": "No data"}

        # --- FACTOR 1: Supply/Demand (Normalized 0 to 1) ---
        # Assuming 20:1 as max saturation (1.0)
        sd_ratio = 15 / 1  # Using your previous proxy/logic
        f1_score = min(1.0, sd_ratio / 20)

        # --- FACTOR 2: Growth Slope ---
        slope = self._calculate_slope(domain_df)
        # If slope is negative, factor score is high (risky)
        f2_score = 1.0 if slope < 0 else (0.5 if slope == 0 else 0.0)

        # --- FACTOR 3: Avg Experience Required ---
        # High exp requirement usually means a saturated entry-level market
        avg_exp = domain_df['Min_Experience'].mean()
        f3_score = min(1.0, avg_exp / 10) # 10 years as max scale

        # --- FACTOR 4: Salary Stagnation ---
        # (Using a simple proxy: if 75th percentile isn't much higher than 25th)
        sal_gap = domain_df['Max_Salary'].mean() - domain_df['Min_Salary'].mean()
        f4_score = 0.8 if sal_gap < 100000 else 0.2

        # 2. Final Saturation Score
        score = (self.w1 * f1_score) + (self.w2 * f2_score) + \
                (self.w3 * f3_score) + (self.w4 * f4_score)

        # 3. Labeling Logic
        if score < 0.4 and slope > 0:
            status, color = "Safe", "Green"
        elif 0.4 <= score <= 0.7 or slope == 0:
            status, color = "Growing Saturated", "Yellow"
        else:
            status, color = "Highly Competitive", "Red"

        return {
            "Domain": target_domain,
            "Saturation_Score": round(score, 2),
            "Market_Trend_Slope": round(slope, 2),
            "Risk_Level": status,
            "Color_Code": color,
            "Signals": {
                "Demand_Trend": "Growing" if slope > 0 else "Declining",
                "Experience_Barrier": "High" if f3_score > 0.6 else "Normal"
            }
        }
    

if __name__ == "__main__":
    path = r"D:\DATA SCIENCE AND ML\Project\job_trend_predictor\data\processed\cleaned\cleaned_job_data.csv"
    df = pd.read_csv(path)
    
    # Example for Jaipur with nearby radius
    sri = SaturationRiskIndicator()
    result = sri.get_saturation_risk(df,"Data Scientist")
    
    print(result)