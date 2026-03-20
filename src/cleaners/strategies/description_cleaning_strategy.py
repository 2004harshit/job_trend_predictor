from .feature_cleaning_strategy import FeatureCleaningStrategy
import pandas as pd
import re
from typing import Union


class DescriptionCleaningStrategy(FeatureCleaningStrategy):
    """
    Cleaning strategy for job description columns.

    Operations:
    - Removes excessive whitespace and normalizes line breaks
    - Strips leading/trailing whitespace
    - Returns None for null / non-string inputs

    Returns:
        pd.Series of cleaned description strings
    """

    def clean_feature(
        self, feature: Union[pd.Series, pd.DataFrame]
    ) -> pd.Series:
        """
        Apply description cleaning to each element in the Series.

        Args:
            feature: Raw job description pd.Series

        Returns:
            pd.Series of cleaned description strings

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
        Clean a single job description string.

        Args:
            value: Raw job description string

        Returns:
            Cleaned string, or None if input is invalid
        """
        # --- null guard ---
        try:
            if value is None or pd.isna(value):
                return None
        except (TypeError, ValueError):
            pass

        if not isinstance(value, str):
            return None

        # Normalize line breaks and tabs to single space
        value = re.sub(r'[\r\n\t]+', ' ', value)

        # Collapse multiple spaces into one
        value = ' '.join(value.split())

        return value.strip() or None