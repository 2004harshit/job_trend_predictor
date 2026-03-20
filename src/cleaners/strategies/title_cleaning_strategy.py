from .feature_cleaning_strategy import FeatureCleaningStrategy
import pandas as pd
import re
import os
from pathlib import Path
import yaml
from fuzzywuzzy import fuzz
from typing import List, Optional


class TitleCleaningStrategy(FeatureCleaningStrategy):
    """
    Cleaning strategy for job title columns.

    Operations:
    - Removes hiring/metadata prefixes (e.g., "Urgent", "Walk-in", "Hiring for")
    - Splits on separators and retains the core title
    - Expands common abbreviations (e.g., "ML" → "machine learning", "SRE" → ...)
    - Strips seniority markers (e.g., "Senior", "Jr.", "Lead")
    - Fuzzy-matches cleaned title against a canonical job list
    - Returns ["Other"] for low-confidence or unparseable inputs

    Confidence thresholds:
        >= 80 : High   → single best match
        >= 70 : Medium → top 2 if second is within 5 points
        <  70 : Low    → ["Other"]
    """

    # ------------------------------------------------------------------ #
    #  Class-level regex constants                                          #
    # ------------------------------------------------------------------ #

    METADATA_PATTERNS = [
        r'\bhiring\b',
        r'\bimmediate\s+joiner?\b',
        r'\bopening\s+for\b',
        r'\burgent\b',
        r'\bimmediate\s+joining\b',
        r'\bwalk-?in\b',
        r'\bfreshers?\b',
        r'\bexperienced?\b',
    ]

    ABBREVIATIONS = [
        # Order matters: longer/more-specific patterns first
        (r'\bgen\s*ai\b',   'generative ai'),
        (r'\bsre\b',        'site reliability engineer'),
        (r'\bml\b',         'machine learning'),
        (r'\bai\b',         'artificial intelligence'),
        (r'\bfs\b',         'full stack'),
        (r'\bdev\b',        'developer'),
        (r'\bengg?\b',      'engineer'),
        (r'\bmgr\b',        'manager'),
    ]

    SENIORITY_PATTERNS = [
        r'\bsenior\b', r'\bjr\.?\b',      r'\bsr\.?\b',
        r'\blead\b',   r'\bprincipal\b',  r'\bassociate\b',
        r'\bintern\b', r'\btrainee\b',    r'\bmid-?level\b',
        r'\bentry-?level\b', r'\bstaff\b',
    ]

    HIGH_CONFIDENCE_THRESHOLD   = 80
    MEDIUM_CONFIDENCE_THRESHOLD = 70
    MEDIUM_CONFIDENCE_GAP       = 5

    DEFAULT_CONFIG_PATH = Path(__file__).resolve().parents[3] / "config" / "cleaning_config.yaml"

    # ------------------------------------------------------------------ #
    #  Constructor                                                          #
    # ------------------------------------------------------------------ #

    def __init__(
        self,
        job_list: Optional[List[str]] = None,
        config_path: Optional[str] = None,
    ):
        """
        Args:
            job_list: Canonical list of standardized job titles for matching.
            config_path: Path to cleaning_config.yaml to load job_list if not provided.

        Raises:
            TypeError:  If job_list is not a list.
            ValueError: If job_list is empty.
        """
        if job_list is None:
            job_list = self._load_job_list_from_config(config_path)

        if not isinstance(job_list, list):
            raise TypeError(
                f"job_list must be a list, got {type(job_list).__name__}"
            )
        if not job_list:
            raise ValueError("job_list cannot be empty.")

        self._job_list = job_list
        # Pre-lowercase for matching (avoid repeating .lower() per row)
        self._job_list_lower = [j.lower() for j in job_list]

    @classmethod
    def _load_job_list_from_config(cls, config_path: Optional[str] = None) -> List[str]:
        """
        Load job_list from YAML config if job_list argument is not provided.

        Returns:
            A list of canonical job titles.

        Raises:
            ValueError: if config path is invalid or job_list missing/invalid.
        """
        if not config_path:
            config_file = cls.DEFAULT_CONFIG_PATH
        else:
            config_file = Path(config_path)

        if not config_file.exists():
            raise ValueError(
                f"Config file not found at '{config_file}'. "
                "Provide a valid config_path or pass job_list explicitly."
            )

        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
        except Exception as e:
            raise ValueError(
                f"Failed to load YAML config from '{config_file}': {e}"
            )

        if not isinstance(config, dict):
            raise ValueError(
                f"Config file '{config_file}' must contain a top-level mapping."
            )

        job_list = config.get('job_list')
        if not isinstance(job_list, list) or not job_list:
            raise ValueError(
                f"Config file '{config_file}' must contain a non-empty 'job_list'."
            )

        return job_list

    # ------------------------------------------------------------------ #
    #  Public interface                                                     #
    # ------------------------------------------------------------------ #

    def clean_feature(self, feature: pd.Series) -> pd.Series:
        """
        Apply title cleaning and fuzzy matching to each element in the Series.

        Args:
            feature: Raw job title Series

        Returns:
            pd.Series where each element is a List[str] of matched titles
            (or ["Other"] for low-confidence / invalid inputs)

        Raises:
            TypeError:  If input is not a pd.Series
            ValueError: If the Series is empty
        """
        if not isinstance(feature, pd.Series):
            raise TypeError(
                f"Expected pd.Series, got {type(feature).__name__}"
            )
        if feature.empty:
            raise ValueError("Input Series is empty.")

        return feature.apply(self._match_title)

    # ------------------------------------------------------------------ #
    #  Private helpers                                                      #
    # ------------------------------------------------------------------ #

    def _match_title(self, raw: str) -> List[str]:
        """
        Clean and fuzzy-match a single raw job title string.

        Args:
            raw: Raw job title string

        Returns:
            List of matched canonical titles, or ["Other"]
        """
        # --- null / non-string guard ---
        try:
            if raw is None or pd.isna(raw):
                return ["Other"]
        except (TypeError, ValueError):
            pass

        if not isinstance(raw, str):
            return ["Other"]

        title = raw.lower().strip()
        if not title:
            return ["Other"]

        # Step 1: Remove metadata keywords
        for pattern in self.METADATA_PATTERNS:
            title = re.sub(pattern, '', title, flags=re.IGNORECASE).strip()

        # Step 2: Split on separators, keep core title
        title = re.split(r'\s*[-|,@]\s*', title)[0].strip()

        # Step 3: Expand abbreviations
        for pattern, replacement in self.ABBREVIATIONS:
            title = re.sub(pattern, replacement, title, flags=re.IGNORECASE)

        # Step 4: Remove seniority markers
        for pattern in self.SENIORITY_PATTERNS:
            title = re.sub(pattern, '', title, flags=re.IGNORECASE).strip()

        # Step 5: Normalize whitespace
        title = re.sub(r'\s+', ' ', title).strip()

        if not title:
            return ["Other"]

        # Step 6: Fuzzy match against canonical list
        return self._fuzzy_match(title)

    def _fuzzy_match(self, cleaned_title: str) -> List[str]:
        """
        Score cleaned title against canonical job list and return best match(es).

        Args:
            cleaned_title: Pre-cleaned, lowercase title string

        Returns:
            List of matched job titles, or ["Other"]
        """
        scores = {
            job: fuzz.token_set_ratio(job_lower, cleaned_title)
            for job, job_lower in zip(self._job_list, self._job_list_lower)
        }

        sorted_matches = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        top_score = sorted_matches[0][1]

        if top_score >= self.HIGH_CONFIDENCE_THRESHOLD:
            return [sorted_matches[0][0]]

        if top_score >= self.MEDIUM_CONFIDENCE_THRESHOLD:
            matches = [sorted_matches[0][0]]
            if (
                len(sorted_matches) > 1
                and sorted_matches[1][1] >= top_score - self.MEDIUM_CONFIDENCE_GAP
            ):
                matches.append(sorted_matches[1][0])
            return matches

        return ["Other"]
    


