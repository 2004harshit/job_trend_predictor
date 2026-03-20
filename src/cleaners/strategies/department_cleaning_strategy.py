from .feature_cleaning_strategy import FeatureCleaningStrategy
import pandas as pd
import re
from typing import Union, List


class DepartmentCleaningStrategy(FeatureCleaningStrategy):
    """
    Cleaning strategy for department columns.

    Operations:
    - Splits comma / slash / pipe / hyphen / ampersand-separated strings or lists
    - Normalizes abbreviations and synonyms via DEPARTMENT_NORMALIZATION map
    - Filters noise tokens via INVALID_DEPARTMENTS set
    - Deduplicates while preserving insertion order

    Returns:
        pd.DataFrame with columns:
        - Department_Cleaned   (List[str])
        - Primary_Department   (str | None)  — first item in cleaned list
        - Department_Count     (int)
    """

    DEPARTMENT_NORMALIZATION = {
        # IT & Technology
        'it': 'Information Technology',
        'information technology': 'Information Technology',
        'tech': 'Technology',
        'technology': 'Technology',
        'software': 'Software Development',
        'software development': 'Software Development',
        'software engineering': 'Software Engineering',
        'engineering': 'Engineering',
        'data': 'Data Science',
        'data science': 'Data Science',
        'analytics': 'Analytics',
        'ai': 'Artificial Intelligence',
        'ml': 'Machine Learning',
        # Business Functions
        'hr': 'Human Resources',
        'human resources': 'Human Resources',
        'human resource': 'Human Resources',
        'finance': 'Finance',
        'accounts': 'Finance',
        'accounting': 'Finance',
        'sales': 'Sales',
        'marketing': 'Marketing',
        'sales & marketing': 'Sales & Marketing',
        'sales and marketing': 'Sales & Marketing',
        'operations': 'Operations',
        'ops': 'Operations',
        'admin': 'Administration',
        'administration': 'Administration',
        'legal': 'Legal',
        # R&D and Product
        'r&d': 'Research & Development',
        'research': 'Research & Development',
        'research and development': 'Research & Development',
        'product': 'Product Management',
        'product management': 'Product Management',
        'project management': 'Project Management',
        'pmo': 'Project Management Office',
        # Operations & Support
        'customer service': 'Customer Service',
        'customer support': 'Customer Support',
        'support': 'Customer Support',
        'technical support': 'Technical Support',
        'quality': 'Quality Assurance',
        'qa': 'Quality Assurance',
        'quality assurance': 'Quality Assurance',
        'testing': 'Quality Assurance',
        # Design & Creative
        'design': 'Design',
        'ui/ux': 'UI/UX Design',
        'ux': 'UX Design',
        'ui': 'UI Design',
        'creative': 'Creative',
        'graphics': 'Graphics Design',
        # Infrastructure
        'devops': 'DevOps',
        'infrastructure': 'Infrastructure',
        'network': 'Network',
        'security': 'Security',
        'cybersecurity': 'Cybersecurity',
        'cloud': 'Cloud',
        # Manufacturing & Production
        'production': 'Production',
        'manufacturing': 'Manufacturing',
        'supply chain': 'Supply Chain',
        'logistics': 'Logistics',
        'procurement': 'Procurement',
        # Consulting & Advisory
        'consulting': 'Consulting',
        'advisory': 'Advisory',
        'strategy': 'Strategy',
        # Other
        'general': 'General',
        'other': 'Other',
        'misc': 'Miscellaneous',
        'miscellaneous': 'Miscellaneous',
    }

    INVALID_DEPARTMENTS = {
        'na', 'n/a', 'none', 'not specified', 'not mentioned',
        'any', 'all', 'multiple', 'various', 'tbd', 'to be decided',
    }

    # ------------------------------------------------------------------ #
    #  Public interface                                                     #
    # ------------------------------------------------------------------ #

    def clean_feature(
        self, feature: Union[pd.Series, pd.DataFrame]
    ) -> pd.DataFrame:
        """
        Apply department cleaning to a Series of raw department strings.

        Args:
            feature: pd.Series of raw department strings or lists

        Returns:
            pd.DataFrame with columns
            [Department_Cleaned, Primary_Department, Department_Count]

        Raises:
            TypeError:  If input is not a pd.Series or pd.DataFrame
            ValueError: If the input is empty
        """
        if not isinstance(feature, (pd.Series, pd.DataFrame)):
            raise TypeError(
                f"Expected pd.Series or pd.DataFrame, "
                f"got {type(feature).__name__}"
            )
        if feature.empty:
            raise ValueError("Input is empty.")

        # Department works on a single column — enforce Series
        if isinstance(feature, pd.DataFrame):
            raise ValueError(
                "DepartmentCleaningStrategy expects a pd.Series, "
                "not a pd.DataFrame. Pass a single column."
            )

        cleaned = feature.apply(self._clean_single)

        return pd.DataFrame(
            {
                "Department_Cleaned":  cleaned,
                "Primary_Department":  cleaned.apply(
                    lambda x: x[0] if x else None
                ),
                "Department_Count":    cleaned.apply(len),
            },
            index=feature.index,
        )

    # ------------------------------------------------------------------ #
    #  Private helpers                                                      #
    # ------------------------------------------------------------------ #

    def _clean_single(self, value: Union[str, list, None]) -> List[str]:
        """
        Parse, normalize, and deduplicate departments from a single value.

        Args:
            value: Raw department string or list

        Returns:
            Ordered, deduplicated list of normalized department strings
        """
        # --- null guard ---
        try:
            if value is None or pd.isna(value):
                return []
        except (TypeError, ValueError):
            pass

        # --- parse to token list ---
        tokens = self._parse_department_input(value)

        # --- normalize + deduplicate ---
        seen: dict = {}
        for token in tokens:
            normalized = self._normalize_department(token)
            if normalized is not None:
                seen.setdefault(normalized, None)

        return list(seen.keys())

    def _parse_department_input(
        self, value: Union[str, list]
    ) -> List[str]:
        """
        Split raw input into individual department token strings.

        Args:
            value: Department string or list

        Returns:
            List of stripped, non-empty raw tokens
        """
        if isinstance(value, list):
            return [str(d).strip() for d in value if d]

        value = str(value).strip()
        value = re.sub(r'^\[|\]$', '', value)   # strip brackets
        value = re.sub(r'["\']', '', value)      # strip quotes

        # Split on comma, slash, pipe, hyphen, ampersand
        # Note: ampersand kept as split char except when part of "R&D",
        # "Sales & Marketing" etc. — normalization map handles those combos.
        tokens = re.split(r'[,/\-|&]', value)
        return [t.strip() for t in tokens if t.strip()]

    def _normalize_department(self, dept: str) -> Union[str, None]:
        """
        Normalize a single raw department token to its canonical label.

        Args:
            dept: Raw department token

        Returns:
            Canonical department string, or None if invalid / noise
        """
        if not dept or not isinstance(dept, str):
            return None

        dept_lower = dept.strip().lower()

        # Strip leading/trailing punctuation
        dept_lower = re.sub(
            r'^[.,;:\-/|()&]+|[.,;:\-/|()&]+$', '', dept_lower
        ).strip()

        if not dept_lower or len(dept_lower) < 2:
            return None

        if dept_lower in self.INVALID_DEPARTMENTS:
            return None

        if dept_lower in self.DEPARTMENT_NORMALIZATION:
            return self.DEPARTMENT_NORMALIZATION[dept_lower]

        return dept.strip().title()