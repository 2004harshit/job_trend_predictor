from .feature_cleaning_strategy import FeatureCleaningStrategy
import pandas as pd
import numpy as np
import re


class SalaryCleaningStrategy(FeatureCleaningStrategy):
    """
    Cleaning strategy for salary columns.

    Extracts and normalizes salary data into three derived columns:
    - min_salary  (float, in LPA)
    - max_salary  (float, in LPA)
    - avg_salary  (float, in LPA)

    Handles formats:
    - Range       : "3-5 LPA", "3 to 5 Lakhs"
    - Single      : "5 LPA", "3.5 Lacs"
    - Upto        : "Upto 7 LPA"
    - Plus        : "5+ LPA"
    - Absolute    : "500000-700000" (auto-converted to LPA)
    - Invalid     : "Not Disclosed", "Negotiable", None → NaN

    Returns:
        pd.DataFrame with columns [min_salary, max_salary, avg_salary]
    """

    INVALID_SALARY_VALUES = {
        "not disclosed", "salary not disclosed", "na", "n/a",
        "not mentioned", "negotiable", "competitive",
        "as per industry standards", "tbd", "to be decided"
    }

    # ------------------------------------------------------------------ #
    #  Regex patterns (compiled once at class level for performance)       #
    # ------------------------------------------------------------------ #
    _UNIT = r'(?:lpa|l\.?p\.?a\.?|lakhs?|lacs?|l)'
    _PA   = r'(?:\s*p\.?a\.?|\s*per\s*annum)?'

    PATTERNS = {
        "upto":           re.compile(
            rf'(?:upto|up\s*to)\s*(\d+\.?\d*)\s*{_UNIT}\b',
            re.IGNORECASE
        ),
        "plus":           re.compile(
            rf'(\d+\.?\d*)\s*\+\s*{_UNIT}\b',
            re.IGNORECASE
        ),
        "range_with_unit": re.compile(
            rf'(\d+\.?\d*)\s*(?:-|to)\s*(\d+\.?\d*)\s*{_UNIT}{_PA}\b',
            re.IGNORECASE
        ),
        "single_with_unit": re.compile(
            rf'(\d+\.?\d*)\s*{_UNIT}{_PA}\b',
            re.IGNORECASE
        ),
        "absolute_range": re.compile(
            r'(\d{5,})\s*(?:-|to)\s*(\d{5,})',
            re.IGNORECASE
        ),
        "absolute_single": re.compile(
            r'(\d{5,})',
            re.IGNORECASE
        ),
        "simple_range":   re.compile(
            r'(\d+\.?\d*)\s*(?:-|to)\s*(\d+\.?\d*)',
            re.IGNORECASE
        ),
    }

    # ------------------------------------------------------------------ #
    #  Public interface                                                     #
    # ------------------------------------------------------------------ #

    def clean_feature(self, feature: pd.Series) -> pd.DataFrame:
        """
        Apply salary cleaning to the entire Series.

        Args:
            feature: Raw salary Series

        Returns:
            pd.DataFrame with columns [min_salary, max_salary, avg_salary]

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

        ranges = feature.apply(self._extract_salary_range)

        return pd.DataFrame({
            "min_salary": ranges.apply(self._get_min),
            "max_salary": ranges.apply(self._get_max),
            "avg_salary": ranges.apply(self._get_avg),
        })

    # ------------------------------------------------------------------ #
    #  Private helpers                                                      #
    # ------------------------------------------------------------------ #

    def _extract_salary_range(self, value: str) -> tuple:
        """
        Parse a single salary string into a (min, max) tuple in LPA.

        Returns:
            (min_lpa, max_lpa) as floats, or (None, None) if unparseable
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

        # --- known-invalid labels ---
        if value.lower() in self.INVALID_SALARY_VALUES:
            return (None, None)

        # --- Pattern 1: Upto X ---
        m = self.PATTERNS["upto"].search(value)
        if m:
            return (0.0, float(m.group(1)))

        # --- Pattern 2: X+ ---
        m = self.PATTERNS["plus"].search(value)
        if m:
            return (float(m.group(1)), None)

        # --- Pattern 3: Range with unit ---
        m = self.PATTERNS["range_with_unit"].search(value)
        if m:
            return self._ordered(float(m.group(1)), float(m.group(2)))

        # --- Pattern 4: Single with unit ---
        m = self.PATTERNS["single_with_unit"].search(value)
        if m:
            v = float(m.group(1))
            return (v, v)

        # --- Pattern 5: Absolute range (rupees → LPA) ---
        m = self.PATTERNS["absolute_range"].search(value)
        if m:
            lo = round(float(m.group(1)) / 100_000, 2)
            hi = round(float(m.group(2)) / 100_000, 2)
            return self._ordered(lo, hi)

        # --- Pattern 6: Single absolute number ---
        m = self.PATTERNS["absolute_single"].search(value)
        if m:
            v = round(float(m.group(1)) / 100_000, 2)
            return (v, v)

        # --- Pattern 7: Plain range fallback (assume LPA if < 100) ---
        m = self.PATTERNS["simple_range"].search(value)
        if m:
            lo, hi = float(m.group(1)), float(m.group(2))
            if lo < 100 and hi < 100:
                return self._ordered(lo, hi)

        return (None, None)

    # ------------------------------------------------------------------ #
    #  Tuple helpers                                                        #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _ordered(a: float, b: float) -> tuple:
        """Return (min, max) — swaps if caller passed them reversed."""
        return (a, b) if a <= b else (b, a)

    @staticmethod
    def _get_min(t: tuple) -> float:
        return t[0] if t and t[0] is not None else np.nan

    @staticmethod
    def _get_max(t: tuple) -> float:
        return t[1] if t and t[1] is not None else np.nan

    @staticmethod
    def _get_avg(t: tuple) -> float:
        if t and t[0] is not None and t[1] is not None:
            return round((t[0] + t[1]) / 2, 2)
        if t and t[0] is not None:
            return t[0]
        return np.nan