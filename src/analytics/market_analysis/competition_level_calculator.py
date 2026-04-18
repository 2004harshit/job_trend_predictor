import re
import ast
import logging
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple


def parse_skills_column(raw) -> List[str]:
    if raw is None or (isinstance(raw, float) and pd.isna(raw)):
        return []
    raw = str(raw).strip()
    if not raw:
        return []
    if raw.startswith('['):
        try:
            parsed = ast.literal_eval(raw)
            if isinstance(parsed, list):
                return [re.sub(r'\s+', ' ', str(s).strip().lower())
                        for s in parsed if str(s).strip()]
        except (ValueError, SyntaxError):
            pass
    return [re.sub(r"['\"\\[\\]]", '', s).strip().lower()
            for s in raw.split(',')
            if re.sub(r"['\"\\[\\]]", '', s).strip()]


def skills_to_text(series: pd.Series) -> str:
    tokens = []
    for raw in series.dropna():
        tokens.extend(parse_skills_column(raw))
    return ' '.join(tokens)


class CompetitionLevelCalculator:

    REQUIRED_COLUMNS = ['skill_count', 'min_experience']
    APPLICANT_COL = 'no_of_applicant'
    OPENINGS_COL  = 'no_of_opening'

    COMPETITION_PERCENTILES = {
        "Very Low":  20, "Low": 40, "Medium": 60, "High": 80, "Very High": 100
    }

    ACTIVE_LISTING_DAYS = 365

    DOMAIN_RATIO_RANGES: Dict[str, Tuple[int, int]] = {
        "data scientist":               (35, 70),
        "machine learning engineer":    (25, 50),
        "data analyst":                 (40, 80),
        "business analyst":             (30, 60),
        "ai engineer":                  (20, 45),
        "research associate":           (25, 55),
        "data engineer":                (20, 40),
        "web developer":                (35, 65),
        "software engineer":            (30, 60),
        "devops engineer":              (10, 25),
        "product manager":              (40, 80),
        "project manager":              (30, 60),
        "ux designer":                  (20, 45),
        "full stack developer":         (30, 65),
        "cloud engineer":               (12, 28),
        "devops specialist":            (8, 20),
        "database administrator":       (15, 35),
        "cybersecurity analyst":        (8, 18),
        "network engineer":             (15, 35),
        "systems analyst":              (20, 40),
        "it support specialist":        (25, 50),
        "mobile app developer":         (20, 45),
        "front end developer":          (30, 60),
        "back end developer":           (20, 45),
        "qa engineer":                  (15, 35),
        "technical writer":             (12, 28),
        "scrum master":                 (15, 30),
        "python developer":             (35, 70),
        "java developer":               (25, 55),
        "ruby on rails developer":      (5, 15),
    }

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._market_index_cache = {}
        self._current_domain = ""

    _DATE_COLUMN_CANDIDATES = [
        'posted_date', 'timestamp', 'posting_date', 'date',
        'job_posted_date', 'scraped_date', 'created_at',
    ]

    def _find_date_column(self, df: pd.DataFrame) -> Optional[str]:
        for col in self._DATE_COLUMN_CANDIDATES:
            if col in df.columns:
                return col
        for col in df.columns:
            col_lower = col.lower()
            if 'date' in col_lower or 'scraped' in col_lower or 'posted' in col_lower:
                self.logger.info(f"Auto-detected date column: '{col}'")
                return col
        return None

    def _filter_active_listings(self, df: pd.DataFrame) -> pd.DataFrame:
        date_col = self._find_date_column(df)
        if date_col is None:
            self.logger.warning("No date column found. All listings treated as active.")
            return df

        df = df.copy()
        df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
        cutoff = pd.Timestamp.now() - pd.Timedelta(days=self.ACTIVE_LISTING_DAYS)
        active = df[df[date_col] >= cutoff]

        if len(active) < 10:
            cutoff = pd.Timestamp.now() - pd.Timedelta(days=730)
            active = df[df[date_col] >= cutoff]

        if len(active) < 10:
            return df

        return active

    def _filter_domain(self, df: pd.DataFrame,
                       target_domain: str,
                       experience_band: Tuple[int, int]) -> pd.DataFrame:
        domain_df = pd.DataFrame()

        if 'title' in df.columns:
            domain_df = df[df['title'].str.lower() == target_domain.lower()].copy()

        if len(domain_df) < 5:
            title_col = next(
                (c for c in ['title'] if c in df.columns), None
            )
            if title_col:
                fallback = df[df[title_col].str.contains(
                    target_domain, case=False, na=False
                )].copy()
                if len(fallback) > len(domain_df):
                    domain_df = fallback

        if domain_df.empty:
            return pd.DataFrame()

        band_min, band_max = experience_band
        if 'min_experience' in domain_df.columns:
            min_exp = pd.to_numeric(domain_df['min_experience'], errors='coerce').fillna(0)
            if 'max_experience' in domain_df.columns:
                max_exp = pd.to_numeric(domain_df['max_experience'], errors='coerce')
                mask = (min_exp <= band_max) & (max_exp.isna() | (max_exp >= band_min))
            else:
                mask = min_exp <= band_max

            filtered = domain_df[mask]
            if len(filtered) < 5:
                relaxed_mask = (min_exp <= band_max + 3)
                filtered = domain_df[relaxed_mask]
            domain_df = filtered

        return domain_df

    def _calculate_supply_demand(self, domain_df: pd.DataFrame) -> dict:
        if self.OPENINGS_COL in domain_df.columns:
            openings_series = pd.to_numeric(
                domain_df[self.OPENINGS_COL], errors='coerce'
            ).fillna(1)
            total_openings = max(int(openings_series.sum()), 1)
            used_actual_openings = True
        else:
            total_openings = max(len(domain_df), 1)
            used_actual_openings = False

        if self.APPLICANT_COL in domain_df.columns:
            applicants_series = pd.to_numeric(
                domain_df[self.APPLICANT_COL], errors='coerce'
            )
            q95 = applicants_series.quantile(0.95)
            applicants_series = applicants_series.clip(upper=q95)
            total_applicants = int(applicants_series.sum())
            used_actual_applicants = True
        else:
            domain_key = self._current_domain.lower().strip()
            ratio_range = self.DOMAIN_RATIO_RANGES.get(domain_key, (15, 35))
            estimated_ratio = float(np.mean(ratio_range))
            total_applicants = int(total_openings * estimated_ratio)
            used_actual_applicants = False

        return {
            "total_openings":         total_openings,
            "total_applicants":       total_applicants,
            "used_actual_openings":   used_actual_openings,
            "used_actual_applicants": used_actual_applicants,
            "listing_count":          len(domain_df)
        }

    def _calculate_skill_overlap(self, domain_df: pd.DataFrame,
                                  user_skills: list = None) -> dict:
        if 'skill_count' not in domain_df.columns:
            return {
                "avg_required_skills":   0,
                "market_overlap_factor": 0.5,
                "user_overlap_factor":   0.5,
                "user_match_pct":        None,
                "missing_star_skills":   []
            }

        avg_required = domain_df['skill_count'].median()
        TYPICAL_SEEKER_SKILLS = 7
        market_overlap = np.clip(TYPICAL_SEEKER_SKILLS / max(avg_required, 1), 0.1, 1.0)

        if user_skills is not None and len(user_skills) > 0:
            count_match = min(1.0, len(user_skills) / max(avg_required, 1))
            qual_match  = 0.5
            missing_star = []

            # ── Use 'skills' column — parse and flatten ───────────────
            if 'skills' in domain_df.columns:
                all_skills_text = skills_to_text(domain_df['skills'])
                user_skills_lower = [s.lower().strip() for s in user_skills]
                matched = sum(1 for s in user_skills_lower if s in all_skills_text)
                qual_match = matched / max(len(user_skills_lower), 1)

                # Missing skills: top skills from domain not in user_skills
                all_domain_skills = []
                for raw in domain_df['skills'].dropna():
                    all_domain_skills.extend(parse_skills_column(raw))

                from collections import Counter
                top_domain = [s for s, _ in Counter(all_domain_skills).most_common(20)]
                user_lower_set = {s.lower().strip() for s in user_skills}
                missing_star = [s for s in top_domain if s not in user_lower_set][:5]
            # ──────────────────────────────────────────────────────────

            user_overlap   = 0.6 * count_match + 0.4 * qual_match
            user_match_pct = round(user_overlap * 100, 1)
        else:
            user_overlap   = market_overlap
            user_match_pct = None
            missing_star   = []

        return {
            "avg_required_skills":   round(avg_required, 1),
            "market_overlap_factor": round(market_overlap, 3),
            "user_overlap_factor":   round(user_overlap, 3),
            "user_match_pct":        user_match_pct,
            "missing_star_skills":   missing_star
        }

    def _build_market_baseline(self, df: pd.DataFrame,
                                experience_band: tuple = (0, 3)) -> pd.Series:
        if 'title' not in df.columns:
            return pd.Series(dtype=float)

        ratios = {}
        active_df = self._filter_active_listings(df)

        if 'min_experience' in active_df.columns:
            min_exp = pd.to_numeric(active_df['min_experience'], errors='coerce').fillna(0)
            active_df = active_df[min_exp <= experience_band[1] + 3]

        for domain in active_df['title'].dropna().unique():
            domain_slice = active_df[active_df['title'] == domain]
            if len(domain_slice) < 5:
                continue
            sd = self._calculate_supply_demand(domain_slice)
            ratio = sd['total_applicants'] / sd['total_openings']
            ratios[domain] = ratio

        return pd.Series(ratios)

    def _classify_competition(self, ratio: float, market_ratios: pd.Series) -> str:
        if market_ratios.empty:
            if ratio < 5:    return "Very Low"
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
        self._current_domain = target_domain

        for col in self.REQUIRED_COLUMNS:
            if col not in df.columns:
                self.logger.warning(f"Missing column: {col}. Results may be approximate.")

        active_df = self._filter_active_listings(df)
        domain_df = self._filter_domain(active_df, target_domain, experience_band)

        if domain_df.empty:
            return {
                "error": (
                    f"No listings found for '{target_domain}' in experience band "
                    f"{experience_band}. "
                    f"Available titles: "
                    f"{list(df['title'].dropna().unique()[:10]) if 'title' in df.columns else 'N/A'}"
                )
            }

        if location and 'location' in domain_df.columns:
            loc_df = domain_df[
                domain_df['location'].str.contains(location, case=False, na=False)
            ]
            if len(loc_df) >= 5:
                domain_df = loc_df

        sd         = self._calculate_supply_demand(domain_df)
        skill_data = self._calculate_skill_overlap(domain_df, user_skills)

        raw_ratio = sd['total_applicants'] / sd['total_openings']
        competition_index = (
            sd['total_applicants'] * skill_data['market_overlap_factor']
        ) / sd['total_openings']

        if user_skills:
            user_advantage = skill_data['user_overlap_factor'] / max(
                skill_data['market_overlap_factor'], 0.01
            )
            user_competition_index = competition_index / max(user_advantage, 0.1)
        else:
            user_competition_index = competition_index

        market_ratios     = self._build_market_baseline(df, experience_band)
        competition_level = self._classify_competition(raw_ratio, market_ratios)
        user_level = self._classify_competition(
            user_competition_index / max(skill_data['market_overlap_factor'], 0.01),
            market_ratios
        ) if user_skills else competition_level

        data_quality = "Actual" if (
            sd['used_actual_applicants'] and sd['used_actual_openings']
        ) else "Estimated"

        return {
            "Domain":           target_domain,
            "Experience_Band":  experience_band,
            "Location":         location or "National",
            "Data_Quality":     data_quality,

            "Market_Competition": {
                "Level":              competition_level,
                "Competition_Index":  round(competition_index, 2),
                "Candidates_Per_Job": round(raw_ratio, 1),
                "Listing_Count":      sd['listing_count'],
            },

            "Your_Competition": {
                "Level":               user_level,
                "Your_Skill_Match":    skill_data['user_match_pct'],
                "Missing_Star_Skills": skill_data['missing_star_skills'],
                "Effective_Index":     round(user_competition_index, 2),
            } if user_skills else None,

            "Skill_Insights": {
                "Avg_Skills_Required":  skill_data['avg_required_skills'],
                "Market_Avg_Match_Pct": round(skill_data['market_overlap_factor'] * 100, 1),
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
        base = {
            "Very Low":  " Excellent opportunity — very few candidates per opening.",
            "Low":       " Favorable market — your odds are good.",
            "Medium":    " Competitive — skills differentiation is key.",
            "High":      " Tough market — you need strong projects + network.",
            "Very High": " Saturated — seriously consider adjacent roles."
        }.get(market_level, "")

        if user_skills and user_level != market_level:
            base += f" Your skills put you at '{user_level}' level personally."

        if missing_skills:
            base += f" Gap: learn {', '.join(missing_skills[:3])} to improve your odds."

        return base


if __name__ == "__main__":
    import json
    df = pd.read_csv(
        r"D:\DATA SCIENCE AND ML\Project\job_trend_predictor\data\processed\cleaned\cleaned_job_data.csv"
    )
    calculator = CompetitionLevelCalculator()
    result = calculator.calculate_competition_level(
        df, target_domain="Data Analyst",
        user_skills=["Python", "SQL"],
        experience_band=(0, 3)
    )
    print(json.dumps(result, indent=4))