# import pandas as pd
# from typing import Dict, List
# from datetime import datetime, date, timedelta
# import calendar




# class DemandScoreCalculator():
#     def __init__(self , data: pd.DataFrame , weight:Dict):
#         self.data = data
#         self.demand_score  = {}
#         self.demand_sccore_report = {}
#         self.weight = weight

    
#     def _filter_fresher_data(self):
#         return self.data[(self.data["Min_Experience"]>=0 ) & (self.data["Max_Experience"]<=5)]

#     def _calculate_job_posting_frequency(self,feature:List[str]):
#         max_freq = 0
#         score_record = {}
#         for domain in feature:
#             freq = self.fresher_data[self.fresher_data["Job_Type"] == domain].shape[0]
#             max_freq = max(max_freq , freq)
            
#         # normalizing against highest demand domain
#         if max_freq == 0:
#             raise ZeroDivisionError("Max frequency of post is zero, leads to zero devision error")
#         for domain in feature:
#             freq = self.fresher_data[self.fresher_data["Job_Type"] == domain].shape[0]
#             score_part_relative_to_max_freq = freq/max_freq
#             score = round(score_part_relative_to_max_freq*10,2)
#             score_record[domain] = score

#         return score_record

#     def _calculate_trend_score(self,feature:List[str]):

#         today = date.today()
#         first_day_of_this_month = today.replace(day = 1)

#         _, last_day_num = calendar.monthrange(today.year, today.month)
#         last_day_of_this_month = today.replace(day = last_day_num)

#         last_day_of_previous_month = first_day_of_this_month - timedelta(days= 1)
#         first_day_of_previous_month = last_day_of_previous_month.replace(day = 1)

#         current_month_data = self.fresher_data[(self.fresher_data["Scraped_At_Cleaned"] >= str(first_day_of_this_month)) & (self.fresher_data["Scraped_At_Cleaned"] <= str(last_day_of_this_month))]
#         previous_month_data = self.fresher_data[(self.fresher_data["Scraped_At_Cleaned"] >= str(first_day_of_previous_month)) & (self.fresher_data["Scraped_At_Cleaned"] <= str(last_day_of_previous_month))]
         
#         trend_score_record = {}
#         for domain in feature:
#             current_month_freq = current_month_data[current_month_data["Job_Type"] == domain].shape[0]
#             previous_month_freq = previous_month_data[previous_month_data["Job_Type"] == domain].shape[0]
#             if previous_month_freq == 0:
#                 trend_score = 10.0
#             else:
#                 trend_change = (current_month_freq - previous_month_freq) / previous_month_freq
#                 trend_score = round(min(max(trend_change * 10, 0), 10),2)
#             trend_score_record[domain] = trend_score
#         return trend_score_record

#     def _calculate_experience_flexibility_score(self,feature:List[str]):
            
#         experience_score = {}
#         # max_experience_frequency = data.shape[0]
#         max_experience_frequency = self.data.shape[0]
#         for domain in feature:
#             freq=  self.fresher_data[(self.fresher_data["Job_Type"]==domain)].shape[0]
#             relative_score = round((freq/max_experience_frequency)*10,2)
#             experience_score[domain] =  relative_score 
        
#         return experience_score
       
#     def get_demand_score_report(self):
#         return self.demand_sccore_report
    
#     def _calculate_skill_diversity_score(self,feature:List[str]):
#         skill_diversity_score = {}
#         max_hiring_frequency = 0
#         for domain in feature:
#             frequency =  self.fresher_data[self.fresher_data["Job_Type"]==domain]["Company_Cleaned"].unique().shape[0]
#             max_hiring_frequency = max(frequency, max_hiring_frequency)

#         for domain in feature:
#             frequency =  self.fresher_data[self.fresher_data["Job_Type"]==domain]["Company_Cleaned"].unique().shape[0]
#             relative_score = round((frequency/max_hiring_frequency)*10,2)
#             skill_diversity_score[domain] = relative_score
        
#         return skill_diversity_score

#     def _demand_score_calculator(self, feature):

