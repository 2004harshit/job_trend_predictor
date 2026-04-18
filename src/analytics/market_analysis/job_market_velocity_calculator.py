import pandas as pd
from typing import List , Dict
import logging
import numpy as np

class JobMarketVelocityCalculator:
    
    # Minimum listings per period for velocity to be meaningful
    MIN_SAMPLE_PER_PERIOD = 5
    
    # Noise threshold — growth below this is "Stable", not "Expanding/Contracting"  
    NOISE_THRESHOLD_PCT = 5.0
    
    # Window sizes for multi-period trend analysis
    WINDOW_DAYS = 30
    N_WINDOWS = 4  # 4 rolling windows = 4 months of trend data
    
    def __init__(self, nearby_cities: list = None, 
                 use_real_date: bool = True):
        """
        nearby_cities: expand local search radius (e.g., ['Sanganer', 'Amer'] for Jaipur)
        use_real_date: if True, use datetime.now() as reference.
                       if False, use max(timestamp) — for offline/historical analysis
        """
        self.nearby_cities = nearby_cities or []
        self.use_real_date = use_real_date
        self.logger = logging.getLogger(__name__)
    
    def _get_reference_date(self, df: pd.DataFrame) -> pd.Timestamp:
        """
        Critical fix: don't use max(scrape_date) as 'today'.
        Use actual current time unless explicitly doing historical analysis.
        """
        if self.use_real_date:
            return pd.Timestamp.now()
        
        # Historical mode: use max date in data
        date_col = 'timestamp' 
        max_date = pd.to_datetime(df[date_col], errors='coerce').max()
        
        if pd.isna(max_date):
            self.logger.warning("No valid dates found. Using current time.")
            return pd.Timestamp.now()
        
        return max_date
    
    def _filter_by_domain(self, df: pd.DataFrame, 
                           domain_keywords: list,
                           experience_band: tuple = (0, 5)) -> pd.DataFrame:
        """
        Priority order:
        1. Job_Type exact match (cleanest)
        2. Title word-boundary match (controlled)
        3. Description match ONLY as last resort (noisy)

        Word boundary prevents 'Machine Learning' matching 
        'no machine learning background required'.
        """
        result = pd.DataFrame()

        # Strategy 1: title exact match
        if 'title' in df.columns:
            mask = df['title'].str.lower().isin(
                [kw.lower() for kw in domain_keywords]
            )
            result = df[mask]
            if len(result) >= self.MIN_SAMPLE_PER_PERIOD * 2:
                self.logger.info(f"Domain filter: title → {len(result)} records")
                return self._apply_experience_filter(result, experience_band)

        # Strategy 2: title word-boundary match
        title_col = 'title' if 'title' in df.columns else None
        if title_col in df.columns:
            # Word boundary regex for each keyword
            patterns = [r'\b' + kw.replace(' ', r'\s+') + r'\b' 
                        for kw in domain_keywords]
            combined_pattern = '|'.join(patterns)

            title_match = df[
                df[title_col].str.contains(
                    combined_pattern, case=False, na=False, regex=True
                )
            ]
            if len(title_match) >= self.MIN_SAMPLE_PER_PERIOD:
                self.logger.info(f"Domain filter: title regex → {len(title_match)} records")
                return self._apply_experience_filter(title_match, experience_band)

        # Strategy 3: description — only for primary keyword, not all
        if 'description_cleaned' in df.columns and len(domain_keywords) > 0:
            primary = domain_keywords[0]
            # Strict: keyword must appear multiple times to indicate it's a core role
            desc_match = df[
                df['description_cleaned'].str.count(
                    r'\b' + primary + r'\b'
                ) >= 2  # Must appear at least twice
            ]
            self.logger.warning(
                f"Domain filter: description fallback — noisy data possible. "
                f"{len(desc_match)} records"
            )
            return self._apply_experience_filter(desc_match, experience_band)

        return pd.DataFrame()

    def _apply_experience_filter(self, df: pd.DataFrame, 
                                  band: tuple) -> pd.DataFrame:
        """Apply experience bracket filter if column exists."""
        if 'min_experience' not in df.columns:
            return df
        min_exp, max_exp = band
        return df[
            (df['min_experience'] >= min_exp) & 
            (df['min_experience'] <= max_exp)
        ].copy()

    def _build_time_series(self, domain_df: pd.DataFrame,
                            reference_date: pd.Timestamp) -> pd.DataFrame:
        """
        Build N rolling windows of job posting counts.
        This enables trend direction AND acceleration detection.

        Returns DataFrame with columns: [period_label, start, end, count, weighted_count]
        """
        date_col = 'timestamp' if 'timestamp' in domain_df.columns else 'timestamp'
        domain_df = domain_df.copy()
        domain_df['_date'] = pd.to_datetime(domain_df[date_col], errors='coerce')
        domain_df = domain_df.dropna(subset=['_date'])

        openings_col = 'no_of_opening'
        has_openings = openings_col in domain_df.columns

        periods = []
        for i in range(self.N_WINDOWS, 0, -1):
            end   = reference_date - pd.Timedelta(days=self.WINDOW_DAYS * (i - 1))
            start = reference_date - pd.Timedelta(days=self.WINDOW_DAYS * i)

            window = domain_df[
                (domain_df['_date'] > start) & 
                (domain_df['_date'] <= end)
            ]

            # Count: use actual openings if available, else listing count
            if has_openings and not window.empty:
                count = pd.to_numeric(
                    window[openings_col], errors='coerce'
                ).fillna(1).sum()
            else:
                count = len(window)

            label = f"T-{i}" if i > 1 else "Current"
            periods.append({
                "period":     label,
                "start":      start.date(),
                "end":        end.date(),
                "count":      int(count),
                "listing_ct": len(window)
            })

        return pd.DataFrame(periods)

    def _calculate_velocity_metrics(self, time_series: pd.DataFrame) -> dict:
        """
        From multi-period time series, extract:
        1. Recent growth (last period vs previous)
        2. Trend direction (slope over all periods)  
        3. Acceleration (is growth speeding up or slowing down?)
        4. Volatility (how stable is the trend?)
        """
        if time_series.empty or len(time_series) < 2:
            return {
                "recent_growth_pct": 0.0,
                "trend_slope": 0.0,
                "acceleration": 0.0,
                "volatility": 0.0,
                "is_emerging": False
            }

        counts = time_series['count'].values.astype(float)

        # 1. Recent growth: last window vs second-to-last
        curr = counts[-1]
        prev = counts[-2]

        if prev == 0 and curr == 0:
            recent_growth = 0.0
            is_emerging = False
        elif prev == 0 and curr > 0:
            # New domain appearing — flag as emerging, not just "infinite growth"
            recent_growth = 100.0  # Cap at 100% to signal emergence
            is_emerging = True
        else:
            # Damped growth: log scale prevents small-number explosion
            # Same fix as Demand Score Calculator
            recent_growth = ((curr - prev) / prev) * 100
            # Cap at ±200% to prevent outliers
            recent_growth = np.clip(recent_growth, -200, 200)
            is_emerging = False

        # 2. Trend slope: linear regression over all N periods
        x = np.arange(len(counts))
        if counts.std() == 0:
            slope = 0.0
        else:
            slope = float(np.polyfit(x, counts, 1)[0])  # Listings per period

        # Normalize slope as % of mean
        mean_count = counts.mean()
        normalized_slope = (slope / mean_count * 100) if mean_count > 0 else 0.0

        # 3. Acceleration: slope of the growth RATES (2nd derivative)
        if len(counts) >= 3:
            growth_rates = np.diff(counts) / np.where(counts[:-1] == 0, 1, counts[:-1])
            accel = float(np.diff(growth_rates).mean()) * 100 if len(growth_rates) > 1 else 0.0
        else:
            accel = 0.0

        # 4. Volatility: coefficient of variation
        volatility = (counts.std() / mean_count * 100) if mean_count > 0 else 0.0

        return {
            "recent_growth_pct":  round(recent_growth, 2),
            "trend_slope_pct":    round(normalized_slope, 2),
            "acceleration":       round(accel, 2),
            "volatility_pct":     round(volatility, 2),
            "is_emerging":        is_emerging,
            "period_counts":      counts.tolist()
        }

    def _classify_velocity_status(self, metrics: dict,
                                    n_samples: int) -> dict:
        """
        5-tier status with noise tolerance and sample size awareness.

        Previous: binary "Expanding/Contracting" with no noise floor.
        Now: 5 tiers + data quality caveat for small samples.
        """
        growth = metrics['recent_growth_pct']
        slope  = metrics['trend_slope_pct']
        accel  = metrics['acceleration']
        is_emerging = metrics['is_emerging']

        # Insufficient data guard
        if n_samples < self.MIN_SAMPLE_PER_PERIOD:
            return {
                "status":      "Insufficient Data",
                "signal":      "⚪",
                "description": f"Only {n_samples} listings found. Need {self.MIN_SAMPLE_PER_PERIOD}+ for reliable velocity."
            }

        if is_emerging:
            return {
                "status":      "Emerging",
                "signal":      "🌱",
                "description": "New domain appearing in market — early mover advantage possible."
            }

        # Noise-tolerant classification
        if abs(growth) <= self.NOISE_THRESHOLD_PCT:
            status = "Stable"
            signal = "⚖️"
            desc = "Market is steady — no significant momentum in either direction."
        elif growth > 30:
            status = "Hot"
            signal = "🔥"
            desc = "Strong hiring surge — companies actively expanding."
        elif growth > self.NOISE_THRESHOLD_PCT:
            status = "Growing"
            signal = "📈"
            desc = "Positive momentum — market is gradually expanding."
        elif growth < -30:
            status = "Cooling Fast"
            signal = "🧊"
            desc = "Sharp decline — hiring has slowed significantly."
        else:
            status = "Slowing"
            signal = "📉"
            desc = "Mild decline — monitor for sustained contraction."

        # Acceleration modifier
        accel_note = ""
        if accel > 5:
            accel_note = " Growth is accelerating — momentum building."
        elif accel < -5:
            accel_note = " Growth is decelerating — pace slowing down."

        return {
            "status":      status,
            "signal":      signal,
            "description": desc + accel_note
        }

    def _calculate_location_metrics(self, 
                                      national_series: pd.DataFrame,
                                      local_series: pd.DataFrame,
                                      target_location: str) -> dict:
        """
        Location gap analysis:
        - Local share trend: is local market growing faster or slower than national?
        - Relocation signal: if national is hot but local is cold → move signal
        """
        nat_counts = national_series['count'].values.astype(float)
        loc_counts = local_series['count'].values.astype(float)

        nat_total = nat_counts.sum()
        loc_total = loc_counts.sum()

        # Current period share
        curr_share = (loc_counts[-1] / nat_counts[-1] * 100) if nat_counts[-1] > 0 else 0
        # Previous period share
        prev_share = (loc_counts[-2] / nat_counts[-2] * 100) if (
            len(nat_counts) >= 2 and nat_counts[-2] > 0
        ) else curr_share

        share_change = curr_share - prev_share

        # Relocation signal logic
        nat_velocity = national_series['count'].pct_change().mean() * 100
        loc_velocity = local_series['count'].pct_change().mean() * 100
        velocity_gap = nat_velocity - loc_velocity

        if velocity_gap > 15:
            relocation_signal = "🚀 National market significantly outpacing local — relocation may accelerate opportunities."
        elif velocity_gap > 5:
            relocation_signal = "📦 Mild advantage to relocating — metros hiring faster."
        elif velocity_gap < -5:
            relocation_signal = "🏠 Local market growing faster than national — strong local opportunity."
        else:
            relocation_signal = "⚖️  Local and national markets moving similarly."

        return {
            "local_openings_30d":   int(loc_counts[-1]),
            "national_openings_30d": int(nat_counts[-1]),
            "local_market_share_pct": round(curr_share, 2),
            "share_change_pct":       round(share_change, 2),
            "velocity_gap_pct":       round(velocity_gap, 2),
            "relocation_signal":      relocation_signal,
            "nearby_cities_included": self.nearby_cities
        }

    def calculate_velocity(self, df: pd.DataFrame,
                            domain_keywords: list,
                            target_location: str,
                            experience_band: tuple = (0, 5)) -> dict:
        """
        Main entry point. Returns comprehensive velocity report.
        """
        # 1. Validate
        if not domain_keywords:
            return {"error": "domain_keywords cannot be empty."}

        df = df.copy()

        # Safe date parsing
        for col in ['timestamp', 'timestamp']:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')

        # 2. Reference date
        reference_date = self._get_reference_date(df)

        # 3. Filter domain
        domain_df = self._filter_by_domain(df, domain_keywords, experience_band)

        if domain_df.empty:
            return {"error": f"No data found for keywords: {domain_keywords}"}

        # 4. Build national time series
        national_series = self._build_time_series(domain_df, reference_date)

        # 5. Build local time series
        location_list = [target_location] + self.nearby_cities
        loc_pattern   = '|'.join(location_list)

        if 'location' in domain_df.columns:
            local_df = domain_df[
                domain_df['location'].str.contains(
                    loc_pattern, case=False, na=False
                )
            ]
        else:
            local_df = pd.DataFrame()

        local_series = self._build_time_series(
            local_df, reference_date
        ) if not local_df.empty else national_series.assign(count=0)

        # 6. Velocity metrics
        nat_metrics = self._calculate_velocity_metrics(national_series)
        loc_metrics = self._calculate_velocity_metrics(local_series)

        # 7. Status classification
        nat_status = self._classify_velocity_status(
            nat_metrics, national_series['count'].sum()
        )
        loc_status = self._classify_velocity_status(
            loc_metrics, local_series['count'].sum()
        )

        # 8. Location gap analysis
        loc_intelligence = self._calculate_location_metrics(
            national_series, local_series, target_location
        )

        # 9. Company velocity (new entrants = strong signal)
        new_companies = 0
        if 'company' in domain_df.columns:
            date_col = 'timestamp' if 'timestamp' in domain_df else 'timestamp'
            recent_cutoff = reference_date - pd.Timedelta(days=self.WINDOW_DAYS)
            older_cutoff  = reference_date - pd.Timedelta(days=self.WINDOW_DAYS * 2)

            recent_cos = set(domain_df[
                domain_df['_date'] > recent_cutoff
            ]['company'].dropna()) if '_date' in domain_df else set()

            older_cos = set(domain_df[
                domain_df['_date'] <= recent_cutoff
            ]['company'].dropna()) if '_date' in domain_df else set()

            new_companies = len(recent_cos - older_cos)  # Companies hiring NOW that weren't before

        return {
            "domain":          domain_keywords,
            "location":        target_location,
            "experience_band": experience_band,
            "reference_date":  str(reference_date.date()),
            "Experience_Band": experience_band,
            "Reference_Date":  str(reference_date.date()),

            "National_Velocity": {
                "Status":          nat_status,
                "Recent_Growth_Pct": nat_metrics['recent_growth_pct'],
                "Trend_Slope_Pct":   nat_metrics['trend_slope_pct'],
                "Acceleration":      nat_metrics['acceleration'],
                "Volatility_Pct":    nat_metrics['volatility_pct'],
                "Period_Counts":     nat_metrics['period_counts'],
                "Is_Emerging":       nat_metrics['is_emerging']
            },

            "Local_Velocity": {
                "Status":          loc_status,
                "Recent_Growth_Pct": loc_metrics['recent_growth_pct'],
                "Trend_Slope_Pct":   loc_metrics['trend_slope_pct'],
                "Acceleration":      loc_metrics['acceleration'],
                "Period_Counts":     loc_metrics['period_counts']
            },

            "Location_Intelligence": loc_intelligence,

            "Market_Signals": {
                "New_Companies_Entering": new_companies,
                "Data_Freshness_Days":    int(
                    (pd.Timestamp.now() - reference_date).days
                ) if not self.use_real_date else 0
            },

            "Time_Series": national_series.to_dict(orient='records')
        }

