from .base_cleaner import DataCleaner
from typing import Dict
from .strategies.feature_cleaning_strategy import FeatureCleaningStrategy
import pandas as pd

class JobDataCleaner(DataCleaner):
    """
    Concrete implementation of DataCleaner for job market data.
    
    Applies column-specific cleaning strategies based on configuration file.
    Uses Strategy pattern to delegate cleaning logic to specialized strategy classes.
    
    Attributes:
        strategy_registry (Dict[str, FeatureCleaningStrategy]): Maps column names to strategies
        config_path (str): Path to configuration JSON file
        config (dict): Loaded configuration dictionary
    
    Example:
        >>> cleaner = JobDataCleaner("config/cleaning_config.json")
        >>> df = pd.read_csv("jobs.csv")
        >>> df = cleaner.clean(df, "Title")
    """
    def __init__(self, config_path:str):
        self.strategy_registry: Dict[str, FeatureCleaningStrategy] = {}
        self.config_path: str = config_path
        self.config: dict = self._load_config(config_path)
        self._initialize_strategies()
    
    def _load_config(self, config_path: str)-> dict:
        # Load configuration from the given path
        pass

    def _initialize_strategies(self)-> None:
        # Initialize cleaning strategies based on the loaded config
        pass

    def clean(self, data: pd.DataFrame, column: str) -> pd.DataFrame:

        # step0 : validate input data and column
        if not self.validate(data, column):
            raise ValueError(f"Validation failed for column '{column}'")
        
        # step1: load preinstanciated cleaning stratgy

        # step 2: apply cleaning strategy on the data

        # step 3: return cleaned data

        pass
