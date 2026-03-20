import pandas as pd
import numpy as np
import logging
from typing import Dict, List, Optional


class AverageSalaryRangeCalculator:
    
    REQUIRED_COLUMNS = ['Avg_Salary', 'Min_Experience', 'Max_Experience']
    TITLE_COLUMN = 'Title_Cleaned'  # Fixed typo from 'TItle_Cleaned'
    
    EXPERIENCE_BANDS = {
        "fresher":  (0, 1),   # True fresher: 0-1 year
        "junior":   (1, 3),   # Junior: 1-3 years  
        "mid":      (3, 6),   # Mid-level: 3-6 years
    }
    
    def __init__(self, lambda_val: float = 0.1):
        """
        lambda_val: decay rate for time weighting.
                    0.1 = 30-day-old data has ~5% less weight than today's
                    0.05 = slower decay (stable markets)
                    0.2 = aggressive decay (fast-moving markets like AI/ML)
        """
        if not 0 < lambda_val < 1:
            raise ValueError(f"lambda_val must be between 0 and 1, got {lambda_val}")
        self.lambda_val = lambda_val
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def _validate_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Validate and return a safe copy — never modify caller's data."""
        df = df.copy()  # Critical: prevent in-place modification bug
        
        missing = [c for c in self.REQUIRED_COLUMNS if c not in df.columns]
        if missing:
            raise ValueError(f"Missing required columns: {missing}")
        
        # # Fix column name typo dynamically
        # if 'TItle_Cleaned' in df.columns and 'Title_Cleaned' not in df.columns:
        #     df = df.rename(columns={'TItle_Cleaned': 'Title_Cleaned'})
        #     self.logger.warning("Auto-fixed column typo: 'TItle_Cleaned' → 'Title_Cleaned'")
        
        # Safe numeric conversion on the COPY only
        for col in ['Min_Salary', 'Max_Salary', 'Avg_Salary', 
                    'Min_Experience', 'Max_Experience']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        return df
    
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

    def _filter_employment_type(self, df: pd.DataFrame) -> pd.DataFrame:
        """Remove contract/freelance/part-time — they skew salary down artificially."""
        if 'Employment Type' not in df.columns:
            return df

        full_time_keywords = ['full time', 'full-time', 'permanent', 'regular']
        pattern = '|'.join(full_time_keywords)

        full_time = df[df['Employment Type'].str.lower().str.contains(
            pattern, na=False
        )]

        # Fallback to all if filter removes too much
        return full_time if len(full_time) >= 5 else df
    
    def _remove_salary_outliers(self, df: pd.DataFrame, 
                                 col: str = 'Avg_Salary') -> pd.DataFrame:
        """
        IQR-based outlier removal.
        Handles cases like ₹1/month test entries or ₹1Cr outliers
        that completely break percentile calculations.
        """
        if df.empty or col not in df.columns:
            return df

        valid = df.dropna(subset=[col])
        if len(valid) < 4:  # Need at least 4 points for IQR
            return valid

        Q1 = valid[col].quantile(0.25)
        Q3 = valid[col].quantile(0.75)
        IQR = Q3 - Q1

        lower = Q1 - 2.5 * IQR  # Slightly wider than standard 1.5x for salary data
        upper = Q3 + 2.5 * IQR  # Salary distributions are right-skewed naturally

        filtered = valid[(valid[col] >= lower) & (valid[col] <= upper)]

        removed = len(valid) - len(filtered)
        if removed > 0:
            self.logger.info(
                f"Outlier removal: {removed} records removed "
                f"(range kept: ₹{lower:,.0f} – ₹{upper:,.0f} LPA)"
            )

        return filtered if len(filtered) >= 5 else valid  # Safety fallback
    
    def _filter_experience_band(self, df: pd.DataFrame, 
                                band: str = "fresher") -> pd.DataFrame:
        """
        Segment by experience band instead of flat <= 2 cutoff.
        Uses BOTH Min and Max experience for accurate bracket detection.
        """
        if band not in self.EXPERIENCE_BANDS:
            raise ValueError(f"Invalid band '{band}'. Choose from: {list(self.EXPERIENCE_BANDS.keys())}")

        min_exp, max_exp = self.EXPERIENCE_BANDS[band]

        band_df = df[
            (df['Min_Experience'] >= min_exp) & 
            (df['Max_Experience'] <= max_exp + 1) &  # +1 tolerance for "0-3 yrs" style
            (df['Min_Experience'].notna()) &
            (df['Max_Experience'].notna())
        ]

        # Graceful fallback chain
        if len(band_df) < 5:
            self.logger.warning(
                f"Band '{band}' has only {len(band_df)} records. "
                f"Expanding to include adjacent experience levels."
            )
            # Expand filter slightly
            band_df = df[df['Min_Experience'] <= max_exp + 2]

        return band_df
    
    def _apply_time_decay(self, df: pd.DataFrame) -> pd.DataFrame:
        """Apply exponential time decay. Newer postings get higher weight."""
        if 'Scraped_At_Cleaned' not in df.columns:
            df['_weight'] = 1.0
            return df

        df = df.copy()
        df['Scraped_At_Cleaned'] = pd.to_datetime(df['Scraped_At_Cleaned'], errors='coerce')

        max_date = df['Scraped_At_Cleaned'].max()
        if pd.isna(max_date):
            df['_weight'] = 1.0
            return df

        df['_months_old'] = (
            (max_date - df['Scraped_At_Cleaned']).dt.days / 30.0
        ).clip(lower=0).fillna(6.0)  # Unknown date → treat as 6 months old

        df['_weight'] = np.exp(-self.lambda_val * df['_months_old'])
        return df

    def _weighted_percentile(self, series: pd.Series, 
                              weights: pd.Series, 
                              percentile: float) -> float:
        """
        Robust weighted percentile with edge case handling.
        percentile: value between 0 and 1 (e.g., 0.25 for P25)
        """
        valid_mask = series.notna() & weights.notna() & (weights > 0)
        data = series[valid_mask]
        w = weights[valid_mask]

        if data.empty:
            return np.nan
        if len(data) == 1:
            return float(data.iloc[0])

        ix = np.argsort(data.values)
        data_sorted = data.values[ix]
        w_sorted = w.values[ix]

        cumulative = np.cumsum(w_sorted)
        total = cumulative[-1]

        if total == 0:
            return np.nan

        # Normalized CDF
        cdf = (cumulative - w_sorted / 2) / total  # Midpoint convention

        return float(np.interp(percentile, cdf, data_sorted))

    def _calculate_location_factor(self, df: pd.DataFrame,
                                    domain_df: pd.DataFrame,
                                    target_location: str) -> float:
        """
        Location factor = local domain median / national domain median.
        Both numerator and denominator are DOMAIN-SPECIFIC.

        """
        # National median for THIS domain only
        national_median = domain_df['Avg_Salary'].median()

        if pd.isna(national_median) or national_median == 0:
            return 1.0  # Neutral factor — no adjustment

        # Local data for THIS domain in target location
        local_domain = domain_df[
            domain_df['Location'].str.contains(
                target_location, case=False, na=False
            )
        ]

        if len(local_domain) < 3:  # Not enough local data
            self.logger.warning(
                f"Insufficient local data for '{target_location}' "
                f"({len(local_domain)} records). Using national figures."
            )
            return 1.0

        local_median = local_domain['Avg_Salary'].median()

        if pd.isna(local_median):
            return 1.0

        factor = local_median / national_median

        # Sanity cap: location shouldn't multiply salary by more than 2x or less than 0.5x
        factor = np.clip(factor, 0.5, 2.0)
        self.logger.info(f"Location factor for '{target_location}': {factor:.3f}")

        return float(factor)

    def _calculate_confidence_interval(self, median: float, 
                                        n_samples: int,
                                        std: float) -> Dict:
        """
        Statistically grounded CI using standard error.
        Previous: hardcoded ±15% regardless of data quality.
        Now: wider CI for small samples, tighter for large ones.
        """
        if pd.isna(median) or median == 0 or n_samples < 2:
            return {"Min": np.nan, "Max": np.nan, "Confidence": "Very Low"}

        # Standard error of median ≈ 1.253 * std / sqrt(n)
        se = 1.253 * std / np.sqrt(n_samples)

        # 90% confidence interval (z=1.645)
        margin = 1.645 * se

        # Cap margin at 40% of median for reasonableness
        margin = min(margin, median * 0.40)

        confidence_label = (
            "High" if n_samples >= 50 else
            "Medium" if n_samples >= 20 else
            "Low"
        )

        return {
            "Min": round(max(0, median - margin), 2),
            "Max": round(median + margin, 2),
            "Confidence": confidence_label,
            "Sample_Size": n_samples
        }

    def calculate_salary_metrics(self, df: pd.DataFrame,
                                  target_domain: str,
                                  target_location: str = None,
                                  experience_band = "fresher") -> Dict:
        # 1. Validate & get safe copy
        df = self._validate_dataframe(df)

        # Normalise experience_band — pipeline passes Tuple[int,int], standalone callers
        # pass a string like "fresher". Handle both so the method is call-site agnostic.
        TUPLE_TO_BAND = {v: k for k, v in self.EXPERIENCE_BANDS.items()}
        if isinstance(experience_band, (tuple, list)):
            band_tuple = tuple(experience_band)
            # Map back to a label for output/logging; fall back to a range string
            experience_band = TUPLE_TO_BAND.get(band_tuple, f"{band_tuple[0]}-{band_tuple[1]}yr")
        else:
            band_tuple = self.EXPERIENCE_BANDS.get(experience_band, (0, 10))

        # 2. Filter domain — resolve band to tuple for _filter_domain
        domain_df = self._filter_domain(df, target_domain, band_tuple)
        if domain_df.empty:
            return {"error": f"No data found for domain: '{target_domain}'"}

        # 3. Filter full-time only
        domain_df = self._filter_employment_type(domain_df)

        # 4. Filter experience band
        band_df = self._filter_experience_band(domain_df, experience_band)
        if band_df.empty:
            return {"error": f"No {experience_band} data for domain: '{target_domain}'"}

        # 5. Remove outliers
        band_df = self._remove_salary_outliers(band_df)
        if band_df.empty:
            return {"error": "All salary data removed as outliers — check data quality."}

        # 6. Apply time decay
        band_df = self._apply_time_decay(band_df)

        # 7. Compute weighted percentiles
        p10 = self._weighted_percentile(band_df['Avg_Salary'], band_df['_weight'], 0.10)
        p25 = self._weighted_percentile(band_df['Avg_Salary'], band_df['_weight'], 0.25)
        p50 = self._weighted_percentile(band_df['Avg_Salary'], band_df['_weight'], 0.50)
        p75 = self._weighted_percentile(band_df['Avg_Salary'], band_df['_weight'], 0.75)
        p90 = self._weighted_percentile(band_df['Avg_Salary'], band_df['_weight'], 0.90)

        # 8. Location adjustment (domain-specific fix)
        loc_factor = 1.0
        if target_location:
            loc_factor = self._calculate_location_factor(df, domain_df, target_location)

        adjusted_p50 = round(p50 * loc_factor, 2) if not pd.isna(p50) else np.nan

        # 9. Confidence interval (statistically grounded)
        std = band_df['Avg_Salary'].std()
        ci = self._calculate_confidence_interval(adjusted_p50, len(band_df), std)

        # 10. Min/Max salary range from raw Min_Salary/Max_Salary columns
        raw_min = band_df['Min_Salary'].quantile(0.25) if 'Min_Salary' in band_df else np.nan
        raw_max = band_df['Max_Salary'].quantile(0.75) if 'Max_Salary' in band_df else np.nan

        return {
            "Domain":           target_domain,
            "Experience_Band":  experience_band,
            "Location":         target_location or "National",
            "Location_Factor":  round(loc_factor, 3),
            "Sample_Size":      len(band_df),

            "Market_Range": {
                "Entry_10th":    round(p10, 2) if not pd.isna(p10) else None,
                "Low_25th":      round(p25, 2) if not pd.isna(p25) else None,
                "Median_50th":   round(p50, 2) if not pd.isna(p50) else None,
                "High_75th":     round(p75, 2) if not pd.isna(p75) else None,
                "Top_90th":      round(p90, 2) if not pd.isna(p90) else None,
            },

            "Raw_Salary_Band": {
                "Typical_Min":   round(raw_min, 2) if not pd.isna(raw_min) else None,
                "Typical_Max":   round(raw_max, 2) if not pd.isna(raw_max) else None,
            },

            "Location_Adjusted_Median": adjusted_p50,
            "Confidence_Interval": ci,

            "Interpretation": self._interpret_salary(adjusted_p50, experience_band)
        }

    def _interpret_salary(self, median: float, band: str) -> str:
        """Plain-English label for the UI / Real Talk engine."""
        if pd.isna(median):
            return "Insufficient data to assess."
        if band == "fresher":
            if median >= 10: return "🔥 Above-market entry salary — high-value domain"
            elif median >= 6: return "✅ Market-standard fresher salary"
            elif median >= 4: return "⚠️  Below-average — negotiate or upskill first"
            else:             return "🚨 Very low — verify data or consider alternatives"
        return f"Median salary: ₹{median:.1f} LPA"
    

if __name__ == "__main__":    # Example usage
   
    calculator = AverageSalaryRangeCalculator(lambda_val=0.1)

    # Load data (example with CSV)
    df = pd.read_csv(r"D:\DATA SCIENCE AND ML\Project\job_trend_predictor\data\processed\cleaned\cleaned_job_data.csv")

    result = calculator.calculate_salary_metrics(
        df=df,
        target_domain="Data Analyst",
        # target_location="Bangalore",
        experience_band="junior"
    )

    print(result)