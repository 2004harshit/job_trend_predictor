import re
import ast
import logging
from typing import Dict, List, Optional, Tuple
from collections import Counter, defaultdict
import pandas as pd


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


class RoleEvolutionEngine:

    MIN_SAMPLES = 5

    TRANSITION_GRAPH = {
        "junior data scientist": {
            "mid data scientist":     0.70,
            "data analyst":           0.15,
            "ml engineer":            0.15,
        },
        "mid data scientist": {
            "senior data scientist":  0.55,
            "ml engineer":            0.25,
            "data science manager":   0.10,
            "data architect":         0.10,
        },
        "senior data scientist": {
            "lead data scientist":      0.40,
            "principal data scientist": 0.25,
            "data science manager":     0.25,
            "chief data scientist":     0.10,
        },
        "lead data scientist": {
            "principal data scientist": 0.45,
            "data science director":    0.35,
            "chief data scientist":     0.20,
        },
        "junior ml engineer": {
            "ml engineer":        0.75,
            "data scientist":     0.15,
            "software engineer":  0.10,
        },
        "ml engineer": {
            "senior ml engineer": 0.65,
            "data scientist":     0.20,
            "mlops engineer":     0.15,
        },
        "senior ml engineer": {
            "staff ml engineer":   0.45,
            "ml architect":        0.30,
            "engineering manager": 0.25,
        },
        "junior software engineer": {
            "software engineer":  0.75,
            "frontend developer": 0.15,
            "backend developer":  0.10,
        },
        "software engineer": {
            "senior software engineer": 0.65,
            "full stack developer":     0.20,
            "devops engineer":          0.15,
        },
        "senior software engineer": {
            "staff engineer":      0.40,
            "tech lead":           0.35,
            "engineering manager": 0.25,
        },
        "tech lead": {
            "engineering manager": 0.50,
            "staff engineer":      0.30,
            "principal engineer":  0.20,
        },
        "staff engineer": {
            "principal engineer":     0.55,
            "engineering manager":    0.25,
            "distinguished engineer": 0.20,
        },
        "junior frontend developer": {
            "frontend developer":  0.75,
            "ui/ux developer":     0.15,
            "full stack developer":0.10,
        },
        "frontend developer": {
            "senior frontend developer": 0.65,
            "full stack developer":      0.25,
            "ui/ux engineer":            0.10,
        },
        "senior frontend developer": {
            "lead frontend developer": 0.45,
            "full stack engineer":     0.30,
            "frontend architect":      0.25,
        },
        "junior backend developer": {
            "backend developer":   0.75,
            "full stack developer":0.15,
            "software engineer":   0.10,
        },
        "backend developer": {
            "senior backend developer": 0.65,
            "software engineer":        0.20,
            "devops engineer":          0.15,
        },
        "senior backend developer": {
            "lead backend developer": 0.40,
            "backend architect":      0.35,
            "engineering manager":    0.25,
        },
        "junior devops engineer": {
            "devops engineer":  0.75,
            "cloud engineer":   0.15,
            "sre":              0.10,
        },
        "devops engineer": {
            "senior devops engineer": 0.60,
            "cloud architect":        0.20,
            "sre":                    0.20,
        },
        "senior devops engineer": {
            "devops architect":    0.45,
            "cloud architect":     0.35,
            "engineering manager": 0.20,
        },
        "data analyst": {
            "senior data analyst": 0.65,
            "data scientist":      0.25,
            "business analyst":    0.10,
        },
        "senior data analyst": {
            "data science manager": 0.40,
            "data scientist":       0.35,
            "analytics lead":       0.25,
        },
        "engineering manager": {
            "senior engineering manager": 0.55,
            "director of engineering":    0.30,
            "vp engineering":             0.15,
        },
        "data science manager": {
            "director of data science": 0.55,
            "vp of data":               0.25,
            "chief data officer":        0.20,
        },
    }

    ROLE_METADATA = {
        "junior data scientist":       {"track": "IC",  "level": 1, "domain": "data_science"},
        "mid data scientist":          {"track": "IC",  "level": 2, "domain": "data_science"},
        "senior data scientist":       {"track": "IC",  "level": 3, "domain": "data_science"},
        "lead data scientist":         {"track": "IC",  "level": 4, "domain": "data_science"},
        "principal data scientist":    {"track": "IC",  "level": 5, "domain": "data_science"},
        "data science manager":        {"track": "MGT", "level": 3, "domain": "data_science"},
        "ml engineer":                 {"track": "IC",  "level": 2, "domain": "ml_engineering"},
        "senior ml engineer":          {"track": "IC",  "level": 3, "domain": "ml_engineering"},
        "software engineer":           {"track": "IC",  "level": 2, "domain": "software"},
        "senior software engineer":    {"track": "IC",  "level": 3, "domain": "software"},
        "tech lead":                   {"track": "IC",  "level": 4, "domain": "software"},
        "staff engineer":              {"track": "IC",  "level": 5, "domain": "software"},
        "principal engineer":          {"track": "IC",  "level": 6, "domain": "software"},
        "engineering manager":         {"track": "MGT", "level": 3, "domain": "software"},
        "frontend developer":          {"track": "IC",  "level": 2, "domain": "frontend"},
        "senior frontend developer":   {"track": "IC",  "level": 3, "domain": "frontend"},
        "backend developer":           {"track": "IC",  "level": 2, "domain": "backend"},
        "senior backend developer":    {"track": "IC",  "level": 3, "domain": "backend"},
        "devops engineer":             {"track": "IC",  "level": 2, "domain": "devops"},
        "senior devops engineer":      {"track": "IC",  "level": 3, "domain": "devops"},
        "data analyst":                {"track": "IC",  "level": 1, "domain": "analytics"},
        "senior data analyst":         {"track": "IC",  "level": 2, "domain": "analytics"},
    }

    TYPICAL_YEARS = {
        1: 1.5, 2: 2.5, 3: 3.0, 4: 3.5, 5: 4.0,
    }

    def __init__(self, custom_transitions: Dict = None):
        if custom_transitions:
            self.TRANSITION_GRAPH.update(custom_transitions)
        self._validate_transition_graph()
        self.logger = logging.getLogger(__name__)

    def _validate_transition_graph(self):
        for role, transitions in self.TRANSITION_GRAPH.items():
            total = sum(transitions.values())
            if not (0.98 <= total <= 1.02):
                raise ValueError(
                    f"Transition probabilities for '{role}' sum to {total:.3f} — must sum to 1.0."
                )

    def _filter_role(self, df: pd.DataFrame, role_title: str) -> pd.DataFrame:
        df = df.copy()
        if 'title' in df.columns:
            exact = df[df['title'].str.lower() == role_title.lower()]
            if len(exact) >= self.MIN_SAMPLES:
                return exact.copy()

        col = 'title' if 'title' in df.columns else None
        if col:
            pattern = r'\b' + re.escape(role_title) + r'\b'
            result  = df[df[col].str.contains(pattern, case=False, na=False, regex=True)]
            return result.copy()

        return pd.DataFrame()

    def _estimate_role_tenure(self, df: pd.DataFrame, role: str) -> dict:
        role_meta  = self.ROLE_METADATA.get(role.lower(), {})
        next_roles = self.TRANSITION_GRAPH.get(role.lower(), {})

        role_df = self._filter_role(df, role)
        if not role_df.empty and 'min_experience' in role_df.columns:
            min_exp = pd.to_numeric(role_df['min_experience'], errors='coerce').dropna()
            if len(min_exp) >= self.MIN_SAMPLES:
                current_median = min_exp.median()
                if next_roles:
                    best_next = max(next_roles, key=next_roles.get)
                    next_df   = self._filter_role(df, best_next)
                    if not next_df.empty and 'min_experience' in next_df.columns:
                        next_exp = pd.to_numeric(next_df['min_experience'], errors='coerce').dropna()
                        if len(next_exp) >= self.MIN_SAMPLES:
                            delta = next_exp.median() - current_median
                            if 0.5 <= delta <= 8.0:
                                return {
                                    "years":      round(delta, 1),
                                    "source":     "data_driven",
                                    "confidence": "High" if len(min_exp) >= 20 else "Medium"
                                }

        if role_meta:
            level   = role_meta.get("level", 2)
            typical = self.TYPICAL_YEARS.get(level, 2.5)
            return {"years": typical, "source": "seniority_level_fallback", "confidence": "Low"}

        return {"years": 2.5, "source": "industry_average", "confidence": "Very Low"}

    def _get_role_salary(self, df: pd.DataFrame, role: str) -> Optional[dict]:
        role_df = self._filter_role(df, role)
        if role_df.empty or 'avg_salary' not in role_df.columns:
            return None

        sal = pd.to_numeric(role_df['avg_salary'], errors='coerce').dropna()
        if len(sal) < self.MIN_SAMPLES:
            return None

        Q1, Q3    = sal.quantile(0.25), sal.quantile(0.75)
        sal_clean = sal[(sal >= Q1 - 1.5*(Q3-Q1)) & (sal <= Q3 + 1.5*(Q3-Q1))]
        if sal_clean.empty:
            return None

        median_lpa = round(sal_clean.median() / 100000, 2)
        return {
            "median_lpa":  median_lpa,
            "p25_lpa":     round(sal_clean.quantile(0.25) / 100000, 2),
            "p75_lpa":     round(sal_clean.quantile(0.75) / 100000, 2),
            "sample_size": len(sal_clean)
        }

    def _get_role_skills(self, df: pd.DataFrame, role: str) -> List[str]:
        """
        Extract top skills for a role from the unified 'skills' column.
        Parses both old list-repr and new plain-string format.
        """
        role_df = self._filter_role(df, role)
        if role_df.empty:
            return []

        # ── Use 'skills' column (new unified schema) ──────────────────
        if 'skills' not in role_df.columns:
            return []

        skill_counts = Counter()
        for raw in role_df['skills'].fillna('').astype(str):
            for skill in parse_skills_column(raw):
                if skill and len(skill) > 1:
                    skill_counts[skill] += 1
        # ──────────────────────────────────────────────────────────────

        return [skill for skill, _ in skill_counts.most_common(10)]

    def _get_all_next_steps(self, role: str, df: pd.DataFrame) -> List[dict]:
        role_lower  = role.lower()
        transitions = self.TRANSITION_GRAPH.get(role_lower, {})
        if not transitions:
            return []

        steps = []
        for next_role, prob in sorted(transitions.items(), key=lambda x: x[1], reverse=True):
            meta         = self.ROLE_METADATA.get(next_role, {})
            salary       = self._get_role_salary(df, next_role)
            current_meta = self.ROLE_METADATA.get(role_lower, {})
            current_level = current_meta.get("level", 0)
            next_level    = meta.get("level", 0)

            if meta.get("track") == "MGT" and current_meta.get("track") == "IC":
                move_type = "Pivot to Management"
            elif next_level > current_level:
                move_type = "Promotion"
            elif meta.get("domain") != current_meta.get("domain"):
                move_type = "Lateral + Domain Switch"
            else:
                move_type = "Lateral Move"

            steps.append({
                "role":        next_role,
                "probability": f"{round(prob * 100)}%",
                "prob_value":  prob,
                "move_type":   move_type,
                "track":       meta.get("track", "Unknown"),
                "level":       meta.get("level"),
                "salary":      salary
            })

        return steps

    def _resolve_role(self, target_role: str) -> Tuple[str, str]:
        role_lower = target_role.lower().strip()
        if role_lower in self.TRANSITION_GRAPH:
            return role_lower, "exact"

        for known_role in self.TRANSITION_GRAPH:
            if known_role in role_lower or role_lower in known_role:
                return known_role, f"fuzzy:{known_role}"

        input_words = set(role_lower.split())
        best_match, best_overlap = None, 0
        for known_role in self.TRANSITION_GRAPH:
            overlap = len(input_words & set(known_role.split()))
            if overlap > best_overlap:
                best_overlap = overlap
                best_match   = known_role

        if best_match and best_overlap >= 1:
            return best_match, f"word_match:{best_match}"

        return role_lower, "no_match"

    def _check_market_availability(self, df: pd.DataFrame, role: str) -> dict:
        role_df      = self._filter_role(df, role)
        OPENINGS_COL = 'no_of_opening'

        if role_df.empty:
            return {"listings": 0, "signal": "⚠️  Not found in market data"}

        listing_count = len(role_df)
        openings      = 0
        if OPENINGS_COL in role_df.columns:
            openings = int(pd.to_numeric(role_df[OPENINGS_COL], errors='coerce').fillna(0).sum())

        signal = (
            "✅ Active market"              if listing_count >= 50 else
            "🟡 Moderate demand"            if listing_count >= 15 else
            "🟠 Niche role — limited openings" if listing_count >= 5 else
            "🔴 Rare in current market"
        )

        return {"listings": listing_count, "openings": openings or None, "signal": signal}

    def predict_evolution_path(self,
                                df: pd.DataFrame,
                                current_role: str,
                                steps: int = 3,
                                show_branches: bool = True) -> dict:
        matched_role, match_type = self._resolve_role(current_role)

        if match_type == "no_match":
            return {
                "error":       f"Role '{current_role}' not found in career transition graph.",
                "suggestions": list(self.TRANSITION_GRAPH.keys())[:10]
            }

        path        = []
        current     = matched_role
        total_years = 0

        for step in range(steps):
            if current not in self.TRANSITION_GRAPH:
                break

            step_data = {
                "step":                step + 1,
                "from_role":           current,
                "tenure_estimate":     self._estimate_role_tenure(df, current),
                "market_availability": self._check_market_availability(df, current)
            }

            if show_branches:
                step_data["next_options"] = self._get_all_next_steps(current, df)
                next_role = step_data["next_options"][0]["role"] if step_data["next_options"] else None
            else:
                transitions = self.TRANSITION_GRAPH.get(current, {})
                if transitions:
                    next_role = max(transitions, key=transitions.get)
                    step_data["next_option"] = {
                        "role":        next_role,
                        "probability": f"{round(transitions[next_role] * 100)}%",
                        "salary":      self._get_role_salary(df, next_role)
                    }
                else:
                    next_role = None

            path.append(step_data)
            years        = step_data["tenure_estimate"]["years"] if step_data["tenure_estimate"] else 2.5
            total_years += years

            if not next_role:
                break
            current = next_role

        final_role = path[-1]["from_role"] if path else matched_role
        final_meta = self.ROLE_METADATA.get(final_role, {})

        return {
            "Starting_Role": current_role,
            "Matched_Role":  matched_role,
            "Match_Type":    match_type,
            "Evolution_Path": path,
            "Journey_Summary": {
                "Total_Steps":  len(path),
                "Total_Years":  round(total_years, 1),
                "Final_Role":   final_role,
                "Final_Level":  final_meta.get("level", "Unknown"),
                "Final_Track":  final_meta.get("track", "Unknown")
            },
            "Insights": {
                "Fastest_Growth_Role": max(
                    self.ROLE_METADATA.items(), key=lambda x: x[1].get("level", 0)
                )[0] if self.ROLE_METADATA else None,
                "Management_Pivot_Point": next(
                    (role for role, meta in self.ROLE_METADATA.items()
                     if meta.get("track") == "MGT"), None
                )
            }
        }