from .feature_cleaning_strategy import FeatureCleaningStrategy
import pandas as pd
import re


class CompanyCleaningStrategy(FeatureCleaningStrategy):
    """
    Cleaning strategy for company name columns.

    Operations:
    - Removes hiring/job posting prefixes (e.g., "Hiring for", "Urgent Hiring")
    - Splits on common separators and retains the main company name
    - Removes legal entity suffixes (e.g., "Pvt. Ltd.", "Inc.", "LLP")
    - Removes urgency/metadata suffixes (e.g., "Remote", "WFH", "Urgent")
    - Normalizes whitespace and punctuation
    - Returns "Unknown" for null, empty, or invalid inputs
    """

    PREFIX_PATTERNS = [
        r'\bHiring\s+for\b',
        r'\bImmediate\s+Hiring\b',
        r'\bPosted\s+by:?\b',
        r'\bUrgent\s+Hiring\b',
        r'\bWalk-?in\b',
        r'\bOpening\s+for\b',
        r'\bNow\s+Hiring\b',
        r'\bJobs?\s+at\b',
        r'\bCareers?\s+at\b',
        r'\bHiring\s*@\b',
        r'\bJoin\b',
        r'\bApply\s+to\b',
        r'\bWork\s+at\b',
    ]

    SUFFIX_PATTERNS = [
        r'\bPvt\.?\s*Ltd\.?\b',
        r'\bPrivate\s+Limited\b',
        r'\bLimited\b',
        r'\bLtd\.?\b',
        r'\bLLP\b',
        r'\bInc\.?\b',
        r'\bCorporation\b',
        r'\bCorp\.?\b',
        r'\bCompany\b',
        r'\bCo\.?\b(?!\w)',
        r'\bPLC\b',
        r'\bLLC\b',
    ]

    URGENCY_PATTERNS = [
        r'\(?\s*Urgent\s*\)?',
        r'\(?\s*Immediate\s+Joiner\s*\)?',
        r'\(?\s*Work\s+From\s+Home\s*\)?',
        r'\(?\s*WFH\s*\)?',
        r'\(?\s*Remote\s*\)?',
        r'\(?\s*Hybrid\s*\)?',
    ]

    def clean_feature(self, feature: pd.Series) -> pd.Series:
        """
        Apply company name cleaning to each element in the Series.

        Args:
            feature: Raw company name Series

        Returns:
            Cleaned company name Series

        Raises:
            TypeError: If input is not a pandas Series
            ValueError: If the Series is empty
        """
        if not isinstance(feature, pd.Series):
            raise TypeError(
                f"Expected pd.Series, got {type(feature).__name__}"
            )
        if feature.empty:
            raise ValueError("Input Series is empty.")

        return feature.apply(self._clean_single)

    def _clean_single(self, company: str) -> str:
        """
        Clean a single company name string.

        Args:
            company: Raw company name

        Returns:
            Cleaned company name or "Unknown" if invalid/empty
        """
        # Step 0: Handle null / non-string inputs
        try:
            if company is None or pd.isna(company):
                return "Unknown"
        except (TypeError, ValueError):
            # pd.isna() can raise on certain types
            pass

        if not isinstance(company, str):
            return "Unknown"

        company = company.strip()
        if not company:
            return "Unknown"

        # Step 1: Remove hiring/job posting prefixes
        for pattern in self.PREFIX_PATTERNS:
            company = re.sub(pattern, '', company, flags=re.IGNORECASE).strip()

        # Step 2: Split on common separators, keep main company name
        company = re.split(r'\s*[-|:@]\s*', company)[0].strip()

        # Step 3: Remove legal entity suffixes
        for pattern in self.SUFFIX_PATTERNS:
            company = re.sub(pattern, '', company, flags=re.IGNORECASE).strip()

        # Step 4: Remove urgency/metadata suffixes
        for pattern in self.URGENCY_PATTERNS:
            company = re.sub(pattern, '', company, flags=re.IGNORECASE).strip()

        # Step 5: Normalize whitespace
        company = re.sub(r'\s+', ' ', company).strip()

        # Step 6: Remove leading/trailing stray punctuation
        company = re.sub(r'^[,;:\-|@\s]+|[,;:\-|@\s]+$', '', company).strip()

        # Step 7: Final validity check
        if not company or len(company) < 2:
            return "Unknown"

        return company