import re
import logging
from typing import Dict, List, Optional, Tuple
from collections import defaultdict
import pandas as pd

class RoleEvolutionEngine:
    
    MIN_SAMPLES = 5
    
    # ── Complete Career Transition Graph ─────────────────────────────
    # Structure: role → {next_role: probability}
    # Probabilities per role must sum to 1.0
    # Covers IC track, management track, and lateral moves
    
    TRANSITION_GRAPH = {
        
        # ── Data Science Track ──
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
            "lead data scientist":    0.40,
            "principal data scientist": 0.25,
            "data science manager":   0.25,
            "chief data scientist":   0.10,
        },
        "lead data scientist": {
            "principal data scientist": 0.45,
            "data science director":  0.35,
            "chief data scientist":   0.20,
        },
        
        # ── ML Engineering Track ──
        "junior ml engineer": {
            "ml engineer":            0.75,
            "data scientist":         0.15,
            "software engineer":      0.10,
        },
        "ml engineer": {
            "senior ml engineer":     0.65,
            "data scientist":         0.20,
            "mlops engineer":         0.15,
        },
        "senior ml engineer": {
            "staff ml engineer":      0.45,
            "ml architect":           0.30,
            "engineering manager":    0.25,
        },
        
        # ── Software Engineering Track ──
        "junior software engineer": {
            "software engineer":      0.75,
            "frontend developer":     0.15,
            "backend developer":      0.10,
        },
        "software engineer": {
            "senior software engineer": 0.65,
            "full stack developer":   0.20,
            "devops engineer":        0.15,
        },
        "senior software engineer": {
            "staff engineer":         0.40,
            "tech lead":              0.35,
            "engineering manager":    0.25,
        },
        "tech lead": {
            "engineering manager":    0.50,
            "staff engineer":         0.30,
            "principal engineer":     0.20,
        },
        "staff engineer": {
            "principal engineer":     0.55,
            "engineering manager":    0.25,
            "distinguished engineer": 0.20,
        },
        
        # ── Frontend Track ──
        "junior frontend developer": {
            "frontend developer":     0.75,
            "ui/ux developer":        0.15,
            "full stack developer":   0.10,
        },
        "frontend developer": {
            "senior frontend developer": 0.65,
            "full stack developer":   0.25,
            "ui/ux engineer":         0.10,
        },
        "senior frontend developer": {
            "lead frontend developer": 0.45,
            "full stack engineer":    0.30,
            "frontend architect":     0.25,
        },
        
        # ── Backend Track ──
        "junior backend developer": {
            "backend developer":      0.75,
            "full stack developer":   0.15,
            "software engineer":      0.10,
        },
        "backend developer": {
            "senior backend developer": 0.65,
            "software engineer":      0.20,
            "devops engineer":        0.15,
        },
        "senior backend developer": {
            "lead backend developer": 0.40,
            "backend architect":      0.35,
            "engineering manager":    0.25,
        },
        
        # ── DevOps / Cloud Track ──
        "junior devops engineer": {
            "devops engineer":        0.75,
            "cloud engineer":         0.15,
            "sre":                    0.10,
        },
        "devops engineer": {
            "senior devops engineer": 0.60,
            "cloud architect":        0.20,
            "sre":                    0.20,
        },
        "senior devops engineer": {
            "devops architect":       0.45,
            "cloud architect":        0.35,
            "engineering manager":    0.20,
        },
        
        # ── Data Analysis Track ──
        "data analyst": {
            "senior data analyst":    0.65,
            "data scientist":         0.25,
            "business analyst":       0.10,
        },
        "senior data analyst": {
            "data science manager":   0.40,
            "data scientist":         0.35,
            "analytics lead":         0.25,
        },
        
        # ── Management Track (convergence point) ──
        "engineering manager": {
            "senior engineering manager": 0.55,
            "director of engineering":    0.30,
            "vp engineering":             0.15,
        },
        "data science manager": {
            "director of data science":   0.55,
            "vp of data":                 0.25,
            "chief data officer":         0.20,
        },
    }
    
    # ── Role Metadata ─────────────────────────────────────────────────
    # Track type and seniority level for each role
    ROLE_METADATA = {
        # IC = Individual Contributor, MGT = Management, SPEC = Specialist
        "junior data scientist":       {"track": "IC",   "level": 1, "domain": "data_science"},
        "mid data scientist":          {"track": "IC",   "level": 2, "domain": "data_science"},
        "senior data scientist":       {"track": "IC",   "level": 3, "domain": "data_science"},
        "lead data scientist":         {"track": "IC",   "level": 4, "domain": "data_science"},
        "principal data scientist":    {"track": "IC",   "level": 5, "domain": "data_science"},
        "data science manager":        {"track": "MGT",  "level": 3, "domain": "data_science"},
        "ml engineer":                 {"track": "IC",   "level": 2, "domain": "ml_engineering"},
        "senior ml engineer":          {"track": "IC",   "level": 3, "domain": "ml_engineering"},
        "software engineer":           {"track": "IC",   "level": 2, "domain": "software"},
        "senior software engineer":    {"track": "IC",   "level": 3, "domain": "software"},
        "tech lead":                   {"track": "IC",   "level": 4, "domain": "software"},
        "staff engineer":              {"track": "IC",   "level": 5, "domain": "software"},
        "principal engineer":          {"track": "IC",   "level": 6, "domain": "software"},
        "engineering manager":         {"track": "MGT",  "level": 3, "domain": "software"},
        "frontend developer":          {"track": "IC",   "level": 2, "domain": "frontend"},
        "senior frontend developer":   {"track": "IC",   "level": 3, "domain": "frontend"},
        "backend developer":           {"track": "IC",   "level": 2, "domain": "backend"},
        "senior backend developer":    {"track": "IC",   "level": 3, "domain": "backend"},
        "devops engineer":             {"track": "IC",   "level": 2, "domain": "devops"},
        "senior devops engineer":      {"track": "IC",   "level": 3, "domain": "devops"},
        "data analyst":                {"track": "IC",   "level": 1, "domain": "analytics"},
        "senior data analyst":         {"track": "IC",   "level": 2, "domain": "analytics"},
    }
    
    # ── Typical Years Per Seniority Level ────────────────────────────
    # Fallback when data is insufficient
    TYPICAL_YEARS = {
        1: 1.5,   # Junior → Mid (fast if learning well)
        2: 2.5,   # Mid → Senior
        3: 3.0,   # Senior → Lead/Staff
        4: 3.5,   # Lead → Principal/Director
        5: 4.0,   # Principal → Distinguished/VP
    }
    
    def __init__(self, custom_transitions: Dict = None):
        if custom_transitions:
            self.TRANSITION_GRAPH.update(custom_transitions)
        self._validate_transition_graph()
        self.logger = logging.getLogger(__name__)
    
    def _validate_transition_graph(self):
        """Ensure all transition probabilities sum to ~1.0."""
        for role, transitions in self.TRANSITION_GRAPH.items():
            total = sum(transitions.values())
            if not (0.98 <= total <= 1.02):
                raise ValueError(
                    f"Transition probabilities for '{role}' sum to {total:.3f} "
                    f"— must sum to 1.0. Fix the transition graph."
                )

    def _filter_role(self, df: pd.DataFrame,
                      role_title: str) -> pd.DataFrame:
        """Job_Type first, Title fallback. Safe copy."""
        df = df.copy()

        if 'TItle_Cleaned' in df.columns and 'Title_Cleaned' not in df.columns:
            df = df.rename(columns={'TItle_Cleaned': 'Title_Cleaned'})

        if 'Job_Type' in df.columns:
            exact = df[df['Job_Type'].str.lower() == role_title.lower()]
            if len(exact) >= self.MIN_SAMPLES:
                return exact.copy()

        col = 'Title_Cleaned' if 'Title_Cleaned' in df.columns else None
        if col:
            pattern = r'\b' + re.escape(role_title) + r'\b'
            result = df[df[col].str.contains(
                pattern, case=False, na=False, regex=True
            )]
            if not result.empty:
                return result.copy()

        return pd.DataFrame()

    def _get_time_in_role(self, df: pd.DataFrame, role: str) -> dict:
        """
        Estimate time spent at a role before transitioning.

        Fix: Max_Exp - Min_Exp is the REQUIREMENT RANGE, not tenure.
        Better proxy: Min_Experience of NEXT level - Min_Experience of current level.
        Also provides fallback from TYPICAL_YEARS table.

        Returns dict with estimate and confidence.
        """
        role_lower = role.lower()
        role_meta  = self.ROLE_METADATA.get(role_lower)

        # Method 1: Data-driven — experience midpoint delta between levels
        role_df = self._filter_role(df, role)

        if not role_df.empty and 'Min_Experience' in role_df.columns:
            min_exp = pd.to_numeric(
                role_df['Min_Experience'], errors='coerce'
            ).dropna()

            if len(min_exp) >= self.MIN_SAMPLES:
                # Find the next role in the transition graph
                next_roles = self.TRANSITION_GRAPH.get(role_lower, {})

                if next_roles:
                    best_next = max(next_roles, key=next_roles.get)
                    next_df   = self._filter_role(df, best_next)

                    if not next_df.empty and 'Min_Experience' in next_df.columns:
                        next_exp = pd.to_numeric(
                            next_df['Min_Experience'], errors='coerce'
                        ).dropna()

                        if len(next_exp) >= self.MIN_SAMPLES:
                            # Delta between median min experience requirements
                            current_median = min_exp.median()
                            next_median    = next_exp.median()
                            delta = next_median - current_median

                            # Sanity check: delta should be positive and reasonable
                            if 0.5 <= delta <= 8.0:
                                return {
                                    "years":      round(delta, 1),
                                    "source":     "data_driven",
                                    "confidence": "High" if len(min_exp) >= 20 else "Medium"
                                }

        # Method 2: Seniority-level fallback
        if role_meta:
            level = role_meta.get("level", 2)
            typical = self.TYPICAL_YEARS.get(level, 2.5)
            return {
                "years":      typical,
                "source":     "seniority_level_fallback",
                "confidence": "Low"
            }

        # Method 3: Industry average
        return {"years": 2.5, "source": "industry_average", "confidence": "Very Low"}


    def _get_role_salary(self, df: pd.DataFrame, role: str) -> Optional[dict]:
        """
        Extract median salary for a role from job data.
        Returns None if insufficient data.
        """
        role_df = self._filter_role(df, role)

        if role_df.empty or 'Avg_Salary' not in role_df.columns:
            return None

        sal = pd.to_numeric(role_df['Avg_Salary'], errors='coerce').dropna()

        if len(sal) < self.MIN_SAMPLES:
            return None

        # IQR outlier removal
        Q1, Q3 = sal.quantile(0.25), sal.quantile(0.75)
        sal_clean = sal[(sal >= Q1 - 1.5*(Q3-Q1)) & (sal <= Q3 + 1.5*(Q3-Q1))]

        if sal_clean.empty:
            return None

        median_lpa = round(sal_clean.median() / 100000, 2)  # Convert to LPA

        return {
            "median_lpa":  median_lpa,
            "p25_lpa":     round(sal_clean.quantile(0.25) / 100000, 2),
            "p75_lpa":     round(sal_clean.quantile(0.75) / 100000, 2),
            "sample_size": len(sal_clean)
        }

    def _get_role_skills(self, df: pd.DataFrame, role: str) -> List[str]:
        """
        Extract top skills required for a role.
        Used for skill gap detection between steps.
        """
        role_df = self._filter_role(df, role)

        if role_df.empty:
            return []

        skill_col = next(
            (c for c in ['Star_Skills', 'Combined_Skills'] if c in role_df.columns),
            None
        )

        if skill_col is None:
            return []

        from collections import Counter
        skill_counts = Counter()

        for skills_str in role_df[skill_col].fillna('').astype(str):
            for skill in skills_str.split(','):
                s = skill.strip().lower()
                if s and len(s) > 1:
                    skill_counts[s] += 1

        # Return top skills by frequency
        return [skill for skill, _ in skill_counts.most_common(10)]


    def _get_all_next_steps(self, role: str,
                              df: pd.DataFrame) -> List[dict]:
        """
        Return ALL possible next steps, not just the greedy best.
        Categorized by track type and with salary data.
        """
        role_lower = role.lower()
        transitions = self.TRANSITION_GRAPH.get(role_lower, {})

        if not transitions:
            return []

        steps = []
        for next_role, prob in sorted(
            transitions.items(), key=lambda x: x[1], reverse=True
        ):
            meta     = self.ROLE_METADATA.get(next_role, {})
            salary   = self._get_role_salary(df, next_role)

            # Determine move type
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
        """
        Fuzzy match target_role to known transition graph keys.
        Returns (matched_key, match_type).
        """
        role_lower = target_role.lower().strip()

        # Exact match
        if role_lower in self.TRANSITION_GRAPH:
            return role_lower, "exact"

        # Partial match
        for known_role in self.TRANSITION_GRAPH:
            if known_role in role_lower or role_lower in known_role:
                return known_role, f"fuzzy:{known_role}"

        # Word overlap
        input_words  = set(role_lower.split())
        best_match   = None
        best_overlap = 0

        for known_role in self.TRANSITION_GRAPH:
            overlap = len(input_words & set(known_role.split()))
            if overlap > best_overlap:
                best_overlap = overlap
                best_match   = known_role

        if best_match and best_overlap >= 1:
            return best_match, f"word_match:{best_match}"

        return role_lower, "no_match"


    def _check_market_availability(self, df: pd.DataFrame,
                                      role: str) -> dict:
        """
        How many postings exist for each step?
        A career step with no market presence is a red flag.
        """
        role_df = self._filter_role(df, role)

        OPENINGS_COL = 'No of job opening cleaned '

        if role_df.empty:
            return {"listings": 0, "signal": "⚠️  Not found in market data"}

        listing_count = len(role_df)

        openings = 0
        if OPENINGS_COL in role_df.columns:
            openings = int(
                pd.to_numeric(role_df[OPENINGS_COL], errors='coerce').fillna(0).sum()
            )

        signal = (
            "✅ Active market"  if listing_count >= 50 else
            "🟡 Moderate demand" if listing_count >= 15 else
            "🟠 Niche role — limited openings" if listing_count >= 5 else
            "🔴 Rare in current market"
        )

        return {
            "listings": listing_count,
            "openings": openings or None,
            "signal":   signal
        }

    def predict_evolution_path(self,
                                 df: pd.DataFrame,
                                 current_role: str,
                                 steps: int = 3,
                                 show_branches: bool = True) -> dict:
        """
        Main entry point. Full career evolution prediction.

        Parameters:
            df:            Job postings DataFrame
            current_role:  User's current or target role
            steps:         How many steps ahead to predict (default: 3)
            show_branches: Show all possible next steps, not just greedy best
        """
        # 1. Resolve role with fuzzy matching
        resolved_role, match_type = self._resolve_role(current_role)

        if match_type == "no_match":
            return {
                "error": f"Role '{current_role}' not found in evolution graph.",
                "suggestion": f"Try one of: {list(self.TRANSITION_GRAPH.keys())[:10]}"
            }

        # 2. Build primary evolution path (greedy most-likely)
        path            = []
        current         = resolved_role
        cumulative_prob = 1.0
        cumulative_years = 0.0

        for step_num in range(steps):
            transitions = self.TRANSITION_GRAPH.get(current, {})
            if not transitions:
                break
            
            # Most likely next step
            next_role = max(transitions, key=transitions.get)
            prob      = transitions[next_role]

            # Time in current role
            time_data = self._get_time_in_role(df, current)
            years     = time_data["years"]

            # Salary data for both current and next role
            current_salary = self._get_role_salary(df, current)
            next_salary    = self._get_role_salary(df, next_role)

            # Salary delta
            salary_delta = None
            if current_salary and next_salary:
                delta_lpa   = next_salary["median_lpa"] - current_salary["median_lpa"]
                delta_pct   = (delta_lpa / current_salary["median_lpa"]) * 100
                salary_delta = {
                    "delta_lpa": round(delta_lpa, 2),
                    "delta_pct": round(delta_pct, 1),
                    "signal": (
                        f"📈 +{delta_pct:.0f}% salary growth"  if delta_pct > 10  else
                        f"➡️  Similar compensation ({delta_pct:+.0f}%)" if abs(delta_pct) <= 10 else
                        f"📉 {delta_pct:.0f}% — verify this transition makes sense"
                    )
                }

            # Skills to acquire for next step
            current_skills = set(self._get_role_skills(df, current))
            next_skills    = set(self._get_role_skills(df, next_role))
            skills_to_gain = list(next_skills - current_skills)[:5]

            # Market availability
            availability = self._check_market_availability(df, next_role)

            # All branches at this step
            branches = self._get_all_next_steps(current, df) if show_branches else []

            # Move classification
            current_meta = self.ROLE_METADATA.get(current, {})
            next_meta    = self.ROLE_METADATA.get(next_role, {})
            current_lvl  = current_meta.get("level", 0)
            next_lvl     = next_meta.get("level", 0)

            if next_meta.get("track") == "MGT" and current_meta.get("track") == "IC":
                move_type = "🔀 Management Pivot"
            elif next_lvl > current_lvl:
                move_type = "⬆️  Promotion"
            else:
                move_type = "↔️  Lateral Move"

            # Update cumulative stats
            cumulative_prob  *= prob
            cumulative_years += years

            path.append({
                "step":                 step_num + 1,
                "from":                 current,
                "to":                   next_role,
                "move_type":            move_type,
                "transition_probability": f"{round(prob * 100)}%",
                "time_in_current_role": {
                    "years":      time_data["years"],
                    "source":     time_data["source"],
                    "confidence": time_data["confidence"]
                },
                "cumulative_years":     round(cumulative_years, 1),
                "salary_at_next_role":  next_salary,
                "salary_progression":   salary_delta,
                "skills_to_acquire":    skills_to_gain,
                "market_availability":  availability,
                "alternative_paths":    [
                    b for b in branches if b["role"] != next_role
                ] if show_branches else []
            })

            current = next_role

        # 3. Final role summary
        final_salary     = self._get_role_salary(df, current)
        start_salary     = self._get_role_salary(df, resolved_role)
        total_sal_growth = None

        if final_salary and start_salary:
            total_growth_pct = (
                (final_salary["median_lpa"] - start_salary["median_lpa"])
                / start_salary["median_lpa"] * 100
            )
            total_sal_growth = f"+{total_growth_pct:.0f}% total compensation growth"

        # 4. IC vs Management fork detection
        has_mgmt_option = any(
            self.ROLE_METADATA.get(r, {}).get("track") == "MGT"
            for step in path
            for r in [step.get("to")]
        )

        track_note = None
        if has_mgmt_option:
            track_note = (
                "🔀 Management track available at this level. "
                "IC track continues to Staff/Principal. "
                "Management track leads to Director/VP. "
                "Both are valid — choose based on your strengths."
            )

        return {
            "Starting_Role":      current_role,
            "Resolved_Role":      resolved_role,
            "Match_Type":         match_type,

            "Evolution_Path":     path,

            "Journey_Summary": {
                "Total_Steps":          len(path),
                "Total_Years":          round(cumulative_years, 1),
                "Path_Confidence":      f"{round(cumulative_prob * 100, 1)}%",
                "Confidence_Note":      (
                    f"Confidence decays with each step. {round(cumulative_prob*100, 1)}% "
                    f"reflects the joint probability of this exact sequence — "
                    f"individual steps are more reliable than the full chain."
                ),
                "Starting_Salary":      start_salary,
                "Ending_Salary":        final_salary,
                "Total_Salary_Growth":  total_sal_growth,
                "Track_Note":           track_note,
            },

            "Data_Coverage": {
                "Roles_In_Dataset": sum(
                    1 for step in path
                    if not self._filter_role(df, step["from"]).empty
                ),
                "Salary_Data_Available": final_salary is not None,
            }
        }
    
if __name__ == "__main__":
    import pandas as pd

    # Load your cleaned job data
    job_data = pd.read_csv(r"D:\DATA SCIENCE AND ML\Project\job_trend_predictor\data\processed\cleaned\cleaned_job_data.csv")

    # Instantiate the engine
    ree = RoleEvolutionEngine()

    # Define the user's current role
    user_current_role = "Junior Data Scientist"

    # Predict evolution path
    evolution_report = ree.predict_evolution_path(
        df=job_data,
        current_role=user_current_role,
        steps=3,
        show_branches=True
    )

    # Print the evolution report
    import json
    print(json.dumps(evolution_report, indent=2))