""" Demand Score Calculator for Job Market Analysis. """
import pandas as pd
import numpy as np
from typing import Dict, List
from datetime import datetime, timedelta
import calendar

class MarketDemandEngine:

    def __init__(self, data: pd.DataFrame, weights: Dict = None):
        self._validate_required_columns(data)
        self.data = data.copy()
        
        default_weights = {
            "Job_Posting_Frequency": 0.30,
            "Trend_Direction": 0.30,
            "Applicant_Demand_Ratio": 0.25,
            "Skill_Diversity": 0.15,
        }
        self.weights = weights or default_weights
        self._validate_weights()
        
        # Safe date parsing - Added dayfirst=True to help infer format and avoid warnings
        self.data['timestamp'] = pd.to_datetime(
            self.data['timestamp'], errors='coerce', dayfirst=True
        )
        self.data['posted_timestamp'] = pd.to_datetime(
            self.data['posted_timestamp'], errors='coerce', dayfirst=True
        )
        
        # Initialize the report dictionary
        self.demand_report = {}

    def _validate_required_columns(self, df):
        required = ['title', 'timestamp', 'min_experience', 'company']
        missing = [c for c in required if c not in df.columns]
        if missing:
            raise ValueError(f"Missing required columns: {missing}")

    def _validate_weights(self):
        total = sum(self.weights.values())
        if not (0.98 <= total <= 1.02):
            raise ValueError(f"Weights must sum to 1.0, got {total:.3f}")
   
    MIN_SAMPLE_THRESHOLD = 30

    def _filter_fresher_data(self, df):
        return df[
            (df["min_experience"] >= 0) & 
            (df["max_experience"] <= 5) &
            (df["min_experience"].notna()) &
            (df["max_experience"].notna())
        ]

    def _get_valid_domains(self, fresher_df, domains):
        counts = fresher_df["title"].value_counts()
        if domains is None:
            domains = counts.index.tolist()

        valid = [d for d in domains if counts.get(d, 0) >= self.MIN_SAMPLE_THRESHOLD]
        skipped = [d for d in domains if d not in valid]

        if skipped:
            print(f"⚠️  Skipped (insufficient data < {self.MIN_SAMPLE_THRESHOLD} jobs): {skipped}")
        return valid, counts
    
    def _calculate_frequency_score(self, fresher_df, domain, max_freq):
        domain_df = fresher_df[fresher_df["title"] == domain].copy()
        if domain_df.empty:
            return 0.0

        today = pd.Timestamp.now()
        domain_df = domain_df.dropna(subset=['timestamp'])
        domain_df['days_ago'] = (today - domain_df['timestamp']).dt.days.clip(lower=0)
        domain_df['decay_weight'] = np.exp(-0.693 * domain_df['days_ago'] / 30)

        weighted_freq = domain_df['decay_weight'].sum()
        return min((weighted_freq / max_freq) * 10, 10.0)
    
    def _calculate_trend_score(self, fresher_df, domain, first_this, first_prev, last_prev):
        curr_df = fresher_df[
            (fresher_df["title"] == domain) &
            (fresher_df["timestamp"] >= first_this)
        ]
        prev_df = fresher_df[
            (fresher_df["title"] == domain) &
            (fresher_df["timestamp"] >= first_prev) &
            (fresher_df["timestamp"] <= last_prev)
        ]

        c_count = curr_df.shape[0]
        p_count = prev_df.shape[0]

        if p_count < 5 and c_count < 5:
            return 5.0

        if p_count == 0:
            return 6.5

        growth_ratio = c_count / p_count
        damped_growth = np.log2(growth_ratio + 1e-9)
        score = np.clip(5 + (damped_growth * 2.5), 0, 10)
        return round(score, 2)
    
    def _calculate_applicant_demand_ratio(self, fresher_df, domain):
        domain_df = fresher_df[fresher_df["title"] == domain].copy()
        has_applicants = 'no_of_applicant' in domain_df.columns
        has_openings = 'no_of_opening' in domain_df.columns

        if not has_applicants or not has_openings:
            return 5.0

        domain_df = domain_df.dropna(
            subset=['no_of_applicant', 'no_of_opening']
        )

        if domain_df.empty:
            return 5.0

        total_applicants = domain_df['no_of_applicant'].sum()
        total_openings = domain_df['no_of_opening'].sum()

        if total_openings == 0:
            return 5.0

        ratio = total_applicants / total_openings
        score = np.clip(10 - (np.log10(ratio + 1) * 4), 0, 10)
        return round(score, 2)
    
    def _calculate_diversity_score(self, fresher_df, domain):
        domain_cos = fresher_df[fresher_df["title"] == domain]["company"].nunique()
        total_cos = fresher_df["company"].nunique()

        if total_cos == 0:
            return 0.0

        score = (np.log1p(domain_cos) / np.log1p(total_cos)) * 10
        return round(min(score, 10.0), 2)
    
    def calculate_metrics(self, domains: List[str] = None) -> Dict:
        fresher_df = self._filter_fresher_data(self.data)

        if fresher_df.empty:
            raise ValueError("No fresher-level data found after filtering.")

        valid_domains, counts = self._get_valid_domains(fresher_df, domains)
        first_this, last_prev, first_prev = self._get_time_metrics()

        # Pre-compute decay weights for all valid domains for normalization
        # We need to compute decay_weight before finding the max_freq
        today = pd.Timestamp.now()
        fresher_df = fresher_df.copy()
        fresher_df['days_ago'] = (today - fresher_df['timestamp']).dt.days.clip(lower=0)
        fresher_df['decay_weight'] = np.exp(-0.693 * fresher_df['days_ago'] / 30)

        max_freq = max(
            fresher_df[fresher_df["title"] == d]['decay_weight'].sum()
            for d in valid_domains
        ) or 1

        for domain in valid_domains:
            score_freq = self._calculate_frequency_score(fresher_df, domain, max_freq)
            score_trend = self._calculate_trend_score(
                fresher_df, domain, first_this, first_prev, last_prev
            )
            score_adr = self._calculate_applicant_demand_ratio(fresher_df, domain)
            score_diversity = self._calculate_diversity_score(fresher_df, domain)

            total_domain = self.data[self.data["title"] == domain].shape[0]
            fresher_count = fresher_df[fresher_df["title"] == domain].shape[0]
            score_flex = round((fresher_count / total_domain * 10) if total_domain > 0 else 0, 2)

            weighted_score = (
                score_freq      * self.weights.get("Job_Posting_Frequency", 0.30) +
                score_trend     * self.weights.get("Trend_Direction", 0.25) +
                score_adr       * self.weights.get("Applicant_Demand_Ratio", 0.20) +
                score_diversity * self.weights.get("Skill_Diversity", 0.15) +
                score_flex      * self.weights.get("Experience_Flexibility", 0.10)
            )

            self.demand_report[domain] = {
                "Overall_Demand_Score": round(weighted_score, 2),
                "Score_Label": self._label_score(weighted_score),
                "Breakdown": {
                    "Volume":           score_freq,
                    "Growth_Trend":        score_trend,
                    "Applicant_Ratio":     score_adr,
                    "Market_Diversity":    score_diversity,
                    "Entry_Flexibility":   score_flex
                },
                "Raw_Counts": {
                    "Fresher_Jobs": fresher_count,
                    "Total_Domain_Jobs": total_domain
                }
            }

        return self.demand_report
    
    def _get_time_metrics(self):
        today = pd.Timestamp.now().normalize()
        first_this = today - pd.Timedelta(days=30)
        last_prev = first_this - pd.Timedelta(days=1)
        first_prev = last_prev - pd.Timedelta(days=30)
        return first_this, last_prev, first_prev
    
    def _label_score(self, score: float) -> str:
        if score >= 8.0: return "🔥 High Demand"
        elif score >= 6.0: return "📈 Growing"
        elif score >= 4.0: return "⚖️  Stable"
        elif score >= 2.0: return "📉 Declining"
        else: return "🧊 Very Low Demand"

if __name__ == "__main__":
    # Ensure your CSV path is correct
    try:
        df = pd.read_csv(r"D:\DATA SCIENCE AND ML\Project\job_trend_predictor\data\processed\cleaned\cleaned_data.csv")
        engine = MarketDemandEngine(df)
       
        report = engine.calculate_metrics()
        import json
        print(json.dumps(report, indent=4))
    except Exception as e:
        print(f"Error: {e}")