from abc import ABC, abstractmethod
import pandas as pd
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from typing import List

class FeatureEngineeringStrategy(ABC):
    @abstractmethod
    def apply_transform(self, df: pd.DataFrame,feature: List[str]) -> pd.DataFrame:

        pass



class FeatureEngineer:
    def __init__(self, strategy: FeatureEngineeringStrategy):
        self.strategy = strategy

    def set_strategy(self, strategy: FeatureEngineeringStrategy):
        self.strategy = strategy

    def execute_transform(self, df: pd.DataFrame,feature: List[str]) -> pd.DataFrame:
        return self.strategy.apply_transform(df,feature)
    

if __name__ == "__main__":
    # Example usage
    data = pd.DataFrame({
        'feature1': ['A', 'B', 'A', 'C'],
        'feature2': [10, 20, 10, 30],
        'salary': [50000, 60000, 55000, 65000]
    })