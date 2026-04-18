import re
import ast
import logging
from typing import Dict, Optional
import pandas as pd
import numpy as np


# ── Central Skills Parser (same helper used across all engines) ───────────────
def parse_skills_column(raw) -> list:
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
# ─────────────────────────────────────────────────────────────────────────────


class DomainStabilityEngine:

    MIN_MONTHS_FOR_TREND = 1
    MIN_MONTHS_FOR_PROJECTION = 3

    SKILL_AUTOMATION_RISK = {
        'data entry':       0.90, 'manual testing':   0.75,
        'excel':            0.65, 'copy editing':     0.60,
        'basic sql':        0.55, 'report generation':0.60,
        'frontend':         0.35, 'web development':  0.30,
        'java':             0.25, 'python':           0.20,
        'devops':           0.20, 'cloud':            0.18,
        'machine learning': 0.12, 'data science':     0.15,
        'system design':    0.10, 'architecture':     0.08,
        'research':         0.07, 'ml engineering':   0.10,
        'llm':              0.05, 'ai research':      0.04,
        'product management':0.10,'cybersecurity':    0.08,
    }

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
            "trend_stability":    0.30,
            "volatility":         0.20,
            "ai_resistance":      0.25,
            "salary_stability":   0.15,
            "supply_health":      0.10,
        }
        self.weights = weights or default_weights
        self._validate_weights()
        self.logger = logging.getLogger(__name__)

    def _validate_weights(self):
        total = sum(self.weights.values())
        if not (0.98 <= total <= 1.02):
            raise ValueError(f"Weights must sum to 1.0, got {total:.3f}")

    def _filter_domain(self, df: pd.DataFrame, target_domain: str) -> pd.DataFrame:
        df = df.copy()
        for col in ['timestamp', 'posted_date']:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')

        if 'job_type' in df.columns:
            exact = df[df['job_type'].str.lower() == target_domain.lower()]
            if len(exact) >= self.MIN_MONTHS_FOR_TREND * 3:
                return exact

        title_col = 'title' if 'title' in df.columns else None
        if title_col:
            pattern = r'\b' + re.escape(target_domain) + r'\b'
            return df[df[title_col].str.contains(
                pattern, case=False, na=False, regex=True
            )]

        return pd.DataFrame()

    def _build_monthly_series(self, domain_df: pd.DataFrame) -> pd.Series:
        date_col = 'posted_date' if 'posted_date' in domain_df.columns else 'timestamp'
        df = domain_df.copy()
        df['_date'] = pd.to_datetime(df[date_col], errors='coerce')
        df = df.dropna(subset=['_date'])

        if df.empty:
            return pd.Series(dtype=float)

        openings_col = 'no_of_opening'
        if openings_col in df.columns:
            df['_count'] = pd.to_numeric(df[openings_col], errors='coerce').fillna(1)
        else:
            df['_count'] = 1

        df['_month'] = df['_date'].dt.to_period('M')
        monthly = df.groupby('_month')['_count'].sum().sort_index()

        if monthly.empty:
            return pd.Series(dtype=float)

        current_period = pd.Timestamp.now().to_period('M')
        if monthly.index[-1] == current_period:
            monthly = monthly.iloc[:-1]
            self.logger.info("Trimmed current (incomplete) month from time series.")

        return monthly

    def _build_salary_series(self, domain_df: pd.DataFrame) -> pd.Series:
        date_col = 'posted_date' if 'posted_date' in domain_df.columns else 'timestamp'
        sal_col = None
        for col in ['avg_salary', 'min_salary']:
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

        y_pred = model.predict(x)
        ss_res = np.sum((values - y_pred) ** 2)
        ss_tot = np.sum((values - values.mean()) ** 2)
        r_squared = max(0.0, 1 - ss_res / ss_tot) if ss_tot > 0 else 0.0

        mean_val = values.mean()
        norm_slope = (raw_slope / mean_val) if mean_val > 0 else 0.0

        if len(monthly) >= self.MIN_MONTHS_FOR_PROJECTION:
            future_step = len(values) + 12
            projected_12m = max(0, float(model.predict([[future_step]])[0]))
            current = values[-1]
            projection_growth = (projected_12m - current) / current if current > 0 else 0.0
        else:
            projection_growth = norm_slope * 12

        trend_score = 1 / (1 + np.exp(-norm_slope * 10))
        reliability = min(1.0, r_squared * 2)
        trend_score = trend_score * reliability + 0.5 * (1 - reliability)

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
        if len(monthly) < 2:
            return {"score": 0.5, "cv": 0.5, "interpretation": "Insufficient data"}

        values = monthly.values.astype(float)
        mean_val = values.mean()

        if mean_val == 0:
            return {"score": 1.0, "cv": 1.0, "interpretation": "No demand — maximum instability"}

        if len(values) >= 4:
            x = np.arange(len(values)).reshape(-1, 1)
            from sklearn.linear_model import LinearRegression
            trend = LinearRegression().fit(x, values).predict(x)
            residuals = values - trend
            cv = residuals.std() / mean_val
        else:
            cv = values.std() / mean_val

        volatility_score = np.clip(cv, 0, 1.5) / 1.5
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
            "score":          round(stability_contribution, 3),
            "cv":             round(cv, 3),
            "volatility_raw": round(volatility_score, 3),
            "interpretation": interpretation
        }

    def _calculate_ai_risk(self, domain_df: pd.DataFrame,
                            target_domain: str) -> dict:
        """
        AI risk from three sources:
        1. Skill-composition from 'skills' column (new unified schema)
        2. Domain-level lookup with fuzzy matching
        3. Structural proxy via skill_count
        """
        # Source 1: parse 'skills' column
        skill_based_risk = None
        if 'skills' in domain_df.columns:
            all_skills_text = skills_to_text(domain_df['skills'])

            total_weight = 0.0
            weighted_risk = 0.0
            for skill_kw, risk in self.SKILL_AUTOMATION_RISK.items():
                count = all_skills_text.count(skill_kw)
                if count > 0:
                    weighted_risk += risk * count
                    total_weight  += count

            if total_weight > 0:
                skill_based_risk = weighted_risk / total_weight
                self.logger.info(
                    f"Skill-based AI risk for '{target_domain}': {skill_based_risk:.2f}"
                )

        # Source 2: Domain lookup
        domain_lower = target_domain.lower()
        domain_risk = None
        for known_domain, risk in self.DOMAIN_BASE_RISK.items():
            if known_domain in domain_lower or domain_lower in known_domain:
                domain_risk = risk
                break

        # Source 3: Structural proxy
        structural_risk = 0.4
        if 'skill_count' in domain_df.columns:
            median_skills = pd.to_numeric(
                domain_df['skill_count'], errors='coerce'
            ).median()
            if not pd.isna(median_skills):
                structural_risk = max(0.05, 0.7 - (median_skills * 0.04))

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
        ai_resistance_score = 1 - final_risk

        return {
            "score":            round(ai_resistance_score, 3),
            "risk_pct":         round(final_risk * 100, 1),
            "risk_label":       self._label_ai_risk(final_risk),
            "source":           source,
            "skill_based_risk": round(skill_based_risk, 3) if skill_based_risk else None,
            "domain_base_risk": round(domain_risk, 3) if domain_risk else None,
        }

    def _label_ai_risk(self, risk: float) -> str:
        if risk < 0.15: return "🟢 Very Low — Highly creative/strategic role"
        elif risk < 0.30: return "🟡 Low — Some automatable tasks but core is safe"
        elif risk < 0.50: return "🟠 Moderate — Significant automation risk in 5-10 years"
        elif risk < 0.70: return "🔴 High — Many tasks automatable now or soon"
        else:             return "🚨 Very High — Role likely disrupted within 3-5 years"

    def _calculate_salary_stability(self, salary_series: pd.Series) -> dict:
        if len(salary_series) < 3:
            return {"score": 0.5, "trend_pct": 0.0, "interpretation": "Insufficient data"}

        values = salary_series.values.astype(float)
        q1, q3 = np.percentile(values, 25), np.percentile(values, 75)
        iqr = q3 - q1
        values = values[(values >= q1 - 1.5 * iqr) & (values <= q3 + 1.5 * iqr)]

        if len(values) < 2:
            return {"score": 0.5, "trend_pct": 0.0, "interpretation": "Insufficient data"}

        x = np.arange(len(values)).reshape(-1, 1)
        from sklearn.linear_model import LinearRegression
        model = LinearRegression().fit(x, values)

        monthly_slope = float(model.coef_[0])
        base_salary   = float(model.predict([[0]])[0])
        monthly_pct   = (monthly_slope / base_salary * 100) if base_salary > 0 else 0
        annual_pct    = monthly_pct * 12

        if annual_pct > 15:
            score = 0.9
        elif annual_pct > 5:
            score = 0.7
        elif annual_pct > 0:
            score = 0.5
        elif annual_pct > -5:
            score = 0.3
        else:
            score = 0.1

        return {
            "score":          score,
            "annual_pct":     round(annual_pct, 2),
            "interpretation": (
                f"Salaries {'growing' if annual_pct > 0 else 'declining'} "
                f"at {abs(annual_pct):.1f}%/yr"
            )
        }

    def _calculate_supply_health(self, domain_df: pd.DataFrame) -> dict:
        APPLICANT_COL = 'no_of_applicant'
        OPENINGS_COL  = 'no_of_opening'

        if APPLICANT_COL not in domain_df.columns or OPENINGS_COL not in domain_df.columns:
            return {"score": 0.5, "ratio": None, "interpretation": "Data unavailable"}

        apps  = pd.to_numeric(domain_df[APPLICANT_COL], errors='coerce').dropna()
        opens = pd.to_numeric(domain_df[OPENINGS_COL],  errors='coerce').fillna(1)

        if apps.empty:
            return {"score": 0.5, "ratio": None, "interpretation": "Data unavailable"}

        ratio = apps.sum() / max(opens.sum(), 1)

        if ratio < 5:
            score = 0.3
        elif ratio <= 30:
            score = 0.8
        elif ratio <= 60:
            score = 0.6
        elif ratio <= 100:
            score = 0.35
        else:
            score = 0.15

        return {
            "score":          score,
            "ratio":          round(ratio, 1),
            "interpretation": f"{ratio:.0f} applicants per opening — {'Healthy' if score >= 0.6 else 'Concerning'}"
        }

    def calculate_stability_score(self, df: pd.DataFrame,
                                   target_domain: str) -> dict:
        domain_df = self._filter_domain(df, target_domain)
        if domain_df.empty:
            return {"error": f"No data found for domain: '{target_domain}'"}

        monthly = self._build_monthly_series(domain_df)
        if len(monthly) < self.MIN_MONTHS_FOR_TREND:
            return {
                "error": f"Insufficient time series: only {len(monthly)} months "
                         f"(need {self.MIN_MONTHS_FOR_TREND}+)."
            }

        trend     = self._calculate_trend_metrics(monthly)
        vol       = self._calculate_volatility_score(monthly)
        ai        = self._calculate_ai_risk(domain_df, target_domain)
        sal_series = self._build_salary_series(domain_df)
        sal_stab  = self._calculate_salary_stability(sal_series)
        supply    = self._calculate_supply_health(domain_df)

        score = (
            trend["trend_score"]   * self.weights["trend_stability"]  +
            vol["score"]           * self.weights["volatility"]        +
            ai["score"]            * self.weights["ai_resistance"]     +
            sal_stab["score"]      * self.weights["salary_stability"]  +
            supply["score"]        * self.weights["supply_health"]
        )
        score = round(float(np.clip(score, 0.0, 1.0)), 3)

        status, color = self._classify_stability(score, trend["direction"])
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
                "Trend_Direction":    trend["direction"],
                "Trend_Reliable":     trend["reliable"],
                "AI_Risk_Pct":        ai["risk_pct"],
                "AI_Risk_Label":      ai["risk_label"],
                "Volatility_Level":   vol["interpretation"],
                "Salary_Trend":       sal_stab["interpretation"],
                "12M_Projection_Pct": trend["projection_12m_pct"]
            }
        }

    def _classify_stability(self, score: float, direction: str) -> tuple:
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


if __name__ == "__main__":
    data_path = r"D:\DATA SCIENCE AND ML\Project\job_trend_predictor\data\processed\cleaned\cleaned_job_data.csv"
    df = pd.read_csv(data_path)
    dse = DomainStabilityEngine()
    result = dse.calculate_stability_score(df, "Data Analyst")
    print(result)