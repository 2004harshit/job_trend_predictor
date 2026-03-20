import logging
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple


class CompetitionLevelCalculator:

    REQUIRED_COLUMNS = ['Skill_Count', 'Min_Experience']
    APPLICANT_COL = 'No of applicant applied cleaned'
    OPENINGS_COL  = 'No of job opening cleaned '   # note trailing space in source data

    # Dynamic thresholds — percentile-based, not hardcoded
    COMPETITION_PERCENTILES = {
        "Very Low":  20,
        "Low":       40,
        "Medium":    60,
        "High":      80,
        "Very High": 100
    }

    ACTIVE_LISTING_DAYS = 365

    # ── All 30 roles from job_queue, grouped by typical Indian market competition ──
    # Ranges represent (min_applicants_per_opening, max_applicants_per_opening)
    # Based on Naukri/LinkedIn India market data patterns
    DOMAIN_RATIO_RANGES: Dict[str, Tuple[int, int]] = {
        # Group 1 — High demand, high supply (very saturated)
        "data scientist":               (35, 70),
        "machine learning engineer":    (25, 50),
        "data analyst":                 (40, 80),

        # Group 2 — Moderate-high competition
        "business analyst":             (30, 60),
        "ai engineer":                  (20, 45),
        "research associate":           (25, 55),

        # Group 3 — High volume roles
        "data engineer":                (20, 40),
        "web developer":                (35, 65),
        "software engineer":            (30, 60),

        # Group 4 — Mixed; PM roles get more applicants than DevOps
        "devops engineer":              (10, 25),
        "product manager":              (40, 80),
        "project manager":              (30, 60),

        # Group 5 — Varied; UX is niche, Full Stack is crowded
        "ux designer":                  (20, 45),
        "full stack developer":         (30, 65),
        "cloud engineer":               (12, 28),

        # Group 6 — Specialist roles, lower but growing competition
        "devops specialist":            (8, 20),
        "database administrator":       (15, 35),
        "cybersecurity analyst":        (8, 18),

        # Group 7 — Infrastructure / support, moderate applicants
        "network engineer":             (15, 35),
        "systems analyst":              (20, 40),
        "it support specialist":        (25, 50),

        # Group 8 — Mobile & frontend/backend splits
        "mobile app developer":         (20, 45),
        "front end developer":          (30, 60),
        "back end developer":           (20, 45),

        # Group 9 — QA/Scrum/Writing — moderate to low competition
        "qa engineer":                  (15, 35),
        "technical writer":             (12, 28),
        "scrum master":                 (15, 30),

        # Group 10 — Language-specific; Python saturated, Ruby niche
        "python developer":             (35, 70),
        "java developer":               (25, 55),
        "ruby on rails developer":      (5, 15),
    }

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._market_index_cache = {}
        self._current_domain = ""

    # ─────────────────────────────────────────────────────────────
    # BUG FIX 1: Robust date column detection
    # ─────────────────────────────────────────────────────────────
    _DATE_COLUMN_CANDIDATES = [
        'Posted_Date', 'Scraped_At_Cleaned', 'Scraped_At',
        'posting_date', 'date', 'Date', 'Job_Posted_Date',
        'scraped_date', 'created_at', 'CreatedAt',
    ]

    def _find_date_column(self, df: pd.DataFrame) -> Optional[str]:
        """
        Try known names first, then fall back to any column whose
        name contains 'date' or 'scraped' (case-insensitive).
        """
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
        """
        Only count listings posted/scraped within ACTIVE_LISTING_DAYS.
        Falls back gracefully if no date column is found.
        """
        date_col = self._find_date_column(df)

        if date_col is None:
            self.logger.warning(
                "No date column found. All listings treated as active. "
                f"Columns available: {list(df.columns)}"
            )
            return df

        df = df.copy()
        df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
        cutoff = pd.Timestamp.now() - pd.Timedelta(days=self.ACTIVE_LISTING_DAYS)

        active = df[df[date_col] >= cutoff]
        self.logger.info(
            f"Date filter on '{date_col}': {len(active)}/{len(df)} listings "
            f"active within {self.ACTIVE_LISTING_DAYS} days."
        )

        if len(active) < 10:
            self.logger.warning(
                f"Only {len(active)} active listings in last {self.ACTIVE_LISTING_DAYS} days. "
                f"Expanding window to 730 days."
            )
            cutoff = pd.Timestamp.now() - pd.Timedelta(days=730)
            active = df[df[date_col] >= cutoff]

        # If still empty after expansion, return all rows with a clear warning
        if len(active) < 10:
            self.logger.warning(
                f"Still only {len(active)} listings after expanding to 730 days. "
                f"This dataset may be old — using ALL listings."
            )
            return df

        return active

    # ─────────────────────────────────────────────────────────────
    # BUG FIX 2: Robust experience band filtering
    # ─────────────────────────────────────────────────────────────
    def _filter_domain(self, df: pd.DataFrame,
                        target_domain: str,
                        experience_band: Tuple[int, int]) -> pd.DataFrame:
        """
        Filter by domain first, then by experience band.

        Experience logic (fixed):
          A listing is relevant if the user's MIN experience fits within
          the posting's range — not if the posting's MAX fits the band.
          A listing requiring 3–8 years IS relevant for a 5-year candidate.

          Rule: listing.Min_Experience <= band_max
                AND (listing.Max_Experience >= band_min OR Max_Experience is NaN)
        """
        # ── Step 1: Domain filter ──
        domain_df = pd.DataFrame()

        if 'Job_Type' in df.columns:
            domain_df = df[df['Job_Type'].str.lower() == target_domain.lower()].copy()

        if len(domain_df) < 5:
            title_col = next(
                (c for c in ['Title_Cleaned', 'Job Title', 'title', 'Title'] if c in df.columns),
                None
            )
            if title_col:
                fallback = df[df[title_col].str.contains(
                    target_domain, case=False, na=False
                )].copy()
                if len(fallback) > len(domain_df):
                    domain_df = fallback
                    self.logger.info(
                        f"Job_Type exact match gave <5 rows; "
                        f"used title fallback → {len(domain_df)} records."
                    )

        if domain_df.empty:
            return pd.DataFrame()

        # ── Step 2: Experience filter (FIXED) ──
        band_min, band_max = experience_band

        if 'Min_Experience' in domain_df.columns:
            min_exp = pd.to_numeric(domain_df['Min_Experience'], errors='coerce').fillna(0)

            if 'Max_Experience' in domain_df.columns:
                max_exp = pd.to_numeric(domain_df['Max_Experience'], errors='coerce')
                # NaN max_experience means "open-ended" → treat as matching any band_min
                mask = (
                    (min_exp <= band_max) &
                    (max_exp.isna() | (max_exp >= band_min))
                )
            else:
                # No Max_Experience column — only filter by min
                mask = min_exp <= band_max

            filtered = domain_df[mask]

            # Graceful degradation: if filter is too tight, relax it
            if len(filtered) < 5:
                self.logger.warning(
                    f"Experience filter ({band_min}-{band_max} yrs) left only "
                    f"{len(filtered)} records for '{target_domain}'. "
                    f"Relaxing to ±3 years."
                )
                relaxed_mask = (min_exp <= band_max + 3)
                filtered = domain_df[relaxed_mask]

            domain_df = filtered

        return domain_df

    def _calculate_supply_demand(self, domain_df: pd.DataFrame) -> dict:
        """
        Supply  = Total applicants across all domain listings
        Demand  = Total actual job openings
        """
        # --- DEMAND ---
        if self.OPENINGS_COL in domain_df.columns:
            openings_series = pd.to_numeric(
                domain_df[self.OPENINGS_COL], errors='coerce'
            ).fillna(1)
            total_openings = max(int(openings_series.sum()), 1)
            used_actual_openings = True
        else:
            total_openings = max(len(domain_df), 1)
            used_actual_openings = False

        # --- SUPPLY ---
        if self.APPLICANT_COL in domain_df.columns:
            applicants_series = pd.to_numeric(
                domain_df[self.APPLICANT_COL], errors='coerce'
            )
            q95 = applicants_series.quantile(0.95)
            applicants_series = applicants_series.clip(upper=q95)
            total_applicants = int(applicants_series.sum())
            used_actual_applicants = True
        else:
            # Estimation from DOMAIN_RATIO_RANGES
            domain_key = self._current_domain.lower().strip()
            ratio_range = self.DOMAIN_RATIO_RANGES.get(domain_key, (15, 35))
            estimated_ratio = float(np.mean(ratio_range))
            total_applicants = int(total_openings * estimated_ratio)
            used_actual_applicants = False
            self.logger.info(
                f"No applicant data. Estimated ratio {estimated_ratio:.1f}x "
                f"for '{self._current_domain}' from DOMAIN_RATIO_RANGES."
            )

        return {
            "total_openings":         total_openings,
            "total_applicants":       total_applicants,
            "used_actual_openings":   used_actual_openings,
            "used_actual_applicants": used_actual_applicants,
            "listing_count":          len(domain_df)
        }

    def _calculate_skill_overlap(self, domain_df: pd.DataFrame,
                                   user_skills: list = None) -> dict:
        if 'Skill_Count' not in domain_df.columns:
            return {
                "avg_required_skills":   0,
                "market_overlap_factor": 0.5,
                "user_overlap_factor":   0.5,
                "user_match_pct":        None,
                "missing_star_skills":   []
            }

        avg_required = domain_df['Skill_Count'].median()
        TYPICAL_SEEKER_SKILLS = 7
        market_overlap = np.clip(TYPICAL_SEEKER_SKILLS / max(avg_required, 1), 0.1, 1.0)

        if user_skills is not None and len(user_skills) > 0:
            count_match = min(1.0, len(user_skills) / max(avg_required, 1))
            qual_match = 0.5
            missing_star = []

            if 'Combined_Skills' in domain_df.columns:
                all_skills_text = ' '.join(
                    domain_df['Combined_Skills'].dropna().str.lower().tolist()
                )
                user_skills_lower = [s.lower().strip() for s in user_skills]
                matched = sum(1 for s in user_skills_lower if s in all_skills_text)
                qual_match = matched / max(len(user_skills_lower), 1)

            if 'Star_Skills' in domain_df.columns:
                star_text = ' '.join(
                    domain_df['Star_Skills'].dropna().str.lower().tolist()
                )
                star_tokens = {s.strip() for s in star_text.split(',') if len(s.strip()) > 2}
                user_lower = {s.lower().strip() for s in user_skills}
                missing_star = list(star_tokens - user_lower)[:5]

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
        if 'Job_Type' not in df.columns:
            return pd.Series(dtype=float)

        ratios = {}
        active_df = self._filter_active_listings(df)

        if 'Min_Experience' in active_df.columns:
            min_exp = pd.to_numeric(active_df['Min_Experience'], errors='coerce').fillna(0)
            active_df = active_df[min_exp <= experience_band[1] + 3]

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

        # 1. Active listings
        active_df = self._filter_active_listings(df)

        # 2. Domain + experience filter
        domain_df = self._filter_domain(active_df, target_domain, experience_band)

        if domain_df.empty:
            return {
                "error": (
                    f"No listings found for '{target_domain}' in experience band "
                    f"{experience_band}. "
                    f"Available Job_Types: "
                    f"{list(df['Job_Type'].dropna().unique()[:10]) if 'Job_Type' in df.columns else 'N/A'}"
                )
            }

        # 3. Location filter
        if location and 'Location' in domain_df.columns:
            loc_df = domain_df[
                domain_df['Location'].str.contains(location, case=False, na=False)
            ]
            if len(loc_df) >= 5:
                domain_df = loc_df
                self.logger.info(f"Location filter '{location}' → {len(domain_df)} records.")
            else:
                self.logger.warning(
                    f"Insufficient data for location '{location}' "
                    f"({len(loc_df)} records). Using national data."
                )

        # 4. Supply / Demand
        sd = self._calculate_supply_demand(domain_df)

        # 5. Skill overlap
        skill_data = self._calculate_skill_overlap(domain_df, user_skills)

        # 6. Competition index
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

        # 7. Dynamic classification
        market_ratios = self._build_market_baseline(df, experience_band)
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
    import json

    df = pd.read_csv(
        r"D:\DATA SCIENCE AND ML\Project\job_trend_predictor\data\processed\cleaned\cleaned_job_data.csv"
    )

    # Quick debug: show date columns and sample Job_Types
    print("=== Columns:", list(df.columns))
    print("=== Date-like columns:",
          [c for c in df.columns if any(k in c.lower() for k in ['date', 'scraped', 'posted'])])
    if 'Job_Type' in df.columns:
        print("=== Sample Job_Types:", df['Job_Type'].dropna().unique()[:15].tolist())

    calculator = CompetitionLevelCalculator()
    result = calculator.calculate_competition_level(
        df,
        target_domain="Data Analyst",
        user_skills=["Python", "SQL"],
        experience_band=(5, 20)
    )
    print(json.dumps(result, indent=4))