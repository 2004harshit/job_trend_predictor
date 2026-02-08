import pandas as pd
from typing import Dict, List
from datetime import datetime, date, timedelta
import calendar




class DemandScoreCalculator():
    def __init__(self , data: pd.DataFrame , weight:Dict):
        self.data = data
        self.demand_score  = {}
        self.demand_sccore_report = {}
        self.weight = weight

    
    def _filter_fresher_data(self):
        return self.data[(self.data["Min_Experience"]>=0 ) & (self.data["Max_Experience"]<=5)]

    def _calculate_job_posting_frequency(self,feature:List[str]):
        max_freq = 0
        score_record = {}
        for domain in feature:
            freq = self.fresher_data[self.fresher_data["Job_Type"] == domain].shape[0]
            max_freq = max(max_freq , freq)
            
        # normalizing against highest demand domain
        if max_freq == 0:
            raise ZeroDivisionError("Max frequency of post is zero, leads to zero devision error")
        for domain in feature:
            freq = self.fresher_data[self.fresher_data["Job_Type"] == domain].shape[0]
            score_part_relative_to_max_freq = freq/max_freq
            score = round(score_part_relative_to_max_freq*10,2)
            score_record[domain] = score

        return score_record

    def _calculate_trend_score(self,feature:List[str]):

        today = date.today()
        first_day_of_this_month = today.replace(day = 1)

        _, last_day_num = calendar.monthrange(today.year, today.month)
        last_day_of_this_month = today.replace(day = last_day_num)

        last_day_of_previous_month = first_day_of_this_month - timedelta(days= 1)
        first_day_of_previous_month = last_day_of_previous_month.replace(day = 1)

        current_month_data = self.fresher_data[(self.fresher_data["Scraped_At_Cleaned"] >= str(first_day_of_this_month)) & (self.fresher_data["Scraped_At_Cleaned"] <= str(last_day_of_this_month))]
        previous_month_data = self.fresher_data[(self.fresher_data["Scraped_At_Cleaned"] >= str(first_day_of_previous_month)) & (self.fresher_data["Scraped_At_Cleaned"] <= str(last_day_of_previous_month))]
         
        trend_score_record = {}
        for domain in feature:
            current_month_freq = current_month_data[current_month_data["Job_Type"] == domain].shape[0]
            previous_month_freq = previous_month_data[previous_month_data["Job_Type"] == domain].shape[0]
            if previous_month_freq == 0:
                trend_score = 10.0
            else:
                trend_change = (current_month_freq - previous_month_freq) / previous_month_freq
                trend_score = round(min(max(trend_change * 10, 0), 10),2)
            trend_score_record[domain] = trend_score
        return trend_score_record

    def _calculate_experience_flexibility_score(self,feature:List[str]):
            
        experience_score = {}
        # max_experience_frequency = data.shape[0]
        max_experience_frequency = self.data.shape[0]
        for domain in feature:
            freq=  self.fresher_data[(self.fresher_data["Job_Type"]==domain)].shape[0]
            relative_score = round((freq/max_experience_frequency)*10,2)
            experience_score[domain] =  relative_score 
        
        return experience_score
       
    def get_demand_score_report(self):
        return self.demand_sccore_report
    
    def _calculate_skill_diversity_score(self,feature:List[str]):
        skill_diversity_score = {}
        max_hiring_frequency = 0
        for domain in feature:
            frequency =  self.fresher_data[self.fresher_data["Job_Type"]==domain]["Company_Cleaned"].unique().shape[0]
            max_hiring_frequency = max(frequency, max_hiring_frequency)

        for domain in feature:
            frequency =  self.fresher_data[self.fresher_data["Job_Type"]==domain]["Company_Cleaned"].unique().shape[0]
            relative_score = round((frequency/max_hiring_frequency)*10,2)
            skill_diversity_score[domain] = relative_score
        
        return skill_diversity_score

    def _demand_score_calculator(self, feature):

        for domain in feature:
            job_demand =round(self.job_posting_frequency_score[domain]*self.weight["Job_Posting_Frequency"] ,2)
            final_trend_score = round(self.trend_score[domain]*self.weight["Trend_Direction"],2)
            final_skill_diversity_score = round(self.skill_diversity_score[domain]*self.weight["Skill_Diversity"],2)
            final_experience_flexibiity_score = round(self.experience_score[domain]*self.weight['Experience_Fleibility'],2)

            total_demand_score =round( job_demand+final_trend_score+final_experience_flexibiity_score+final_skill_diversity_score,2)

            self.demand_score[domain] = total_demand_score
            self.demand_sccore_report[domain] = {"Job Score":job_demand, "trend_score":final_trend_score,"skill_diversity_score":final_skill_diversity_score,"experience_flexibility_score":final_experience_flexibiity_score, "demand score":total_demand_score}
    


    def calculate_demand_score(self, feature: List[str]):

        # step 0 : initilizing feature 
        if feature is None:
            feature = self.fresher_data["Job_Type"].unique()
        
        # filter fresher data
        self.fresher_data = self._filter_fresher_data()
    
        # step 1: calculate job_posting_frequency score.
        self.job_posting_frequency_score = self._calculate_job_posting_frequency(feature)
        # step 2: calculate trend score.
        self.trend_score = self._calculate_trend_score(feature)
        # step 3: calculate experience_flexibility score.
        self.experience_score = self._calculate_experience_flexibility_score(feature)
        # step 4: calculate skill_diversity_score score. 
        self.skill_diversity_score = self._calculate_skill_diversity_score(feature)
        # step5: calculate demand score
        self._demand_score_calculator(feature)
        # return demand score
        return self.demand_score


if __name__ == "__main__":
  
    data = pd.read_csv(r"D:\DATA SCIENCE AND ML\Project\job_trend_predictor\data\processed\cleaned\cleaned_job_data.csv")
    feature = data["Job_Type"].unique()

    weight = {
        "Job_Posting_Frequency": 0.4,
        "Trend_Direction": 0.3,
        "Skill_Diversity":0.15,
        "Experience_Fleibility":0.15
    }
    
    DSC = DemandScoreCalculator(data,weight)
    demand_score = DSC.calculate_demand_score(feature)

    # print(f"Deamnd Score : {demand_score}")
    print(f"Deamnd Score Report : {DSC.get_demand_score_report()}")
    