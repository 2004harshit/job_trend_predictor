from .feature_cleaning_strategy import FeatureCleaningStrategy
import pandas as pd
import re
from typing import Union


class RoleCategoryCleaningStrategy(FeatureCleaningStrategy):
    """
    Cleaning strategy for Role Category column.

    Operations:
    - Strips whitespace and punctuation noise
    - Normalizes known role category variants
    - Returns None for invalid / empty inputs

    Observed patterns from data:
    - "Software Development"              → "Software Development"
    - "IT Security"                       → "IT Security"
    - "DBA / Data warehousing"            → "DBA / Data Warehousing"
    - "Business Intelligence & Analytics" → "Business Intelligence & Analytics"

    Returns:
        pd.Series of cleaned role category strings (or None)
    """

    ROLE_CATEGORY_NORMALIZATION = {
        # Engineering & Development
        "software development":               "Software Development",
        "software engineering":               "Software Engineering",
        "front end development":              "Front End Development",
        "frontend development":               "Front End Development",
        "back end development":               "Back End Development",
        "backend development":                "Back End Development",
        "full stack development":             "Full Stack Development",
        "mobile development":                 "Mobile Development",
        "embedded systems":                   "Embedded Systems",
        "devops":                             "DevOps",
        # Data & Analytics
        "data science":                       "Data Science",
        "data engineering":                   "Data Engineering",
        "data analytics":                     "Data Analytics",
        "business intelligence & analytics":  "Business Intelligence & Analytics",
        "business intelligence and analytics":"Business Intelligence & Analytics",
        "bi & analytics":                     "Business Intelligence & Analytics",
        "dba / data warehousing":             "DBA / Data Warehousing",
        "dba/data warehousing":               "DBA / Data Warehousing",
        "database administration":            "Database Administration",
        # Security & Infrastructure
        "it security":                        "IT Security",
        "cybersecurity":                      "Cybersecurity",
        "network & system admin":             "Network & System Administration",
        "network and system admin":           "Network & System Administration",
        "cloud infrastructure":               "Cloud Infrastructure",
        "infrastructure":                     "Infrastructure",
        # Management
        "project management":                 "Project Management",
        "product management":                 "Product Management",
        "it management":                      "IT Management",
        # Support & QA
        "it support":                         "IT Support",
        "technical support":                  "Technical Support",
        "quality assurance":                  "Quality Assurance",
        "qa":                                 "Quality Assurance",
        "testing":                            "Quality Assurance",
        # Design
        "ui/ux":                              "UI/UX Design",
        "design":                             "Design",
    }

    INVALID_VALUES = {
        "na", "n/a", "none", "not specified",
        "not mentioned", "tbd", "other"
    }

    def clean_feature(
        self, feature: Union[pd.Series, pd.DataFrame]
    ) -> pd.Series:
        """
        Apply role category cleaning to each element in the Series.

        Args:
            feature: Raw Role Category pd.Series

        Returns:
            pd.Series of normalized role category strings

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
        Normalize a single Role Category string.

        Args:
            value: Raw role category (e.g., "DBA / Data warehousing")

        Returns:
            Normalized string, or None if invalid
        """
        # --- null guard ---
        try:
            if value is None or pd.isna(value):
                return None
        except (TypeError, ValueError):
            pass

        if not isinstance(value, str):
            return None

        # Strip trailing/leading noise
        value = re.sub(r'^[,;:|/\s]+|[,;:|/\s]+$', '', value).strip()
        value = re.sub(r'\s+', ' ', value).strip()

        if not value or len(value) < 2:
            return None

        if value.lower() in self.INVALID_VALUES:
            return None

        return self.ROLE_CATEGORY_NORMALIZATION.get(
            value.lower(), value.title()
        )