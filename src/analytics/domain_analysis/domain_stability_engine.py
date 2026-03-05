import re
import logging
from typing import Dict, Optional
import pandas as pd
import numpy as np

class DomainStabilityEngine:
    
    MIN_MONTHS_FOR_TREND = 3
    MIN_MONTHS_FOR_PROJECTION = 6
    
    # Skill-level AI automation risk weights
    # Based on Oxford/McKinsey automation research frameworks
    SKILL_AUTOMATION_RISK = {
        # High automation risk skills
        'data entry':       0.90, 'manual testing':   0.75,
        'excel':            0.65, 'copy editing':     0.60,
        'basic sql':        0.55, 'report generation':0.60,
        # Medium risk
        'frontend':         0.35, 'web development':  0.30,
        'java':             0.25, 'python':           0.20,
        'devops':           0.20, 'cloud':            0.18,
        # Low risk
        'machine learning': 0.12, 'data science':     0.15,
        'system design':    0.10, 'architecture':     0.08,
        'research':         0.07, 'ml engineering':   0.10,
        # Very low risk
        'llm':              0.05, 'ai research':      0.04,
        'product management':0.10,'cybersecurity':    0.08,
    }
    
    # Domain-level base AI risk (fallback if no skill data)
    DOMAIN_BASE_RISK = {
        'data entry':          0.88, 'manual tester':     0.72,
        'web developer':       0.30, 'frontend developer':0.28,
        'backend developer':   0.22, 'full stack':        0.25,
        'data scientist':      0.18, 'data analyst':      0.35,
        'ml engineer':         0.10, 'ai engineer':       0.08,
        'devops engineer':     0.15, 'cloud engineer':    0.12,
        'software engineer':   0.20, 'java developer':    0.22,
        'python developer':    0.18, 'react developer':   0.28,
        'cybersecurity':       0.08, 'security engineer': 0.07,
        'product manager':     0.10, 'scrum master':      0.25,
    }
    
    def __init__(self, weights: Dict = None):
        default_weights = {
            "trend_stability":    0.30,  # Long-term demand trajectory
            "volatility":         0.20,  # Month-to-month consistency
            "ai_resistance":      0.25,  # How automation-proof is the role?
            "salary_stability":   0.15,  # Salary consistency over time
            "supply_health":      0.10,  # Healthy demand/supply ratio trend
        }
        self.weights = weights or default_weights
        self._validate_weights()
        self.logger = logging.getLogger(__name__)
    
    def _validate_weights(self):
        total = sum(self.weights.values())
        if not (0.98 <= total <= 1.02):
            raise ValueError(f"Weights must sum to 1.0, got {total:.3f}")
        
    def _filter_domain(self, df: pd.DataFrame, 
                        target_domain: str) -> pd.DataFrame:
        """Never mutates input. Job_Type first, Title fallback."""
        df = df.copy()

        if 'TItle_Cleaned' in df.columns and 'Title_Cleaned' not in df.columns:
            df = df.rename(columns={'TItle_Cleaned': 'Title_Cleaned'})

        # Parse dates safely
        for col in ['Scraped_At_Cleaned', 'Posted_Date']:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')

        # Priority 1: Job_Type
        if 'Job_Type' in df.columns:
            exact = df[df['Job_Type'].str.lower() == target_domain.lower()]
            if len(exact) >= self.MIN_MONTHS_FOR_TREND * 3:
                return exact

        # Priority 2: Title word-boundary
        title_col = 'Title_Cleaned' if 'Title_Cleaned' in df.columns else None
        if title_col:
            pattern = r'\b' + re.escape(target_domain) + r'\b'
            return df[df[title_col].str.contains(
                pattern, case=False, na=False, regex=True
            )]

        return pd.DataFrame()

    def _build_monthly_series(self, domain_df: pd.DataFrame) -> pd.Series:
        """
        Safe monthly aggregation with:
        1. Null date guard
        2. Incomplete last-month trimming
        3. Actual openings if available
        """
        date_col = 'Posted_Date' if 'Posted_Date' in domain_df.columns else 'Scraped_At_Cleaned'

        df = domain_df.copy()
        df['_date'] = pd.to_datetime(df[date_col], errors='coerce')
        df = df.dropna(subset=['_date'])

        if df.empty:
            return pd.Series(dtype=float)

        # Use actual openings if available
        openings_col = 'No of job opening cleaned '
        if openings_col in df.columns:
            df['_count'] = pd.to_numeric(df[openings_col], errors='coerce').fillna(1)
        else:
            df['_count'] = 1  # Each listing = 1 opening

        df['_month'] = df['_date'].dt.to_period('M')
        monthly = df.groupby('_month')['_count'].sum().sort_index()

        if monthly.empty:
            return pd.Series(dtype=float)

        # Drop last month if it's the current month (incomplete data)
        current_period = pd.Timestamp.now().to_period('M')
        if monthly.index[-1] == current_period:
            monthly = monthly.iloc[:-1]
            self.logger.info("Trimmed current (incomplete) month from time series.")

        return monthly

    def _build_salary_series(self, domain_df: pd.DataFrame) -> pd.Series:
        """Monthly median salary series for salary stability dimension."""
        date_col = 'Posted_Date' if 'Posted_Date' in domain_df.columns else 'Scraped_At_Cleaned'

        sal_col = None
        for col in ['Avg_Salary', 'Min_Salary']:
            if col in domain_df.columns:
                sal_col = col
                break
            
        if sal_col is None or date_col not in domain_df.columns:
            return pd.Series(dtype=float)

        df = domain_df.copy()
        df['_date'] = pd.to_datetime(df[date_col], errors='coerce')
        df[sal_col] = pd.to_numeric(df[sal_col], errors='coerce')
        df = df.dropna(subset=['_date', sal_col])

        if df.empty:
            return pd.Series(dtype=float)

        df['_month'] = df['_date'].dt.to_period('M')
        return df.groupby('_month')[sal_col].median().sort_index()

    def _calculate_trend_metrics(self, monthly: pd.Series) -> dict:
        """
        Replace naive 60-month linear extrapolation with:
        1. R²-weighted confidence
        2. Short-horizon projection (12 months max, not 60)
        3. Normalized slope (not raw count change)
        4. Trend classification with noise tolerance
        """
        if len(monthly) < self.MIN_MONTHS_FOR_TREND:
            return {
                "slope_normalized": 0.0, "r_squared": 0.0,
                "trend_score": 0.5, "direction": "Insufficient Data",
                "reliable": False, "months_analyzed": len(monthly)
            }

        values = monthly.values.astype(float)
        x = np.arange(len(values)).reshape(-1, 1)

        from sklearn.linear_model import LinearRegression
        model = LinearRegression().fit(x, values)
        raw_slope = float(model.coef_[0])

        # R² for reliability
        y_pred = model.predict(x)
        ss_res = np.sum((values - y_pred) ** 2)
        ss_tot = np.sum((values - values.mean()) ** 2)
        r_squared = max(0.0, 1 - ss_res / ss_tot) if ss_tot > 0 else 0.0

        # Normalized slope: % change per month relative to mean
        mean_val = values.mean()
        norm_slope = (raw_slope / mean_val) if mean_val > 0 else 0.0

        # Short-horizon projection: 12 months only (not 60)
        if len(monthly) >= self.MIN_MONTHS_FOR_PROJECTION:
            future_step = len(values) + 12
            projected_12m = max(0, float(model.predict([[future_step]])[0]))
            current = values[-1]
            projection_growth = (projected_12m - current) / current if current > 0 else 0.0
        else:
            projection_growth = norm_slope * 12  # Simple estimate

        # Trend score: sigmoid of normalized slope
        # Positive slope → score > 0.5, negative slope → score < 0.5
        trend_score = 1 / (1 + np.exp(-norm_slope * 10))

        # Pull toward 0.5 if unreliable
        reliability = min(1.0, r_squared * 2)
        trend_score = trend_score * reliability + 0.5 * (1 - reliability)

        # Direction with noise tolerance (±2% monthly = "Stable")
        if abs(norm_slope) < 0.02:
            direction = "Stable"
        elif norm_slope > 0.05:
            direction = "Strong Growth"
        elif norm_slope > 0:
            direction = "Mild Growth"
        elif norm_slope > -0.05:
            direction = "Mild Decline"
        else:
            direction = "Strong Decline"

        return {
            "slope_normalized":   round(norm_slope, 4),
            "r_squared":          round(r_squared, 3),
            "trend_score":        round(trend_score, 3),
            "direction":          direction,
            "projection_12m_pct": round(projection_growth * 100, 1),
            "reliable":           r_squared >= 0.3,
            "months_analyzed":    len(monthly)
        }

    def _calculate_volatility_score(self, monthly: pd.Series) -> dict:
        """
        CV-based volatility with:
        1. Market-context normalization
        2. Trend-adjusted CV (remove trend before measuring noise)
        3. Score mapping with domain of 0-1
        """
        if len(monthly) < 2:
            return {"score": 0.5, "cv": 0.5, "interpretation": "Insufficient data"}

        values = monthly.values.astype(float)
        mean_val = values.mean()

        if mean_val == 0:
            return {"score": 1.0, "cv": 1.0, "interpretation": "No demand — maximum instability"}

        # Detrended CV: remove linear trend first, then measure residual noise
        if len(values) >= 4:
            x = np.arange(len(values)).reshape(-1, 1)
            from sklearn.linear_model import LinearRegression
            trend = LinearRegression().fit(x, values).predict(x)
            residuals = values - trend
            cv = residuals.std() / mean_val  # Noise around trend, not trend itself
        else:
            cv = values.std() / mean_val

        # Normalize CV to 0-1 score
        # CV of 0 = perfectly stable → score 0.0 (no volatility penalty)
        # CV of 1.0+ = highly volatile → score 1.0 (maximum penalty)
        volatility_score = np.clip(cv, 0, 1.5) / 1.5

        # Stability score = inverse of volatility score
        stability_contribution = 1 - volatility_score

        if volatility_score < 0.2:
            interpretation = "Very stable — consistent monthly demand"
        elif volatility_score < 0.4:
            interpretation = "Mildly volatile — normal seasonal variation"
        elif volatility_score < 0.6:
            interpretation = "Moderately volatile — noticeable hiring cycles"
        else:
            interpretation = "Highly volatile — unpredictable hiring patterns"

        return {
            "score":          round(stability_contribution, 3),  # Higher = more stable
            "cv":             round(cv, 3),
            "volatility_raw": round(volatility_score, 3),
            "interpretation": interpretation
        }

    def _calculate_ai_risk(self, domain_df: pd.DataFrame, 
                             target_domain: str) -> dict:
        """
        AI risk from three sources (priority order):
        1. Skill-composition analysis from actual job postings
        2. Domain-level lookup with fuzzy matching
        3. Structural task analysis (how many skills are codifiable?)
        """
        # Source 1: Skill-composition from actual postings
        skill_based_risk = None
        if 'Combined_Skills' in domain_df.columns:
            all_skills_text = ' '.join(
                domain_df['Combined_Skills'].dropna().str.lower().tolist()
            )

            total_weight = 0.0
            weighted_risk = 0.0

            for skill_kw, risk in self.SKILL_AUTOMATION_RISK.items():
                # Count occurrences as weight
                count = all_skills_text.count(skill_kw)
                if count > 0:
                    weighted_risk += risk * count
                    total_weight  += count

            if total_weight > 0:
                skill_based_risk = weighted_risk / total_weight
                self.logger.info(
                    f"Skill-based AI risk for '{target_domain}': {skill_based_risk:.2f}"
                )

        # Source 2: Domain lookup with partial matching
        domain_lower = target_domain.lower()
        domain_risk = None

        for known_domain, risk in self.DOMAIN_BASE_RISK.items():
            if known_domain in domain_lower or domain_lower in known_domain:
                domain_risk = risk
                break
            
        # Source 3: Structural proxy — Skill_Count as complexity signal
        # More unique skills required = harder to automate (requires breadth)
        structural_risk = 0.4  # Default
        if 'Skill_Count' in domain_df.columns:
            median_skills = pd.to_numeric(
                domain_df['Skill_Count'], errors='coerce'
            ).median()

            if not pd.isna(median_skills):
                # More skills required = lower automation risk
                # 5 skills → risk ~0.5, 15 skills → risk ~0.15
                structural_risk = max(0.05, 0.7 - (median_skills * 0.04))

        # Combine sources with priority weighting
        if skill_based_risk is not None and domain_risk is not None:
            final_risk = 0.5 * skill_based_risk + 0.35 * domain_risk + 0.15 * structural_risk
            source = "skill_composition + domain_lookup + structural"
        elif skill_based_risk is not None:
            final_risk = 0.6 * skill_based_risk + 0.4 * structural_risk
            source = "skill_composition + structural"
        elif domain_risk is not None:
            final_risk = 0.65 * domain_risk + 0.35 * structural_risk
            source = "domain_lookup + structural"
        else:
            final_risk = structural_risk
            source = "structural_only"

        final_risk = float(np.clip(final_risk, 0.03, 0.95))

        # AI resistance score for stability formula (inverse of risk)
        ai_resistance_score = 1 - final_risk

        return {
            "score":             round(ai_resistance_score, 3),  # Higher = more resistant
            "risk_pct":          round(final_risk * 100, 1),
            "risk_label":        self._label_ai_risk(final_risk),
            "source":            source,
            "skill_based_risk":  round(skill_based_risk, 3) if skill_based_risk else None,
            "domain_base_risk":  round(domain_risk, 3) if domain_risk else None,
        }

    def _label_ai_risk(self, risk: float) -> str:
        if risk < 0.15: return "🟢 Very Low — Highly creative/strategic role"
        elif risk < 0.30: return "🟡 Low — Some automatable tasks but core is safe"
        elif risk < 0.50: return "🟠 Moderate — Significant automation risk in 5-10 years"
        elif risk < 0.70: return "🔴 High — Many tasks automatable now or soon"
        else:             return "🚨 Very High — Role likely disrupted within 3-5 years"

    def _calculate_salary_stability(self, salary_series: pd.Series) -> dict:
        """
        Stable salary trend = healthy domain.
        Compressed or declining salary = saturation/disruption signal.
        """
        if len(salary_series) < 3:
            return {"score": 0.5, "trend_pct": 0.0, "interpretation": "Insufficient data"}

        values = salary_series.values.astype(float)

        # Remove outliers
        q1, q3 = np.percentile(values, 25), np.percentile(values, 75)
        iqr = q3 - q1
        values = values[(values >= q1 - 1.5 * iqr) & (values <= q3 + 1.5 * iqr)]

        if len(values) < 2:
            return {"score": 0.5, "trend_pct": 0.0, "interpretation": "Insufficient data"}

        # Monthly salary growth rate
        x = np.arange(len(values)).reshape(-1, 1)
        from sklearn.linear_model import LinearRegression
        model = LinearRegression().fit(x, values)

        monthly_slope = float(model.coef_[0])
        base_salary   = float(model.predict([[0]])[0])
        monthly_pct   = (monthly_slope / base_salary * 100) if base_salary > 0 else 0
        annual_pct    = monthly_pct * 12

        # Score: salary growing at 5-20%/yr = healthy = high score
        # Declining or flat = unstable = low score
        if annual_pct > 15:
            score = 0.9  # Fast growing salary = domain is in demand
        elif annual_pct > 5:
            score = 0.7  # Healthy growth
        elif annual_pct > 0:
            score = 0.5  # Stagnant but positive
        elif annual_pct > -5:
            score = 0.3  # Mildly declining
        else:
            score = 0.1  # Salary compression — bad stability signal

        return {
            "score":          score,
            "annual_pct":     round(annual_pct, 2),
            "interpretation": (
                f"Salaries {'growing' if annual_pct > 0 else 'declining'} "
                f"at {abs(annual_pct):.1f}%/yr"
            )
        }

    def _calculate_supply_health(self, domain_df: pd.DataFrame) -> dict:
        """
        Healthy supply = moderate, consistent applicant/opening ratio.
        Exploding applicants = saturation signal.
        Falling applicants = declining interest = also bad.
        """
        APPLICANT_COL = 'No of applicant applied cleaned'
        OPENINGS_COL  = 'No of job opening cleaned '

        if APPLICANT_COL not in domain_df.columns or OPENINGS_COL not in domain_df.columns:
            return {"score": 0.5, "ratio": None, "interpretation": "Data unavailable"}

        apps    = pd.to_numeric(domain_df[APPLICANT_COL], errors='coerce').dropna()
        opens   = pd.to_numeric(domain_df[OPENINGS_COL],  errors='coerce').fillna(1)

        if apps.empty:
            return {"score": 0.5, "ratio": None, "interpretation": "Data unavailable"}

        ratio = apps.sum() / max(opens.sum(), 1)

        # Healthy ratio: 10-30 applicants per opening
        # Too low (<5): domain not attracting talent — declining interest
        # Too high (>100): severely saturated — unstable for newcomers
        if ratio < 5:
            score = 0.3   # Under-interest — domain may be dying
        elif ratio <= 30:
            score = 0.8   # Healthy competition
        elif ratio <= 60:
            score = 0.6   # Elevated but manageable
        elif ratio <= 100:
            score = 0.35  # High saturation
        else:
            score = 0.15  # Extreme saturation

        return {
            "score":          score,
            "ratio":          round(ratio, 1),
            "interpretation": f"{ratio:.0f} applicants per opening — {'Healthy' if score >= 0.6 else 'Concerning'}"
        }

    def calculate_stability_score(self, df: pd.DataFrame,
                                   target_domain: str) -> dict:
        # 1. Filter domain safely
        domain_df = self._filter_domain(df, target_domain)
        if domain_df.empty:
            return {"error": f"No data found for domain: '{target_domain}'"}

        # 2. Build time series
        monthly = self._build_monthly_series(domain_df)
        if len(monthly) < self.MIN_MONTHS_FOR_TREND:
            return {
                "error": f"Insufficient time series: only {len(monthly)} months "
                         f"(need {self.MIN_MONTHS_FOR_TREND}+)."
            }

        # 3. Calculate all factors
        trend     = self._calculate_trend_metrics(monthly)
        vol       = self._calculate_volatility_score(monthly)
        ai        = self._calculate_ai_risk(domain_df, target_domain)
        sal_series = self._build_salary_series(domain_df)
        sal_stab  = self._calculate_salary_stability(sal_series)
        supply    = self._calculate_supply_health(domain_df)

        # 4. Weighted composite score
        score = (
            trend["trend_score"]   * self.weights["trend_stability"]  +
            vol["score"]           * self.weights["volatility"]        +
            ai["score"]            * self.weights["ai_resistance"]     +
            sal_stab["score"]      * self.weights["salary_stability"]  +
            supply["score"]        * self.weights["supply_health"]
        )
        score = round(float(np.clip(score, 0.0, 1.0)), 3)

        # 5. 5-tier classification (not binary)
        status, color = self._classify_stability(score, trend["direction"])

        # 6. Alerts
        alerts = self._generate_alerts(trend, vol, ai, sal_stab, supply)

        return {
            "Domain":           target_domain,
            "Sample_Size":      len(domain_df),
            "Months_Analyzed":  len(monthly),
            "Stability_Score":  score,
            "Status":           status,
            "Color_Code":       color,

            "Factor_Breakdown": {
                "Trend_Stability":  trend,
                "Volatility":       vol,
                "AI_Resistance":    ai,
                "Salary_Stability": sal_stab,
                "Supply_Health":    supply
            },

            "Alerts": alerts,

            "Summary": {
                "Trend_Direction":   trend["direction"],
                "Trend_Reliable":    trend["reliable"],
                "AI_Risk_Pct":       ai["risk_pct"],
                "AI_Risk_Label":     ai["risk_label"],
                "Volatility_Level":  vol["interpretation"],
                "Salary_Trend":      sal_stab["interpretation"],
                "12M_Projection_Pct": trend["projection_12m_pct"]
            }
        }

    def _classify_stability(self, score: float, 
                              direction: str) -> tuple:
        """5-tier — removes binary cliff edge."""
        if score >= 0.80:
            return ("🟢 Highly Stable", "Green")
        elif score >= 0.65:
            status = "📈 Growing Stable" if "Growth" in direction else "🟡 Mostly Stable"
            return (status, "Light Green")
        elif score >= 0.50:
            return ("⚖️  Moderate Stability", "Yellow")
        elif score >= 0.35:
            status = "📉 Declining" if "Decline" in direction else "🟠 At Risk"
            return (status, "Orange")
        else:
            return ("🔴 High Risk — Avoid Long-Term Bet", "Red")

    def _generate_alerts(self, trend, vol, ai, sal_stab, supply) -> list:
        """Actionable alerts for AdaptiveRealTalkEngine."""
        alerts = []

        if not trend["reliable"]:
            alerts.append("⚠️  Trend signal unreliable — insufficient historical data.")
        if "Decline" in trend["direction"] and trend["reliable"]:
            alerts.append(f"📉 Job postings declining ({trend['projection_12m_pct']:+.1f}% projected next 12 months).")
        if ai["risk_pct"] > 50:
            alerts.append(f"🤖 High AI automation risk ({ai['risk_pct']:.0f}%). {ai['risk_label']}")
        if vol["cv"] > 0.6:
            alerts.append("📊 Highly volatile hiring — unpredictable job availability month-to-month.")
        if sal_stab["annual_pct"] < -3:
            alerts.append(f"💰 Salary compression detected ({sal_stab['annual_pct']:.1f}%/yr). Employer power increasing.")
        if supply.get("ratio") and supply["ratio"] > 80:
            alerts.append(f"👥 Very high competition ({supply['ratio']:.0f} applicants/opening). Difficult market to enter.")

        return alerts if alerts else ["✅ No major stability concerns detected."]