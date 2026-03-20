from .feature_cleaning_strategy import FeatureCleaningStrategy
import pandas as pd
from datetime import datetime, date
from typing import Union


class LastApplyDateCleaningStrategy(FeatureCleaningStrategy):
    """
    Cleaning strategy for Last_Apply_Date column.

    Parses absolute date strings into 'YYYY-MM-DD' format.
    No expiry logic — dates are kept as-is regardless of whether
    the deadline has passed.

    Handles formats:
    - "27 Nov 2024"       → "2024-11-27"
    - "20 November 2025"  → "2025-11-20"
    - "2024-11-27"        → "2024-11-27"  (already clean)
    - NaN / None / "NA"   → None

    Returns:
        pd.Series of date strings in 'YYYY-MM-DD' format (or None)
    """

    DATE_FORMATS = [
        "%d %b %Y",    # "27 Nov 2024"
        "%d %B %Y",    # "27 November 2024"
        "%Y-%m-%d",    # "2024-11-27"   already clean
        "%d/%m/%Y",    # "27/11/2024"
        "%d-%m-%Y",    # "27-11-2024"
        "%B %d, %Y",   # "November 27, 2024"
    ]

    INVALID_VALUES = {
        "nan", "na", "n/a", "none", "not mentioned",
        "not specified", "tbd", "to be decided"
    }

    # ------------------------------------------------------------------ #
    #  Public interface                                                     #
    # ------------------------------------------------------------------ #

    def clean_feature(
        self, feature: Union[pd.Series, pd.DataFrame]
    ) -> pd.Series:
        """
        Parse each Last_Apply_Date value into 'YYYY-MM-DD' format.

        Args:
            feature: Raw Last_Apply_Date pd.Series

        Returns:
            pd.Series of parsed date strings (None for unparseable values)

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

        return feature.apply(self._clean_single)

    # ------------------------------------------------------------------ #
    #  Private helpers                                                      #
    # ------------------------------------------------------------------ #

    def _clean_single(self, value: str) -> Union[str, None]:
        """
        Parse a single Last_Apply_Date string.

        Args:
            value: Raw date string (e.g., "27 Nov 2024")

        Returns:
            "YYYY-MM-DD" string, or None if unparseable / invalid
        """
        # --- null guard ---
        try:
            if value is None or pd.isna(value):
                return None
        except (TypeError, ValueError):
            pass

        if not isinstance(value, str):
            return None

        value = value.strip()

        if not value or value.lower() in self.INVALID_VALUES:
            return None

        parsed = self._parse_date(value)
        return parsed.strftime("%Y-%m-%d") if parsed else None

    def _parse_date(self, value: str) -> Union[date, None]:
        """
        Try each supported format until one matches.

        Args:
            value: Cleaned date string

        Returns:
            datetime.date, or None if no format matched
        """
        for fmt in self.DATE_FORMATS:
            try:
                return datetime.strptime(value, fmt).date()
            except ValueError:
                continue
        return None