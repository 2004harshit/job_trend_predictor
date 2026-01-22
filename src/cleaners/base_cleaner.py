from abc import ABC, abstractmethod
import pandas as pd

class DataCleaner(ABC):
    @abstractmethod
    def clean(self, data: pd.DataFrame, column: str) -> pd.DataFrame:
        """Cleans the input DataFrame and returns the cleaned version."""
        pass

    def validate_column_exists(self, data: pd.DataFrame, column: str) -> bool:
        """Validates if the specified column exists in the DataFrame."""
        return column in data.columns
    
    def validate_dataframe(self, data: pd.DataFrame) -> bool:
        """Validates if the input is a valid DataFrame."""
        return isinstance(data, pd.DataFrame) and not data.empty
    
    def validate_column_data(self, data: pd.DataFrame, column: str) -> bool:
        """Validate column data quality (nulls, types, etc.)"""
        if column not in data.columns:
            return False
        # Check for all nulls
        if data[column].isna().all():
            return False
        return True
    
    def validate(self, data: pd.DataFrame, column: str) -> bool:
        """
        Validates the DataFrame and specified column.
        Checks are performed in order: DataFrame → Column exists → Column data quality
        """
        if not self.validate_dataframe(data):
            return False

        if not self.validate_column_exists(data, column):
            return False

        if not self.validate_column_data(data, column):
            return False

        return True