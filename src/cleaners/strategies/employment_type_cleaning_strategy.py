from .feature_cleaning_strategy import FeatureCleaningStrategy
import pandas as pd
import re
from typing import Union, List


class EmploymentTypeCleaningStrategy(FeatureCleaningStrategy):
    """
    Cleaning strategy for Employment Type column.

    Operations:
    - Splits comma-separated employment types into a list
    - Normalizes known variants via EMPLOYMENT_NORMALIZATION map
    - Deduplicates while preserving order
    - Filters noise tokens

    Observed patterns from data:
    - "Full Time, Permanent" → ["Full Time", "Permanent"]
    - "Part Time"            → ["Part Time"]

    Returns:
        pd.DataFrame with columns:
        - employment_types    (List[str])
        - primary_employment  (str | None) — first type in list
        - employment_count    (int)
    """

    EMPLOYMENT_NORMALIZATION = {
        # Full Time variants
        "full time":        "Full Time",
        "full-time":        "Full Time",
        "fulltime":         "Full Time",
        "ft":               "Full Time",
        # Part Time variants
        "part time":        "Part Time",
        "part-time":        "Part Time",
        "parttime":         "Part Time",
        "pt":               "Part Time",
        # Contract
        "contract":         "Contract",
        "contractual":      "Contract",
        "contract basis":   "Contract",
        # Permanent
        "permanent":        "Permanent",
        "regular":          "Permanent",
        "regular/permanent":"Permanent",
        # Temporary
        "temporary":        "Temporary",
        "temp":             "Temporary",
        # Internship
        "internship":       "Internship",
        "intern":           "Internship",
        "trainee":          "Trainee",
        # Freelance
        "freelance":        "Freelance",
        "freelancer":       "Freelance",
        # Remote
        "remote":           "Remote",
        "work from home":   "Work From Home",
        "wfh":              "Work From Home",
    }

    INVALID_VALUES = {
        "na", "n/a", "none", "not specified",
        "not mentioned", "tbd", "other"
    }

    def clean_feature(
        self, feature: Union[pd.Series, pd.DataFrame]
    ) -> pd.DataFrame:
        """
        Apply employment type cleaning to each element in the Series.

        Args:
            feature: Raw Employment Type pd.Series

        Returns:
            pd.DataFrame with columns
            [employment_types, primary_employment, employment_count]

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

        cleaned = feature.apply(self._clean_single)

        return pd.DataFrame(
            {
                "employment_types":   cleaned,
                "primary_employment": cleaned.apply(
                    lambda x: x[0] if x else None
                ),
                "employment_count":   cleaned.apply(len),
            },
            index=feature.index,
        )

    def _clean_single(self, value: Union[str, None]) -> List[str]:
        """
        Parse and normalize a single Employment Type string.

        Args:
            value: Raw employment type string (e.g., "Full Time, Permanent")

        Returns:
            List of normalized employment type strings
        """
        # --- null guard ---
        try:
            if value is None or pd.isna(value):
                return []
        except (TypeError, ValueError):
            pass

        if not isinstance(value, str):
            return []

        value = value.strip()
        if not value:
            return []

        # Split on comma
        tokens = [t.strip() for t in value.split(",") if t.strip()]

        # Normalize + deduplicate
        seen: dict = {}
        for token in tokens:
            # Strip trailing/leading punctuation
            token = re.sub(r'^[,;:|/\s]+|[,;:|/\s]+$', '', token).strip()
            if not token or token.lower() in self.INVALID_VALUES:
                continue
            normalized = self.EMPLOYMENT_NORMALIZATION.get(
                token.lower(), token.title()
            )
            seen.setdefault(normalized, None)

        return list(seen.keys())