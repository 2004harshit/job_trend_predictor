import re
import ast
import logging
from typing import Dict, List, Set, Tuple
from collections import defaultdict
import pandas as pd


def parse_skills_column(raw) -> List[str]:
    """
    Handles both storage formats for the 'skills' column:
      Format A (old list repr): "['python', 'machine learning', 'sql']"
      Format B (new plain str):  "python, machine learning, sql"
    """
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


class PrerequisiteEngine:

    MIN_SAMPLES = 5

    SKILL_TREE = {
        'basic math':         [],
        'logic':              [],
        'english':            [],
        'calculus':           ['basic math'],
        'linear algebra':     ['basic math'],
        'probability':        ['basic math'],
        'statistics':         ['calculus', 'probability'],
        'discrete math':      ['basic math', 'logic'],
        'programming basics': ['logic'],
        'python':             ['programming basics'],
        'java':               ['programming basics'],
        'javascript':         ['programming basics', 'html', 'css'],
        'c++':                ['programming basics'],
        'r':                  ['programming basics', 'statistics'],
        'html':               [],
        'css':                ['html'],
        'typescript':         ['javascript'],
        'react':              ['javascript', 'typescript'],
        'vue.js':             ['javascript'],
        'angular':            ['javascript', 'typescript'],
        'node.js':            ['javascript'],
        'rest api':           ['programming basics'],
        'django':             ['python', 'rest api'],
        'flask':              ['python', 'rest api'],
        'fastapi':            ['python', 'rest api'],
        'spring boot':        ['java', 'rest api'],
        'express.js':         ['node.js', 'rest api'],
        'sql':                ['logic'],
        'mysql':              ['sql'],
        'postgresql':         ['sql'],
        'mongodb':            ['programming basics'],
        'redis':              ['programming basics'],
        'database design':    ['sql', 'logic'],
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
        'data structures':    ['programming basics', 'discrete math'],
        'algorithms':         ['data structures', 'discrete math'],
        'system design':      ['algorithms', 'database design', 'rest api'],
        'microservices':      ['system design', 'docker', 'rest api'],
        'distributed systems':['system design', 'algorithms'],
        'networking basics':  ['programming basics'],
        'cybersecurity':      ['networking basics', 'linux', 'programming basics'],
        'penetration testing':['cybersecurity', 'python'],
    }

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
        self.skill_tree = {**self.SKILL_TREE}
        if custom_skill_tree:
            self.skill_tree.update(custom_skill_tree)
        self._validate_tree()
        self.logger = logging.getLogger(__name__)

    def _validate_tree(self):
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
                    raise ValueError(f"Cycle detected in skill_tree starting from '{skill}'.")

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

        if not domain_df.empty and 'min_experience' in domain_df.columns:
            min_e, max_e = experience_band
            domain_df = domain_df[
                (domain_df['min_experience'] >= min_e) &
                (domain_df['min_experience'] <= max_e + 1)
            ]

        return domain_df.copy()

    def _extract_domain_skills(self, domain_df: pd.DataFrame) -> Dict[str, float]:
        """
        Extracts skill importance profile from the unified 'skills' column.
        Handles both old list-repr and new plain-string format.
        """
        if domain_df.empty:
            return {}

        if 'skills' not in domain_df.columns:
            return {}

        total_postings = len(domain_df)
        skill_counts   = defaultdict(float)

        # ── Single 'skills' column — uniform weight 1.0 ───────────────
        for raw in domain_df['skills'].fillna(''):
            skills = parse_skills_column(raw)
            for skill in skills:
                skill = re.sub(r'\s+', ' ', skill)
                skill_counts[skill] += 1.0
        # ──────────────────────────────────────────────────────────────

        if not skill_counts:
            return {}

        importance = {
            skill: count / total_postings
            for skill, count in skill_counts.items()
            if count / total_postings > 0.02
        }

        return dict(sorted(importance.items(), key=lambda x: x[1], reverse=True))

    def _get_max_depth(self, skill: str, visited: Set[str] = None) -> int:
        if visited is None:
            visited = set()
        skill_lower = skill.lower()
        if skill_lower not in self.skill_tree:
            return 0
        prereqs = self.skill_tree.get(skill_lower, [])
        if not prereqs:
            return 0
        if skill_lower in visited:
            return 0
        visited = visited | {skill_lower}
        depths = [self._get_max_depth(p, visited) + 1 for p in prereqs]
        return max(depths)

    def _get_full_prereq_chain(self, skill: str, visited: Set[str] = None) -> List[str]:
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

        acquired = set(user_skills_normalized)
        path = []
        for skill in ordered_skills:
            prereqs       = self.skill_tree.get(skill, [])
            prereq_ready  = all(p in acquired for p in prereqs)
            can_start_now = all(p in user_skills_normalized for p in prereqs)
            weeks         = self.LEARNING_WEEKS.get(skill, self.DEFAULT_WEEKS)
            path.append({
                "skill":          skill,
                "weeks_to_learn": weeks,
                "prerequisites":  prereqs,
                "prereq_ready":   prereq_ready,
                "can_start_now":  can_start_now,
                "depth":          self._get_max_depth(skill)
            })
            acquired.add(skill)

        return path

    def _normalize_user_skills(self, user_skills: List[str]) -> Set[str]:
        ALIASES = {
            'python3': 'python', 'python 3': 'python', 'py': 'python',
            'js': 'javascript', 'react.js': 'react', 'reactjs': 'react',
            'node': 'node.js', 'nodejs': 'node.js',
            'ml': 'machine learning', 'dl': 'deep learning',
            'tf': 'tensorflow', 'sklearn': 'scikit-learn', 'scikit learn': 'scikit-learn',
            'postgres': 'postgresql', 'mongo': 'mongodb', 'k8s': 'kubernetes',
            'ts': 'typescript', 'vue': 'vue.js', 'spring': 'spring boot',
            'fast api': 'fastapi', 'cv': 'computer vision',
        }
        normalized = set()
        for skill in user_skills:
            cleaned  = re.sub(r'\s+', ' ', skill.lower().strip())
            resolved = ALIASES.get(cleaned, cleaned)
            normalized.add(resolved)
        return normalized

    def _analyze_domain_complexity(self, required_skills: Dict[str, float]) -> dict:
        depths = {skill: self._get_max_depth(skill) for skill in required_skills}

        if not depths:
            return {"max_depth": 0, "avg_depth": 0, "classification": "Unknown"}

        depth_values  = list(depths.values())
        max_depth     = max(depth_values)
        avg_depth     = sum(depth_values) / len(depth_values)
        skill_count   = len(required_skills)
        breadth_component = min(skill_count / 15, 4.0)
        complexity_index  = (max_depth * 0.6) + (breadth_component * 0.4)
        deepest = sorted(depths.items(), key=lambda x: x[1], reverse=True)[:5]

        if complexity_index < 1:
            classification, barrier_level = "🟢 Direct Entry — minimal prerequisites", "Very Low"
        elif complexity_index < 2:
            classification, barrier_level = "🟡 Basic Foundation — 1-2 months prep needed", "Low"
        elif complexity_index < 3:
            classification, barrier_level = "🟠 Intermediate Foundation — 3-6 months prep", "Medium"
        elif complexity_index < 4:
            classification, barrier_level = "🔴 Deep Foundation — 6-12 months structured learning", "High"
        else:
            classification, barrier_level = "🚨 Expert Prerequisites — 12+ months before job-ready", "Very High"

        return {
            "max_depth":        max_depth,
            "avg_depth":        round(avg_depth, 2),
            "skill_count":      skill_count,
            "complexity_index": round(complexity_index, 2),
            "classification":   classification,
            "barrier_level":    barrier_level,
            "deepest_skills":   [{"skill": s, "depth": d} for s, d in deepest]
        }

    def _calculate_readiness(self,
                              user_skills: Set[str],
                              required_profile: Dict[str, float]) -> dict:
        if not required_profile:
            return {"score": 0.0, "weighted_coverage": 0.0, "status": "No data"}

        total_importance   = sum(required_profile.values())
        covered_importance = sum(
            imp for skill, imp in required_profile.items() if skill in user_skills
        )
        common_count    = len(set(required_profile.keys()) & user_skills)
        count_ratio     = common_count / len(required_profile)
        weighted_coverage = (
            covered_importance / total_importance if total_importance > 0 else 0.0
        )
        composite = 0.6 * weighted_coverage + 0.4 * count_ratio

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
            "composite_score":   round(composite, 3),
            "weighted_coverage": round(weighted_coverage, 3),
            "count_ratio":       round(count_ratio, 3),
            "matched_skills":    common_count,
            "total_required":    len(required_profile),
            "status":            status
        }

    def analyze_prerequisites(self,
                               df: pd.DataFrame,
                               target_domain: str,
                               user_skills: List[str],
                               experience_band: Tuple = (0, 3)) -> dict:
        domain_df = self._filter_domain(df, target_domain, experience_band)

        if domain_df.empty:
            return {"error": f"No data found for domain: '{target_domain}'"}
        if len(domain_df) < self.MIN_SAMPLES:
            return {"error": f"Insufficient data: {len(domain_df)} records (need {self.MIN_SAMPLES}+)."}

        required_profile = self._extract_domain_skills(domain_df)
        if not required_profile:
            return {"error": f"No skill data found for domain: '{target_domain}'"}

        user_skills_normalized = self._normalize_user_skills(user_skills)
        complexity             = self._analyze_domain_complexity(required_profile)
        readiness              = self._calculate_readiness(user_skills_normalized, required_profile)

        missing_skills = [
            {"skill": skill, "importance": round(imp, 3)}
            for skill, imp in sorted(required_profile.items(), key=lambda x: x[1], reverse=True)
            if skill not in user_skills_normalized
        ]

        missing_skill_names = [m["skill"] for m in missing_skills[:15]]
        learning_path       = self._build_learning_path(missing_skill_names, user_skills_normalized)
        can_start_now       = [step for step in learning_path if step["can_start_now"]]
        total_weeks         = sum(s["weeks_to_learn"] for s in learning_path)
        total_months        = round(total_weeks / 4.3, 1)

        # Education signal from actual schema columns
        edu_signal = None
        if 'pg_degree' in domain_df.columns:
            pg_pct = domain_df['pg_degree'].notna().mean() * 100
            ug_pct = domain_df['ug_degree'].notna().mean() * 100 if 'ug_degree' in domain_df.columns else 0
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
                "Skills_You_Have": list(user_skills_normalized & set(required_profile.keys())),
                "Skills_You_Gave": list(user_skills_normalized),
            },

            "Missing_Skills_Prioritized": missing_skills[:10],

            "Learning_Path": {
                "Ordered_Steps":       learning_path,
                "Can_Start_Now":       can_start_now,
                "Total_Skills_Needed": len(learning_path),
                "Estimated_Months":    total_months,
                "Time_Assumption":     "10 hrs/week dedicated learning"
            },

            "Education_Signal": edu_signal,

            "Quick_Summary": self._generate_summary(
                complexity, readiness, total_months, can_start_now
            )
        }

    def _generate_summary(self, complexity, readiness, total_months, can_start_now) -> str:
        barrier  = complexity["barrier_level"]
        score    = readiness["composite_score"]

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
                f"Begin immediately with: {', '.join(s['skill'] for s in can_start_now[:2])}."
            )
        else:
            return (
                f"🔴 Significant gap. Entry barrier is '{barrier}'. "
                f"Realistic timeline: ~{total_months} months. "
                f"This is doable but requires serious commitment and structured learning."
            )


if __name__ == "__main__":
    df = pd.read_csv(r"D:\DATA SCIENCE AND ML\Project\job_trend_predictor\data\processed\cleaned\cleaned_job_data.csv")
    engine = PrerequisiteEngine()
    result = engine.analyze_prerequisites(
        df=df, target_domain="Data Analyst",
        user_skills=["Python", "SQL", "Statistics"],
        experience_band=(0, 3)
    )
    print(result)