#         for domain in feature:
#             job_demand =round(self.job_posting_frequency_score[domain]*self.weight["Job_Posting_Frequency"] ,2)
#             final_trend_score = round(self.trend_score[domain]*self.weight["Trend_Direction"],2)
#             final_skill_diversity_score = round(self.skill_diversity_score[domain]*self.weight["Skill_Diversity"],2)
#             final_experience_flexibiity_score = round(self.experience_score[domain]*self.weight['Experience_Fleibility'],2)

#             total_demand_score =round( job_demand+final_trend_score+final_experience_flexibiity_score+final_skill_diversity_score,2)

#             self.demand_score[domain] = total_demand_score
#             self.demand_sccore_report[domain] = {"Job Score":job_demand, "trend_score":final_trend_score,"skill_diversity_score":final_skill_diversity_score,"experience_flexibility_score":final_experience_flexibiity_score, "demand score":total_demand_score}
    


#     def calculate_demand_score(self, feature: List[str]):

#         # step 0 : initilizing feature 
#         if feature is None:
#             feature = self.fresher_data["Job_Type"].unique()
        
#         # filter fresher data
#         self.fresher_data = self._filter_fresher_data()
    
#         # step 1: calculate job_posting_frequency score.
#         self.job_posting_frequency_score = self._calculate_job_posting_frequency(feature)
#         # step 2: calculate trend score.
#         self.trend_score = self._calculate_trend_score(feature)
#         # step 3: calculate experience_flexibility score.
#         self.experience_score = self._calculate_experience_flexibility_score(feature)
#         # step 4: calculate skill_diversity_score score. 
#         self.skill_diversity_score = self._calculate_skill_diversity_score(feature)
#         # step5: calculate demand score
#         self._demand_score_calculator(feature)
#         # return demand score
#         return self.demand_score


# if __name__ == "__main__":
  
#     data = pd.read_csv(r"D:\DATA SCIENCE AND ML\Project\job_trend_predictor\data\processed\cleaned\cleaned_job_data.csv")
#     feature = data["Job_Type"].unique()

#     weight = {
#         "Job_Posting_Frequency": 0.4,
#         "Trend_Direction": 0.3,
#         "Skill_Diversity":0.15,
#         "Experience_Fleibility":0.15
#     }
    
#     DSC = DemandScoreCalculator(data,weight)
#     demand_score = DSC.calculate_demand_score(feature)

#     # print(f"Deamnd Score : {demand_score}")
#     print(f"Deamnd Score Report : {DSC.get_demand_score_report()}")




import pandas as pd
import numpy as np
from typing import Dict, List
from datetime import datetime, timedelta
import calendar

