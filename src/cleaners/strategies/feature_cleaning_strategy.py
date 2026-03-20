from abc import ABC, abstractmethod
import pandas as pd
from typing import Union


class FeatureCleaningStrategy(ABC):
    """
    Abstract base class for all feature cleaning strategies.

    clean_feature accepts either a pd.Series (single column)
    or a pd.DataFrame (multi-column), depending on the strategy.
    """

    @abstractmethod
    def clean_feature(
        self, feature: Union[pd.Series, pd.DataFrame]
    ) -> Union[pd.Series, pd.DataFrame]:
        """
        Clean the input feature(s) and return the cleaned result.

        Args:
            feature: A pd.Series for single-column strategies,
                     or a pd.DataFrame for multi-column strategies
                     (e.g., SkillsCleaningStrategy).

        Returns:
            pd.Series  → single cleaned column
            pd.DataFrame → multiple derived columns
        """
        pass