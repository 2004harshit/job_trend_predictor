import re
import logging
from typing import Dict, Optional, Tuple
import pandas as pd
import numpy as np


class SalaryGrowthEngine:
    
    MIN_SAMPLES_PER_BAND = 5  # Minimum data points for reliable median
    
    # Experience bands: label → (min_exp, max_exp, years_of_experience)
    EXPERIENCE_BANDS = {
        "fresher":    (0, 1,  0.5),   # 0-1 yr → represent as 0.5yr midpoint
        "junior":     (1, 3,  2.0),   # 1-3 yr → 2yr midpoint
        "mid":        (3, 6,  4.5),   # 3-6 yr → 4.5yr midpoint
        "senior":     (6, 12, 9.0),   # 6-12 yr → 9yr midpoint
    }
    
    def __init__(self, default_projection_years: int = 3):
        if default_projection_years < 1 or default_projection_years > 10:
            raise ValueError("projection_years must be between 1 and 10.")
        self.default_projection_years = default_projection_years
        self.logger = logging.getLogger(__name__)
    
    def _validate_weights(self, weights: dict):
        total = sum(weights.values())
        if not (0.98 <= total <= 1.02):
            raise ValueError(f"Scenario weights must sum to 1.0, got {total:.3f}")
        
    def _filter_domain(self, df: pd.DataFrame, 
                        target_domain: str) -> pd.DataFrame:
        """Job_Type first, Title fallback. Never mutates input."""
        df = df.copy()  # Safe copy — never touch caller's data

        # Fix recurring typo
        if 'TItle_Cleaned' in df.columns and 'Title_Cleaned' not in df.columns:
            df = df.rename(columns={'TItle_Cleaned': 'Title_Cleaned'})

        # Priority 1: Job_Type exact match
        if 'Job_Type' in df.columns:
            exact = df[df['Job_Type'].str.lower() == target_domain.lower()]
            if len(exact) >= self.MIN_SAMPLES_PER_BAND * 2:
                return exact

        # Priority 2: Title word-boundary
        title_col = 'Title_Cleaned' if 'Title_Cleaned' in df.columns else None
        if title_col:
            pattern = r'\b' + re.escape(target_domain) + r'\b'
            return df[df[title_col].str.contains(
                pattern, case=False, na=False, regex=True
            )]

        return pd.DataFrame()

    def _preprocess_salary(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Returns clean copy with unified Salary_Mid column.
        Priority: Avg_Salary (already computed) > (Min+Max)/2 > either bound.
        Never modifies input.
        """
        df = df.copy()

        for col in ['Min_Salary', 'Max_Salary', 'Avg_Salary']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')

        # Priority 1: Use Avg_Salary if available (already cleaned in your pipeline)
        if 'Avg_Salary' in df.columns:
            df['Salary_Mid'] = df['Avg_Salary']
        else:
            df['Salary_Mid'] = np.nan

        # Fill missing with (Min+Max)/2
        if 'Min_Salary' in df.columns and 'Max_Salary' in df.columns:
            computed_mid = (df['Min_Salary'] + df['Max_Salary']) / 2
            df['Salary_Mid'] = df['Salary_Mid'].fillna(computed_mid)

        # Last resort: either bound
        if 'Min_Salary' in df.columns:
            df['Salary_Mid'] = df['Salary_Mid'].fillna(df['Min_Salary'])
        if 'Max_Salary' in df.columns:
            df['Salary_Mid'] = df['Salary_Mid'].fillna(df['Max_Salary'])

        # IQR outlier removal for salary
        valid = df.dropna(subset=['Salary_Mid'])
        if len(valid) >= 4:
            Q1 = valid['Salary_Mid'].quantile(0.25)
            Q3 = valid['Salary_Mid'].quantile(0.75)
            IQR = Q3 - Q1
            df = df[
                (df['Salary_Mid'] >= Q1 - 2.5 * IQR) &
                (df['Salary_Mid'] <= Q3 + 2.5 * IQR)
            ]

        # Full-time filter
        if 'Employment Type' in df.columns:
            full_time = df[df['Employment Type'].str.lower().str.contains(
                'full.?time|permanent', na=False, regex=True
            )]
            df = full_time if len(full_time) >= self.MIN_SAMPLES_PER_BAND else df

        return df.dropna(subset=['Salary_Mid'])

    def _cross_sectional_growth(self, domain_df: pd.DataFrame) -> dict:
        """
        Signal 1: Salary ladder across experience bands.
        Measures: "How much more does a 3-yr exp person earn vs a fresher?"

        This is NOT longitudinal — it's a market snapshot.
        But it's a reliable proxy for expected salary progression.
        """
        band_salaries = {}

        for band, (min_e, max_e, midpoint_yr) in self.EXPERIENCE_BANDS.items():
            band_df = domain_df[
                (domain_df['Min_Experience'] >= min_e) &
                (domain_df['Min_Experience'] < max_e)
            ]

            if len(band_df) >= self.MIN_SAMPLES_PER_BAND:
                band_salaries[band] = {
                    "median":   round(float(band_df['Salary_Mid'].median()), 2),
                    "p25":      round(float(band_df['Salary_Mid'].quantile(0.25)), 2),
                    "p75":      round(float(band_df['Salary_Mid'].quantile(0.75)), 2),
                    "n":        len(band_df),
                    "exp_midpoint_yr": midpoint_yr
                }
            else:
                self.logger.warning(
                    f"Band '{band}' has only {len(band_df)} samples "
                    f"(need {self.MIN_SAMPLES_PER_BAND}). Skipping."
                )

        # Calculate CAGR between consecutive bands
        band_order = ["fresher", "junior", "mid", "senior"]
        cagr_segments = {}

        for i in range(len(band_order) - 1):
            b1, b2 = band_order[i], band_order[i+1]
            if b1 in band_salaries and b2 in band_salaries:
                s1 = band_salaries[b1]["median"]
                s2 = band_salaries[b2]["median"]
                t  = band_salaries[b2]["exp_midpoint_yr"] - band_salaries[b1]["exp_midpoint_yr"]

                cagr = self._safe_cagr(s1, s2, t)
                cagr_segments[f"{b1}_to_{b2}"] = round(cagr * 100, 2)

        return {
            "band_salaries": band_salaries,
            "cagr_segments": cagr_segments,
            "data_source":   "cross_sectional"
        }

    def _time_series_growth(self, domain_df: pd.DataFrame) -> dict:
        """
        Signal 2: Actual salary trend over posting dates.
        Measures: "Are salaries being posted higher now vs 6 months ago?"

        This captures MARKET inflation, not just seniority premium.
        """
        date_col = 'Posted_Date' if 'Posted_Date' in domain_df.columns else 'Scraped_At_Cleaned'

        if date_col not in domain_df.columns:
            return {"available": False, "monthly_slope_pct": 0.0, "annualized_pct": 0.0}

        df = domain_df.copy()
        df['_date'] = pd.to_datetime(df[date_col], errors='coerce')
        df = df.dropna(subset=['_date', 'Salary_Mid'])

        if len(df) < 10:
            return {"available": False, "monthly_slope_pct": 0.0, "annualized_pct": 0.0}

        # Group by month, get median salary
        df['_month'] = df['_date'].dt.to_period('M')
        monthly = df.groupby('_month').agg(
            median_salary=('Salary_Mid', 'median'),
            count=('Salary_Mid', 'size')
        ).reset_index()

        # Need at least 3 months of data
        if len(monthly) < 3:
            return {"available": False, "monthly_slope_pct": 0.0, "annualized_pct": 0.0}

        # Weighted linear regression (weight by sample count)
        x = np.arange(len(monthly)).reshape(-1, 1)
        y = monthly['median_salary'].values
        w = monthly['count'].values.astype(float)

        # Weighted fit
        from sklearn.linear_model import LinearRegression
        model = LinearRegression().fit(x, y, sample_weight=w)

        monthly_slope = float(model.coef_[0])
        base_salary   = float(model.predict([[0]])[0])

        # R² for reliability
        y_pred = model.predict(x)
        ss_res = np.sum(w * (y - y_pred) ** 2)
        ss_tot = np.sum(w * (y - np.average(y, weights=w)) ** 2)
        r_squared = max(0.0, 1 - ss_res / ss_tot) if ss_tot > 0 else 0.0

        # Monthly slope as % of base
        monthly_slope_pct = (monthly_slope / base_salary * 100) if base_salary > 0 else 0.0
        annualized_pct    = monthly_slope_pct * 12

        return {
            "available":         True,
            "monthly_slope_pct": round(monthly_slope_pct, 3),
            "annualized_pct":    round(annualized_pct, 2),
            "r_squared":         round(r_squared, 3),
            "reliable":          r_squared >= 0.3,
            "months_analyzed":   len(monthly),
            "data_source":       "time_series"
        }

    def _safe_cagr(self, start_val: float, end_val: float, 
                    periods: float) -> float:
        """CAGR with full guard rails."""
        if start_val <= 0:
            self.logger.warning(f"CAGR: start_val={start_val} is invalid.")
            return 0.0
        if end_val <= 0:
            self.logger.warning(f"CAGR: end_val={end_val} is invalid.")
            return 0.0
        if periods <= 0:
            self.logger.warning(f"CAGR: periods={periods} must be positive.")
            return 0.0

        raw = (end_val / start_val) ** (1 / periods) - 1

        # Sanity cap: salary CAGR above 100%/yr or below -50%/yr is data error
        return float(np.clip(raw, -0.50, 1.00))

    def _build_scenarios(self, fresher_salary: float,
                          base_cagr: float,
                          time_series_data: dict,
                          projection_years: int) -> dict:
        """
        Replace magic 0.7x / 1.4x multipliers with percentile-based scenarios.

        Conservative: P25 growth (things don't go as planned)
        Expected:     Median CAGR from cross-sectional data
        Optimistic:   P75 growth + market inflation boost
        Aggressive:   Top performer + job switch premium
        """
        # Blend cross-sectional CAGR with time-series market inflation
        market_inflation = 0.0
        if time_series_data.get("available") and time_series_data.get("reliable"):
            market_inflation = time_series_data["annualized_pct"] / 100
            self.logger.info(f"Market inflation signal: {market_inflation:.2%}/yr")

        # Four scenarios with clear economic logic
        scenarios = {
            "Conservative": {
                "rate":        max(0.0, base_cagr * 0.6 + market_inflation * 0.5),
                "description": "Slow growth path — minimal skill upgrades, same company"
            },
            "Expected": {
                "rate":        base_cagr + market_inflation,
                "description": "Market-average progression with standard raises"
            },
            "Optimistic": {
                "rate":        base_cagr * 1.3 + market_inflation,
                "description": "Above-average growth — 1 job switch or strong upskilling"
            },
            "Aggressive": {
                "rate":        base_cagr * 1.7 + market_inflation,
                "description": "Top performer path — multiple switches, high-demand skills"
            }
        }

        projections = {}
        for label, config in scenarios.items():
            rate  = float(np.clip(config["rate"], -0.3, 1.5))  # Sanity bounds

            yearly_breakdown = {}
            for yr in range(1, projection_years + 1):
                future = fresher_salary * (1 + rate) ** yr
                yearly_breakdown[f"Year_{yr}"] = round(future / 100000, 2)  # Convert to LPA

            projections[label] = {
                "Annual_CAGR":        f"{round(rate * 100, 1)}%",
                "Yearly_Salary_LPA":  yearly_breakdown,
                "Final_Salary_LPA":   yearly_breakdown[f"Year_{projection_years}"],
                "Total_Growth_Pct":   round(((1 + rate) ** projection_years - 1) * 100, 1),
                "Description":        config["description"]
            }

        return projections

    def _location_adjustment(self, df: pd.DataFrame,
                               domain_df: pd.DataFrame,
                               target_location: str) -> float:
        """
        Location multiplier for salary growth rate.
        Metro cities have faster salary growth curves.
        """
        if 'Location' not in domain_df.columns or 'Avg_Salary' not in df.columns:
            return 1.0

        # Domain salary in target location
        local = domain_df[
            domain_df['Location'].str.contains(target_location, case=False, na=False)
        ]

        if len(local) < self.MIN_SAMPLES_PER_BAND:
            self.logger.warning(
                f"Insufficient local data for '{target_location}'. "
                f"Using national growth rates."
            )
            return 1.0

        national_median = domain_df['Salary_Mid'].median()
        local_median    = local['Salary_Mid'].median()

        if pd.isna(national_median) or national_median == 0:
            return 1.0

        # Locations with higher salaries tend to have faster growth too
        factor = local_median / national_median
        return float(np.clip(factor, 0.7, 1.5))

    def project_growth(self, df: pd.DataFrame,
                        target_domain: str,
                        projection_years: int = None,
                        target_location: str = None) -> dict:
        """
        Main entry point. Returns full salary growth projection.
        """
        years = projection_years or self.default_projection_years

        if years < 1 or years > 10:
            return {"error": "projection_years must be between 1 and 10."}

        # 1. Filter domain (safe copy, no mutation)
        domain_df = self._filter_domain(df, target_domain)
        if domain_df.empty:
            return {"error": f"No data found for domain: '{target_domain}'"}

        # 2. Preprocess salary (outliers removed, full-time filtered)
        domain_df = self._preprocess_salary(domain_df)
        if domain_df.empty:
            return {"error": "No valid salary data after preprocessing."}

        # 3. Cross-sectional growth (experience ladder)
        cs_data = self._cross_sectional_growth(domain_df)

        # 4. Time-series growth (market inflation signal)
        ts_data = self._time_series_growth(domain_df)

        # 5. Determine base CAGR for projections
        # Use fresher→junior CAGR as primary growth engine
        base_cagr = 0.15  # Conservative fallback: 15% CAGR

        if "fresher_to_junior" in cs_data["cagr_segments"]:
            base_cagr = cs_data["cagr_segments"]["fresher_to_junior"] / 100
        elif cs_data["band_salaries"]:
            # Use any available consecutive bands
            segments = cs_data["cagr_segments"]
            if segments:
                base_cagr = list(segments.values())[0] / 100

        # 6. Get fresher starting salary
        fresher_data = cs_data["band_salaries"].get("fresher")
        if fresher_data:
            fresher_median = fresher_data["median"]
        else:
            # Fallback: P25 of cleaned domain salary
            fresher_median = domain_df['Salary_Mid'].quantile(0.25)

        if pd.isna(fresher_median) or fresher_median <= 0:
            return {"error": "Cannot determine fresher salary baseline."}

        fresher_lpa = round(fresher_median / 100000, 2)

        # 7. Location adjustment
        loc_factor = 1.0
        if target_location:
            loc_factor = self._location_adjustment(df, domain_df, target_location)
            base_cagr *= loc_factor

        # 8. Build scenarios
        scenarios = self._build_scenarios(
            fresher_median, base_cagr, ts_data, years
        )

        # 9. Confidence assessment
        n_fresher = fresher_data["n"] if fresher_data else 0
        confidence = (
            "High"   if n_fresher >= 50 else
            "Medium" if n_fresher >= 20 else
            "Low"
        )

        return {
            "Domain":              target_domain,
            "Location":            target_location or "National",
            "Projection_Years":    years,
            "Data_Quality": {
                "Confidence":           confidence,
                "Fresher_Sample_Size":  n_fresher,
                "Time_Series_Signal":   ts_data.get("available", False),
                "TS_Reliable":          ts_data.get("reliable", False),
            },
            "Baseline": {
                "Fresher_Median_LPA":   fresher_lpa,
                "Location_Factor":      round(loc_factor, 3),
                "Base_CAGR_Pct":        round(base_cagr * 100, 2),
            },
            "Market_Inflation": {
                "Annualized_Pct":       ts_data.get("annualized_pct", 0.0),
                "Trend_R2":             ts_data.get("r_squared", 0.0),
                "Months_Analyzed":      ts_data.get("months_analyzed", 0),
            },
            "Experience_Ladder":       cs_data["band_salaries"],
            "CAGR_By_Segment":         cs_data["cagr_segments"],
            "Scenarios":               scenarios,
            "Interpretation":          self._interpret_growth(base_cagr, ts_data)
        }

    def _interpret_growth(self, base_cagr: float, 
                           ts_data: dict) -> str:
        """Plain-English summary for Real Talk Engine."""
        cagr_pct = base_cagr * 100

        if cagr_pct >= 30:
            base = "🚀 Exceptional growth trajectory — top-tier domain for salary progression."
        elif cagr_pct >= 20:
            base = "📈 Strong growth path — above-market salary acceleration expected."
        elif cagr_pct >= 12:
            base = "✅ Healthy growth — market-standard salary progression."
        elif cagr_pct >= 6:
            base = "⚖️  Modest growth — salary increases exist but are gradual."
        else:
            base = "⚠️  Slow growth — consider adjacent domains or skill upgrades for acceleration."

        if ts_data.get("available") and ts_data.get("reliable"):
            inflation = ts_data["annualized_pct"]
            if inflation > 5:
                base += f" Market is also inflating at {inflation:.1f}%/yr — good timing to enter."
            elif inflation < -2:
                base += f" ⚠️  Posted salaries are declining at {abs(inflation):.1f}%/yr — market under pressure."

        return base


if __name__ =="main":
    # Load sample data
    data_path = r"D:\DATA SCIENCE AND ML\Project\job_trend_predictor\data\processed\cleaned\cleaned_job_data.csv"
    
    df = pd.read_csv(data_path)

    sge = SalaryGrowthEngine()

    result = sge.project_growth("Data Scientist",3)
    

    print(result)

    