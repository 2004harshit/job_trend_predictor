from .feature_cleaning_strategy import FeatureCleaningStrategy
import pandas as pd
import re
from typing import Union, List


class IndustryTypeCleaningStrategy(FeatureCleaningStrategy):
    """
    Cleaning strategy for Industry Type column.

    Operations:
    - Strips trailing commas and whitespace noise
    - Splits multi-value strings
    - Normalizes known industry variants
    - Deduplicates while preserving order

    Observed patterns from data:
    - "IT Services & Consulting ," → ["IT Services & Consulting"]
    - "Banking ,"                  → ["Banking"]
    - "Education / Training ,"     → ["Education", "Training"]

    Returns:
        pd.DataFrame with columns:
        - industry_types    (List[str])
        - primary_industry  (str | None)
        - industry_count    (int)
    """

    INDUSTRY_NORMALIZATION = {
        # Technology
        "it services & consulting":  "IT Services & Consulting",
        "it services and consulting": "IT Services & Consulting",
        "information technology":    "Information Technology",
        "it":                        "Information Technology",
        "software":                  "Software",
        "software product":          "Software Product",
        "internet":                  "Internet",
        "saas":                      "SaaS",
        # Finance
        "banking":                   "Banking",
        "banking / finance":         "Banking & Finance",
        "banking and finance":       "Banking & Finance",
        "financial services":        "Financial Services",
        "insurance":                 "Insurance",
        "fintech":                   "Fintech",
        # Other sectors
        "education / training":      "Education & Training",
        "education and training":    "Education & Training",
        "education":                 "Education",
        "edtech":                    "EdTech",
        "healthcare":                "Healthcare",
        "health care":               "Healthcare",
        "pharma":                    "Pharmaceuticals",
        "pharmaceuticals":           "Pharmaceuticals",
        "e-commerce":                "E-Commerce",
        "ecommerce":                 "E-Commerce",
        "retail":                    "Retail",
        "manufacturing":             "Manufacturing",
        "automotive":                "Automotive",
        "telecom":                   "Telecommunications",
        "telecommunications":        "Telecommunications",
        "media":                     "Media",
        "media & entertainment":     "Media & Entertainment",
        "recruitment / staffing":    "Recruitment & Staffing",
        "recruitment and staffing":  "Recruitment & Staffing",
        "staffing":                  "Recruitment & Staffing",
        "consulting":                "Consulting",
        "urban transport":           "Urban Transport",
        "logistics":                 "Logistics",
        "supply chain":              "Supply Chain",
        "government":                "Government",
        "public sector":             "Public Sector",
        "ngo":                       "NGO",
        "real estate":               "Real Estate",
        "energy":                    "Energy",
        "oil and gas":               "Oil & Gas",
        "oil & gas":                 "Oil & Gas",
    }

    INVALID_VALUES = {
        "na", "n/a", "none", "not specified",
        "not mentioned", "tbd", "other"
    }

    def clean_feature(
        self, feature: Union[pd.Series, pd.DataFrame]
    ) -> pd.DataFrame:
        """
        Apply industry type cleaning to each element in the Series.

        Args:
            feature: Raw Industry Type pd.Series

        Returns:
            pd.DataFrame with columns
            [industry_types, primary_industry, industry_count]

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
                "industry_types":   cleaned,
                "primary_industry": cleaned.apply(
                    lambda x: x[0] if x else None
                ),
                "industry_count":   cleaned.apply(len),
            },
            index=feature.index,
        )

    def _clean_single(self, value: Union[str, None]) -> List[str]:
        """
        Parse and normalize a single Industry Type string.

        Args:
            value: Raw industry string (e.g., "IT Services & Consulting ,")

        Returns:
            List of normalized industry strings
        """
        # --- null guard ---
        try:
            if value is None or pd.isna(value):
                return []
        except (TypeError, ValueError):
            pass

        if not isinstance(value, str):
            return []

        # Strip trailing noise first (handles "Banking ,")
        value = re.sub(r'[,\s]+$', '', value).strip()

        if not value:
            return []

        # Split on comma only (slash handled by normalization map)
        tokens = [t.strip() for t in value.split(",") if t.strip()]

        seen: dict = {}
        for token in tokens:
            token = re.sub(r'^[,;:|/\s]+|[,;:|/\s]+$', '', token).strip()
            if not token or token.lower() in self.INVALID_VALUES:
                continue
            normalized = self.INDUSTRY_NORMALIZATION.get(
                token.lower(), token.title()
            )
            seen.setdefault(normalized, None)

        return list(seen.keys())