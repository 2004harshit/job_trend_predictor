import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression

class DomainStabilityEngine:
    def __init__(self):
        # AI Risk Factors (Industry standard estimates for automation impact)
        # 0.0 = No Risk, 1.0 = Fully Automatable
        self.ai_risk_mapping = {
            'data entry': 0.85,
            'manual tester': 0.70,
            'web developer': 0.30,
            'data scientist': 0.20,
            'ml engineer': 0.10,
            'ai researcher': 0.05
        }

    def _calculate_volatility(self, monthly_counts):
        """Math: Std_Dev / Mean (Coefficient of Variation)"""
        if len(monthly_counts) < 2: return 0.5 # Default medium volatility
        mean_val = monthly_counts.mean()
        if mean_val == 0: return 1.0
        return monthly_counts.std() / mean_val

    def _forecast_demand(self, monthly_counts, years=5):
        """Uses Linear Trend Extrapolation to project 5-year demand"""
        if len(monthly_counts) < 2: return monthly_counts.sum()
        
        X = np.arange(len(monthly_counts)).reshape(-1, 1)
        y = monthly_counts.values
        
        model = LinearRegression().fit(X, y)
        # Predict the value 60 months (5 years) into the future
        future_step = len(monthly_counts) + (years * 12)
        projected_demand = max(0, model.predict([[future_step]])[0])
        return projected_demand

    def calculate_stability_score(self, df, target_domain):
        # 1. Prepare Time Series Data
        domain_df = df[df['TItle_Cleaned'].str.contains(target_domain, case=False, na=False)].copy()
        domain_df['Scraped_At_Cleaned'] = pd.to_datetime(domain_df['Scraped_At_Cleaned'])
        
        # Monthly job posting aggregation
        monthly_series = domain_df.resample('M', on='Scraped_At_Cleaned').size()
        
        if monthly_series.empty: return {"error": "Insufficient historical data"}

        # 2. Math Logic: Stability & Volatility
        current_demand = monthly_series.iloc[-1]
        peak_demand = monthly_series.max()
        projected_5yr = self._forecast_demand(monthly_series)
        
        # Base Stability Formula: (Current + Projected) / (2 * Peak)
        base_stability = (current_demand + projected_5yr) / (2 * peak_demand) if peak_demand > 0 else 0
        
        # Volatility: Lower is better for stability
        volatility = self._calculate_volatility(monthly_series)
        
        # 3. AI Risk Integration
        # Default risk to 0.4 if domain not in mapping
        ai_risk = self.ai_risk_mapping.get(target_domain.lower(), 0.4)
        
        # Final Score: Adjusting base stability by volatility and AI risk
        # We subtract a penalty for high volatility
        final_score = base_stability * (1 - ai_risk) * (1 - (volatility * 0.2))

        return {
            "Domain": target_domain,
            "Stability_Score": round(min(1.0, final_score), 2),
            "Volatility_Index": round(volatility, 2),
            "AI_Automation_Risk": f"{int(ai_risk * 100)}%",
            "Trend": "Growing" if projected_5yr > current_demand else "Declining",
            "Status": "Stable" if final_score > 0.6 else "High Risk"
        }

if __name__ == "__main__":
    # Example usage
    path = r"D:\DATA SCIENCE AND ML\Project\job_trend_predictor\data\processed\cleaned\cleaned_job_data.csv"
    df = pd.read_csv(path)
    dse = DomainStabilityEngine()
    # report = dse.calculate_stability_score(df, "Web Developer")
    report = dse.calculate_stability_score(df, "Data Scientist")
    print(report)
    