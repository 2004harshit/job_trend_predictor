from .feature_cleaning_strategy import FeatureCleaningStrategy
import pandas as pd
import numpy as np
import re


class ExperienceCleaningStrategy(FeatureCleaningStrategy):
    """
    Cleaning strategy for experience columns.

    Extracts and normalizes experience data into two derived columns:
    - Min_Experience (float, in years)
    - Max_Experience (float, in years)

    Handles formats:
    - Range   : "3-5 years", "3 to 5 yrs"
    - Single  : "5 years", "3.5 yrs"
    - Plus    : "5+ years"          → (5.0, NaN)
    - Fresher : "Fresher", "0 years" → (0.0, 0.0)
    - Invalid : "Not Mentioned", None → (NaN, NaN)

    Returns:
        pd.DataFrame with columns [Min_Experience, Max_Experience]
    """

    INVALID_EXPERIENCE_VALUES = {
        "no fixed duration", "not fixed", "not mentioned",
        "na", "n/a", "tbd", "to be decided", "negotiable"
    }

    PATTERNS = {
        "fresher": re.compile(
            r'\b(fresher|entry[\s-]?level|no\s+experience|0\s*years?)\b',
            re.IGNORECASE
        ),
        "range": re.compile(
            r'(\d+\.?\d*)\s*(?:-|to)\s*(\d+\.?\d*)\s*(?:years?|yrs?)\b',
            re.IGNORECASE
        ),
        "plus": re.compile(
            r'(\d+\.?\d*)\s*\+\s*(?:years?|yrs?)\b',
            re.IGNORECASE
        ),
        "single": re.compile(
            r'\b(\d+\.?\d*)\s*(?:years?|yrs?)\b',
            re.IGNORECASE
        ),
        "bare_number": re.compile(
            r'\b(\d+\.?\d*)\b',
            re.IGNORECASE
        ),
    }

    # ------------------------------------------------------------------ #
    #  Public interface                                                     #
    # ------------------------------------------------------------------ #

    def clean_feature(self, feature: pd.Series) -> pd.DataFrame:
        """
        Apply experience cleaning to the entire Series.

        Args:
            feature: Raw experience Series

        Returns:
            pd.DataFrame with columns [Min_Experience, Max_Experience]

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

        ranges = feature.apply(self._extract_experience_range)

        return pd.DataFrame({
            "Min_Experience": ranges.apply(self._get_min),
            "Max_Experience": ranges.apply(self._get_max),
        })

    # ------------------------------------------------------------------ #
    #  Private helpers                                                      #
    # ------------------------------------------------------------------ #

    def _extract_experience_range(self, value: str) -> tuple:
        """
        Parse a single experience string into a (min, max) tuple in years.

        Args:
            value: Raw experience string

        Returns:
            (min_years, max_years) as floats, or (None, None) if unparseable
        """
        # --- null / non-string guard ---
        try:
            if value is None or pd.isna(value):
                return (None, None)
        except (TypeError, ValueError):
            pass

        if not isinstance(value, str):
            return (None, None)

        value = value.strip()
        if not value:
            return (None, None)

        # --- known-invalid labels (case-insensitive set lookup) ---
        if value.lower() in self.INVALID_EXPERIENCE_VALUES:
            return (None, None)

        # --- Pattern 1: Fresher / Entry Level / No Experience ---
        if self.PATTERNS["fresher"].search(value):
            return (0.0, 0.0)

        # --- Pattern 2: Range (e.g., "3-5 years", "3 to 5 yrs") ---
        m = self.PATTERNS["range"].search(value)
        if m:
            return self._ordered(float(m.group(1)), float(m.group(2)))

        # --- Pattern 3: Plus (e.g., "5+ years") ---
        m = self.PATTERNS["plus"].search(value)
        if m:
            return (float(m.group(1)), None)

        # --- Pattern 4: Single value (e.g., "5 years") ---
        m = self.PATTERNS["single"].search(value)
        if m:
            v = float(m.group(1))
            return (v, v)

        # --- Pattern 5: Bare number fallback (e.g., "5", "3.5") ---
        m = self.PATTERNS["bare_number"].search(value)
        if m:
            v = float(m.group(1))
            return (v, v)

        return (None, None)

    # ------------------------------------------------------------------ #
    #  Tuple helpers                                                        #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _ordered(a: float, b: float) -> tuple:
        """Return (min, max) — swaps if reversed."""
        return (a, b) if a <= b else (b, a)

    @staticmethod
    def _get_min(t: tuple) -> float:
        return t[0] if t and t[0] is not None else np.nan

    @staticmethod
    def _get_max(t: tuple) -> float:
        return t[1] if t and t[1] is not None else np.nan