if __name__ == "__main__":
    # Example usage of JobMarketVelocityCalculator

    # Load sample job data (using first 100 rows for demonstration)
    df = pd.read_csv(r"D:\DATA SCIENCE AND ML\Project\job_trend_predictor\data\processed\cleaned\cleaned_job_data.csv")

   

    # Initialize the calculator
    calculator = JobMarketVelocityCalculator(
        nearby_cities=['Hyderabad', 'Chennai'],  # Nearby cities for location analysis
        use_real_date=True  # Use current date as reference
    )

    # Calculate velocity for Data Scientist roles in Bengaluru
    result = calculator.calculate_velocity(
        df=df,
        domain_keywords=['Data Scientist'],
        target_location='Bengaluru',
        experience_band=(0, 5)  # 0-5 years experience
    )

    # Print the results
    if 'error' in result:
        print(f"Error: {result['error']}")
    else:
        print("Job Market Velocity Report")
        print("=" * 50)
        print(f"Domain: {result['Domain']}")
        print(f"Location: {result['Location']}")
        print(f"Experience Band: {result['Experience_Band']}")
        print(f"Reference Date: {result['Reference_Date']}")
        print()

        print("National Velocity:")
        nat_vel = result['National_Velocity']
        print(f"  Status: {nat_vel['Status']['status']} {nat_vel['Status']['signal']}")
        print(f"  Description: {nat_vel['Status']['description']}")
        print(f"  Recent Growth: {nat_vel['Recent_Growth_Pct']}%")
        print(f"  Trend Slope: {nat_vel['Trend_Slope_Pct']}%")
        print(f"  Acceleration: {nat_vel['Acceleration']}")
        print(f"  Volatility: {nat_vel['Volatility_Pct']}%")
        print()

        print("Local Velocity:")
        loc_vel = result['Local_Velocity']
        print(f"  Status: {loc_vel['Status']['status']} {loc_vel['Status']['signal']}")
        print(f"  Description: {loc_vel['Status']['description']}")
        print(f"  Recent Growth: {loc_vel['Recent_Growth_Pct']}%")
        print()

        print("Location Intelligence:")
        loc_intel = result['Location_Intelligence']
        print(f"  Local Openings (30d): {loc_intel['local_openings_30d']}")
        print(f"  National Openings (30d): {loc_intel['national_openings_30d']}")
        print(f"  Local Market Share: {loc_intel['local_market_share_pct']}%")
        print(f"  Share Change: {loc_intel['share_change_pct']}%")
        print(f"  Velocity Gap: {loc_intel['velocity_gap_pct']}%")
        print(f"  Relocation Signal: {loc_intel['relocation_signal']}")
        print()

        print("Market Signals:")
        signals = result['Market_Signals']
        print(f"  New Companies Entering: {signals['New_Companies_Entering']}")
        print(f"  Data Freshness: {signals['Data_Freshness_Days']} days")