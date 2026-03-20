from .feature_cleaning_strategy import FeatureCleaningStrategy
import pandas as pd
import re
import os
from pathlib import Path
import yaml
from fuzzywuzzy import fuzz
from typing import Union, List, Optional


class RoleCleaningStrategy(FeatureCleaningStrategy):
    """
    Cleaning strategy for Role column.

    Mirrors TitleCleaningStrategy exactly — strips noise then
    fuzzy-matches against a canonical job list.

    Operations:
    - Strips trailing commas, whitespace, punctuation noise
    - Normalizes whitespace
    - Fuzzy-matches cleaned value against canonical job_list

    Observed patterns from data:
    - "Webmaster ,"         → ["Other"]  (not in job list)
    - "Cyber Security ,"    → ["Cybersecurity Analyst"]
    - "Back End Developer ,"→ ["Back End Developer"]

    Confidence thresholds:
        >= 80 : High   → single best match
        >= 70 : Medium → top 2 if second is within 5 points
        <  70 : Low    → ["Other"]

    Returns:
        pd.Series where each element is a List[str] of matched titles
    """

    HIGH_CONFIDENCE_THRESHOLD   = 80
    MEDIUM_CONFIDENCE_THRESHOLD = 70
    MEDIUM_CONFIDENCE_GAP       = 5

    DEFAULT_CONFIG_PATH = Path(__file__).resolve().parents[3] / "config" / "cleaning_config.yaml"

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
            TypeError:  If job_list is not a list
            ValueError: If job_list is empty
        """
        if job_list is None:
            job_list = self._load_job_list_from_config(config_path)

        if not isinstance(job_list, list):
            raise TypeError(
                f"job_list must be a list, got {type(job_list).__name__}"
            )
        if not job_list:
            raise ValueError("job_list cannot be empty.")

        self._job_list       = job_list
        self._job_list_lower = [j.lower() for j in job_list]

    @classmethod
    def _load_job_list_from_config(cls, config_path: Optional[str] = None) -> List[str]:
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

    def clean_feature(
        self, feature: Union[pd.Series, pd.DataFrame]
    ) -> pd.Series:
        """
        Apply noise stripping and fuzzy matching to each element.

        Args:
            feature: Raw Role pd.Series

        Returns:
            pd.Series where each element is List[str] of matched titles

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

        return feature.apply(self._match_role)

    # ------------------------------------------------------------------ #
    #  Private helpers                                                      #
    # ------------------------------------------------------------------ #

    def _match_role(self, value: str) -> List[str]:
        """
        Strip noise from a single Role string then fuzzy match.

        Args:
            value: Raw role string (e.g., "Cyber Security ,")

        Returns:
            List of matched canonical titles, or ["Other"]
        """
        # --- null guard ---
        try:
            if value is None or pd.isna(value):
                return ["Other"]
        except (TypeError, ValueError):
            pass

        if not isinstance(value, str):
            return ["Other"]

        # Step 1: Strip trailing/leading commas, pipes, whitespace
        value = re.sub(r'^[,;:|/\s]+|[,;:|/\s]+$', '', value).strip()

        # Step 2: Normalize internal whitespace
        value = re.sub(r'\s+', ' ', value).strip()

        if not value or len(value) < 2:
            return ["Other"]

        # Step 3: Fuzzy match against canonical list
        return self._fuzzy_match(value.lower())

    def _fuzzy_match(self, cleaned: str) -> List[str]:
        """
        Score cleaned role string against canonical job list.

        Args:
            cleaned: Pre-cleaned, lowercase role string

        Returns:
            List of matched job titles, or ["Other"]
        """
        scores = {
            job: fuzz.token_set_ratio(job_lower, cleaned)
            for job, job_lower in zip(self._job_list, self._job_list_lower)
        }

        sorted_matches = sorted(
            scores.items(), key=lambda x: x[1], reverse=True
        )
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