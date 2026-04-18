from .feature_cleaning_strategy import FeatureCleaningStrategy
import pandas as pd
import re
from datetime import date, timedelta
from typing import Union


class PostedDateCleaningStrategy(FeatureCleaningStrategy):
    """
    Cleaning strategy for Posted_Date column.

    Converts relative date strings (e.g., "2 days ago", "1 week ago")
    into absolute dates using the Scraped_At timestamp as the reference.

    Requires a pd.DataFrame with columns:
    - posted_date  : relative date string
    - scraped_at   : ISO 8601 timestamp string (e.g., "2024-11-15T10:30:00")

    Relative format rules:
    - "X days ago"    → scraped_date - X days
    - "X day ago"     → scraped_date - X days
    - "X weeks ago"   → scraped_date - X*7 days
    - "X+ weeks ago"  → scraped_date - (X+1)*7 days  (round up)
    - "today"         → scraped_date
    - "yesterday"     → scraped_date - 1 day
    - "just now"      → scraped_date

    Returns:
        pd.DataFrame with columns:
        - posted_date_parsed  (str | None)  — "YYYY-MM-DD"
        - days_since_posted   (int | None)  — days between posted and scraped
    """

    REQUIRED_COLUMNS = {"posted_date", "scraped_at"}

    INVALID_VALUES = {
        "nan", "na", "n/a", "none", "not mentioned", "not specified"
    }

    # Compiled patterns — ordered most-specific to least-specific
    _DAYS_PATTERN  = re.compile(r'(\d+)\+?\s*days?\s+ago', re.IGNORECASE)
    _WEEKS_PATTERN = re.compile(r'(\d+)(\+?)\s*weeks?\s+ago', re.IGNORECASE)
    _TODAY_PATTERN = re.compile(r'\b(today|just\s*now)\b', re.IGNORECASE)
    _YESTERDAY_PATTERN = re.compile(r'\byesterday\b', re.IGNORECASE)

    # ------------------------------------------------------------------ #
    #  Public interface                                                     #
    # ------------------------------------------------------------------ #

    def clean_feature(
        self, feature: Union[pd.Series, pd.DataFrame]
    ) -> pd.DataFrame:
        """
        Parse posted_date relative strings into absolute dates.

        Args:
            feature: pd.DataFrame with columns [posted_date, scraped_at]

        Returns:
            pd.DataFrame with columns [posted_date_parsed, days_since_posted]

        Raises:
            TypeError:  If input is not a pd.Series or pd.DataFrame
            ValueError: If required columns are missing or input is empty
        """
        if not isinstance(feature, (pd.Series, pd.DataFrame)):
            raise TypeError(
                f"Expected pd.Series or pd.DataFrame, "
                f"got {type(feature).__name__}"
            )
        if feature.empty:
            raise ValueError("Input is empty.")

        if isinstance(feature, pd.Series):
            raise ValueError(
                "PostedDateCleaningStrategy requires a pd.DataFrame with "
                f"columns {self.REQUIRED_COLUMNS} (snake_case), got a pd.Series."
            )

        missing = self.REQUIRED_COLUMNS - set(feature.columns)
        if missing:
            raise ValueError(
                f"Input DataFrame missing required columns: {missing}"
            )

        records = feature.apply(
            lambda row: self._clean_single(
                row["posted_date"], row["scraped_at"]
            ),
            axis=1,
        )

        return pd.DataFrame(
            {
                "posted_date_parsed": records.apply(lambda r: r["parsed"]),
                "days_since_posted":  records.apply(lambda r: r["days_since"]),
            },
            index=feature.index,
        )

    # ------------------------------------------------------------------ #
    #  Private helpers                                                      #
    # ------------------------------------------------------------------ #

    def _clean_single(
        self, posted: str, scraped_at: str
    ) -> dict:
        """
        Resolve a single relative Posted_Date using its Scraped_At anchor.

        Args:
            posted:     Raw Posted_Date string (e.g., "3 days ago")
            scraped_at: Raw Scraped_At string  (e.g., "2024-11-15T10:30:00")

        Returns:
            Dict with keys: parsed (str|None), days_since (int|None)
        """
        empty = {"parsed": None, "days_since": None}

        # --- parse scrape anchor date ---
        scraped_date = self._parse_scraped_date(scraped_at)
        if scraped_date is None:
            return empty

        # --- null guard on posted ---
        try:
            if posted is None or pd.isna(posted):
                return empty
        except (TypeError, ValueError):
            pass

        if not isinstance(posted, str):
            return empty

        posted = posted.strip()
        if not posted or posted.lower() in self.INVALID_VALUES:
            return empty

        # --- resolve relative expression ---
        posted_date = self._resolve_relative(posted, scraped_date)
        if posted_date is None:
            return empty

        days_since = (scraped_date - posted_date).days

        return {
            "parsed":     posted_date.strftime("%Y-%m-%d"),
            "days_since": days_since if days_since >= 0 else None,
        }

    def _resolve_relative(
        self, posted: str, reference: date
    ) -> Union[date, None]:
        """
        Convert a relative date expression to an absolute date.

        Args:
            posted:    Cleaned Posted_Date string
            reference: Scraped_At date used as anchor

        Returns:
            Resolved datetime.date, or None if unrecognised format
        """
        # "today" / "just now"
        if self._TODAY_PATTERN.search(posted):
            return reference

        # "yesterday"
        if self._YESTERDAY_PATTERN.search(posted):
            return reference - timedelta(days=1)

        # "X days ago"
        m = self._DAYS_PATTERN.search(posted)
        if m:
            return reference - timedelta(days=int(m.group(1)))

        # "X+ weeks ago" → round up to X+1 weeks
        # "X weeks ago"  → exactly X weeks
        m = self._WEEKS_PATTERN.search(posted)
        if m:
            weeks = int(m.group(1))
            has_plus = bool(m.group(2))          # "+" captured in group 2
            if has_plus:
                weeks += 1                        # round up per user choice
            return reference - timedelta(weeks=weeks)

        return None

    def _parse_scraped_date(self, scraped_at: str) -> Union[date, None]:
        """
        Extract the date portion from a Scraped_At ISO 8601 string.

        Args:
            scraped_at: Raw Scraped_At string (e.g., "2024-11-15T10:30:00")

        Returns:
            datetime.date, or None if invalid
        """
        try:
            if scraped_at is None or pd.isna(scraped_at):
                return None
        except (TypeError, ValueError):
            pass

        if not isinstance(scraped_at, str):
            return None

        # Reuse the same "split on T" logic as TimestampCleaningStrategy
        date_str = scraped_at.strip().split("T")[0]

        try:
            return date.fromisoformat(date_str)   # "YYYY-MM-DD"
        except ValueError:
            return None