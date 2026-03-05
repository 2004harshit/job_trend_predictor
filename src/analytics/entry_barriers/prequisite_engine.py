import re
import logging
from typing import Dict, List, Set, Tuple, Optional
from collections import defaultdict
import pandas as pd
import ast

class PrerequisiteEngine:
    
    MIN_SAMPLES = 5
    
    # ── Comprehensive Skill Dependency Tree ──────────────────────────
    # Format: skill → [prerequisites] (what you must know BEFORE this)
    SKILL_TREE = {
        # ── Foundations ──
        'basic math':         [],
        'logic':              [],
        'english':            [],
        
        # ── Math Layer ──
        'calculus':           ['basic math'],
        'linear algebra':     ['basic math'],
        'probability':        ['basic math'],
        'statistics':         ['calculus', 'probability'],
        'discrete math':      ['basic math', 'logic'],
        
        # ── Programming Foundations ──
        'programming basics': ['logic'],
        'python':             ['programming basics'],
        'java':               ['programming basics'],
        'javascript': ['programming basics', 'html', 'css'],
        'c++':                ['programming basics'],
        'r':                  ['programming basics', 'statistics'],
        
        # ── Web Foundations ──
        'html':               [],
        'css':                ['html'],
        'typescript':         ['javascript'],
        'react':              ['javascript', 'typescript'],
        'vue.js':             ['javascript'],
        'angular':            ['javascript', 'typescript'],
        'node.js':            ['javascript'],
        
        # ── Backend ──
        'rest api':           ['programming basics'],
        'django':             ['python', 'rest api'],
        'flask':              ['python', 'rest api'],
        'fastapi':            ['python', 'rest api'],
        'spring boot':        ['java', 'rest api'],
        'express.js':         ['node.js', 'rest api'],
        
        # ── Data Layer ──
        'sql':                ['logic'],
        'mysql':              ['sql'],
        'postgresql':         ['sql'],
        'mongodb':            ['programming basics'],
        'redis':              ['programming basics'],
        'database design':    ['sql', 'logic'],
        
        # ── Data Science / ML ──
        'data analysis':      ['python', 'statistics', 'sql'],
        'data visualization': ['python', 'statistics'],
        'pandas':             ['python'],
        'numpy':              ['python', 'linear algebra'],
        'machine learning':   ['statistics', 'python', 'linear algebra'],
        'scikit-learn':       ['machine learning', 'python'],
        'feature engineering':['machine learning', 'pandas'],
        'deep learning':      ['machine learning', 'linear algebra', 'calculus'],
        'nlp':                ['deep learning', 'python'],
        'computer vision':    ['deep learning', 'numpy'],
        'tensorflow':         ['deep learning', 'python'],
        'pytorch':            ['deep learning', 'python'],
        'data science':       ['statistics', 'python', 'sql', 'machine learning'],
        'mlops':              ['machine learning', 'docker', 'python'],
        'llm':                ['deep learning', 'nlp'],
        
        # ── DevOps / Cloud ──
        'linux':              ['programming basics'],
        'bash':               ['linux'],
        'git':                ['programming basics'],
        'docker':             ['linux', 'programming basics'],
        'kubernetes':         ['docker', 'linux'],
        'ci/cd':              ['git', 'docker'],
        'aws':                ['linux', 'programming basics'],
        'azure':              ['linux', 'programming basics'],
        'gcp':                ['linux', 'python'],
        'terraform':          ['aws', 'linux'],
        
        # ── System Design ──
        'data structures':    ['programming basics', 'discrete math'],
        'algorithms':         ['data structures', 'discrete math'],
        'system design':      ['algorithms', 'database design', 'rest api'],
        'microservices':      ['system design', 'docker', 'rest api'],
        'distributed systems':['system design', 'algorithms'],
        
        # ── Security ──
        'networking basics':  ['programming basics'],
        'cybersecurity':      ['networking basics', 'linux', 'programming basics'],
        'penetration testing':['cybersecurity', 'python'],
    }
    
    # Learning time estimates in weeks (at ~10hrs/week)
    LEARNING_WEEKS = {
        'basic math':         1, 'logic':              1,
        'programming basics': 3, 'html':               1,
        'css':                2, 'sql':                3,
        'python':             4, 'javascript':         5,
        'typescript':         3, 'react':              6,
        'node.js':            5, 'django':             6,
        'statistics':         8, 'linear algebra':     6,
        'calculus':           6, 'machine learning':   14,
        'deep learning':      18,'docker':             3,
        'kubernetes':         5, 'aws':                8,
        'system design':      10,'data science':       20,
        'pytorch':            10,'tensorflow':         10,
    }
    DEFAULT_WEEKS = 5
    
    def __init__(self, custom_skill_tree: Dict = None):
        """
        custom_skill_tree: allows adding domain-specific skills without modifying core tree.
        """
        self.skill_tree = {**self.SKILL_TREE}
        if custom_skill_tree:
            self.skill_tree.update(custom_skill_tree)
        
        self._validate_tree()  # Check for cycles on init
        self.logger = logging.getLogger(__name__)
    
    def _validate_tree(self):
        """Detect cycles in skill tree at initialization — not at runtime."""
        def has_cycle(node, visited, rec_stack):
            visited.add(node)
            rec_stack.add(node)
            for prereq in self.skill_tree.get(node, []):
                if prereq not in visited:
                    if has_cycle(prereq, visited, rec_stack):
                        return True
                elif prereq in rec_stack:
                    return True
            rec_stack.discard(node)
            return False
        
        visited, rec_stack = set(), set()
        for skill in self.skill_tree:
            if skill not in visited:
                if has_cycle(skill, visited, rec_stack):
                    raise ValueError(
                        f"Cycle detected in skill_tree starting from '{skill}'. "
                        f"Fix the dependency definition."
                    )
                
    def _filter_domain(self, df: pd.DataFrame,
                        target_domain: str,
                        experience_band: Tuple = (0, 3)) -> pd.DataFrame:
        """Job_Type first, Title fallback. Safe copy. Experience filtered."""
        df = df.copy()

        if 'TItle_Cleaned' in df.columns and 'Title_Cleaned' not in df.columns:
            df = df.rename(columns={'TItle_Cleaned': 'Title_Cleaned'})

        if 'Job_Type' in df.columns:
            exact = df[df['Job_Type'].str.lower() == target_domain.lower()]
            if len(exact) >= self.MIN_SAMPLES:
                domain_df = exact
            else:
                domain_df = pd.DataFrame()
        else:
            domain_df = pd.DataFrame()

        if domain_df.empty:
            col = 'Title_Cleaned' if 'Title_Cleaned' in df.columns else None
            if col:
                pattern = r'\b' + re.escape(target_domain) + r'\b'
                domain_df = df[df[col].str.contains(
                    pattern, case=False, na=False, regex=True
                )]

        # Experience filter — don't mix senior skill profiles with fresher analysis
        if not domain_df.empty and 'Min_Experience' in domain_df.columns:
            min_e, max_e = experience_band
            domain_df = domain_df[
                (domain_df['Min_Experience'] >= min_e) &
                (domain_df['Min_Experience'] <= max_e + 1)
            ]

        return domain_df.copy()

    def _extract_domain_skills(self, domain_df: pd.DataFrame) -> Dict[str, float]:
        """
        NaN-safe skill extraction with importance weighting.
        Star_Skills get 2x weight — they're must-haves.
        Returns: {skill_name: importance_score}
        """
        if domain_df.empty:
            return {}

        total_postings = len(domain_df)
        skill_counts = defaultdict(float)

        skill_columns = {
            'Star_Skills':     2.0,
            'Combined_Skills': 1.0,
            'Normal_Skills':   0.6,
        }

        for col, weight in skill_columns.items():
            if col not in domain_df.columns:
                continue
            
            for skills_str in domain_df[col].fillna('').astype(str):
                if not skills_str.strip():
                    continue

                skills = self._parse_skills_string(skills_str)
                for skill in skills:
                    skill = re.sub(r'\s+', ' ', skill)
                    skill_counts[skill] += weight

        if not skill_counts:
            return {}

        # Normalize by postings
        importance = {
            skill: count / total_postings
            for skill, count in skill_counts.items()
            if count / total_postings > 0.02  # Minimum 2% presence
        }

        return dict(sorted(importance.items(), key=lambda x: x[1], reverse=True))


    def _get_max_depth(self, skill: str,
                        visited: Set[str] = None) -> int:
        """
        Recursive depth with visited set — prevents infinite loops.
        visited tracks the current recursion path (not globally visited nodes).
        """
        if visited is None:
            visited = set()

        skill_lower = skill.lower()

        if skill_lower not in self.skill_tree:
            return 0  # Unknown skill = no known prerequisites

        prereqs = self.skill_tree.get(skill_lower, [])
        if not prereqs:
            return 0

        # Cycle guard: if we've seen this skill in current path, stop
        if skill_lower in visited:
            self.logger.warning(f"Cycle detected at '{skill_lower}' — skipping.")
            return 0

        visited = visited | {skill_lower}  # Immutable update — don't share state between branches

        depths = [self._get_max_depth(p, visited) + 1 for p in prereqs]
        return max(depths)

    def _get_full_prereq_chain(self, skill: str,
                                 visited: Set[str] = None) -> List[str]:
        """
        Returns ALL prerequisites recursively in topological order.
        This builds the complete learning path.
        """
        if visited is None:
            visited = set()

        skill_lower = skill.lower()
        if skill_lower in visited or skill_lower not in self.skill_tree:
            return []

        visited.add(skill_lower)
        chain = []

        for prereq in self.skill_tree.get(skill_lower, []):
            sub_chain = self._get_full_prereq_chain(prereq, visited)
            for item in sub_chain:
                if item not in chain:
                    chain.append(item)
            if prereq not in chain:
                chain.append(prereq)

        return chain

    def _build_learning_path(self,
                           missing_skills: List[str],
                           user_skills_normalized: Set[str]) -> List[dict]:

        all_needed = set()
        for skill in missing_skills:
            chain = self._get_full_prereq_chain(skill)
            all_needed.update(chain)
            all_needed.add(skill.lower())

        to_learn = all_needed - user_skills_normalized

        # Topological sort (unchanged)
        def get_order(skill, ordered, temp_visited):
            if skill in temp_visited or skill in ordered:
                return
            temp_visited.add(skill)
            for prereq in self.skill_tree.get(skill, []):
                if prereq in to_learn:
                    get_order(prereq, ordered, temp_visited)
            temp_visited.discard(skill)
            if skill not in ordered:
                ordered.append(skill)

        ordered_skills = []
        for skill in to_learn:
            get_order(skill, ordered_skills, set())

        # ── FIX: simulate progressive acquisition ──
        acquired = set(user_skills_normalized)  # grows as we walk the path

        path = []
        for skill in ordered_skills:
            prereqs          = self.skill_tree.get(skill, [])
            prereq_ready     = all(p in acquired for p in prereqs)
            can_start_now    = all(p in user_skills_normalized for p in prereqs)  # only true if user has prereqs TODAY
            weeks            = self.LEARNING_WEEKS.get(skill, self.DEFAULT_WEEKS)

            path.append({
                "skill":          skill,
                "weeks_to_learn": weeks,
                "prerequisites":  prereqs,
                "prereq_ready":   prereq_ready,   # ready at this point in the path
                "can_start_now":  can_start_now,  # ready TODAY without any learning
                "depth":          self._get_max_depth(skill)
            })

            acquired.add(skill)  # ← user "learns" this skill, unlocking downstream

        return path

    def _parse_skills_string(self, raw: str) -> List[str]:
        """
        Handles both storage formats in the CSV:
          Format A (list repr): "['python', 'machine learning', 'sql']"
          Format B (CSV):       "python, machine learning, sql"
        """
        raw = raw.strip()
        if not raw:
            return []
    
        # Format A: Python list literal — try ast.literal_eval first
        if raw.startswith('['):
            try:
                parsed = ast.literal_eval(raw)
                if isinstance(parsed, list):
                    return [
                        re.sub(r'\s+', ' ', str(s).strip().lower())
                        for s in parsed
                        if str(s).strip()
                    ]
            except (ValueError, SyntaxError):
                pass  # Fall through to Format B
            
        # Format B: plain comma-separated — strip any stray quotes/brackets
        return [
            re.sub(r"['\"\[\]]", '', s).strip().lower()
            for s in raw.split(',')
            if re.sub(r"['\"\[\]]", '', s).strip()
        ]
    
    def _normalize_user_skills(self, user_skills: List[str]) -> Set[str]:
        """
        Handles real-world user input variations:
        - "Python3" → "python"
        - "React.js" → "react"
        - "AWS S3" → "aws"
        - "ML" → "machine learning"
        """
        ALIASES = {
            'python3':          'python',
            'python 3':         'python',
            'py':               'python',
            'js':               'javascript',
            'react.js':         'react',
            'reactjs':          'react',
            'node':             'node.js',
            'nodejs':           'node.js',
            'ml':               'machine learning',
            'dl':               'deep learning',
            'ai':                'artificial intelligence', 
            'tf':               'tensorflow',
            'sklearn':          'scikit-learn',
            'scikit learn':     'scikit-learn',
            'postgres':         'postgresql',
            'mongo':            'mongodb',
            'k8s':              'kubernetes',
            'ts':               'typescript',
            'vue':              'vue.js',
            'spring':           'spring boot',
            'fast api':         'fastapi',
            'nlp':              'nlp',
            'cv':               'computer vision',
        }

        normalized = set()
        for skill in user_skills:
            cleaned = re.sub(r'\s+', ' ', skill.lower().strip())
            # Apply alias
            resolved = ALIASES.get(cleaned, cleaned)
            normalized.add(resolved)

        return normalized
    
    def _analyze_domain_complexity(self, 
                                     required_skills: Dict[str, float]) -> dict:
        """
        Replace single max_depth with full complexity profile.

        A domain with 50 shallow skills is DIFFERENT from one with 5 deep skills.
        Both dimensions matter for entry difficulty.
        """
        depths = {}
        for skill in required_skills:
            depths[skill] = self._get_max_depth(skill)

        if not depths:
            return {"max_depth": 0, "avg_depth": 0, "classification": "Unknown"}

        depth_values = list(depths.values())
        max_depth  = max(depth_values)
        avg_depth  = sum(depth_values) / len(depth_values)
        skill_count = len(required_skills)

        # Complexity index: combines depth AND breadth
        # High max_depth = deep theoretical foundation needed
        # High skill_count = broad skill surface needed
        breadth_component = min(skill_count / 15, 4.0)   # 60 skills → 4.0 (vs 3.0 before)
        complexity_index  = (max_depth * 0.6) + (breadth_component * 0.4)

        # Deepest skills (hardest to reach)
        deepest = sorted(depths.items(), key=lambda x: x[1], reverse=True)[:5]

        # Classification: 5 tiers
        if complexity_index < 1:
            classification = "🟢 Direct Entry — minimal prerequisites"
            barrier_level  = "Very Low"
        elif complexity_index < 2:
            classification = "🟡 Basic Foundation — 1-2 months prep needed"
            barrier_level  = "Low"
        elif complexity_index < 3:
            classification = "🟠 Intermediate Foundation — 3-6 months prep"
            barrier_level  = "Medium"
        elif complexity_index < 4:
            classification = "🔴 Deep Foundation — 6-12 months structured learning"
            barrier_level  = "High"
        else:
            classification = "🚨 Expert Prerequisites — 12+ months before job-ready"
            barrier_level  = "Very High"

        return {
            "max_depth":         max_depth,
            "avg_depth":         round(avg_depth, 2),
            "skill_count":       skill_count,
            "complexity_index":  round(complexity_index, 2),
            "classification":    classification,
            "barrier_level":     barrier_level,
            "deepest_skills":    [
                {"skill": s, "depth": d} for s, d in deepest
            ]
        }

    def _calculate_readiness(self,
                               user_skills: Set[str],
                               required_profile: Dict[str, float]) -> dict:
        """
        Replace flat overlap_ratio with importance-weighted readiness.

        "You have 3/10 skills" is less useful than
        "You have the 3 most important skills (covering 65% of market weight)"
        """
        if not required_profile:
            return {"score": 0.0, "weighted_coverage": 0.0, "status": "No data"}

        total_importance = sum(required_profile.values())
        covered_importance = sum(
            importance
            for skill, importance in required_profile.items()
            if skill in user_skills
        )

        # Raw count overlap
        common_count = len(set(required_profile.keys()) & user_skills)
        count_ratio  = common_count / len(required_profile)

        # Importance-weighted coverage (0-1)
        weighted_coverage = (
            covered_importance / total_importance
            if total_importance > 0 else 0.0
        )

        # Composite: 60% weighted, 40% count
        composite = 0.6 * weighted_coverage + 0.4 * count_ratio

        # Status with 5 tiers
        if composite >= 0.75:
            status = "🟢 Strong Ready — minor gaps only"
        elif composite >= 0.55:
            status = "🟡 Mostly Ready — a few key skills to add"
        elif composite >= 0.35:
            status = "🟠 Partially Ready — meaningful upskilling needed"
        elif composite >= 0.15:
            status = "🔴 Early Stage — significant learning ahead"
        else:
            status = "⚪ Starting Fresh — build from foundations"

        return {
            "composite_score":    round(composite, 3),
            "weighted_coverage":  round(weighted_coverage, 3),
            "count_ratio":        round(count_ratio, 3),
            "matched_skills":     common_count,
            "total_required":     len(required_profile),
            "status":             status
        }

    def analyze_prerequisites(self,
                                df: pd.DataFrame,
                                target_domain: str,
                                user_skills: List[str],
                                experience_band: Tuple = (0, 3)) -> dict:
        """
        Main entry point. Full prerequisite analysis with learning path.
        """
        # 1. Filter domain
        domain_df = self._filter_domain(df, target_domain, experience_band)

        if domain_df.empty:
            return {"error": f"No data found for domain: '{target_domain}'"}

        if len(domain_df) < self.MIN_SAMPLES:
            return {
                "error": f"Insufficient data: {len(domain_df)} records "
                         f"(need {self.MIN_SAMPLES}+)."
            }

        # 2. Extract domain skill requirements
        required_profile = self._extract_domain_skills(domain_df)

        if not required_profile:
            return {"error": f"No skill data found for domain: '{target_domain}'"}

        # 3. Normalize user skills (fuzzy matching)
        user_skills_normalized = self._normalize_user_skills(user_skills)

        # 4. Domain complexity analysis
        complexity = self._analyze_domain_complexity(required_profile)

        # 5. User readiness
        readiness = self._calculate_readiness(user_skills_normalized, required_profile)

        # 6. Missing skills — ranked by importance
        missing_skills = [
            {"skill": skill, "importance": round(imp, 3)}
            for skill, imp in sorted(
                required_profile.items(), key=lambda x: x[1], reverse=True
            )
            if skill not in user_skills_normalized
        ]

        # 7. Learning path with topological ordering
        missing_skill_names = [m["skill"] for m in missing_skills[:15]]
        learning_path = self._build_learning_path(
            missing_skill_names, user_skills_normalized
        )

        # 8. Skills you can start learning RIGHT NOW
        can_start_now = [
            step for step in learning_path if step["can_start_now"]
        ]

        # 9. Total time estimate
        total_weeks = sum(s["weeks_to_learn"] for s in learning_path)
        total_months = round(total_weeks / 4.3, 1)

        # 10. Education requirement signal
        edu_signal = None
        if 'Education_Cleaned' in domain_df.columns:
            pg_pct = domain_df['PG_Degree'].notna().mean() * 100 if 'PG_Degree' in domain_df else 0
            ug_pct = domain_df['UG_Degree'].notna().mean() * 100 if 'UG_Degree' in domain_df else 0
            if pg_pct > 30:
                edu_signal = f"⚠️  {pg_pct:.0f}% of postings prefer PG degree — consider if relevant."
            elif ug_pct > 80:
                edu_signal = f"✅ UG degree sufficient — {ug_pct:.0f}% of postings accept UG."

        return {
            "Domain":          target_domain,
            "Experience_Band": experience_band,
            "Sample_Size":     len(domain_df),

            "Domain_Complexity": complexity,

            "Your_Readiness": {
                **readiness,
                "Skills_You_Have":  list(user_skills_normalized & set(required_profile.keys())),
                "Skills_You_Gave":  list(user_skills_normalized),
            },

            "Missing_Skills_Prioritized": missing_skills[:10],

            "Learning_Path": {
                "Ordered_Steps":      learning_path,
                "Can_Start_Now":      can_start_now,
                "Total_Skills_Needed": len(learning_path),
                "Estimated_Months":   total_months,
                "Time_Assumption":    "10 hrs/week dedicated learning"
            },

            "Education_Signal": edu_signal,

            "Quick_Summary": self._generate_summary(
                complexity, readiness, total_months, can_start_now
            )
        }

    def _generate_summary(self, complexity: dict, readiness: dict,
                            total_months: float, can_start_now: List) -> str:
        """Plain-English summary for Real Talk Engine and UI."""
        barrier   = complexity["barrier_level"]
        r_status  = readiness["status"]
        score     = readiness["composite_score"]

        if score >= 0.75:
            return (
                f"✅ You're well-prepared for this domain. "
                f"Barrier is '{barrier}' — focus on the remaining {len(can_start_now)} "
                f"skills you can start today."
            )
        elif score >= 0.45:
            return (
                f"🟡 Solid foundation with gaps. Entry barrier is '{barrier}'. "
                f"~{total_months} months of focused upskilling needed. "
                f"Start with: {', '.join(s['skill'] for s in can_start_now[:3])}."
            )
        elif total_months <= 4:
            return (
                f"🟠 Moderate gap but achievable. ~{total_months} months to job-ready. "
                f"Begin immediately with: "
                f"{', '.join(s['skill'] for s in can_start_now[:2])}."
            )
        else:
            return (
                f"🔴 Significant gap. Entry barrier is '{barrier}'. "
                f"Realistic timeline: ~{total_months} months. "
                f"This is doable but requires serious commitment and structured learning."
            )
        

if __name__ == "__main__":
    import pandas as pd

    # Example usage
    df = pd.read_csv(r"D:\DATA SCIENCE AND ML\Project\job_trend_predictor\data\processed\cleaned\cleaned_job_data.csv")
    engine = PrerequisiteEngine()
    result = engine.analyze_prerequisites(
        df=df,
        target_domain="Data Science",
        user_skills=["Python", "SQL", "Statistics"],
        experience_band=(0, 3)
    )
    print(result)