import pandas as pd
import numpy as np

class SalaryGrowthEngine:
    def __init__(self):
        self.years_projection = 2
      
    def calculate_cagr(self, start_val, end_val, periods):
        """Math Logic: (End/Start)^(1/n) - 1"""
        if start_val <= 0 or periods <= 0: return 0
        return (end_val / start_val) ** (1 / periods) - 1
    
    def preprocess_salary_data(self, df):
        """
        Cleans and creates the Mid_Salary column.
        """
        # 1. Ensure columns are numeric (converts strings like '500000' to int)
        df['Min_Salary'] = pd.to_numeric(df['Min_Salary'], errors='coerce')
        df['Max_Salary'] = pd.to_numeric(df['Max_Salary'], errors='coerce')

        # 2. Calculate Mid_Salary
        # We use (min + max) / 2
        df['Salary_Mid'] = (df['Min_Salary'] + df['Max_Salary']) / 2

        # 3. Handle cases where only one value is present
        # If Max is missing, use Min. If Min is missing, use Max.
        df['Salary_Mid'] = df['Salary_Mid'].fillna(df['Min_Salary']).fillna(df['Max_Salary'])

        # 4. Remove rows where we have absolutely no salary info
        df = df.dropna(subset=['Salary_Mid'])

        return df

    def project_growth(self, df, target_domain):
        # 1. Filter Domain
        domain_df = df[df['TItle_Cleaned'].str.contains(target_domain, case=False, na=False)].copy()
        if domain_df.empty: return {"error": "No data for domain"}

        # 2. Get Salary Benchmarks for Fresher vs 2-Year Exp
        domain_df = self.preprocess_salary_data(domain_df)
        # We use medians (50th percentile) to avoid outlier skew
        fresher_salary = domain_df[domain_df['Min_Experience'] <= 1]['Salary_Mid'].median()
        mid_level_salary = domain_df[(domain_df['Min_Experience'] >= 2) & 
                                     (domain_df['Min_Experience'] <= 3)]['Salary_Mid'].median()

        # Handle cases with insufficient historical data
        if pd.isna(fresher_salary) or pd.isna(mid_level_salary):
            fresher_salary = domain_df['Salary_Mid'].quantile(0.25)
            mid_level_salary = domain_df['Salary_Mid'].quantile(0.75)

        # 3. Calculate Market growth_rate
        market_growth_rate = self.calculate_cagr(fresher_salary, mid_level_salary, 2)

        # 4. Define Percentile Range Multipliers
        # Conservative (25th), Expected (50th), Optimistic (75th)
        ranges = {
            "Conservative": market_growth_rate * 0.7, # 70% of market median
            "Expected": market_growth_rate,
            "Optimistic": market_growth_rate * 1.4    # 140% for top performers/switchers
        }

        projections = {}
        for label, rate in ranges.items():
            # Future_Salary = Starting * (1 + r)^t
            future_val = fresher_salary * (1 + rate) ** self.years_projection
            projections[label] = {
                "Annual_Growth_Rate": f"{round(rate * 100, 1)}%",
                "Projected_Salary_2Yr": round(future_val, -3) # Round to nearest thousand
            }

        return {
            "Domain": target_domain,
            "Starting_Median": fresher_salary,
            "Projections": projections
        }

if __name__ == "__main__":
    path = r"D:\DATA SCIENCE AND ML\Project\job_trend_predictor\data\processed\cleaned\cleaned_job_data.csv"
    df = pd.read_csv(path)
    sge = SalaryGrowthEngine()
    # report = sge.project_growth(df, "Data Scientist")
    report = sge.project_growth(df, "Web Developer")
    print(report)