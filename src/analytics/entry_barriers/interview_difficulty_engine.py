import re
import ast
import logging
from typing import Dict, List, Tuple
import pandas as pd
import numpy as np


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


def skills_to_text(series: pd.Series) -> str:
    tokens = []
    for raw in series.dropna():
        tokens.extend(parse_skills_column(raw))
    return ' '.join(tokens)


class InterviewDifficultyEngine:

    MIN_SAMPLES = 8

    DOMAIN_WEIGHTS = {
        'software engineer':         {'a': 0.50, 'b': 0.30, 'g': 0.20},
        'software developer':        {'a': 0.50, 'b': 0.30, 'g': 0.20},
        'backend developer':         {'a': 0.45, 'b': 0.30, 'g': 0.25},
        'backend engineer':          {'a': 0.45, 'b': 0.30, 'g': 0.25},
        'full stack developer':      {'a': 0.40, 'b': 0.40, 'g': 0.20},
        'full stack engineer':       {'a': 0.40, 'b': 0.40, 'g': 0.20},
        'frontend developer':        {'a': 0.35, 'b': 0.55, 'g': 0.10},
        'frontend engineer':         {'a': 0.35, 'b': 0.55, 'g': 0.10},
        'react developer':           {'a': 0.30, 'b': 0.60, 'g': 0.10},
        'ui developer':              {'a': 0.25, 'b': 0.65, 'g': 0.10},
        'data scientist':            {'a': 0.15, 'b': 0.65, 'g': 0.20},
        'data analyst':              {'a': 0.10, 'b': 0.70, 'g': 0.20},
        'ml engineer':               {'a': 0.25, 'b': 0.45, 'g': 0.30},
        'machine learning engineer': {'a': 0.25, 'b': 0.45, 'g': 0.30},
        'ai engineer':               {'a': 0.20, 'b': 0.50, 'g': 0.30},
        'nlp engineer':              {'a': 0.20, 'b': 0.55, 'g': 0.25},
        'computer vision engineer':  {'a': 0.20, 'b': 0.55, 'g': 0.25},
        'devops engineer':           {'a': 0.25, 'b': 0.40, 'g': 0.35},
        'cloud engineer':            {'a': 0.20, 'b': 0.45, 'g': 0.35},
        'site reliability engineer': {'a': 0.30, 'b': 0.35, 'g': 0.35},
        'platform engineer':         {'a': 0.30, 'b': 0.35, 'g': 0.35},
        'cybersecurity engineer':    {'a': 0.20, 'b': 0.60, 'g': 0.20},
        'security analyst':          {'a': 0.15, 'b': 0.65, 'g': 0.20},
        'android developer':         {'a': 0.35, 'b': 0.55, 'g': 0.10},
        'ios developer':             {'a': 0.35, 'b': 0.55, 'g': 0.10},
    }

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
        'direct_hard': [
            'competitive programming', 'cp background', 'icpc', 'codeforces',
            'leetcode hard', 'top coder'
        ],
        'direct_easy': [
            'basic coding', 'simple problem solving', 'fundamental programming',
            'beginner friendly', 'no dsa required'
        ]
    }

    SYSTEM_DESIGN_KEYWORDS = {
        'basic':        ['rest api', 'crud', 'database design', 'mvc', 'basic architecture', 'monolithic'],
        'intermediate': ['microservices', 'scalable', 'distributed system', 'caching',
                         'load balancer', 'message queue', 'kafka', 'rabbitmq', 'api gateway', 'service mesh'],
        'advanced':     ['system design interview', 'high level design', 'hld', 'low level design',
                         'lld', 'design at scale', 'millions of users', 'globally distributed',
                         'consensus algorithm', 'cap theorem', 'event sourcing']
    }

    DOMAIN_DEPTH_KEYWORDS = {
        'surface':      ['html', 'css', 'basic sql', 'git', 'json', 'rest', 'basic python', 'excel', 'tableau'],
        'intermediate': ['react hooks', 'state management', 'orm', 'indexing', 'query optimization',
                         'docker', 'ci/cd', 'unit testing', 'design patterns', 'solid principles'],
        'deep':         ['compiler', 'os internals', 'memory management', 'concurrency', 'multithreading',
                         'jvm', 'kernel', 'network protocol', 'gpu programming', 'cuda',
                         'transformer architecture', 'custom loss function', 'reinforcement learning']
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
                raise ValueError(f"Weights for '{domain}' sum to {total:.3f} — must sum to 1.0")

    def _filter_domain(self, df: pd.DataFrame,
                       target_domain: str,
                       experience_band: Tuple = (0, 5)) -> pd.DataFrame:
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
                (domain_df['min_experience'] <= max_e)
            ]

        return domain_df.copy()

    def _resolve_weights(self, target_domain: str) -> Tuple[Dict, str]:
        domain_lower = target_domain.lower().strip()
        if domain_lower in self.DOMAIN_WEIGHTS:
            return self.DOMAIN_WEIGHTS[domain_lower], "exact"

        best_match, best_overlap = None, 0
        for known_domain in self.DOMAIN_WEIGHTS:
            if known_domain in domain_lower or domain_lower in known_domain:
                overlap = len(set(known_domain.split()) & set(domain_lower.split()))
                if overlap > best_overlap:
                    best_overlap = overlap
                    best_match = known_domain

        if best_match:
            return self.DOMAIN_WEIGHTS[best_match], f"fuzzy:{best_match}"

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

        return {'a': 0.35, 'b': 0.40, 'g': 0.25}, "default:equal_split"

    def _calculate_dsa_score(self, domain_df: pd.DataFrame) -> dict:
        """
        DSA score from 'description' column (lowercase — actual schema).
        Also checks 'skills' column for DSA-related skill keywords.
        """
        # ── Use 'description' (not 'Description_Cleaned') ─────────────
        if 'description' not in domain_df.columns:
            return {"score": 0.40, "distribution": None, "confidence": "None"}

        desc = domain_df['description'].dropna().astype(str)
        n_valid = len(desc)
        if n_valid == 0:
            return {"score": 0.40, "distribution": None, "confidence": "None"}

        def kw_pct(keywords):
            pattern = r'\b(?:' + '|'.join(re.escape(k) for k in keywords) + r')\b'
            return float(desc.str.contains(pattern, case=False, na=False).mean())

        easy_p  = kw_pct(self.DSA_KEYWORDS['easy'])
        med_p   = kw_pct(self.DSA_KEYWORDS['medium'])
        hard_p  = kw_pct(self.DSA_KEYWORDS['hard'])
        direct_hard = kw_pct(self.DSA_KEYWORDS['direct_hard'])
        direct_easy = kw_pct(self.DSA_KEYWORDS['direct_easy'])

        if direct_hard > 0.20:
            hard_p = min(1.0, hard_p + 0.30)
            med_p  = min(1.0, med_p + 0.15)
        if direct_easy > 0.20:
            hard_p = max(0.0, hard_p - 0.20)
            easy_p = min(1.0, easy_p + 0.20)

        dsa_score = (easy_p * 0.15) + (med_p * 0.35) + (hard_p * 0.50)
        dsa_score = float(np.clip(dsa_score, 0.0, 1.0))

        # ── Check 'skills' column for DSA signals ──────────────────────
        if 'skills' in domain_df.columns:
            star_text = skills_to_text(domain_df['skills'])
            if any(kw in star_text for kw in ['dsa', 'data structures', 'algorithms', 'leetcode']):
                dsa_score = min(1.0, dsa_score + 0.10)
        # ──────────────────────────────────────────────────────────────

        confidence = (
            "High"   if n_valid >= 50 else
            "Medium" if n_valid >= 20 else
            "Low"
        )

        return {
            "score":       round(dsa_score, 3),
            "easy_pct":    round(easy_p * 100, 1),
            "medium_pct":  round(med_p * 100, 1),
            "hard_pct":    round(hard_p * 100, 1),
            "direct_hard": round(direct_hard * 100, 1),
            "confidence":  confidence,
            "n_valid":     n_valid
        }

    def _calculate_domain_score(self, domain_df: pd.DataFrame) -> dict:
        """
        Domain depth score from 'description' column.
        Falls back to 'skill_count' (lowercase) if description missing.
        """
        if 'description' not in domain_df.columns:
            # ── Fallback: use lowercase 'skill_count' ──────────────────
            if 'skill_count' in domain_df.columns:
                median_skills = pd.to_numeric(
                    domain_df['skill_count'], errors='coerce'
                ).median()
                score = min(1.0, median_skills / 20) if not pd.isna(median_skills) else 0.5
                return {"score": round(score, 3), "source": "skill_count_fallback"}
            return {"score": 0.50, "source": "default"}

        desc = domain_df['description'].dropna().astype(str)

        def kw_pct(keywords):
            pattern = r'\b(?:' + '|'.join(re.escape(k) for k in keywords) + r')\b'
            return float(desc.str.contains(pattern, case=False, na=False).mean())

        surface_p      = kw_pct(self.DOMAIN_DEPTH_KEYWORDS['surface'])
        intermediate_p = kw_pct(self.DOMAIN_DEPTH_KEYWORDS['intermediate'])
        deep_p         = kw_pct(self.DOMAIN_DEPTH_KEYWORDS['deep'])

        domain_score = (surface_p * 0.15) + (intermediate_p * 0.40) + (deep_p * 0.45)
        domain_score = float(np.clip(domain_score, 0.0, 1.0))

        # ── Blend with skill_count signal (lowercase) ──────────────────
        if 'skill_count' in domain_df.columns:
            median_skills = pd.to_numeric(
                domain_df['skill_count'], errors='coerce'
            ).median()
            if not pd.isna(median_skills):
                skill_signal = min(1.0, median_skills / 20)
                domain_score = 0.70 * domain_score + 0.30 * skill_signal
        # ──────────────────────────────────────────────────────────────

        return {
            "score":            round(domain_score, 3),
            "surface_pct":      round(surface_p * 100, 1),
            "intermediate_pct": round(intermediate_p * 100, 1),
            "deep_pct":         round(deep_p * 100, 1),
            "source":           "keyword_analysis"
        }

    def _calculate_system_design_score(self, domain_df: pd.DataFrame) -> dict:
        if 'description' not in domain_df.columns:
            return {"score": 0.30, "tier": "Unknown", "confidence": "None"}

        desc = domain_df['description'].dropna().astype(str)
        n_valid = len(desc)
        if n_valid == 0:
            return {"score": 0.30, "tier": "Unknown", "confidence": "None"}

        def kw_pct(keywords):
            pattern = r'\b(?:' + '|'.join(re.escape(k) for k in keywords) + r')\b'
            return float(desc.str.contains(pattern, case=False, na=False).mean())

        basic_p        = kw_pct(self.SYSTEM_DESIGN_KEYWORDS['basic'])
        intermediate_p = kw_pct(self.SYSTEM_DESIGN_KEYWORDS['intermediate'])
        advanced_p     = kw_pct(self.SYSTEM_DESIGN_KEYWORDS['advanced'])

        sys_score = (basic_p * 0.10) + (intermediate_p * 0.35) + (advanced_p * 0.55)
        sys_score = float(np.clip(sys_score, 0.0, 1.0))

        if advanced_p > 0.25:
            tier = "Advanced — HLD/LLD rounds expected"
        elif intermediate_p > 0.30:
            tier = "Intermediate — microservices & scalability questions"
        elif basic_p > 0.20:
            tier = "Basic — API design and DB schema questions"
        else:
            tier = "Minimal — system design unlikely in interview"

        return {
            "score":            round(sys_score, 3),
            "basic_pct":        round(basic_p * 100, 1),
            "intermediate_pct": round(intermediate_p * 100, 1),
            "advanced_pct":     round(advanced_p * 100, 1),
            "tier":             tier,
            "confidence":       "High" if n_valid >= 30 else "Medium" if n_valid >= 10 else "Low"
        }

    def _estimate_interview_structure(self, weights, dsa, domain, sysdes, experience_band):
        rounds = []
        oa_difficulty = "Easy-Medium" if dsa["score"] < 0.40 else "Medium-Hard"
        rounds.append({
            "round": 1, "type": "Online Assessment / Screening",
            "focus": f"DSA problems ({oa_difficulty} level)",
            "duration": "60-90 min", "probability": "Very High"
        })
        if domain["score"] > 0.50:
            rounds.append({
                "round": 2, "type": "Technical Interview",
                "focus": f"Domain depth: {domain.get('deep_pct', '?')}% of JDs mention advanced topics",
                "duration": "45-60 min", "probability": "High"
            })
        if weights['a'] >= 0.35:
            hard_signal = dsa.get("hard_pct", 0)
            rounds.append({
                "round": len(rounds) + 1, "type": "Coding Round",
                "focus": f"{'Medium-Hard' if hard_signal > 15 else 'Easy-Medium'} DSA problems",
                "duration": "60 min",
                "probability": "High" if weights['a'] > 0.40 else "Medium"
            })
        if weights['g'] >= 0.20 and sysdes["score"] > 0.25:
            rounds.append({
                "round": len(rounds) + 1, "type": "System Design",
                "focus": sysdes["tier"], "duration": "45-60 min",
                "probability": "High" if weights['g'] > 0.30 else "Medium"
            })
        rounds.append({
            "round": len(rounds) + 1, "type": "HR / Behavioral",
            "focus": "Culture fit, projects, career goals",
            "duration": "30-45 min", "probability": "Very High"
        })
        total_rounds = len(rounds)
        return {
            "rounds": rounds, "total_rounds": total_rounds,
            "approx_hours": total_rounds * 1.0,
            "intensity": "Intense" if total_rounds >= 5 else "Moderate" if total_rounds >= 3 else "Light"
        }

    def _generate_preparation_plan(self, weights, dsa, domain, sysdes, difficulty_score):
        tracks = []

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
                "track": "DSA / Problem Solving",
                "priority": round(weights['a'] * dsa_intensity * 10, 1),
                "weight_pct": f"{weights['a']*100:.0f}%",
                "intensity": f"{dsa_intensity*10:.1f}/10",
                "recommendation": rec, "weeks_needed": weeks
            })

        if weights['b'] > 0.10:
            domain_intensity = domain["score"]
            deep_pct = domain.get("deep_pct", 0)
            if deep_pct > 20:
                rec = "Deep dive into internals: OS, memory, concurrency, advanced frameworks."
                weeks = 10
            elif domain_intensity > 0.40:
                rec = "Build 2-3 non-trivial projects. Study design patterns, testing, and production practices."
                weeks = 8
            else:
                rec = "Complete core framework tutorials. Build 1 full-stack project."
                weeks = 5
            tracks.append({
                "track": "Domain Knowledge",
                "priority": round(weights['b'] * domain_intensity * 10, 1),
                "weight_pct": f"{weights['b']*100:.0f}%",
                "intensity": f"{domain_intensity*10:.1f}/10",
                "recommendation": rec, "weeks_needed": weeks
            })

        if weights['g'] >= 0.15 and sysdes["score"] > 0.15:
            sys_intensity = sysdes["score"]
            if sys_intensity > 0.55:
                rec = "Study Grokking System Design. Practice HLD + LLD. Design 10+ systems."
                weeks = 10
            elif sys_intensity > 0.30:
                rec = "Learn microservices, caching, load balancing. Practice 5-6 common systems."
                weeks = 6
            else:
                rec = "Understand REST API design and basic DB schema design."
                weeks = 3
            tracks.append({
                "track": "System Design",
                "priority": round(weights['g'] * sys_intensity * 10, 1),
                "weight_pct": f"{weights['g']*100:.0f}%",
                "intensity": f"{sys_intensity*10:.1f}/10",
                "recommendation": rec, "weeks_needed": weeks
            })

        tracks.sort(key=lambda x: x["priority"], reverse=True)
        total_weeks = max(t["weeks_needed"] for t in tracks) if tracks else 4
        return tracks, total_weeks

    def calculate_interview_difficulty(self,
                                        df: pd.DataFrame,
                                        target_domain: str,
                                        experience_band: Tuple = (0, 5)) -> dict:
        domain_df = self._filter_domain(df, target_domain, experience_band)

        if domain_df.empty:
            return {"error": f"No data found for domain: '{target_domain}'"}
        if len(domain_df) < self.MIN_SAMPLES:
            return {"error": f"Insufficient data: {len(domain_df)} records (need {self.MIN_SAMPLES}+)."}

        weights, weight_source = self._resolve_weights(target_domain)
        dsa    = self._calculate_dsa_score(domain_df)
        domain = self._calculate_domain_score(domain_df)
        sysdes = self._calculate_system_design_score(domain_df)

        raw_index = (
            weights['a'] * dsa["score"]    +
            weights['b'] * domain["score"] +
            weights['g'] * sysdes["score"]
        )
        raw_index     = float(np.clip(raw_index, 0.0, 1.0))
        difficulty_10 = round(raw_index * 10, 1)

        if difficulty_10 >= 8.0:   label = "🔴 Extremely Difficult"
        elif difficulty_10 >= 6.5: label = "🟠 Hard"
        elif difficulty_10 >= 5.0: label = "🟡 Moderate"
        elif difficulty_10 >= 3.0: label = "🟢 Manageable"
        else:                       label = "⚪ Accessible"

        structure   = self._estimate_interview_structure(weights, dsa, domain, sysdes, experience_band)
        prep_tracks, total_prep_weeks = self._generate_preparation_plan(
            weights, dsa, domain, sysdes, raw_index
        )

        return {
            "Domain":          target_domain,
            "Experience_Band": experience_band,
            "Sample_Size":     len(domain_df),
            "Weight_Profile":  weight_source,

            "Difficulty": {
                "Index":     difficulty_10,
                "Label":     label,
                "Raw_Score": round(raw_index, 3),
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

            "Interview_Structure": structure,

            "Preparation_Plan": {
                "Tracks":             prep_tracks,
                "Total_Weeks_Needed": total_prep_weeks,
                "Time_Assumption":    "10-15 hrs/week",
            }
        }


if __name__ == "__main__":
    import json
    df = pd.read_csv("D:\\DATA SCIENCE AND ML\\Project\\job_trend_predictor\\data\\processed\\cleaned\\cleaned_job_data.csv")
    engine = InterviewDifficultyEngine()
    result = engine.calculate_interview_difficulty(df, target_domain="Data Analyst", experience_band=(0, 3))
    print(json.dumps(result, indent=2))