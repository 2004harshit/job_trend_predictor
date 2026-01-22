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
        import json
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
        except Exception as e:
            raise ValueError(f"Failed to load config from {config_path}: {e}")
        return config
        

    def _initialize_strategies(self)-> None:
        # Initialize cleaning strategies based on the loaded config
        from .strategies.title_cleaning_strategy import TitleCleaningStrategy
        from.strategies.company_cleaning_strategy import CompanyCleaningStrategy
        from .strategies.location_cleaning_strategy import LocationCleaningStrategy
        from .strategies.salary_cleaning_strategy import SalaryCleaningStrategy 

        strategy_classes = {
            "TitleCleaningStrategy": TitleCleaningStrategy,
            "CompanyCleaningStrategy": CompanyCleaningStrategy,
            "LocationCleaningStrategy": LocationCleaningStrategy,
            "SalaryCleaningStrategy": SalaryCleaningStrategy

        }
        column_mappings = self.config.get("column_mappings", {})
        for column, strategy_name in column_mappings.items():
            strategy_class = strategy_classes.get(strategy_name)
            if strategy_class is None:
                raise ValueError(f"Strategy class '{strategy_name}' not found for column '{column}'")
            
            self.strategy_registry[column] = strategy_class()
        pass

    def clean(self, data: pd.DataFrame, column: str) -> pd.DataFrame:

        # step0 : validate input data and column
        if not self.validate(data, column):
            raise ValueError(f"Validation failed for column '{column}'")
        
        # step1: load preinstanciated cleaning stratgy
        strategy = self.strategy_registry.get(column)
        if not strategy:
            raise ValueError(f"No cleaning strategy found for column '{column}'")
        # step 2: apply cleaning strategy on the data
        cleaned_feature = strategy.clean_feature(data[column])
        # step 3: return cleaned data
        if isinstance(cleaned_feature, pd.Series):
            data[f"{column}_cleaned"] = cleaned_feature
        elif isinstance(cleaned_feature, pd.DataFrame):
            for sub_col in cleaned_feature.columns:
                data[f"{column}_{sub_col}_cleaned"] = cleaned_feature[sub_col]
        else:
            raise TypeError(f"Strategy returned unexpected type: {type(cleaned_feature)} ")
        return data
    
