import pandas as pd
from typing import List  , Dict
import logging
import re
import numpy as np
from sklearn.linear_model import LinearRegression 

class SaturationRiskIndicator:
    
    MIN_SAMPLES = 10  # Minimum listings for reliable saturation signal
    MAX_SD_RATIO = 50  # Saturation ceiling: 50 applicants/opening = fully saturated
    
    def __init__(self, weights: dict = None):
        default_weights = {
            "supply_demand":      0.35,  # Applicant/Opening ratio (biggest signal)
            "trend_slope":        0.25,  # Growth/decline trajectory
            "experience_barrier": 0.15,  # Rising exp requirements = crowding out freshers
            "salary_compression": 0.15,  # Flat salary = employer power = oversupply
            "skill_inflation":    0.10   # NEW: More skills required = more competition
        }
        self.weights = weights or default_weights
        self._validate_weights()
        self.logger = logging.getLogger(__name__)
    
    def _validate_weights(self):
        total = sum(self.weights.values())
        if not (0.98 <= total <= 1.02):
            raise ValueError(
                f"Weights must sum to 1.0, got {total:.3f}. "
                f"Current weights: {self.weights}"
            )
        
    def _filter_domain(self, df, target_domain, experience_band):
        # 1. title exact match — fastest, most accurate
        if 'title' in df.columns:
            result = df[df['title'].str.lower() == target_domain.lower()]
            result = result[(result["min_experience"]>= experience_band[0]) & (result["max_experience"]<=experience_band[1])]
            
            if len(result) >= 5:
                return result

    def _factor_supply_demand(self, domain_df: pd.DataFrame,
                               all_df: pd.DataFrame) -> dict:
        """
        The biggest fix: replace sd_ratio = 15/1 with actual data.

        Saturation = applicants per opening.
        Normalized against market-wide distribution (not arbitrary 20:1 ceiling).
        """
        APPLICANT_COL = 'no_of_applicant'
        OPENINGS_COL  = 'no_of_opening'

        has_applicants = APPLICANT_COL in domain_df.columns
        has_openings   = OPENINGS_COL in domain_df.columns

        # --- Domain ratio ---
        if has_applicants and has_openings:
            applicants = pd.to_numeric(
                domain_df[APPLICANT_COL], errors='coerce'
            ).clip(upper=domain_df[APPLICANT_COL].quantile(0.95))  # Remove viral outliers

            openings = pd.to_numeric(
                domain_df[OPENINGS_COL], errors='coerce'
            ).fillna(1)

            total_apps  = applicants.sum()
            total_opens = max(openings.sum(), 1)
            domain_ratio = total_apps / total_opens
            data_quality = "Actual"

        else:
            # Estimation: use listing count as proxy
            domain_ratio = len(domain_df) * 15  # Conservative estimate
            total_opens  = len(domain_df)
            data_quality = "Estimated"

        # --- Market-wide normalization ---
        # Get ratios for all domains to normalize dynamically
        if has_applicants and has_openings and 'title' in all_df.columns:
            market_ratios = []
            for d in all_df['title'].dropna().unique():
                d_slice = all_df[all_df['title'] == d]
                if len(d_slice) < 5:
                    continue
                d_apps  = pd.to_numeric(d_slice[APPLICANT_COL], errors='coerce').sum()
                d_opens = max(pd.to_numeric(d_slice[OPENINGS_COL], errors='coerce').fillna(1).sum(), 1)
                market_ratios.append(d_apps / d_opens)

            if market_ratios:
                # Percentile rank in market (0 = least saturated, 1 = most)
                f1_score = float(np.mean([r < domain_ratio for r in market_ratios]))
            else:
                f1_score = min(1.0, domain_ratio / self.MAX_SD_RATIO)
        else:
            f1_score = min(1.0, domain_ratio / self.MAX_SD_RATIO)

        return {
            "score":        round(f1_score, 3),
            "ratio":        round(domain_ratio, 1),
            "total_openings": int(total_opens),
            "data_quality": data_quality
        }

    def _calculate_slope(self, domain_df: pd.DataFrame) -> dict:
        """
        Returns gradient slope score with proper normalization.
        Fixed: no longer mutates input. No longer binary.
        """
        df = domain_df.copy()  # Never mutate input

        date_col = 'posted_date' if 'posted_date' in df.columns else 'timestamp'
        df['_date'] = pd.to_datetime(df[date_col], errors='coerce')
        df = df.dropna(subset=['_date'])

        if len(df) < self.MIN_SAMPLES:
            return {"score": 0.5, "slope": 0.0, "r_squared": 0.0, "reliable": False}

        # Group by month
        df['_month'] = df['_date'].dt.to_period('M')
        monthly = df.groupby('_month').size().reset_index(name='count')

        if len(monthly) < 3:
            return {"score": 0.5, "slope": 0.0, "r_squared": 0.0, "reliable": False}

        x = np.arange(len(monthly)).reshape(-1, 1)
        y = monthly['count'].values.astype(float)

        model = LinearRegression().fit(x, y)
        raw_slope = float(model.coef_[0])

        # R² tells us how reliable the trend is
        y_pred = model.predict(x)
        ss_res = np.sum((y - y_pred) ** 2)
        ss_tot = np.sum((y - y.mean()) ** 2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0

        # Normalize slope as % of mean monthly count
        mean_count = y.mean()
        normalized_slope = (raw_slope / mean_count) if mean_count > 0 else 0.0

        # Score: negative slope → high risk (1.0), positive → low risk (0.0)
        # Sigmoid-like mapping for gradient (not binary)
        # normalized_slope of -0.5 = severe decline = score ~0.9
        # normalized_slope of +0.5 = strong growth = score ~0.1
        f2_score = 1 / (1 + np.exp(5 * normalized_slope))  # Sigmoid centered at 0

        # If R² is low, trend is unreliable — pull score toward neutral (0.5)
        reliability_weight = min(1.0, r_squared * 2)  # Full weight at R²=0.5
        f2_score = f2_score * reliability_weight + 0.5 * (1 - reliability_weight)

        return {
            "score":      round(float(f2_score), 3),
            "slope":      round(raw_slope, 3),
            "norm_slope": round(normalized_slope, 3),
            "r_squared":  round(float(r_squared), 3),
            "reliable":   r_squared >= 0.3,
            "months_analyzed": len(monthly)
        }

    def _factor_trend(self, slope_data: dict) -> float:
        """Extract the final trend factor score."""
        return slope_data["score"]

    def _factor_experience_barrier(self, domain_df: pd.DataFrame,
                                     all_df: pd.DataFrame) -> dict:
        """
        Experience barrier = how hard is entry for freshers?

        Fixes:
        1. Median instead of mean (robust to outliers)
        2. Domain-relative normalization (not arbitrary /10)
        3. Experience inflation trend (is it getting harder over time?)
        """
        if 'min_experience' not in domain_df.columns:
            return {"score": 0.5, "median_exp": None, "trend": "Unknown"}

        domain_exp = pd.to_numeric(
            domain_df['min_experience'], errors='coerce'
        ).dropna()

        if domain_exp.empty:
            return {"score": 0.5, "median_exp": None, "trend": "Unknown"}

        median_exp = domain_exp.median()

        # Market-relative normalization
        if 'min_experience' in all_df.columns and 'title' in all_df.columns:
            market_medians = all_df.groupby('title')['min_experience'].median().dropna()
            if not market_medians.empty:
                # Percentile rank: what fraction of domains require less experience?
                f3_score = float((market_medians < median_exp).mean())
            else:
                f3_score = min(1.0, median_exp / 8)  # Fallback: 8yr = fully saturated
        else:
            f3_score = min(1.0, median_exp / 8)

        # Experience inflation: is the bar rising over time?
        trend = "Stable"
        if 'timestamp' in domain_df.columns and len(domain_df) >= 20:
            df_t = domain_df.copy()
            df_t['_date'] = pd.to_datetime(df_t['timestamp'], errors='coerce')
            df_t = df_t.dropna(subset=['_date', 'min_experience'])

            if len(df_t) >= 10:
                # Split into first half and second half
                df_t = df_t.sort_values('_date')
                mid = len(df_t) // 2
                old_median = df_t.iloc[:mid]['min_experience'].median()
                new_median = df_t.iloc[mid:]['min_experience'].median()

                if new_median > old_median + 0.5:
                    trend = "Rising"   # Experience bar getting higher
                    f3_score = min(1.0, f3_score + 0.1)  # Penalty
                elif new_median < old_median - 0.5:
                    trend = "Falling"  # Market becoming more accessible
                    f3_score = max(0.0, f3_score - 0.1)  # Bonus

        return {
            "score":       round(f3_score, 3),
            "median_exp":  round(median_exp, 1),
            "exp_trend":   trend,
            "fresher_pct": round(
                float((domain_df['min_experience'] <= 1).mean() * 100), 1
            ) if 'min_experience' in domain_df else None
        }

    def _factor_salary_compression(self, domain_df: pd.DataFrame,
                                     all_df: pd.DataFrame) -> dict:
        """
        Salary compression = employer power = oversupply of candidates.

        Fixes:
        1. Per-row gap calculation (not mean(max) - mean(min))
        2. Market-relative normalization (not hardcoded ₹1L threshold)
        3. Salary growth trend as additional signal
        """
        if 'min_salary' not in domain_df.columns or 'max_salary' not in domain_df.columns:
            # Fallback: use avg_salary std if available
            if 'avg_salary' in domain_df.columns:
                avg_sal = pd.to_numeric(domain_df['avg_salary'], errors='coerce').dropna()
                if avg_sal.empty:
                    return {"score": 0.5, "compression_ratio": None}
                cv = avg_sal.std() / avg_sal.mean() if avg_sal.mean() > 0 else 0
                # Low CV = compressed salaries = saturation signal
                f4_score = max(0.0, 1 - cv * 2)
                return {"score": round(f4_score, 3), "compression_ratio": round(cv, 3)}
            return {"score": 0.5, "compression_ratio": None}

        df = domain_df.copy()
        df['min_salary'] = pd.to_numeric(df['min_salary'], errors='coerce')
        df['max_salary'] = pd.to_numeric(df['max_salary'], errors='coerce')

        valid = df.dropna(subset=['min_salary', 'max_salary'])
        valid = valid[valid['max_salary'] > valid['min_salary']]

        if valid.empty:
            return {"score": 0.5, "compression_ratio": None}

        # CORRECT: per-row gap, then aggregate
        valid['_gap'] = valid['max_salary'] - valid['min_salary']
        valid['_mid'] = (valid['max_salary'] + valid['min_salary']) / 2

        # Compression ratio: gap as % of midpoint (normalized for salary level)
        valid['_compression'] = valid['_gap'] / valid['_mid'].replace(0, np.nan)
        domain_compression = valid['_compression'].median()

        # Market-relative normalization
        if 'min_salary' in all_df.columns and 'max_salary' in all_df.columns:
            all_valid = all_df.copy()
            all_valid['min_salary'] = pd.to_numeric(all_valid['min_salary'], errors='coerce')
            all_valid['max_salary'] = pd.to_numeric(all_valid['max_salary'], errors='coerce')
            all_valid = all_valid.dropna(subset=['min_salary', 'max_salary'])
            all_valid = all_valid[all_valid['max_salary'] > all_valid['min_salary']]

            if not all_valid.empty:
                all_valid['_comp'] = (
                    (all_valid['max_salary'] - all_valid['min_salary']) /
                    ((all_valid['max_salary'] + all_valid['min_salary']) / 2)
                )
                market_compressions = all_valid.groupby('title')['_comp'].median() if 'title' in all_valid else pd.Series()

                if not market_compressions.empty:
                    # Lower compression than market = more saturation (employers pay less spread)
                    f4_score = float((market_compressions > domain_compression).mean())
                else:
                    f4_score = max(0.0, 1 - domain_compression)
            else:
                f4_score = max(0.0, 1 - domain_compression)
        else:
            f4_score = max(0.0, 1 - domain_compression)

        return {
            "score":             round(f4_score, 3),
            "compression_ratio": round(domain_compression, 3),
            "median_gap_lpa":    round(valid['_gap'].median(), 2),
            "interpretation":    "Compressed" if f4_score > 0.6 else "Normal" if f4_score > 0.3 else "Healthy spread"
        }

    def _factor_skill_inflation(self, domain_df: pd.DataFrame,
                                  all_df: pd.DataFrame) -> dict:
        """
        Skill inflation = employers demanding more skills over time = market oversupply.
        When companies can be picky, they ask for more.

        Signal: if avg Skill_Count is rising over time → saturation pressure increasing.
        """
        if 'skill_count' not in domain_df.columns:
            return {"score": 0.5, "avg_skills": None, "trend": "Unknown"}

        domain_df = domain_df.copy()
        domain_df['skill_count'] = pd.to_numeric(domain_df['skill_count'], errors='coerce')

        valid = domain_df.dropna(subset=['skill_count'])
        if valid.empty:
            return {"score": 0.5, "avg_skills": None, "trend": "Unknown"}

        domain_median_skills = valid['skill_count'].median()

        # Market-relative: what percentile is this domain's skill demand?
        if 'skill_count' in all_df.columns and 'title' in all_df.columns:
            market_skills = all_df.groupby('title')['skill_count'].median().dropna()
            if not market_skills.empty:
                f5_score = float((market_skills < domain_median_skills).mean())
            else:
                f5_score = min(1.0, domain_median_skills / 15)
        else:
            f5_score = min(1.0, domain_median_skills / 15)

        # Skill inflation trend
        trend = "Stable"
        if 'timestamp' in valid.columns and len(valid) >= 20:
            valid['_date'] = pd.to_datetime(valid['timestamp'], errors='coerce')
            valid = valid.sort_values('_date').dropna(subset=['_date'])
            mid = len(valid) // 2
            old_skills = valid.iloc[:mid]['skill_count'].median()
            new_skills = valid.iloc[mid:]['skill_count'].median()

            if new_skills > old_skills + 1:
                trend = "Inflating"  # Employers want more skills — oversupply condition
                f5_score = min(1.0, f5_score + 0.1)
            elif new_skills < old_skills - 1:
                trend = "Deflating"  # Market becoming less demanding
                f5_score = max(0.0, f5_score - 0.05)

        return {
            "score":          round(f5_score, 3),
            "median_skills":  round(domain_median_skills, 1),
            "skill_trend":    trend,
            "market_percentile": round(f5_score * 100, 1)
        }

    def get_saturation_risk(self, df: pd.DataFrame, 
                             target_domain: str) -> dict:
        # 1. Validate & filter
        if len(df) < self.MIN_SAMPLES:
            return {"error": f"Dataset too small: {len(df)} records."}

        domain_df = self._filter_domain(df, target_domain, experience_band=(0, 10))

        if domain_df.empty:
            return {"error": f"No data found for domain: '{target_domain}'"}

        if len(domain_df) < self.MIN_SAMPLES:
            return {
                "error": f"Insufficient data: only {len(domain_df)} listings for '{target_domain}'. "
                         f"Need {self.MIN_SAMPLES}+."
            }

        # 2. Calculate all factors
        f1 = self._factor_supply_demand(domain_df, df)
        slope_data = self._calculate_slope(domain_df)
        f2_score = self._factor_trend(slope_data)
        f3 = self._factor_experience_barrier(domain_df, df)
        f4 = self._factor_salary_compression(domain_df, df)
        f5 = self._factor_skill_inflation(domain_df, df)

        # 3. Weighted composite score
        score = (
            f1["score"]   * self.weights["supply_demand"]      +
            f2_score      * self.weights["trend_slope"]         +
            f3["score"]   * self.weights["experience_barrier"]  +
            f4["score"]   * self.weights["salary_compression"]  +
            f5["score"]   * self.weights["skill_inflation"]
        )
        score = round(float(score), 3)

        # 4. Dynamic labeling (slope + score combined)
        status, color = self._classify_saturation(score, slope_data)

        # 5. Actionable insights
        alerts = self._generate_alerts(f1, slope_data, f3, f4, f5)

        return {
            "Domain":           target_domain,
            "Sample_Size":      len(domain_df),
            "Saturation_Score": score,
            "Risk_Level":       status,
            "Color_Code":       color,

            "Factor_Breakdown": {
                "Supply_Demand":      f1,
                "Trend_Slope":        slope_data,
                "Experience_Barrier": f3,
                "Salary_Compression": f4,
                "Skill_Inflation":    f5
            },

            "Alerts":           alerts,

            "Signals": {
                "Demand_Trend":        "Growing" if slope_data["slope"] > 0 else "Declining",
                "Trend_Reliable":      slope_data["reliable"],
                "Experience_Barrier":  "High" if f3["score"] > 0.6 else "Normal",
                "Experience_Trend":    f3.get("exp_trend", "Unknown"),
                "Salary_State":        f4.get("interpretation", "Unknown"),
                "Skill_Inflation":     f5.get("skill_trend", "Unknown"),
                "Fresher_Pct":         f3.get("fresher_pct", None)
            }
        }

    def _classify_saturation(self, score: float, 
                               slope_data: dict) -> tuple:
        """
        5-tier classification using both score AND slope direction.
        Previous: 3 tiers with slope == 0 dead-code bug.
        """
        slope = slope_data.get("slope", 0)
        reliable = slope_data.get("reliable", False)

        if score < 0.25:
            return ("Safe Zone", "Green")
        elif score < 0.40:
            status = "Low Risk — Growing" if slope > 0 else "Low Risk — Watch"
            return (status, "Light Green")
        elif score < 0.60:
            status = "Moderate Risk" if not reliable else (
                "Moderate — Stabilizing" if slope > 0 else "Moderate — Declining"
            )
            return (status, "Yellow")
        elif score < 0.75:
            return ("High Saturation", "Orange")
        else:
            return ("Critically Saturated", "Red")

    def _generate_alerts(self, f1, slope_data, f3, f4, f5) -> list:
        """Generate plain-English alerts for Real Talk Engine."""
        alerts = []

        if f1["score"] > 0.7:
            alerts.append(
                f"🚨 Very high applicant/opening ratio ({f1['ratio']:.0f}:1). "
                f"Expect intense competition for every role."
            )
        if not slope_data["reliable"]:
            alerts.append("⚠️  Trend signal is weak — insufficient historical data for confident prediction.")
        if slope_data["slope"] < 0 and slope_data["reliable"]:
            alerts.append("📉 Job postings are declining month-over-month. Market may be contracting.")
        if f3.get("exp_trend") == "Rising":
            alerts.append("📈 Experience requirements are rising — entry barrier increasing for freshers.")
        if f3.get("fresher_pct", 100) < 20:
            alerts.append(
                f"🔒 Only {f3['fresher_pct']}% of roles open to freshers. "
                f"Experienced candidates dominate this market."
            )
        if f4.get("interpretation") == "Compressed":
            alerts.append("💰 Salary bands are compressed — limited negotiation power. Employer's market.")
        if f5.get("skill_trend") == "Inflating":
            alerts.append("📚 Skill requirements are increasing over time — market becoming harder to enter.")

        return alerts if alerts else ["✅ No major saturation alerts detected."]


if __name__  == "__main__":
    # Example usage of SaturationRiskIndicator

    # Load sample job data (using first 200 rows for demonstration)
    df = pd.read_csv(r"D:\DATA SCIENCE AND ML\Project\job_trend_predictor\data\processed\cleaned\cleaned_job_data.csv")

    # Initialize the indicator with default weights
    indicator = SaturationRiskIndicator()

    # Get saturation risk for Data Scientist roles
    result = indicator.get_saturation_risk(df, target_domain='Data Scientist')

    # Print the results
    if 'error' in result:
        print(f"Error: {result['error']}")
    else:
        print("Saturation Risk Indicator Report")
        print("=" * 50)
        print(f"Domain: {result['Domain']}")
        print(f"Sample Size: {result['Sample_Size']}")
        print(f"Saturation Score: {result['Saturation_Score']}")
        print(f"Risk Level: {result['Risk_Level']} ({result['Color_Code']})")
        print()

        print("Factor Breakdown:")
        factors = result['Factor_Breakdown']
        print(f"  Supply/Demand: {factors['Supply_Demand']['score']} (Ratio: {factors['Supply_Demand']['ratio']}:1)")
        print(f"  Trend Slope: {factors['Trend_Slope']['score']} (Slope: {factors['Trend_Slope']['slope']})")
        print(f"  Experience Barrier: {factors['Experience_Barrier']['score']} (Median Exp: {factors['Experience_Barrier']['median_exp']} yrs)")
        print(f"  Salary Compression: {factors['Salary_Compression']['score']} ({factors['Salary_Compression'].get('interpretation', 'N/A')})")
        print(f"  Skill Inflation: {factors['Skill_Inflation']['score']} (Median Skills: {factors['Skill_Inflation']['median_skills']})")
        print()

        print("Key Signals:")
        signals = result['Signals']
        print(f"  Demand Trend: {signals['Demand_Trend']}")
        print(f"  Trend Reliable: {signals['Trend_Reliable']}")
        print(f"  Experience Barrier: {signals['Experience_Barrier']}")
        print(f"  Experience Trend: {signals['Experience_Trend']}")
        print(f"  Salary State: {signals['Salary_State']}")
        print(f"  Skill Inflation: {signals['Skill_Inflation']}")
        if signals['Fresher_Pct'] is not None:
            print(f"  Fresher Percentage: {signals['Fresher_Pct']}%")
        print()

        print("Alerts:")
        for alert in result['Alerts']:
            print(f"  {alert}")