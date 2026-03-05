import logging
import pandas as pd
import numpy as np
from typing import Dict, List, Optional


class CompetitionLevelCalculator:
    
    REQUIRED_COLUMNS = ['Skill_Count', 'Min_Experience']
    APPLICANT_COL = 'No of applicant applied cleaned'
    OPENINGS_COL  = 'No of job opening cleaned '   # note trailing space in your data
    
    # Dynamic thresholds — percentile-based, not hardcoded
    COMPETITION_PERCENTILES = {
        "Very Low":  20,   # Bottom 20% of all domains
        "Low":       40,
        "Medium":    60,
        "High":      80,
        "Very High": 100   # Top 20%
    }
    
    # How many days back to consider a listing "active"
    ACTIVE_LISTING_DAYS = 60
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._market_index_cache = {}  # Cache computed market ratios


    def _filter_active_listings(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Only count listings posted/scraped within ACTIVE_LISTING_DAYS.
        Prevents 6-month-old listings inflating 'available positions'.
        """
        date_col = None
        for col in ['Posted_Date', 'Scraped_At_Cleaned']:
            if col in df.columns:
                date_col = col
                break
            
        if date_col is None:
            self.logger.warning("No date column found. Using all listings as active.")
            return df

        df = df.copy()
        df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
        cutoff = pd.Timestamp.now() - pd.Timedelta(days=self.ACTIVE_LISTING_DAYS)

        active = df[df[date_col] >= cutoff]

        if len(active) < 10:
            self.logger.warning(
                f"Only {len(active)} active listings in last {self.ACTIVE_LISTING_DAYS} days. "
                f"Expanding window to 120 days."
            )
            cutoff = pd.Timestamp.now() - pd.Timedelta(days=120)
            active = df[df[date_col] >= cutoff]

        return active

    def _filter_domain(self , df, target_domain, experience_band):
        # 1. Job_Type exact match — fastest, most accurate
        if 'Job_Type' in df.columns:
            result = df[df['Job_Type'].str.lower() == target_domain.lower()]
            result = result[(result["Min_Experience"]>= experience_band[0]) & (result["Max_Experience"]<=experience_band[1])]
            
            if len(result) >= 5:
                return result

        # 2. Title_Cleaned fallback
        title_col = 'Title_Cleaned' if 'Title_Cleaned' in df.columns else None
        if title_col:
            result = df[df[title_col].str.contains(target_domain, case=False, na=False)]
            if not result.empty:
                return result.copy()

        return pd.DataFrame()

    def _calculate_supply_demand(self, domain_df: pd.DataFrame) -> dict:
        """
        Supply  = Total applicants across all domain listings (actual or estimated)
        Demand  = Total actual job openings (not listing count)

        This is the core fix: 1 listing with 50 openings ≠ 50 listings.
        """
        # --- DEMAND: Actual openings ---
        if self.OPENINGS_COL in domain_df.columns:
            openings_series = pd.to_numeric(
                domain_df[self.OPENINGS_COL], errors='coerce'
            ).fillna(1)  # Each listing = at least 1 opening
            total_openings = max(int(openings_series.sum()), 1)
            used_actual_openings = True
        else:
            # Fallback: each listing = 1 opening
            total_openings = max(len(domain_df), 1)
            used_actual_openings = False

        # --- SUPPLY: Actual applicants ---
        if self.APPLICANT_COL in domain_df.columns:
            applicants_series = pd.to_numeric(
                domain_df[self.APPLICANT_COL], errors='coerce'
            )

            # Remove outlier applicant counts (viral listings distort market)
            q95 = applicants_series.quantile(0.95)
            applicants_series = applicants_series.clip(upper=q95)

            total_applicants = int(applicants_series.sum())
            used_actual_applicants = True
        else:
            # No applicant data — use domain-aware estimation
            # Estimation based on typical Indian job market ratios
            # (these are ranges, not hardcoded single values)
            domain_lower = self.target_domain.lower() if hasattr(self, '_current_domain') else ''

            DOMAIN_RATIO_RANGES = {
                'data scientist':    (20, 40),
                'ml engineer':       (15, 30),
                'web developer':     (30, 60),
                'software engineer': (25, 50),
                'devops':            (10, 20),
                'cybersecurity':     (8, 15),
            }

            ratio_range = DOMAIN_RATIO_RANGES.get(domain_lower, (15, 35))
            # Use midpoint with a note that this is estimated
            estimated_ratio = np.mean(ratio_range)
            total_applicants = int(total_openings * estimated_ratio)
            used_actual_applicants = False

        return {
            "total_openings":          total_openings,
            "total_applicants":        total_applicants,
            "used_actual_openings":    used_actual_openings,
            "used_actual_applicants":  used_actual_applicants,
            "listing_count":           len(domain_df)
        }

    def _calculate_skill_overlap(self, domain_df: pd.DataFrame,
                                   user_skills: list = None) -> dict:
        """
        Two distinct overlap calculations:
        1. Market Overlap: How hard is it for a TYPICAL candidate?
        2. User Overlap: How hard is it for THIS specific user?
        """
        if 'Skill_Count' not in domain_df.columns:
            return {
                "avg_required_skills": 0,
                "market_overlap_factor": 0.5,
                "user_overlap_factor": 0.5,
                "user_match_pct": None,
                "missing_star_skills": []
            }

        avg_required = domain_df['Skill_Count'].median()  # median > mean for skewed data

        # --- Market-level overlap ---
        # Typical Indian fresher knows ~6-8 skills (based on your Naukri dataset context)
        TYPICAL_SEEKER_SKILLS = 7
        market_overlap = np.clip(TYPICAL_SEEKER_SKILLS / max(avg_required, 1), 0.1, 1.0)

        # --- User-level overlap ---
        if user_skills is not None and len(user_skills) > 0:

            # Quantitative match: skill count ratio
            count_match = min(1.0, len(user_skills) / max(avg_required, 1))

            # Qualitative match: do user's skills appear in job requirements?
            qual_match = 0.5  # Default if no skill text available
            missing_star = []

            if 'Combined_Skills' in domain_df.columns:
                # Aggregate all required skills from postings
                all_skills_text = ' '.join(
                    domain_df['Combined_Skills'].dropna().str.lower().tolist()
                )
                user_skills_lower = [s.lower().strip() for s in user_skills]

                # Count how many user skills appear in market requirements
                matched = sum(1 for s in user_skills_lower if s in all_skills_text)
                qual_match = matched / max(len(user_skills_lower), 1)

            if 'Star_Skills' in domain_df.columns:
                # Star skills = must-have skills. Missing these hurts most.
                star_text = ' '.join(
                    domain_df['Star_Skills'].dropna().str.lower().tolist()
                )
                # Find unique star skills
                star_tokens = set(star_text.split(','))
                star_tokens = {s.strip() for s in star_tokens if len(s.strip()) > 2}

                user_lower = {s.lower().strip() for s in user_skills}
                missing_star = list(star_tokens - user_lower)[:5]  # Top 5 missing

            # Combined: 60% count match, 40% qualitative match
            user_overlap = 0.6 * count_match + 0.4 * qual_match
            user_match_pct = round(user_overlap * 100, 1)

        else:
            user_overlap = market_overlap
            user_match_pct = None
            missing_star = []

        return {
            "avg_required_skills":   round(avg_required, 1),
            "market_overlap_factor": round(market_overlap, 3),
            "user_overlap_factor":   round(user_overlap, 3),
            "user_match_pct":        user_match_pct,
            "missing_star_skills":   missing_star
        }


    def _build_market_baseline(self, df: pd.DataFrame,
                                experience_band: tuple = (0, 3)) -> pd.Series:
        """
        Compute applicant/opening ratios for ALL domains.
        Used to set dynamic thresholds — not hardcoded <5, 5-15, >15.

        A ratio of 16 in cybersecurity might be "Low" relative to 
        web dev's ratio of 80.
        """
        if 'Job_Type' not in df.columns:
            return pd.Series(dtype=float)

        ratios = {}
        active_df = self._filter_active_listings(df)

        # Apply experience filter
        if 'Min_Experience' in active_df.columns:
            active_df = active_df[active_df['Min_Experience'] <= experience_band[1] + 1]

        for domain in active_df['Job_Type'].dropna().unique():
            domain_slice = active_df[active_df['Job_Type'] == domain]
            if len(domain_slice) < 5:
                continue
            
            sd = self._calculate_supply_demand(domain_slice)
            ratio = sd['total_applicants'] / sd['total_openings']
            ratios[domain] = ratio

        return pd.Series(ratios)

    def _classify_competition(self, ratio: float, 
                               market_ratios: pd.Series) -> str:
        """
        Dynamic classification using market percentiles.
        If market_ratios is empty, fall back to absolute thresholds.
        """
        if market_ratios.empty:
            # Absolute fallback thresholds
            if ratio < 5:   return "Very Low"
            elif ratio < 15: return "Low"
            elif ratio < 30: return "Medium"
            elif ratio < 60: return "High"
            else:            return "Very High"

        percentile = (market_ratios < ratio).mean() * 100

        if percentile < 20:   return "Very Low"
        elif percentile < 40: return "Low"
        elif percentile < 60: return "Medium"
        elif percentile < 80: return "High"
        else:                 return "Very High"

    def calculate_competition_level(self, df: pd.DataFrame,
                                     target_domain: str,
                                     user_skills: list = None,
                                     experience_band: tuple = (0, 3),
                                     location: str = None) -> dict:
        self._current_domain = target_domain  # For proxy fallback reference

        # 1. Validate columns
        for col in self.REQUIRED_COLUMNS:
            if col not in df.columns:
                self.logger.warning(f"Missing column: {col}. Results may be approximate.")

        # 2. Filter active listings only
        active_df = self._filter_active_listings(df)

        # 3. Filter domain + experience band
        domain_df = self._filter_domain(
            active_df, target_domain, experience_band
        )

        if domain_df.empty:
            return {"error": f"No active listings found for '{target_domain}' "
                             f"in experience band {experience_band}"}

        # 4. Optional location filter
        if location and 'Location' in domain_df.columns:
            loc_df = domain_df[
                domain_df['Location'].str.contains(location, case=False, na=False)
            ]
            if len(loc_df) >= 5:
                domain_df = loc_df
                self.logger.info(f"Location filter applied: {location} → {len(domain_df)} records")
            else:
                self.logger.warning(f"Insufficient data for location '{location}'. Using national data.")

        # 5. Supply/Demand calculation
        sd = self._calculate_supply_demand(domain_df)

        # 6. Skill overlap
        skill_data = self._calculate_skill_overlap(domain_df, user_skills)

        # 7. Competition Index (using actual competition_index for classification)
        raw_ratio = sd['total_applicants'] / sd['total_openings']

        competition_index = (
            sd['total_applicants'] * skill_data['market_overlap_factor']
        ) / sd['total_openings']

        # User-adjusted index: if user has better skills, their EFFECTIVE competition is lower
        if user_skills:
            user_advantage = skill_data['user_overlap_factor'] / max(
                skill_data['market_overlap_factor'], 0.01
            )
            # Higher user overlap vs market = lower effective competition for them
            user_competition_index = competition_index / max(user_advantage, 0.1)
        else:
            user_competition_index = competition_index

        # 8. Dynamic classification
        market_ratios = self._build_market_baseline(df, experience_band)
        competition_level = self._classify_competition(raw_ratio, market_ratios)
        user_level = self._classify_competition(
            user_competition_index / max(skill_data['market_overlap_factor'], 0.01),
            market_ratios
        ) if user_skills else competition_level

        # 9. Data quality flag
        data_quality = "Actual" if (
            sd['used_actual_applicants'] and sd['used_actual_openings']
        ) else "Estimated"

        return {
            "Domain":           target_domain,
            "Experience_Band":  experience_band,
            "Location":         location or "National",
            "Data_Quality":     data_quality,

            "Market_Competition": {
                "Level":             competition_level,
                "Competition_Index": round(competition_index, 2),
                "Candidates_Per_Job": round(raw_ratio, 1),
                "Listing_Count":     sd['listing_count'],
            },

            "Your_Competition": {
                "Level":             user_level,
                "Your_Skill_Match":  skill_data['user_match_pct'],
                "Missing_Star_Skills": skill_data['missing_star_skills'],
                "Effective_Index":   round(user_competition_index, 2),
            } if user_skills else None,

            "Skill_Insights": {
                "Avg_Skills_Required": skill_data['avg_required_skills'],
                "Market_Avg_Match_Pct": round(
                    skill_data['market_overlap_factor'] * 100, 1
                ),
            },

            "Raw_Numbers": {
                "Total_Applicants": sd['total_applicants'],
                "Total_Openings":   sd['total_openings'],
            },

            "Interpretation": self._interpret_competition(
                competition_level, user_level, 
                skill_data['missing_star_skills'], user_skills
            )
        }

    def _interpret_competition(self, market_level: str, user_level: str,
                                 missing_skills: list, user_skills) -> str:
        """Plain-English for the Real Talk Engine."""
        base = {
            "Very Low":  "🟢 Excellent opportunity — very few candidates per opening.",
            "Low":       "✅ Favorable market — your odds are good.",
            "Medium":    "⚖️  Competitive — skills differentiation is key.",
            "High":      "🔴 Tough market — you need strong projects + network.",
            "Very High": "🚨 Saturated — seriously consider adjacent roles."
        }.get(market_level, "")

        if user_skills and user_level != market_level:
            base += f" Your skills put you at '{user_level}' level personally."

        if missing_skills:
            base += f" Gap: learn {', '.join(missing_skills[:3])} to improve your odds."

        return base
    
if __name__ == "__main__":

    df = pd.read_csv(r"D:\DATA SCIENCE AND ML\Project\job_trend_predictor\data\processed\cleaned\cleaned_job_data.csv")
    calculator = CompetitionLevelCalculator()
    result = calculator.calculate_competition_level(
        df, target_domain="Data Scientist", user_skills=["Python", "SQL", "Machine Learning"]
    )
    import json
    print(json.dumps(result, indent=4))