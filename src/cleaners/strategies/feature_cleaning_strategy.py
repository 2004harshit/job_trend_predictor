from abc import ABC, abstractmethod
import pandas as pd

class FeatureCleaningStrategy(ABC):
    """
    Abstract base class for feature cleaning strategies.
    
    Strategies operate on individual Series (columns) and return cleaned Series.
    """
    
    @abstractmethod
    def clean_feature(self, feature: pd.Series) -> pd.Series|pd.DataFrame:
        """
        Clean a feature (column) and return cleaned version.
        
        Args:
            feature: Input Series to clean
        
        Returns:
            pd.Series: For single-column output
            pd.DataFrame: For multi-column output
        """
        pass
    
    def validate(self, feature: pd.Series) -> bool:
        """
        Optional validation hook. Override if needed.
        
        Args:
            feature: Series to validate
        
        Returns:
            True if valid for cleaning
        """
        return True