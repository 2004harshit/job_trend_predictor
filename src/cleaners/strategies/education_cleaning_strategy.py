from .feature_cleaning_strategy import FeatureCleaningStrategy
import pandas as pd
import re


class EducationCleaningStrategy(FeatureCleaningStrategy):
    """
    Cleaning strategy for education columns.

    Extracts and normalizes education data into four derived columns:
    - ug_degree           (str | None)
    - ug_specialization   (str | None)
    - pg_degree           (str | None)
    - pg_specialization   (str | None)

    Handles formats seen in raw Naukri data:
    - "EducationUG:B.Tech/B.E. in Any SpecializationPG:M.Tech in AI"
    - "EducationUG:Any GraduatePG:Any Postgraduate"
    - "EducationUG:B.Tech/B.E. in Any Specialization"
    - "EducationUG:Not Required"
    - "UG: B.Tech/B.E. in Computer Science"    (space-after-colon variant)
    - Missing / null / empty → all four fields None

    Returns:
        pd.DataFrame with columns
        [ug_degree, ug_specialization, pg_degree, pg_specialization]
    """

    # ------------------------------------------------------------------ #
    #  Degree normalisation map  (pattern → canonical label)               #
    # ------------------------------------------------------------------ #

    DEGREE_MAP = {
        # Undergraduate — b.tech before b.e to avoid partial match on "B.E" inside "B.Tech"
        r'\b(b\.?tech|bachelor\s+of\s+technology)\b':                                       'B.Tech',
        r'\b(b\.?e\.?|bachelor\s+of\s+engineering)\b':                                      'B.E',
        r'\b(bca|bachelor\s+of\s+computer\s+applications?)\b':                              'BCA',
        r'\b(bsc|b\.?sc\.?|bachelor\s+of\s+science)\b':                                    'B.Sc',
        r'\b(bcom|b\.?com\.?|bachelor\s+of\s+commerce)\b':                                 'B.Com',
        r'\b(bba|bachelor\s+of\s+business\s+administration)\b':                             'BBA',
        r'\b(ba|b\.?a\.?|bachelor\s+of\s+arts)\b':                                         'B.A',
        r'\b(diploma)\b':                                                                    'Diploma',
        # Postgraduate
        r'\b(m\.?tech|master\s+of\s+technology)\b':                                         'M.Tech',
        r'\b(m\.?e\.?|master\s+of\s+engineering)\b':                                        'M.E',
        r'\b(mca|master\s+of\s+computer\s+applications?)\b':                               'MCA',
        r'\b(msc|m\.?sc\.?|master\s+of\s+science)\b':                                      'M.Sc',
        r'\b(mba|master\s+of\s+business\s+administration)\b':                              'MBA',
        r'\b(mcom|m\.?com\.?|master\s+of\s+commerce)\b':                                   'M.Com',
        r'\b(ma|m\.?a\.?|master\s+of\s+arts)\b':                                           'M.A',
        r'\b(phd|ph\.?d\.?|doctorate)\b':                                                  'Ph.D',
    }

    # ------------------------------------------------------------------ #
    #  Compiled patterns                                                    #
    # ------------------------------------------------------------------ #

    # Strips the "Education" word Naukri prepends before the UG/PG markers.
    # "EducationUG:B.Tech..." → "UG:B.Tech..."
    _EDUCATION_PREFIX = re.compile(r'^education', re.IGNORECASE)

    # Splits value into (level, content) pairs.
    # Handles both "EducationUG:..." (no space) and "UG: ..." (space after colon).
    # Lookahead (?=UG:|PG:|$) stops content at the next section boundary.
    _SECTION_PATTERN = re.compile(
        r'(UG|PG):\s*(.*?)(?=(?:UG|PG):|$)',
        re.IGNORECASE | re.DOTALL
    )

    # "Degree in Specialization" — e.g. "B.Tech/B.E. in Computer Science"
    _DEGREE_SPEC_PATTERN = re.compile(
        r'([A-Za-z./]+(?:\s*\/\s*[A-Za-z./]+)*)\s+in\s+(.+)',
        re.IGNORECASE
    )

    # Only matches genuinely invalid/missing values — NOT "any" alone,
    # because "Any Graduate" and "Any Postgraduate" are valid degree values.
    _NOT_REQUIRED_PATTERN = re.compile(
        r'\b(not\s+required|not\s+specified|na|n/a)\b',
        re.IGNORECASE
    )

    _ANY_GRADUATE_PATTERN = re.compile(
        r'\bany\s+(graduate|postgraduate)\b',
        re.IGNORECASE
    )

    # Output keys — lowercase, matching the pipeline's all-lowercase column contract
    _EMPTY_RECORD = {
        "ug_degree":         None,
        "ug_specialization": None,
        "pg_degree":         None,
        "pg_specialization": None,
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
            [ug_degree, ug_specialization, pg_degree, pg_specialization]

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
        return pd.DataFrame(records.tolist(), index=feature.index)

    # ------------------------------------------------------------------ #
    #  Private helpers                                                      #
    # ------------------------------------------------------------------ #

    def _clean_single(self, value: str) -> dict:
        """
        Parse a single education string into a structured dict.

        Args:
            value: Raw education string (e.g. "EducationUG:B.Tech/B.E. in CS")

        Returns:
            Dict with keys: ug_degree, ug_specialization, pg_degree, pg_specialization
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

        # Strip the "Education" prefix Naukri prepends before UG/PG markers
        value = self._EDUCATION_PREFIX.sub('', value).strip()

        # --- Extract UG / PG sections ---
        matches = self._SECTION_PATTERN.findall(value)

        if not matches:
            # No UG/PG markers at all — treat entire value as UG degree
            value_stripped = value.strip().rstrip(',').strip()
            if value_stripped:
                self._parse_section("UG", value_stripped, result)
            return result

        for level, content in matches:
            content = content.strip().rstrip(',').strip()
            if content:
                self._parse_section(level.upper(), content, result)

        return result

    def _parse_section(self, level: str, content: str, result: dict) -> None:
        """
        Parse a single UG or PG section and write into result in-place.

        Args:
            level:   "UG" or "PG"  (always uppercase when called)
            content: Raw section content (e.g. "B.Tech/B.E. in Any Specialization")
            result:  Dict to write into — keys are lowercase (ug_degree, pg_degree, ...)
        """
        # Keys lowercase — matches _EMPTY_RECORD and the pipeline's lowercase contract
        degree_key = f"{level.lower()}_degree"          # "ug_degree" / "pg_degree"
        spec_key   = f"{level.lower()}_specialization"  # "ug_specialization" / "pg_specialization"

        # --- "Not Required / N/A" ---
        if self._NOT_REQUIRED_PATTERN.search(content):
            result[degree_key] = "Not Required"
            result[spec_key]   = None
            return

        # --- "Any Graduate / Any Postgraduate" ---
        if self._ANY_GRADUATE_PATTERN.search(content):
            result[degree_key] = "Any Graduate" if level == "UG" else "Any Postgraduate"
            result[spec_key]   = None
            return

        # --- "Degree in Specialization" — e.g. "B.Tech/B.E. in Computer Science" ---
        m = self._DEGREE_SPEC_PATTERN.search(content)
        if m:
            result[degree_key] = self._normalize_degree(m.group(1).strip())
            raw_spec = m.group(2).strip()
            # "Any Specialization" is a Naukri filler — store as None
            result[spec_key] = None if raw_spec.lower() == "any specialization" else raw_spec
            return

        # --- Degree only (no "in" keyword) — e.g. "MBA", "MCA" ---
        result[degree_key] = self._normalize_degree(content)
        result[spec_key]   = None

    def _normalize_degree(self, degree: str) -> str:
        """
        Normalise a raw degree string to its canonical label.

        For slash-separated variants like "B.Tech/B.E.", the first matching
        pattern wins (B.Tech is listed before B.E in DEGREE_MAP).

        Args:
            degree: Raw degree string (e.g. "B.Tech/B.E.", "Bachelor of Technology")

        Returns:
            Canonical label (e.g. "B.Tech") or the original string stripped of noise
        """
        degree = degree.strip()

        for pattern, canonical in self.DEGREE_MAP.items():
            if re.search(pattern, degree, re.IGNORECASE):
                return canonical

        # BUG FIX 1: was `degree.replace('/', ' ').str` — `.str` is a pandas
        # accessor and does not exist on plain Python strings. Fixed to `.strip()`.
        return degree.replace('/', ' ').strip()