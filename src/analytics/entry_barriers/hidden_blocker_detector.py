import re
import logging
from typing import Dict, List, Tuple
import pandas as pd
import numpy as np


class HiddenBlockerDetector:

    MIN_SAMPLES = 10

    BLOCKER_DEFINITIONS = {
        "experience_inflation": {
            "category":    "Experience Barrier",
            "weight":      0.90,
            "description": "Entry-level roles scarce — prior experience effectively required",
            "resolution":  "Target internships, freelance projects, or open-source to build verifiable experience before applying."
        },
        "senior_dominated": {
            "category":    "Experience Barrier",
            "weight":      0.80,
            "description": "Domain heavily favors 3+ year experienced candidates",
            "resolution":  "Apply to startups and early-stage companies — they hire more flexibly on experience."
        },
        "portfolio_dependency": {
            "category":    "Portfolio Barrier",
            "weight":      0.80,
            "description": "Portfolio/GitHub/live projects explicitly required",
            "resolution":  "Build 2-3 deployed projects with GitHub. Focus on quality over quantity."
        },
        "github_required": {
            "category":    "Portfolio Barrier",
            "weight":      0.75,
            "description": "GitHub profile or code samples directly requested",
            "resolution":  "Maintain active GitHub with pinned repositories, good READMEs, and recent commits."
        },
        "cgpa_filter": {
            "category":    "Academic Barrier",
            "weight":      0.70,
            "description": "CGPA/GPA minimum thresholds mentioned in job descriptions",
            "resolution":  "Compensate with strong projects and GitHub if CGPA is below threshold."
        },
        "premium_degree": {
            "category":    "Academic Barrier",
            "weight":      0.65,
            "description": "IIT/NIT/premier institute preference mentioned",
            "resolution":  "Focus on off-campus applications and referrals — tier-1 filter is less strict in product startups."
        },
        "pg_required": {
            "category":    "Academic Barrier",
            "weight":      0.75,
            "description": "Masters/Post-Graduate degree strongly preferred or required",
            "resolution":  "Consider online MS programs or certifications as PG equivalents for early applications."
        },
        "math_heavy": {
            "category":    "Technical Depth Barrier",
            "weight":      0.70,
            "description": "Heavy theoretical math (statistics, calculus, linear algebra) expected",
            "resolution":  "Complete Khan Academy Statistics + Linear Algebra before applying."
        },
        "dsa_intensive": {
            "category":    "Technical Depth Barrier",
            "weight":      0.75,
            "description": "Strong DSA/competitive programming expected in interviews",
            "resolution":  "Solve 150+ LeetCode problems (focus on medium). Practice arrays, trees, DP patterns."
        },
        "system_design_required": {
            "category":    "Technical Depth Barrier",
            "weight":      0.70,
            "description": "System design rounds expected even for junior roles",
            "resolution":  "Study Grokking System Design. Practice designing URL shorteners, chat apps, news feeds."
        },
        "relocation_mandatory": {
            "category":    "Logistics Barrier",
            "weight":      0.60,
            "description": "On-site/relocation to specific cities required",
            "resolution":  "Filter for remote-first companies or target the required city proactively."
        },
        "bond_agreement": {
            "category":    "Logistics Barrier",
            "weight":      0.85,
            "description": "Service bond or notice period commitments mentioned",
            "resolution":  "Read bond terms carefully. Negotiate or avoid companies with aggressive bond clauses."
        },
        "applicant_surge": {
            "category":    "Market Barrier",
            "weight":      0.85,
            "description": "Extremely high applicant-to-opening ratio",
            "resolution":  "Apply within 24 hours of posting. Use referrals. Customize every application."
        },
        "niche_tool_lock": {
            "category":    "Technical Barrier",
            "weight":      0.65,
            "description": "Highly specific proprietary tools required (SAP, Salesforce, specific ERP systems)",
            "resolution":  "Get certified in the specific tool. Free trials often available for practice."
        },
    }

    BLOCKER_KEYWORDS = {
        "portfolio_dependency": [
            'portfolio', 'personal project', 'side project',
            'live link', 'demo link', 'deployed project', 'showcase'
        ],
        "github_required": [
            'github', 'gitlab', 'bitbucket', 'code sample',
            'code repository', 'open source contribution', 'github profile'
        ],
        "math_heavy": [
            'linear algebra', 'calculus', 'probability theory',
            'statistical inference', 'bayesian', 'stochastic',
            'mathematical modeling', 'differential equations',
            'convex optimization', 'matrix decomposition'
        ],
        "dsa_intensive": [
            'data structures', 'algorithms', 'leetcode', 'competitive programming',
            'dynamic programming', 'graph algorithms', 'tree traversal',
            'time complexity', 'space complexity', 'problem solving round'
        ],
        "system_design_required": [
            'system design', 'low level design', 'lld', 'high level design',
            'hld', 'design patterns', 'scalable system', 'distributed system',
            'microservices architecture', 'design interview'
        ],
        "cgpa_filter": [
            'cgpa', 'gpa', 'percentage above', 'minimum aggregate',
            'academic score', '7.5 cgpa', '8 cgpa', '60%', '65%', '70%'
        ],
        "premium_degree": [
            'iit', 'nit', 'bits', 'iiit', 'premier institute',
            'tier 1', 'top university', 'reputed college', 'top college'
        ],
        "pg_required": [
            'masters', 'mtech', 'm.tech', 'msc', 'm.sc', 'post graduate',
            'pg degree', 'postgraduate', 'ms degree', 'mba preferred'
        ],
        "relocation_mandatory": [
            'must relocate', 'relocation required', 'bangalore only',
            'pune only', 'onsite mandatory', 'work from office',
            'no remote', 'hybrid mandatory', 'immediate joiner'
        ],
        "bond_agreement": [
            'service bond', 'training bond', 'bond period',
            'bond agreement', '2 year bond', '1 year bond',
            'clawback', 'recovery clause', 'training cost recovery'
        ],
        "niche_tool_lock": [
            'sap', 'salesforce', 'oracle erp', 'workday', 'servicenow',
            'tibco', 'informatica', 'ab initio', 'datastage'
        ],
    }

    def __init__(self, custom_weights: Dict = None):
        if custom_weights:
            for key, val in custom_weights.items():
                if key in self.BLOCKER_DEFINITIONS:
                    self.BLOCKER_DEFINITIONS[key]["weight"] = val
        self.logger = logging.getLogger(__name__)

    def _filter_domain(self, df: pd.DataFrame,
                       target_domain: str,
                       experience_band: Tuple = (0, 3)) -> pd.DataFrame:
        df = df.copy()
        if 'title' in df.columns:
            exact = df[df['title'].str.lower() == target_domain.lower()]
            domain_df = exact if len(exact) >= self.MIN_SAMPLES else pd.DataFrame()
        else:
            domain_df = pd.DataFrame()

        if domain_df.empty:
            col = 'title' if 'title' in df.columns else None
            if col:
                pattern = r'\b' + re.escape(target_domain) + r'\b'
                domain_df = df[df[col].str.contains(pattern, case=False, na=False, regex=True)]

        if domain_df.empty:
            return pd.DataFrame()

        if 'min_experience' in domain_df.columns:
            min_e, max_e = experience_band
            domain_df = domain_df[
                (domain_df['min_experience'] >= min_e) &
                (domain_df['min_experience'] <= max_e + 1)
            ]

        return domain_df.copy()

    def _safe_keyword_pct(self, series: pd.Series,
                           keywords: List[str]) -> Tuple[float, int]:
        valid   = series.dropna().astype(str)
        n_valid = len(valid)
        if n_valid == 0:
            return 0.0, 0
        pattern = r'\b(?:' + '|'.join(re.escape(kw) for kw in keywords) + r')\b'
        matches = valid.str.contains(pattern, case=False, na=False, regex=True)
        return float(matches.mean() * 100), n_valid

    def _compute_market_baselines(self, df: pd.DataFrame,
                                   experience_band: Tuple) -> Dict:
        if 'title' not in df.columns:
            return {}

        baselines = {}

        if 'min_experience' in df.columns:
            min_e, max_e = experience_band
            df_band = df[df['min_experience'] <= max_e + 1]
        else:
            df_band = df

        # Fresher % across all domains
        fresher_pcts = []
        for domain in df_band['title'].dropna().unique():
            d = df_band[df_band['title'] == domain]
            if len(d) < 5:
                continue
            if 'min_experience' in d.columns:
                pct = (d['min_experience'] <= 1).mean() * 100
                fresher_pcts.append(pct)

        if fresher_pcts:
            baselines['fresher_pct_p25'] = float(np.percentile(fresher_pcts, 25))
            baselines['fresher_pct_p50'] = float(np.percentile(fresher_pcts, 50))

        # ── Applicant ratio baseline — uses actual column names ────────
        APPLICANT_COL = 'no_of_applicant'
        OPENINGS_COL  = 'no_of_opening'
        if APPLICANT_COL in df.columns and OPENINGS_COL in df.columns:
            ratios = []
            for domain in df_band['title'].dropna().unique():
                d = df_band[df_band['title'] == domain]
                if len(d) < 5:
                    continue
                apps  = pd.to_numeric(d[APPLICANT_COL], errors='coerce').sum()
                opens = max(pd.to_numeric(d[OPENINGS_COL], errors='coerce').fillna(1).sum(), 1)
                ratios.append(apps / opens)
            if ratios:
                baselines['applicant_ratio_p75'] = float(np.percentile(ratios, 75))
                baselines['applicant_ratio_p90'] = float(np.percentile(ratios, 90))
        # ──────────────────────────────────────────────────────────────

        return baselines

    def _detect_experience_blockers(self, domain_df: pd.DataFrame,
                                    baselines: Dict) -> List[dict]:
        blockers = []
        if 'min_experience' not in domain_df.columns:
            return blockers

        fresher_threshold = baselines.get('fresher_pct_p25', 30.0)
        fresher_pct = (domain_df['min_experience'] <= 1).mean() * 100

        if fresher_pct < fresher_threshold:
            gap      = (fresher_threshold - fresher_pct) / fresher_threshold
            severity = gap * self.BLOCKER_DEFINITIONS["experience_inflation"]["weight"]
            blockers.append({
                "blocker_id": "experience_inflation",
                "category":   "Experience Barrier",
                "severity":   round(severity, 3),
                "evidence":   f"Only {fresher_pct:.1f}% of postings accept 0-1yr exp (market avg: {fresher_threshold:.1f}%)",
                "message":    self.BLOCKER_DEFINITIONS["experience_inflation"]["description"],
                "resolution": self.BLOCKER_DEFINITIONS["experience_inflation"]["resolution"]
            })

        senior_pct       = (domain_df['min_experience'] >= 3).mean() * 100
        senior_threshold = baselines.get('senior_pct_p75', 50.0)
        if senior_pct > senior_threshold:
            severity = (senior_pct / 100) * self.BLOCKER_DEFINITIONS["senior_dominated"]["weight"]
            blockers.append({
                "blocker_id": "senior_dominated",
                "category":   "Experience Barrier",
                "severity":   round(severity, 3),
                "evidence":   f"{senior_pct:.1f}% of postings require 3+ years experience.",
                "message":    self.BLOCKER_DEFINITIONS["senior_dominated"]["description"],
                "resolution": self.BLOCKER_DEFINITIONS["senior_dominated"]["resolution"]
            })

        return blockers

    def _detect_description_blockers(self, domain_df: pd.DataFrame) -> List[dict]:
        """
        Uses 'description' column (lowercase — actual schema).
        Previously was checking for 'Description_Cleaned' which didn't exist.
        """
        blockers = []

        # ── Use lowercase 'description' column ────────────────────────
        if 'description' not in domain_df.columns:
            return blockers

        desc = domain_df['description']
        # ──────────────────────────────────────────────────────────────

        keyword_blockers = [
            "portfolio_dependency", "github_required", "math_heavy",
            "dsa_intensive", "system_design_required", "cgpa_filter",
            "premium_degree", "pg_required", "relocation_mandatory",
            "bond_agreement", "niche_tool_lock"
        ]

        thresholds = {
            "portfolio_dependency":   40.0,
            "github_required":        35.0,
            "math_heavy":             35.0,
            "dsa_intensive":          35.0,
            "system_design_required": 25.0,
            "cgpa_filter":            20.0,
            "premium_degree":         15.0,
            "pg_required":            20.0,
            "relocation_mandatory":   20.0,
            "bond_agreement":         15.0,
            "niche_tool_lock":        25.0,
        }

        for blocker_id in keyword_blockers:
            if blocker_id not in self.BLOCKER_KEYWORDS:
                continue

            keywords = self.BLOCKER_KEYWORDS[blocker_id]
            pct, n_valid = self._safe_keyword_pct(desc, keywords)

            if n_valid < 3:
                continue

            threshold = thresholds.get(blocker_id, 30.0)
            if pct >= threshold:
                defn       = self.BLOCKER_DEFINITIONS[blocker_id]
                weight     = defn["weight"]
                normalized = min(1.0, (pct - threshold) / threshold + 0.3)
                severity   = round(normalized * weight, 3)

                blockers.append({
                    "blocker_id": blocker_id,
                    "category":   defn["category"],
                    "severity":   severity,
                    "evidence":   f"{pct:.1f}% of job descriptions mention this requirement (threshold: {threshold:.0f}%)",
                    "message":    defn["description"],
                    "resolution": defn["resolution"]
                })

        return blockers

    def _detect_market_blockers(self, domain_df: pd.DataFrame,
                                 all_df: pd.DataFrame,
                                 baselines: Dict) -> List[dict]:
        """
        Uses actual column names: 'no_of_applicant' and 'no_of_opening'.
        """
        blockers = []

        # ── Actual column names ────────────────────────────────────────
        APPLICANT_COL = 'no_of_applicant'
        OPENINGS_COL  = 'no_of_opening'
        # ──────────────────────────────────────────────────────────────

        if APPLICANT_COL not in domain_df.columns:
            return blockers

        apps  = pd.to_numeric(domain_df[APPLICANT_COL], errors='coerce')
        opens = pd.to_numeric(
            domain_df[OPENINGS_COL] if OPENINGS_COL in domain_df.columns
            else pd.Series([1] * len(domain_df)),
            errors='coerce'
        ).fillna(1)

        valid_apps = apps.dropna()
        if valid_apps.empty:
            return blockers

        apps_clipped = apps.clip(upper=apps.quantile(0.95))
        ratio = apps_clipped.sum() / max(opens.sum(), 1)

        surge_threshold = baselines.get('applicant_ratio_p75', 50.0)
        if ratio > surge_threshold:
            normalized = min(1.0, (ratio - surge_threshold) / surge_threshold + 0.3)
            severity   = round(normalized * self.BLOCKER_DEFINITIONS["applicant_surge"]["weight"], 3)
            blockers.append({
                "blocker_id": "applicant_surge",
                "category":   "Market Barrier",
                "severity":   severity,
                "evidence":   f"{ratio:.0f} applicants per opening (market P75: {surge_threshold:.0f})",
                "message":    self.BLOCKER_DEFINITIONS["applicant_surge"]["description"],
                "resolution": self.BLOCKER_DEFINITIONS["applicant_surge"]["resolution"]
            })

        return blockers

    def _analyze_blocker_interactions(self, blockers: List[dict]) -> dict:
        blocker_ids  = {b["blocker_id"] for b in blockers}
        interactions = []

        INTERACTION_RULES = [
            {
                "combo":   {"experience_inflation", "applicant_surge"},
                "label":   "🚨 Double Entry Lock",
                "message": "Scarce fresher roles + massive competition. Breaking in requires exceptional differentiation.",
                "penalty": 0.15
            },
            {
                "combo":   {"math_heavy", "dsa_intensive", "system_design_required"},
                "label":   "🔬 Full Technical Gauntlet",
                "message": "3-layer technical interview expected: math theory + DSA + system design.",
                "penalty": 0.20
            },
            {
                "combo":   {"cgpa_filter", "premium_degree"},
                "label":   "🎓 Double Credential Lock",
                "message": "Both CGPA threshold AND college tier filter active.",
                "penalty": 0.15
            },
            {
                "combo":   {"portfolio_dependency", "github_required"},
                "label":   "💻 Full Proof-of-Work Required",
                "message": "Both portfolio AND GitHub explicitly required.",
                "penalty": 0.10
            },
            {
                "combo":   {"experience_inflation", "pg_required"},
                "label":   "📚 Experience + Education Lock",
                "message": "Needs both work experience AND advanced degree for entry.",
                "penalty": 0.20
            },
            {
                "combo":   {"bond_agreement", "relocation_mandatory"},
                "label":   "⛓️  Commitment Lock",
                "message": "Must relocate AND sign bond. Very low flexibility.",
                "penalty": 0.10
            },
        ]

        interaction_penalty = 0.0
        for rule in INTERACTION_RULES:
            if rule["combo"].issubset(blocker_ids):
                interactions.append({
                    "label": rule["label"], "message": rule["message"], "penalty": rule["penalty"]
                })
                interaction_penalty += rule["penalty"]

        return {"detected_interactions": interactions, "interaction_penalty": round(interaction_penalty, 3)}

    def _normalize_risk_score(self, blockers: List[dict], interaction_penalty: float) -> dict:
        if not blockers:
            return {"score": 0.0, "label": "🟢 No Blockers Detected", "color": "Green"}

        severities = sorted([b["severity"] for b in blockers], reverse=True)
        combined   = sum(s * (0.8 ** i) for i, s in enumerate(severities))
        combined   = min(1.0, combined + interaction_penalty)

        if combined < 0.20:   label, color = "🟢 Low Barrier",                        "Green"
        elif combined < 0.40: label, color = "🟡 Moderate Barrier",                   "Yellow"
        elif combined < 0.60: label, color = "🟠 High Barrier",                       "Orange"
        elif combined < 0.80: label, color = "🔴 Very High Barrier",                  "Red"
        else:                 label, color = "🚨 Extreme Barrier — Expect Rejections", "Dark Red"

        return {"score": round(combined, 3), "label": label, "color": color}

    def scan_for_blockers(self, df: pd.DataFrame,
                           target_domain: str,
                           experience_band: Tuple = (0, 3)) -> dict:
        domain_df = self._filter_domain(df, target_domain, experience_band)

        if domain_df.empty:
            return {"error": f"No data found for domain: '{target_domain}'"}
        if len(domain_df) < self.MIN_SAMPLES:
            return {"error": f"Insufficient data: {len(domain_df)} records (need {self.MIN_SAMPLES}+)."}

        baselines    = self._compute_market_baselines(df, experience_band)
        all_blockers = []
        all_blockers.extend(self._detect_experience_blockers(domain_df, baselines))
        all_blockers.extend(self._detect_description_blockers(domain_df))
        all_blockers.extend(self._detect_market_blockers(domain_df, df, baselines))

        interaction_data = self._analyze_blocker_interactions(all_blockers)
        risk = self._normalize_risk_score(all_blockers, interaction_data["interaction_penalty"])

        all_blockers.sort(key=lambda x: x["severity"], reverse=True)

        top_resolutions = [
            {"blocker": b["blocker_id"], "action": b["resolution"]}
            for b in all_blockers[:4]
        ]

        return {
            "Domain":          target_domain,
            "Experience_Band": experience_band,
            "Sample_Size":     len(domain_df),

            "Overall_Risk": risk,

            "Detected_Blockers": [
                {"blocker_id": b["blocker_id"], "category": b["category"],
                 "severity": b["severity"], "evidence": b["evidence"], "message": b["message"]}
                for b in all_blockers
            ],

            "Blocker_Interactions": interaction_data["detected_interactions"],
            "Priority_Actions":     top_resolutions,

            "Blocker_Summary": {
                "Total_Blockers":      len(all_blockers),
                "Categories_Affected": list({b["category"] for b in all_blockers}),
                "Highest_Severity":    all_blockers[0]["blocker_id"] if all_blockers else None,
            }
        }


if __name__ == "__main__":
    import json
    df = pd.read_csv(r"D:\DATA SCIENCE AND ML\Project\job_trend_predictor\data\processed\cleaned\cleaned_job_data.csv")
    detector = HiddenBlockerDetector()
    result = detector.scan_for_blockers(df, target_domain="Data Scientist", experience_band=(0, 3))
    print(json.dumps(result, indent=2))