class MarketDemandEngine:
    def __init__(self, data: pd.DataFrame, weights: Dict = None):
        self.data = data.copy()
        self.weights = weights or {
            "Job_Posting_Frequency": 0.4,
            "Trend_Direction": 0.3,
            "Skill_Diversity": 0.15,
            "Experience_Flexibility": 0.15
        }
        self.demand_report = {}
        
        # Pre-process dates to ensure safety
        self.data['Scraped_At_Cleaned'] = pd.to_datetime(self.data['Scraped_At_Cleaned'])

    def _filter_fresher_data(self, df):
        """Focuses on the 0-5 year bracket where demand volatility is highest."""
        return df[(df["Min_Experience"] >= 0) & (df["Min_Experience"] <= 5)]

    def _get_time_metrics(self):
        """Utility to calculate accurate month boundaries."""
        today = datetime.now().date()
        first_this = today.replace(day=1)
        last_prev = first_this - timedelta(days=1)
        first_prev = last_prev.replace(day=1)
        return first_this, last_prev, first_prev

    def calculate_metrics(self, domains: List[str] = None):
        fresher_df = self._filter_fresher_data(self.data)
        if domains is None:
            domains = fresher_df["Job_Type"].unique()

        first_this, last_prev, first_prev = self._get_time_metrics()

        # 1. Job Posting Frequency (Volume)
        counts = fresher_df["Job_Type"].value_counts()
        max_freq = counts.max() if not counts.empty else 1

        # 2. Monthly Trend Analysis
        curr_month = fresher_df[fresher_df["Scraped_At_Cleaned"].dt.date >= first_this]
        prev_month = fresher_df[(fresher_df["Scraped_At_Cleaned"].dt.date >= first_prev) & 
                                (fresher_df["Scraped_At_Cleaned"].dt.date <= last_prev)]

        for domain in domains:
            # Frequency Score (0-10)
            freq = counts.get(domain, 0)
            score_freq = (freq / max_freq) * 10

            # Trend Score (Growth logic)
            c_count = curr_month[curr_month["Job_Type"] == domain].shape[0]
            p_count = prev_month[prev_month["Job_Type"] == domain].shape[0]
            
            if p_count == 0:
                score_trend = 5.0  # Neutral if no history
            else:
                growth = (c_count - p_count) / p_count
                score_trend = np.clip(5 + (growth * 10), 0, 10) # Centered at 5

            # Skill/Company Diversity (How many unique companies are hiring?)
            unique_cos = fresher_df[fresher_df["Job_Type"] == domain]["Company_Cleaned"].nunique()
            max_cos = fresher_df["Company_Cleaned"].nunique()
            score_diversity = (unique_cos / (max_cos * 0.2)) * 10 # Scaled to 20% of total market
            score_diversity = min(score_diversity, 10)

            # Experience Flexibility (Ratio of fresher jobs to total domain jobs)
            total_domain_jobs = self.data[self.data["Job_Type"] == domain].shape[0]
            fresher_domain_jobs = fresher_df[fresher_df["Job_Type"] == domain].shape[0]
            score_flex = (fresher_domain_jobs / total_domain_jobs * 10) if total_domain_jobs > 0 else 0

            # Weighted Total
            total_score = (
                (score_freq * self.weights["Job_Posting_Frequency"]) +
                (score_trend * self.weights["Trend_Direction"]) +
                (score_diversity * self.weights["Skill_Diversity"]) +
                (score_flex * self.weights["Experience_Flexibility"])
            )

            self.demand_report[domain] = {
                "Overall_Demand_Score": round(total_score, 2),
                "Breakdown": {
                    "Volume": round(score_freq, 2),
                    "Growth_Trend": round(score_trend, 2),
                    "Market_Diversity": round(score_diversity, 2),
                    "Entry_Flexibility": round(score_flex, 2)
                }
            }

        return self.demand_report
    

if __name__ == "__main__":
    import pandas as pd

# 1. Setup Sample Data (In your case, load your CSV)
df = pd.read_csv(r"D:\DATA SCIENCE AND ML\Project\job_trend_predictor\data\processed\cleaned\cleaned_job_data.csv")

# 2. Define your strategic weights
# Do you care more about "Volume" or "Current Growth"? 
custom_weights = {
    "Job_Posting_Frequency": 0.35,  # Total volume of jobs
    "Trend_Direction": 0.40,       # How much it grew this month
    "Skill_Diversity": 0.15,       # Number of different companies hiring
    "Experience_Flexibility": 0.10 # Percentage of roles open to freshers
}

# 3. Initialize the Engine
mde = MarketDemandEngine(data=df, weights=custom_weights)

# 4. Calculate metrics for specific domains
# You can pass a list of domains or leave it as None to calculate for all
target_domains = ["Data Scientist", "Web Developer", "ML Engineer"]
demand_results = mde.calculate_metrics(domains=target_domains)

# 5. Display the "Real Talk" summary for a specific domain
target = "Data Scientist"
if target in demand_results:
    stats = demand_results[target]
    print(f"--- Market Demand Report: {target} ---")
    print(f"Overall Demand Score: {stats['Overall_Demand_Score']}/10")
    print(f"Growth Trend Score:  {stats['Breakdown']['Growth_Trend']}/10")
    print(f"Market Diversity:    {stats['Breakdown']['Market_Diversity']}/10")
    print(f"Entry Ease:          {stats['Breakdown']['Entry_Flexibility']}/10")
    
    # Logic integration for the "Real Talk" layer
    if stats['Overall_Demand_Score'] > 7.5:
        print("\n🔥 STATUS: High Demand. Companies are hiring aggressively.")
    elif stats['Breakdown']['Growth_Trend'] < 4.0:
        print("\n🧊 STATUS: Cooling Down. Growth has slowed compared to last month.")