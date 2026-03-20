import re
import logging
from typing import Dict, List, Tuple
import pandas as pd
import numpy as np

class InterviewDifficultyEngine:
    
    MIN_SAMPLES = 8
    
    # ── Domain Weight Profiles ────────────────────────────────────────
    # alpha=DSA, beta=Domain Knowledge, gamma=System Design
    # All must sum to 1.0
    DOMAIN_WEIGHTS = {
        # SWE variants
        'software engineer':      {'a': 0.50, 'b': 0.30, 'g': 0.20},
        'software developer':     {'a': 0.50, 'b': 0.30, 'g': 0.20},
        'backend developer':      {'a': 0.45, 'b': 0.30, 'g': 0.25},
        'backend engineer':       {'a': 0.45, 'b': 0.30, 'g': 0.25},
        'full stack developer':   {'a': 0.40, 'b': 0.40, 'g': 0.20},
        'full stack engineer':    {'a': 0.40, 'b': 0.40, 'g': 0.20},
        # Frontend
        'frontend developer':     {'a': 0.35, 'b': 0.55, 'g': 0.10},
        'frontend engineer':      {'a': 0.35, 'b': 0.55, 'g': 0.10},
        'react developer':        {'a': 0.30, 'b': 0.60, 'g': 0.10},
        'ui developer':           {'a': 0.25, 'b': 0.65, 'g': 0.10},
        # Data / ML
        'data scientist':         {'a': 0.15, 'b': 0.65, 'g': 0.20},
        'data analyst':           {'a': 0.10, 'b': 0.70, 'g': 0.20},
        'ml engineer':            {'a': 0.25, 'b': 0.45, 'g': 0.30},
        'machine learning engineer': {'a': 0.25, 'b': 0.45, 'g': 0.30},
        'ai engineer':            {'a': 0.20, 'b': 0.50, 'g': 0.30},
        'nlp engineer':           {'a': 0.20, 'b': 0.55, 'g': 0.25},
        'computer vision engineer':{'a': 0.20, 'b': 0.55, 'g': 0.25},
        # DevOps / Cloud
        'devops engineer':        {'a': 0.25, 'b': 0.40, 'g': 0.35},
        'cloud engineer':         {'a': 0.20, 'b': 0.45, 'g': 0.35},
        'site reliability engineer': {'a': 0.30, 'b': 0.35, 'g': 0.35},
        'platform engineer':      {'a': 0.30, 'b': 0.35, 'g': 0.35},
        # Security
        'cybersecurity engineer': {'a': 0.20, 'b': 0.60, 'g': 0.20},
        'security analyst':       {'a': 0.15, 'b': 0.65, 'g': 0.20},
        # Mobile
        'android developer':      {'a': 0.35, 'b': 0.55, 'g': 0.10},
        'ios developer':          {'a': 0.35, 'b': 0.55, 'g': 0.10},
    }
    
    # ── DSA Difficulty Keywords ───────────────────────────────────────
    DSA_KEYWORDS = {
        'easy': [
            'arrays', 'strings', 'hashing', 'basic sorting', 'linear search',
            'stack', 'queue', 'linked list', 'basic recursion', 'two pointers'
        ],
        'medium': [
            'dynamic programming', 'binary search', 'backtracking', 'bfs', 'dfs',
            'sliding window', 'merge sort', 'quick sort', 'heap', 'priority queue',
            'trie', 'segment tree', 'bit manipulation', 'greedy algorithm'
        ],
        'hard': [
            'advanced dp', 'network flow', 'computational geometry',
            'suffix array', 'heavy light decomposition', 'convex hull',
            'np hard', 'approximation algorithm', 'advanced graph'
        ],
        # Direct signals
        'direct_hard': [
            'competitive programming', 'cp background', 'icpc', 'codeforces',
            'leetcode hard', 'top coder'
        ],
        'direct_easy': [
            'basic coding', 'simple problem solving', 'fundamental programming',
            'beginner friendly', 'no dsa required'
        ]
    }
    
    # ── System Design Keyword Tiers ───────────────────────────────────
    SYSTEM_DESIGN_KEYWORDS = {
        'basic': [
            'rest api', 'crud', 'database design', 'mvc',
            'basic architecture', 'monolithic'
        ],
        'intermediate': [
            'microservices', 'scalable', 'distributed system', 'caching',
            'load balancer', 'message queue', 'kafka', 'rabbitmq',
            'api gateway', 'service mesh'
        ],
        'advanced': [
            'system design interview', 'high level design', 'hld',
            'low level design', 'lld', 'design at scale',
            'millions of users', 'globally distributed',
            'consensus algorithm', 'cap theorem', 'event sourcing'
        ]
    }
    
    # ── Domain Knowledge Keyword Tiers ────────────────────────────────
    DOMAIN_DEPTH_KEYWORDS = {
        'surface': [
            'html', 'css', 'basic sql', 'git', 'json', 'rest',
            'basic python', 'excel', 'tableau'
        ],
        'intermediate': [
            'react hooks', 'state management', 'orm', 'indexing',
            'query optimization', 'docker', 'ci/cd', 'unit testing',
            'design patterns', 'solid principles'
        ],
        'deep': [
            'compiler', 'os internals', 'memory management', 'concurrency',
            'multithreading', 'jvm', 'kernel', 'network protocol',
            'gpu programming', 'cuda', 'transformer architecture',
            'custom loss function', 'reinforcement learning'
        ]
    }
    
    def __init__(self, custom_weights: Dict = None):
        if custom_weights:
            self.DOMAIN_WEIGHTS.update(custom_weights)
        self._validate_all_weights()
        self.logger = logging.getLogger(__name__)
    
    def _validate_all_weights(self):
        for domain, w in self.DOMAIN_WEIGHTS.items():
            total = w['a'] + w['b'] + w['g']
            if not (0.98 <= total <= 1.02):
                raise ValueError(
                    f"Weights for '{domain}' sum to {total:.3f} — must sum to 1.0"
                )
            
    def _filter_domain(self, df: pd.DataFrame,
                        target_domain: str,
                        experience_band: Tuple = (0, 5)) -> pd.DataFrame:
        """Job_Type first, Title fallback. Safe copy. Experience filtered."""
        df = df.copy()

        if 'TItle_Cleaned' in df.columns and 'Title_Cleaned' not in df.columns:
            df = df.rename(columns={'TItle_Cleaned': 'Title_Cleaned'})

        if 'Job_Type' in df.columns:
            exact = df[df['Job_Type'].str.lower() == target_domain.lower()]
            domain_df = exact if len(exact) >= self.MIN_SAMPLES else pd.DataFrame()
        else:
            domain_df = pd.DataFrame()

        if domain_df.empty:
            col = 'Title_Cleaned' if 'Title_Cleaned' in df.columns else None
            if col:
                pattern = r'\b' + re.escape(target_domain) + r'\b'
                domain_df = df[df[col].str.contains(
                    pattern, case=False, na=False, regex=True
                )]

        if domain_df.empty:
            return pd.DataFrame()

        if 'Min_Experience' in domain_df.columns:
            min_e, max_e = experience_band
            domain_df = domain_df[
                (domain_df['Min_Experience'] >= min_e) &
                (domain_df['Min_Experience'] <= max_e)
            ]

        return domain_df.copy()

    def _resolve_weights(self, target_domain: str) -> Tuple[Dict, str]:
        """
        Fuzzy weight lookup — handles partial matches.
        'ML Engineer' → finds 'ml engineer' profile.
        Falls back gracefully with role-category inference.
        """
        domain_lower = target_domain.lower().strip()

        # Exact match
        if domain_lower in self.DOMAIN_WEIGHTS:
            return self.DOMAIN_WEIGHTS[domain_lower], "exact"

        # Partial match — find best overlap
        best_match = None
        best_overlap = 0
        for known_domain in self.DOMAIN_WEIGHTS:
            # Check both directions
            if known_domain in domain_lower or domain_lower in known_domain:
                overlap = len(set(known_domain.split()) & set(domain_lower.split()))
                if overlap > best_overlap:
                    best_overlap = overlap
                    best_match = known_domain

        if best_match:
            return self.DOMAIN_WEIGHTS[best_match], f"fuzzy:{best_match}"

        # Role-category inference from keywords
        if any(kw in domain_lower for kw in ['ml', 'machine learning', 'ai', 'deep learning', 'nlp']):
            return {'a': 0.20, 'b': 0.50, 'g': 0.30}, "inferred:ml_category"
        elif any(kw in domain_lower for kw in ['data', 'analyst', 'science']):
            return {'a': 0.15, 'b': 0.65, 'g': 0.20}, "inferred:data_category"
        elif any(kw in domain_lower for kw in ['devops', 'cloud', 'sre', 'platform']):
            return {'a': 0.25, 'b': 0.40, 'g': 0.35}, "inferred:devops_category"
        elif any(kw in domain_lower for kw in ['frontend', 'ui', 'react', 'angular', 'vue']):
            return {'a': 0.35, 'b': 0.55, 'g': 0.10}, "inferred:frontend_category"
        elif any(kw in domain_lower for kw in ['security', 'cyber', 'pentest']):
            return {'a': 0.20, 'b': 0.60, 'g': 0.20}, "inferred:security_category"

        # True fallback: equal weights
        return {'a': 0.35, 'b': 0.40, 'g': 0.25}, "default:equal_split"


    def _calculate_dsa_score(self, domain_df: pd.DataFrame) -> dict:
        """
        Replace hardcoded (0.5, 0.4, 0.1) distributions with actual
        keyword analysis from job descriptions.

        Fix: Hard problems weighted MORE than medium — 
             Hard(0.5) > Medium(0.35) > Easy(0.15)
        """
        if 'Description_Cleaned' not in domain_df.columns:
            return {"score": 0.40, "distribution": None, "confidence": "None"}

        desc = domain_df['Description_Cleaned'].dropna().astype(str)
        n_valid = len(desc)

        if n_valid == 0:
            return {"score": 0.40, "distribution": None, "confidence": "None"}

        def kw_pct(keywords):
            pattern = r'\b(?:' + '|'.join(re.escape(k) for k in keywords) + r')\b'
            return float(desc.str.contains(pattern, case=False, na=False).mean())

        easy_p  = kw_pct(self.DSA_KEYWORDS['easy'])
        med_p   = kw_pct(self.DSA_KEYWORDS['medium'])
        hard_p  = kw_pct(self.DSA_KEYWORDS['hard'])

        # Direct override signals
        direct_hard = kw_pct(self.DSA_KEYWORDS['direct_hard'])
        direct_easy = kw_pct(self.DSA_KEYWORDS['direct_easy'])

        # Adjust for direct signals
        if direct_hard > 0.20:
            hard_p = min(1.0, hard_p + 0.30)
            med_p  = min(1.0, med_p + 0.15)
        if direct_easy > 0.20:
            hard_p = max(0.0, hard_p - 0.20)
            easy_p = min(1.0, easy_p + 0.20)

        # Fixed weights: Hard > Medium > Easy (logically correct)
        # Hard problems in interviews = much harder to pass than easy ones
        dsa_score = (easy_p * 0.15) + (med_p * 0.35) + (hard_p * 0.50)
        dsa_score = float(np.clip(dsa_score, 0.0, 1.0))

        # Also check Star_Skills for DSA signals
        if 'Star_Skills' in domain_df.columns:
            star_text = ' '.join(domain_df['Star_Skills'].fillna('').str.lower())
            if any(kw in star_text for kw in ['dsa', 'data structures', 'algorithms', 'leetcode']):
                dsa_score = min(1.0, dsa_score + 0.10)

        confidence = (
            "High"   if n_valid >= 50 else
            "Medium" if n_valid >= 20 else
            "Low"
        )

        return {
            "score":        round(dsa_score, 3),
            "easy_pct":     round(easy_p * 100, 1),
            "medium_pct":   round(med_p * 100, 1),
            "hard_pct":     round(hard_p * 100, 1),
            "direct_hard":  round(direct_hard * 100, 1),
            "confidence":   confidence,
            "n_valid":      n_valid
        }


    def _calculate_domain_score(self, domain_df: pd.DataFrame) -> dict:
        """
        Replace skill_count/15 with tiered keyword depth analysis.

        Fix: Market-relative normalization replaces magic /15.
        """
        if 'Description_Cleaned' not in domain_df.columns:
            # Fallback to Skill_Count if available
            if 'Skill_Count' in domain_df.columns:
                median_skills = pd.to_numeric(
                    domain_df['Skill_Count'], errors='coerce'
                ).median()
                # Market-normalized: median skill count / 20 skill ceiling
                score = min(1.0, median_skills / 20) if not pd.isna(median_skills) else 0.5
                return {"score": round(score, 3), "source": "skill_count_fallback"}
            return {"score": 0.50, "source": "default"}

        desc = domain_df['Description_Cleaned'].dropna().astype(str)

        def kw_pct(keywords):
            pattern = r'\b(?:' + '|'.join(re.escape(k) for k in keywords) + r')\b'
            return float(desc.str.contains(pattern, case=False, na=False).mean())

        surface_p      = kw_pct(self.DOMAIN_DEPTH_KEYWORDS['surface'])
        intermediate_p = kw_pct(self.DOMAIN_DEPTH_KEYWORDS['intermediate'])
        deep_p         = kw_pct(self.DOMAIN_DEPTH_KEYWORDS['deep'])

        # Depth-weighted score: deep knowledge mentions = harder interviews
        domain_score = (surface_p * 0.15) + (intermediate_p * 0.40) + (deep_p * 0.45)
        domain_score = float(np.clip(domain_score, 0.0, 1.0))

        # Skill count as additive signal
        if 'Skill_Count' in domain_df.columns:
            median_skills = pd.to_numeric(
                domain_df['Skill_Count'], errors='coerce'
            ).median()
            if not pd.isna(median_skills):
                skill_signal = min(1.0, median_skills / 20)
                # Blend: 70% keyword depth, 30% skill count signal
                domain_score = 0.70 * domain_score + 0.30 * skill_signal

        return {
            "score":          round(domain_score, 3),
            "surface_pct":    round(surface_p * 100, 1),
            "intermediate_pct": round(intermediate_p * 100, 1),
            "deep_pct":       round(deep_p * 100, 1),
            "source":         "keyword_analysis"
        }


    def _calculate_system_design_score(self, domain_df: pd.DataFrame) -> dict:
        """
        Replace 3-keyword check with tiered system design depth analysis.
        'cloud' mention ≠ system design interview — removed from basic check.
        """
        if 'Description_Cleaned' not in domain_df.columns:
            return {"score": 0.30, "tier": "Unknown", "confidence": "None"}

        desc = domain_df['Description_Cleaned'].dropna().astype(str)
        n_valid = len(desc)

        if n_valid == 0:
            return {"score": 0.30, "tier": "Unknown", "confidence": "None"}

        def kw_pct(keywords):
            pattern = r'\b(?:' + '|'.join(re.escape(k) for k in keywords) + r')\b'
            return float(desc.str.contains(pattern, case=False, na=False).mean())

        basic_p        = kw_pct(self.SYSTEM_DESIGN_KEYWORDS['basic'])
        intermediate_p = kw_pct(self.SYSTEM_DESIGN_KEYWORDS['intermediate'])
        advanced_p     = kw_pct(self.SYSTEM_DESIGN_KEYWORDS['advanced'])

        # Weighted: advanced system design = exponentially harder
        sys_score = (basic_p * 0.10) + (intermediate_p * 0.35) + (advanced_p * 0.55)
        sys_score = float(np.clip(sys_score, 0.0, 1.0))

        # Tier label
        if advanced_p > 0.25:
            tier = "Advanced — HLD/LLD rounds expected"
        elif intermediate_p > 0.30:
            tier = "Intermediate — microservices & scalability questions"
        elif basic_p > 0.20:
            tier = "Basic — API design and DB schema questions"
        else:
            tier = "Minimal — system design unlikely in interview"

        return {
            "score":           round(sys_score, 3),
            "basic_pct":       round(basic_p * 100, 1),
            "intermediate_pct": round(intermediate_p * 100, 1),
            "advanced_pct":    round(advanced_p * 100, 1),
            "tier":            tier,
            "confidence":      "High" if n_valid >= 30 else "Medium" if n_valid >= 10 else "Low"
        }

    def _estimate_interview_structure(self,
                                        weights: Dict,
                                        dsa: dict,
                                        domain: dict,
                                        sysdes: dict,
                                        experience_band: Tuple) -> dict:
        """
        Translate scores into concrete round-by-round structure.
        Gives users actionable "what to expect" intel.
        """
        rounds = []

        # Round 1: Always present — Online Assessment or Phone Screen
        oa_difficulty = "Easy-Medium" if dsa["score"] < 0.40 else "Medium-Hard"
        rounds.append({
            "round": 1,
            "type":  "Online Assessment / Screening",
            "focus": f"DSA problems ({oa_difficulty} level)",
            "duration": "60-90 min",
            "probability": "Very High"
        })

        # Round 2: Technical / Domain
        if domain["score"] > 0.50:
            rounds.append({
                "round": 2,
                "type":  "Technical Interview",
                "focus": f"Domain depth: {domain.get('deep_pct', '?')}% of JDs mention advanced topics",
                "duration": "45-60 min",
                "probability": "High"
            })

        # Round 3: Coding round (if DSA weight is significant)
        if weights['a'] >= 0.35:
            hard_signal = dsa.get("hard_pct", 0)
            rounds.append({
                "round": len(rounds) + 1,
                "type":  "Coding Round",
                "focus": f"{'Medium-Hard' if hard_signal > 15 else 'Easy-Medium'} DSA problems",
                "duration": "60 min",
                "probability": "High" if weights['a'] > 0.40 else "Medium"
            })

        # Round 4: System Design (if gamma weight significant)
        if weights['g'] >= 0.20 and sysdes["score"] > 0.25:
            rounds.append({
                "round": len(rounds) + 1,
                "type":  "System Design",
                "focus": sysdes["tier"],
                "duration": "45-60 min",
                "probability": "High" if weights['g'] > 0.30 else "Medium"
            })

        # Final: HR / Behavioral (always)
        rounds.append({
            "round": len(rounds) + 1,
            "type":  "HR / Behavioral",
            "focus": "Culture fit, projects, career goals",
            "duration": "30-45 min",
            "probability": "Very High"
        })

        total_rounds = len(rounds)
        total_hours  = total_rounds * 1.0  # Approximate

        return {
            "rounds":           rounds,
            "total_rounds":     total_rounds,
            "approx_hours":     total_hours,
            "intensity":        (
                "Intense" if total_rounds >= 5 else
                "Moderate" if total_rounds >= 3 else
                "Light"
            )
        }

    def _generate_preparation_plan(self,
                                     weights: Dict,
                                     dsa: dict,
                                     domain: dict,
                                     sysdes: dict,
                                     difficulty_score: float) -> List[dict]:
        """
        Replace single binary string with ranked preparation tracks.
        Ranked by weight × score (highest impact areas first).
        """
        tracks = []

        # DSA track
        if weights['a'] > 0.10:
            dsa_intensity = dsa["score"]
            if dsa_intensity > 0.60:
                rec = "Solve 300+ LeetCode (focus: 50% Medium, 30% Hard, 20% Easy). Study DP, graphs, trees thoroughly."
                weeks = 12
            elif dsa_intensity > 0.35:
                rec = "Solve 150-200 LeetCode (focus: 60% Medium, 20% Hard). Cover arrays, strings, trees, DP basics."
                weeks = 8
            else:
                rec = "Solve 75-100 LeetCode Easy-Medium. Focus on arrays, strings, hashing, basic sorting."
                weeks = 4

            tracks.append({
                "track":       "DSA / Problem Solving",
                "priority":    round(weights['a'] * dsa_intensity * 10, 1),
                "weight_pct":  f"{weights['a']*100:.0f}%",
                "intensity":   f"{dsa_intensity*10:.1f}/10",
                "recommendation": rec,
                "weeks_needed": weeks
            })

        # Domain knowledge track
        if weights['b'] > 0.10:
            domain_intensity = domain["score"]
            deep_pct = domain.get("deep_pct", 0)
            if deep_pct > 20:
                rec = "Deep dive into internals: OS, memory, concurrency, advanced frameworks. Read source code."
                weeks = 10
            elif domain_intensity > 0.40:
                rec = "Build 2-3 non-trivial projects. Study design patterns, testing, and production practices."
                weeks = 8
            else:
                rec = "Complete core framework tutorials. Build 1 full-stack project. Practice common interview questions."
                weeks = 5

            tracks.append({
                "track":       "Domain Knowledge",
                "priority":    round(weights['b'] * domain_intensity * 10, 1),
                "weight_pct":  f"{weights['b']*100:.0f}%",
                "intensity":   f"{domain_intensity*10:.1f}/10",
                "recommendation": rec,
                "weeks_needed": weeks
            })

        # System design track
        if weights['g'] >= 0.15 and sysdes["score"] > 0.15:
            sys_intensity = sysdes["score"]
            if sys_intensity > 0.55:
                rec = "Study Grokking System Design. Practice HLD + LLD. Design 10+ systems from scratch."
                weeks = 10
            elif sys_intensity > 0.30:
                rec = "Learn microservices, caching, load balancing. Practice designing 5-6 common systems."
                weeks = 6
            else:
                rec = "Understand REST API design and basic DB schema design. Light system design prep."
                weeks = 3

            tracks.append({
                "track":       "System Design",
                "priority":    round(weights['g'] * sys_intensity * 10, 1),
                "weight_pct":  f"{weights['g']*100:.0f}%",
                "intensity":   f"{sys_intensity*10:.1f}/10",
                "recommendation": rec,
                "weeks_needed": weeks
            })

        # Sort by priority (highest impact first)
        tracks.sort(key=lambda x: x["priority"], reverse=True)

        # Total preparation time
        total_weeks = max(t["weeks_needed"] for t in tracks) if tracks else 4

        return tracks, total_weeks


    def calculate_interview_difficulty(self,
                                        df: pd.DataFrame,
                                        target_domain: str,
                                        experience_band: Tuple = (0, 5)) -> dict:
        """Main entry point. Full interview difficulty analysis."""

        # 1. Filter domain
        domain_df = self._filter_domain(df, target_domain, experience_band)

        if domain_df.empty:
            return {"error": f"No data found for domain: '{target_domain}'"}

        if len(domain_df) < self.MIN_SAMPLES:
            return {
                "error": f"Insufficient data: {len(domain_df)} records "
                         f"(need {self.MIN_SAMPLES}+)."
            }

        # 2. Resolve weights with fuzzy matching
        weights, weight_source = self._resolve_weights(target_domain)

        # 3. Calculate all three pillars
        dsa    = self._calculate_dsa_score(domain_df)
        domain = self._calculate_domain_score(domain_df)
        sysdes = self._calculate_system_design_score(domain_df)

        # 4. Composite difficulty index
        raw_index = (
            weights['a'] * dsa["score"]    +
            weights['b'] * domain["score"] +
            weights['g'] * sysdes["score"]
        )

        # Clamp strictly to [0, 1] before scaling
        raw_index = float(np.clip(raw_index, 0.0, 1.0))
        difficulty_10 = round(raw_index * 10, 1)

        # 5. Difficulty label
        if difficulty_10 >= 8.0:
            label = "🔴 Extremely Difficult"
        elif difficulty_10 >= 6.5:
            label = "🟠 Hard"
        elif difficulty_10 >= 5.0:
            label = "🟡 Moderate"
        elif difficulty_10 >= 3.0:
            label = "🟢 Manageable"
        else:
            label = "⚪ Accessible"

        # 6. Interview structure
        structure = self._estimate_interview_structure(
            weights, dsa, domain, sysdes, experience_band
        )

        # 7. Preparation plan
        prep_tracks, total_prep_weeks = self._generate_preparation_plan(
            weights, dsa, domain, sysdes, raw_index
        )

        return {
            "Domain":          target_domain,
            "Experience_Band": experience_band,
            "Sample_Size":     len(domain_df),
            "Weight_Profile":  weight_source,

            "Difficulty": {
                "Index":       difficulty_10,
                "Label":       label,
                "Raw_Score":   round(raw_index, 3),
            },

            "Pillar_Scores": {
                "DSA": {
                    "Score":      dsa["score"],
                    "Weight":     f"{weights['a']*100:.0f}%",
                    "Weighted":   round(weights['a'] * dsa["score"] * 10, 2),
                    "Easy_Pct":   dsa.get("easy_pct"),
                    "Medium_Pct": dsa.get("medium_pct"),
                    "Hard_Pct":   dsa.get("hard_pct"),
                    "Confidence": dsa.get("confidence")
                },
                "Domain_Knowledge": {
                    "Score":        domain["score"],
                    "Weight":       f"{weights['b']*100:.0f}%",
                    "Weighted":     round(weights['b'] * domain["score"] * 10, 2),
                    "Surface_Pct":  domain.get("surface_pct"),
                    "Deep_Pct":     domain.get("deep_pct"),
                    "Source":       domain.get("source")
                },
                "System_Design": {
                    "Score":        sysdes["score"],
                    "Weight":       f"{weights['g']*100:.0f}%",
                    "Weighted":     round(weights['g'] * sysdes["score"] * 10, 2),
                    "Tier":         sysdes.get("tier"),
                    "Advanced_Pct": sysdes.get("advanced_pct"),
                    "Confidence":   sysdes.get("confidence")
                }
            },

            "Interview_Structure":    structure,

            "Preparation_Plan": {
                "Tracks":             prep_tracks,
                "Total_Weeks_Needed": total_prep_weeks,
                "Time_Assumption":    "10-15 hrs/week",
            }
        }
    

if __name__ == "__main__":
    import json
    import pandas as pd

    # Example usage
    df = pd.read_csv("D:\DATA SCIENCE AND ML\Project\job_trend_predictor\data\processed\cleaned\cleaned_job_data.csv")
    engine = InterviewDifficultyEngine()
    result = engine.calculate_interview_difficulty(df, target_domain="Data Analyst", experience_band=(0, 3))
    
    print(json.dumps(result, indent=2))