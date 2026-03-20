from .feature_cleaning_strategy import FeatureCleaningStrategy
import pandas as pd
import re


class EducationCleaningStrategy(FeatureCleaningStrategy):
    """
    Cleaning strategy for education columns.

    Extracts and normalizes education data into four derived columns:
    - UG_Degree           (str | None)
    - UG_Specialization   (str | None)
    - PG_Degree           (str | None)
    - PG_Specialization   (str | None)

    Handles formats:
    - "UG: B.Tech/B.E. in Computer Science, PG: M.Tech in AI"
    - "UG: Any Graduate, PG: Any Postgraduate"
    - "UG: Not Required, PG: MBA"
    - Missing / null / empty → all four fields None

    Returns:
        pd.DataFrame with columns
        [UG_Degree, UG_Specialization, PG_Degree, PG_Specialization]
    """

    # ------------------------------------------------------------------ #
    #  Degree normalisation map  (pattern → canonical label)               #
    # ------------------------------------------------------------------ #

    DEGREE_MAP = {
        # Undergraduate
        r'\b(b\.?tech|b\.?e\.?|bachelor\s+of\s+technology|bachelor\s+of\s+engineering)\b': 'B.Tech',
        r'\b(bca|bachelor\s+of\s+computer\s+applications?)\b':                              'BCA',
        r'\b(bsc|b\.?sc\.?|bachelor\s+of\s+science)\b':                                    'B.Sc',
        r'\b(bcom|b\.?com\.?|bachelor\s+of\s+commerce)\b':                                 'B.Com',
        r'\b(ba|b\.?a\.?|bachelor\s+of\s+arts)\b':                                         'B.A',
        r'\b(bba|bachelor\s+of\s+business\s+administration)\b':                             'BBA',
        r'\b(diploma)\b':                                                                    'Diploma',
        # Postgraduate
        r'\b(m\.?tech|m\.?e\.?|master\s+of\s+technology|master\s+of\s+engineering)\b':     'M.Tech',
        r'\b(mca|master\s+of\s+computer\s+applications?)\b':                               'MCA',
        r'\b(msc|m\.?sc\.?|master\s+of\s+science)\b':                                      'M.Sc',
        r'\b(mba|master\s+of\s+business\s+administration)\b':                              'MBA',
        r'\b(ma|m\.?a\.?|master\s+of\s+arts)\b':                                           'M.A',
        r'\b(phd|ph\.?d\.?|doctorate)\b':                                                  'Ph.D',
        r'\b(mcom|m\.?com\.?|master\s+of\s+commerce)\b':                                   'M.Com',
    }

    # Compiled once at class level
    _SECTION_PATTERN    = re.compile(r'(UG|PG):\s*(.*?)(?=\s*(?:UG|PG):|$)', re.IGNORECASE)
    _DEGREE_SPEC_PATTERN = re.compile(
        r'([A-Za-z./]+(?:\s*\/\s*[A-Za-z./]+)*)\s+in\s+(.+)',
        re.IGNORECASE
    )
    _NOT_REQUIRED_PATTERN = re.compile(
        r'\b(not required|not specified|any|na|n/a)\b',
        re.IGNORECASE
    )
    _ANY_GRADUATE_PATTERN = re.compile(
        r'\bany\s+(graduate|postgraduate)\b',
        re.IGNORECASE
    )

    _EMPTY_RECORD = {
        "UG_Degree": None, "UG_Specialization": None,
        "PG_Degree": None, "PG_Specialization": None,
    }

    # ------------------------------------------------------------------ #
    #  Public interface                                                     #
    # ------------------------------------------------------------------ #

    def clean_feature(self, feature: pd.Series) -> pd.DataFrame:
        """
        Apply education cleaning to the entire Series.

        Args:
            feature: Raw education Series

        Returns:
            pd.DataFrame with columns
            [UG_Degree, UG_Specialization, PG_Degree, PG_Specialization]

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

        records = feature.apply(self._clean_single)
        return pd.DataFrame(records.tolist())

    # ------------------------------------------------------------------ #
    #  Private helpers                                                      #
    # ------------------------------------------------------------------ #

    def _clean_single(self, value: str) -> dict:
        """
        Parse a single education string into a structured dict.

        Args:
            value: Raw education string

        Returns:
            Dict with keys: UG_Degree, UG_Specialization, PG_Degree, PG_Specialization
        """
        result = self._EMPTY_RECORD.copy()

        # --- null / non-string / empty guard ---
        try:
            if value is None or pd.isna(value):
                return result
        except (TypeError, ValueError):
            pass

        if not isinstance(value, str):
            return result

        value = value.strip()
        if not value:
            return result

        # --- "Not Required / Any / N/A" shortcut ---
        if self._NOT_REQUIRED_PATTERN.search(value):
            if "UG" in value.upper():
                result["UG_Degree"] = "Not Required"
            if "PG" in value.upper():
                result["PG_Degree"] = "Not Required"
            return result

        # --- Extract UG / PG sections ---
        for level, content in self._SECTION_PATTERN.findall(value):
            level   = level.upper()
            content = content.strip().rstrip(',').strip()

            if not content:
                continue

            self._parse_section(level, content, result)

        return result

    def _parse_section(self, level: str, content: str, result: dict) -> None:
        """
        Parse a single UG or PG section and write into result in-place.

        Args:
            level:   "UG" or "PG"
            content: Raw section content string
            result:  Dict to write parsed values into
        """
        degree_key = f"{level}_Degree"
        spec_key   = f"{level}_Specialization"

        # --- "Any Graduate / Any Postgraduate" ---
        if self._ANY_GRADUATE_PATTERN.search(content):
            result[degree_key] = "Any Graduate" if level == "UG" else "Any Postgraduate"
            return

        # --- "Degree in Specialization" ---
        m = self._DEGREE_SPEC_PATTERN.search(content)
        if m:
            result[degree_key] = self._normalize_degree(m.group(1).strip())
            result[spec_key]   = m.group(2).strip()
            return

        # --- Degree only (no "in" keyword) ---
        result[degree_key] = self._normalize_degree(content)
        result[spec_key]   = "Any Specialization"

    def _normalize_degree(self, degree: str) -> str:
        """
        Normalise a raw degree string to its canonical label.

        Args:
            degree: Raw degree string (e.g., "B.Tech/B.E.", "Bachelor of Technology")

        Returns:
            Canonical label (e.g., "B.Tech") or cleaned fallback string
        """
        degree = degree.strip()

        for pattern, canonical in self.DEGREE_MAP.items():
            if re.search(pattern, degree, re.IGNORECASE):
                return canonical

        # Fallback: clean up slash-separated variants
        return degree.replace('/', ' ').strip()