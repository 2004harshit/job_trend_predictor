from .feature_cleaning_strategy import FeatureCleaningStrategy
import pandas as pd
import re
from typing import Union, List


class SkillsCleaningStrategy(FeatureCleaningStrategy):
    """
    Cleaning strategy for skills columns.

    Unlike other strategies, this accepts a pd.DataFrame with two columns:
    - Star_Skills   : Primary / featured skills
    - Normal_Skills : Additional skills

    Operations:
    - Parses comma / pipe / semicolon / slash-separated strings or lists
    - Normalizes abbreviations and synonyms via SKILL_NORMALIZATION map
    - Filters noise tokens via INVALID_SKILLS set
    - Deduplicates with star skills taking priority (insertion order preserved)

    Returns:
        pd.DataFrame with columns [Combined_Skills, Skill_Count]
    """

    REQUIRED_COLUMNS = {"Star_Skills", "Normal_Skills"}

    SKILL_NORMALIZATION = {
        # Programming Languages
        'js': 'JavaScript',         'javascript': 'JavaScript',
        'reactjs': 'React',         'react.js': 'React',
        'nodejs': 'Node.js',        'node.js': 'Node.js',        'node': 'Node.js',
        'ts': 'TypeScript',         'typescript': 'TypeScript',
        'py': 'Python',             'python': 'Python',
        'c++': 'C++',               'cpp': 'C++',
        'c#': 'C#',                 'csharp': 'C#',
        'golang': 'Go',
        # Frameworks & Libraries
        'angular.js': 'Angular',    'angularjs': 'Angular',
        'vue.js': 'Vue',            'vuejs': 'Vue',
        'nextjs': 'Next.js',        'next.js': 'Next.js',
        'expressjs': 'Express.js',  'express.js': 'Express.js',
        'django': 'Django',         'flask': 'Flask',
        'springboot': 'Spring Boot', 'spring boot': 'Spring Boot',
        # Data Science & ML
        'ml': 'Machine Learning',   'machine learning': 'Machine Learning',
        'ai': 'Artificial Intelligence',
        'artificial intelligence': 'Artificial Intelligence',
        'dl': 'Deep Learning',      'deep learning': 'Deep Learning',
        'nlp': 'Natural Language Processing',
        'cv': 'Computer Vision',    'computer vision': 'Computer Vision',
        'tensorflow': 'TensorFlow', 'pytorch': 'PyTorch',
        'scikit-learn': 'Scikit-learn', 'sklearn': 'Scikit-learn',
        'pandas': 'Pandas',         'numpy': 'NumPy',
        # Databases
        'sql': 'SQL',               'mysql': 'MySQL',
        'postgresql': 'PostgreSQL', 'postgres': 'PostgreSQL',
        'mongodb': 'MongoDB',       'mongo': 'MongoDB',
        'nosql': 'NoSQL',           'redis': 'Redis',
        # Cloud & DevOps
        'aws': 'AWS',               'amazon web services': 'AWS',
        'azure': 'Azure',
        'gcp': 'Google Cloud Platform',
        'google cloud': 'Google Cloud Platform',
        'docker': 'Docker',         'kubernetes': 'Kubernetes',  'k8s': 'Kubernetes',
        'ci/cd': 'CI/CD',           'jenkins': 'Jenkins',
        'git': 'Git',               'github': 'GitHub',          'gitlab': 'GitLab',
        # Other
        'api': 'API',               'rest api': 'REST API',      'restful': 'REST API',
        'graphql': 'GraphQL',
        'html': 'HTML',             'css': 'CSS',
        'sass': 'SASS',             'scss': 'SCSS',
    }

    INVALID_SKILLS = {
        'etc', 'and', 'or', 'with', 'using', 'knowledge', 'experience',
        'skills', 'good', 'strong', 'excellent', 'basic', 'advanced',
        'familiarity', 'understanding', 'ability', 'na', 'n/a', 'none',
        'required', 'preferred', 'must', 'have', 'plus', 'bonus',
    }

    _SINGLE_LETTER_ALLOWED = {'r', 'c'}

    # ------------------------------------------------------------------ #
    #  Public interface                                                     #
    # ------------------------------------------------------------------ #

    def clean_feature(
        self, feature: Union[pd.Series, pd.DataFrame]
    ) -> pd.DataFrame:
        """
        Apply skills cleaning to a DataFrame containing Star_Skills
        and Normal_Skills columns.

        Args:
            feature: pd.DataFrame with columns [Star_Skills, Normal_Skills]

        Returns:
            pd.DataFrame with columns [Combined_Skills, Skill_Count]

        Raises:
            TypeError:  If input is not a pd.Series or pd.DataFrame
            ValueError: If the input is empty or required columns are missing
        """
        if not isinstance(feature, (pd.Series, pd.DataFrame)):
            raise TypeError(
                f"Expected pd.Series or pd.DataFrame, "
                f"got {type(feature).__name__}"
            )
        if feature.empty:
            raise ValueError("Input is empty.")

        # Coerce single Series into a one-column DataFrame for uniform handling
        if isinstance(feature, pd.Series):
            raise ValueError(
                f"SkillsCleaningStrategy requires a pd.DataFrame with columns "
                f"{self.REQUIRED_COLUMNS}, got a pd.Series."
            )

        missing = self.REQUIRED_COLUMNS - set(feature.columns)
        if missing:
            raise ValueError(
                f"Input DataFrame is missing required columns: {missing}"
            )

        combined = feature.apply(
            lambda row: self._get_combined_skills(
                row["Star_Skills"], row["Normal_Skills"]
            ),
            axis=1,
        )

        return pd.DataFrame(
            {
                "Combined_Skills": combined,
                "Skill_Count":     combined.apply(len),
            },
            index=feature.index,
        )

    # ------------------------------------------------------------------ #
    #  Private helpers                                                      #
    # ------------------------------------------------------------------ #

    def _get_combined_skills(
        self,
        star_skills:   Union[str, list, None],
        normal_skills: Union[str, list, None],
    ) -> List[str]:
        """
        Merge, normalize, and deduplicate skills from two sources.
        Star skills appear first in output.
        """
        star_norm   = [
            s for s in
            (self._normalize_skill(x) for x in self._parse_skills_string(star_skills))
            if s
        ]
        normal_norm = [
            s for s in
            (self._normalize_skill(x) for x in self._parse_skills_string(normal_skills))
            if s
        ]

        # dict.fromkeys preserves insertion order and deduplicates
        seen: dict = dict.fromkeys(star_norm)
        for skill in normal_norm:
            seen.setdefault(skill, None)

        return list(seen.keys())

    def _parse_skills_string(
        self, skills_input: Union[str, list, None]
    ) -> List[str]:
        """
        Parse a skills string or list into individual raw tokens.
        """
        try:
            if skills_input is None or pd.isna(skills_input):
                return []
        except (TypeError, ValueError):
            pass

        if isinstance(skills_input, list):
            return [str(s).strip() for s in skills_input if s]

        skills_str = str(skills_input).strip()
        skills_str = re.sub(r'^\[|\]$', '', skills_str)   # strip brackets
        skills_str = re.sub(r'["\']', '', skills_str)      # strip quotes

        tokens = re.split(r'[,|;/]', skills_str)
        return [t.strip() for t in tokens if t.strip()]

    def _normalize_skill(self, skill: str) -> Union[str, None]:
        """
        Normalize a single raw skill token to its canonical form.
        Returns None if the token is noise or invalid.
        """
        if not skill or not isinstance(skill, str):
            return None

        skill = skill.strip().lower()
        skill = re.sub(r'^[.,;:\-/|()]+|[.,;:\-/|()]+$', '', skill).strip()

        if not skill or len(skill) < 2:
            return None
        if skill in self.INVALID_SKILLS:
            return None
        if len(skill) == 1 and skill not in self._SINGLE_LETTER_ALLOWED:
            return None

        if skill in self.SKILL_NORMALIZATION:
            return self.SKILL_NORMALIZATION[skill]

        return skill.title()