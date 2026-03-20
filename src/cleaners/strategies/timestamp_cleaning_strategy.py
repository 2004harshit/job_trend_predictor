from .feature_cleaning_strategy import FeatureCleaningStrategy
import pandas as pd
from typing import Union


class TimestampCleaningStrategy(FeatureCleaningStrategy):
    """
    Cleaning strategy for timestamp columns.

    Extracts the date portion from ISO 8601 datetime strings.

    Handles formats:
    - "2024-01-15T10:30:00"  → "2024-01-15"
    - "2024-01-15"           → "2024-01-15"  (already clean)
    - None / non-string      → None

    Returns:
        pd.Series of date strings in 'YYYY-MM-DD' format
    """

    def clean_feature(
        self, feature: Union[pd.Series, pd.DataFrame]
    ) -> pd.Series:
        """
        Apply timestamp cleaning to each element in the Series.

        Args:
            feature: Raw timestamp pd.Series

        Returns:
            pd.Series of cleaned date strings

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

    def _clean_single(self, value: str) -> Union[str, None]:
        """
        Extract date part from a single timestamp string.

        Args:
            value: Raw timestamp string (e.g., "2024-01-15T10:30:00")

        Returns:
            Date string "YYYY-MM-DD", or None if input is invalid
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
        if not value:
            return None

        # Split on "T" and return date portion
        return value.split("T")[0]