# import pandas as pd

# class AverageSalaryRangeCalculator:

#     def __init__(self):
        
#         pass

#     def _filter_data(self, df, target_domain):
#         """Filters data based on the cleaned title."""
#         if 'TItle_Cleaned' not in df.columns:
#             self.logger.error("Column 'TItle_Cleaned' not found in DataFrame.")
#             return pd.DataFrame()
#         return df[df['TItle_Cleaned'].str.contains(target_domain, case=False, na=False)].copy()

#     def calculate_average_salary(self, df, target_domain):

#         domain_df = self._filter_data(df, target_domain)

#         average_min_salary = domain_df["Min_Salary"].mean()
#         average_max_salary = domain_df["Max_Salary"].mean

#         return {"Average Min Salary": average_min_salary,
#                 "Average Max Salary": average_max_salary}
    

# if __name__ == "__main__":
#     path = r"D:\DATA SCIENCE AND ML\Project\job_trend_predictor\data\processed\cleaned\cleaned_job_data.csv"

#     df = pd.read_csv(path)    

#     asrc = AverageSalaryRangeCalculator()
     
#     result = asrc.calculate_average_salary(df, "Data Scientist")

#     print(result)



import pandas as pd
import numpy as np
import logging

class AverageSalaryRangeCalculator:
    def __init__(self, lambda_val=0.1):
        self.lambda_val = lambda_val
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    def _filter_data(self, df, target_domain):
        if 'TItle_Cleaned' not in df.columns:
            return pd.DataFrame()
        # Using case=False and na=False for better matching
        return df[df['TItle_Cleaned'].str.contains(target_domain, case=False, na=False)].copy()

    def calculate_salary_metrics(self, df, target_domain, target_location=None):
        # 1. Clean Experience Data (Convert to numeric if it's not)
        df['Min_Experience'] = pd.to_numeric(df['Min_Experience'], errors='coerce').fillna(0)
        df['Avg_Salary'] = pd.to_numeric(df['Avg_Salary'], errors='coerce')
        
        # 2. Filter for Domain
        domain_df = self._filter_data(df, target_domain)
        
        # 3. Filter for Freshers (Adjusted to be more inclusive for testing)
        fresher_df = domain_df[domain_df['Min_Experience'] <= 2].dropna(subset=['Avg_Salary']).copy()

        if fresher_df.empty:
            self.logger.warning(f"No fresher data found for {target_domain}. Falling back to all experience levels.")
            fresher_df = domain_df.dropna(subset=['Avg_Salary']).copy()
            if fresher_df.empty:
                return {"error": "No salary data available for this domain."}

        # 4. Handle Time Decay Weights
        if 'Scraped_At_Cleaned' in fresher_df.columns:
            fresher_df['Scraped_At_Cleaned'] = pd.to_datetime(fresher_df['Scraped_At_Cleaned'])
            max_date = fresher_df['Scraped_At_Cleaned'].max()
            fresher_df['months_old'] = (max_date - fresher_df['Scraped_At_Cleaned']).dt.days / 30
            fresher_df['weight'] = np.exp(-self.lambda_val * fresher_df['months_old'])
        else:
            fresher_df['weight'] = 1.0 # Default weight if date is missing

        # 5. Calculate Weighted Percentiles
        def get_weighted_percentile(data, weights, percentile):
            if len(data) == 0: return np.nan
            # Sort data and weights
            ix = np.argsort(data)
            data_sorted, weights_sorted = data.iloc[ix].values, weights.iloc[ix].values
            cdf = np.cumsum(weights_sorted) / np.sum(weights_sorted)
            return np.interp(percentile, cdf, data_sorted)

        p25 = get_weighted_percentile(fresher_df['Avg_Salary'], fresher_df['weight'], 0.25)
        p50 = get_weighted_percentile(fresher_df['Avg_Salary'], fresher_df['weight'], 0.50)
        p75 = get_weighted_percentile(fresher_df['Avg_Salary'], fresher_df['weight'], 0.75)

        # 6. Location Factor
        location_median = p50
        if target_location and not np.isnan(p50):
            # Calculate National Avg of the whole dataset
            national_avg = df['Avg_Salary'].mean()
            # Calculate Local Avg
            loc_data = df[df['Location'].str.contains(target_location, case=False, na=False)]
            loc_avg = loc_data['Avg_Salary'].mean()
            
            if not np.isnan(loc_avg) and national_avg > 0:
                loc_factor = loc_avg / national_avg
                location_median = p50 * loc_factor

        # 7. Final Metrics
        margin = 0.15 # 15% Confidence margin
        return {
            "Domain": target_domain,
            "Location": target_location if target_location else "National",
            "Market_Range": {
                "Low_End_25th": round(p25, 2),
                "Median_50th": round(p50, 2),
                "High_End_75th": round(p75, 2)
            },
            "Location_Adjusted_Median": round(location_median, 2),
            "Confidence_Interval": {
                "Min": round(location_median * (1 - margin), 2),
                "Max": round(location_median * (1 + margin), 2)
            }
        }
    
if __name__ == "__main__":
    path = r"D:\DATA SCIENCE AND ML\Project\job_trend_predictor\data\processed\cleaned\cleaned_job_data.csv"
    df = pd.read_csv(path)    

    asrc = AverageSalaryRangeCalculator()
    # Calculate for Data Scientist in Jaipur
    result = asrc.calculate_salary_metrics(df, "Data Scientist", target_location="Hyderabad")

    print(result)