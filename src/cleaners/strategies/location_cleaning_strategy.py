from .feature_cleaning_strategy import FeatureCleaningStrategy
import pandas as pd
import re
from typing import Union, List


class LocationCleaningStrategy(FeatureCleaningStrategy):
    """
    Cleaning strategy for location columns.

    Operations:
    - Splits comma-separated city strings into a list
    - Strips whitespace and trailing punctuation from each city
    - Detects remote/WFH indicators
    - Normalizes known city name variants (e.g., "Bangalore" → "Bengaluru")
    - Filters empty or noise tokens

    Returns:
        pd.DataFrame with columns:
        - location_cities   (List[str])  — list of cleaned city names
        - primary_location  (str | None) — first city in list
        - location_count    (int)        — number of cities
        - is_remote         (bool)       — True if remote/WFH role
    """

    REMOTE_INDICATORS = {
        "remote", "work from home", "wfh", "anywhere",
        "work from anywhere", "virtual", "pan india"
    }

    # Common city name normalization for Indian job market
    CITY_NORMALIZATION = {
        "bangalore":  "Bengaluru",
        "bengaluru":  "Bengaluru",
        "bombay":     "Mumbai",
        "mumbai":     "Mumbai",
        "delhi":      "Delhi",
        "new delhi":  "New Delhi",
        "calcutta":   "Kolkata",
        "kolkata":    "Kolkata",
        "hyderabad":  "Hyderabad",
        "pune":       "Pune",
        "chennai":    "Chennai",
        "ahmedabad":  "Ahmedabad",
        "noida":      "Noida",
        "gurugram":   "Gurugram",
        "gurgaon":    "Gurugram",
    }

    # ------------------------------------------------------------------ #
    #  Public interface                                                     #
    # ------------------------------------------------------------------ #

    def clean_feature(
        self, feature: Union[pd.Series, pd.DataFrame]
    ) -> pd.DataFrame:
        """
        Apply location cleaning to each element in the Series.

        Args:
            feature: Raw location pd.Series

        Returns:
            pd.DataFrame with columns:
            [location_cities, primary_location, location_count, is_remote]

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

        return pd.DataFrame(
            {
                "location_cities":  records.apply(lambda r: r["cities"]),
                "primary_location": records.apply(lambda r: r["cities"][0] if r["cities"] else None),
                "location_count":   records.apply(lambda r: len(r["cities"])),
                "is_remote":        records.apply(lambda r: r["is_remote"]),
            },
            index=feature.index,
        )

    # ------------------------------------------------------------------ #
    #  Private helpers                                                      #
    # ------------------------------------------------------------------ #

    def _clean_single(self, value: str) -> dict:
        """
        Parse and clean a single location string.

        Args:
            value: Raw location string (e.g., "Hyderabad,Chennai,Bengaluru")

        Returns:
            Dict with keys: cities (List[str]), is_remote (bool)
        """
        empty = {"cities": [], "is_remote": False}

        # --- null guard ---
        try:
            if value is None or pd.isna(value):
                return empty
        except (TypeError, ValueError):
            pass

        if not isinstance(value, str):
            return empty

        value = value.strip()
        if not value:
            return empty

        # --- remote detection on raw string first ---
        is_remote = self._is_remote(value)

        # --- split into city tokens ---
        raw_cities = [c.strip() for c in value.split(",") if c.strip()]

        # --- clean and normalize each city ---
        cities = []
        for raw in raw_cities:
            city = self._clean_city(raw)
            if city:
                cities.append(city)

        # Deduplicate while preserving order
        seen = dict.fromkeys(cities)
        cities = list(seen.keys())

        return {"cities": cities, "is_remote": is_remote}

    def _is_remote(self, value: str) -> bool:
        """
        Check if the raw location string indicates a remote role.

        Args:
            value: Raw location string

        Returns:
            True if any remote indicator is found
        """
        value_lower = value.lower()
        return any(indicator in value_lower for indicator in self.REMOTE_INDICATORS)

    def _clean_city(self, city: str) -> Union[str, None]:
        """
        Clean and normalize a single city name token.

        Args:
            city: Raw city string

        Returns:
            Normalized city string, or None if invalid/noise
        """
        if not city or not isinstance(city, str):
            return None

        # Strip leading/trailing punctuation and whitespace
        city = re.sub(r'^[.,;:\-/|()\s]+|[.,;:\-/|()\s]+$', '', city).strip()

        if not city or len(city) < 2:
            return None

        # Normalize known variants (case-insensitive lookup)
        city_lower = city.lower()
        if city_lower in self.CITY_NORMALIZATION:
            return self.CITY_NORMALIZATION[city_lower]

        # Title case fallback
        return city.title()