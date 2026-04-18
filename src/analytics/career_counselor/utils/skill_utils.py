"""
Skill parsing, normalization, and alias resolution utilities.

All analytics that touch the `skills` column must go through these
functions so that "ReactJS", "React.js", and "react" all resolve
to the same canonical token "react".
"""

import re
from typing import Optional

# ---------------------------------------------------------------------------
# Canonical alias map
# key   → what appears (raw, lowercased) in job postings
# value → canonical token stored everywhere in the dashboard
# ---------------------------------------------------------------------------
SKILL_ALIAS_MAP: dict[str, str] = {
    # JavaScript ecosystem
    "reactjs": "react",
    "react.js": "react",
    "react js": "react",
    "react native": "react native",
    "nodejs": "node.js",
    "node js": "node.js",
    "node": "node.js",
    "vuejs": "vue.js",
    "vue js": "vue.js",
    "angularjs": "angular",
    "angular js": "angular",
    "nextjs": "next.js",
    "next js": "next.js",
    "expressjs": "express",
    "express js": "express",
    "typescript": "typescript",
    "ts": "typescript",
    "js": "javascript",
    # Python ecosystem
    "py": "python",
    "python3": "python",
    "sklearn": "scikit-learn",
    "sci-kit learn": "scikit-learn",
    "tensorflow2": "tensorflow",
    "tf": "tensorflow",
    "keras": "keras",
    "pytorch": "pytorch",
    "torch": "pytorch",
    "pandas": "pandas",
    "numpy": "numpy",
    "matplotlib": "matplotlib",
    "seaborn": "seaborn",
    "fastapi": "fastapi",
    "flask": "flask",
    "django": "django",
    # Data / ML
    "ml": "machine learning",
    "deep learning": "deep learning",
    "dl": "deep learning",
    "nlp": "nlp",
    "natural language processing": "nlp",
    "computer vision": "computer vision",
    "cv": "computer vision",
    "gen ai": "generative ai",
    "genai": "generative ai",
    "large language model": "llm",
    "large language models": "llm",
    "llms": "llm",
    "rag": "rag",
    "langchain": "langchain",
    # Cloud
    "amazon web services": "aws",
    "google cloud platform": "gcp",
    "google cloud": "gcp",
    "azure cloud": "azure",
    "microsoft azure": "azure",
    # DevOps / infra
    "kubernetes": "kubernetes",
    "k8s": "kubernetes",
    "docker": "docker",
    "containerization": "docker",
    "ci/cd": "ci/cd",
    "cicd": "ci/cd",
    "jenkins": "jenkins",
    "terraform": "terraform",
    "ansible": "ansible",
    "linux": "linux",
    "unix": "linux",
    "bash": "bash",
    "shell scripting": "bash",
    # Databases
    "postgresql": "postgresql",
    "postgres": "postgresql",
    "mysql": "mysql",
    "mongo": "mongodb",
    "mongodb": "mongodb",
    "redis": "redis",
    "elasticsearch": "elasticsearch",
    "elastic search": "elasticsearch",
    "sql": "sql",
    "nosql": "nosql",
    # Mobile
    "react native": "react native",
    "flutter": "flutter",
    "android": "android",
    "ios": "ios",
    "swift": "swift",
    "kotlin": "kotlin",
    # Java ecosystem
    "java": "java",
    "spring boot": "spring boot",
    "springboot": "spring boot",
    "spring": "spring boot",
    "hibernate": "hibernate",
    "maven": "maven",
    "gradle": "gradle",
    # Other languages
    "c++": "c++",
    "c plus plus": "c++",
    "golang": "go",
    "go lang": "go",
    "ruby on rails": "ruby on rails",
    "ror": "ruby on rails",
    "rust": "rust",
    "scala": "scala",
    "php": "php",
    # Analytics / BI
    "power bi": "power bi",
    "powerbi": "power bi",
    "tableau": "tableau",
    "looker": "looker",
    "excel": "excel",
    "ms excel": "excel",
    "spark": "apache spark",
    "apache spark": "apache spark",
    "hadoop": "hadoop",
    "kafka": "kafka",
    "airflow": "airflow",
    "dbt": "dbt",
    "etl": "etl",
    # Soft / generic
    "rest api": "rest api",
    "restful": "rest api",
    "graphql": "graphql",
    "microservices": "microservices",
    "system design": "system design",
    "agile": "agile",
    "scrum": "agile",
    "jira": "jira",
    "git": "git",
    "github": "git",
    "gitlab": "git",
}

# Delimiters used in the `skills` column of general_job_data
_SKILL_DELIMITERS = re.compile(r"[,|;/\n]+")

# Tokens that are noise, not skills
_NOISE_TOKENS: set[str] = {
    "", "and", "or", "the", "with", "of", "in", "to", "a", "an",
    "knowledge", "experience", "proficiency", "understanding",
    "good", "strong", "basic", "working", "hands-on",
}


def parse_skills(raw: Optional[str]) -> list[str]:
    """
    Parse the raw skills string from a job posting row into a clean list
    of normalized canonical skill tokens.

    Parameters
    ----------
    raw : str or None
        The value of the `skills` column for one row.

    Returns
    -------
    list[str]
        Deduplicated, normalized skill tokens. Empty list if input is null/empty.

    Examples
    --------
    >>> parse_skills("Python, ReactJS | Node.js, ML")
    ['python', 'react', 'node.js', 'machine learning']
    """
    if not raw or not isinstance(raw, str):
        return []

    tokens = _SKILL_DELIMITERS.split(raw)
    result: list[str] = []
    seen: set[str] = set()

    for tok in tokens:
        tok = tok.strip().lower()
        # Remove wrapping parentheses / brackets
        tok = re.sub(r"[\(\)\[\]]", "", tok).strip()
        # Collapse multiple spaces
        tok = re.sub(r"\s+", " ", tok)

        if tok in _NOISE_TOKENS or len(tok) < 2:
            continue

        canonical = normalize_skill(tok)

        if canonical not in seen:
            seen.add(canonical)
            result.append(canonical)

    return result


def normalize_skill(raw_skill: str) -> str:
    """
    Map a single raw skill token (already lowercased) to its canonical form.
    Falls back to the original token if no alias is found.
    """
    raw_skill = raw_skill.strip().lower()
    return SKILL_ALIAS_MAP.get(raw_skill, raw_skill)


def jaccard_similarity(set_a: set, set_b: set) -> float:
    """
    Compute Jaccard similarity between two skill sets.
    Returns 0.0 if both sets are empty.

    Used by: SkillGapService, DomainComparisonService (overlap matrix)
    """
    if not set_a and not set_b:
        return 0.0
    intersection = len(set_a & set_b)
    union = len(set_a | set_b)
    return round(intersection / union, 4) if union > 0 else 0.0


def skill_match_percentage(student_skills: list[str], job_skills: list[str]) -> float:
    """
    What fraction of the job's required skills does the student already have?
    Uses canonical normalization on both sides before comparing.

    Returns a float between 0.0 and 1.0.
    """
    norm_student = {normalize_skill(s) for s in student_skills}
    norm_job = {normalize_skill(s) for s in job_skills}
    if not norm_job:
        return 0.0
    matched = norm_student & norm_job
    return round(len(matched) / len(norm_job), 4)