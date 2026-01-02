from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple, Union
import pandas as pd
from sklearn.model_selection import train_test_split


class DataSplittingStrategy(ABC):
    @abstractmethod
    def split(self, data: pd.DataFrame, *args, **kwargs) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        pass


class SimpleTrainTestSplittingStrategy(DataSplittingStrategy):

    def __init__(self, test_size: float = 0.2, random_state: Optional[int] = None):
        self.test_size = test_size
        self.random_state = random_state
    
    def split(self , data: pd.DataFrame, target_column: str) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        X = data.drop(columns=[target_column])
        y = data[target_column]
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=self.test_size, random_state=self.random_state)
        return X_train, X_test, y_train, y_test
    

class DataSplitter:
    def __init__(self , strategy: DataSplittingStrategy):
        self.strategy = strategy
    
    def split(self , data: pd.DataFrame, target_column: str) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        return self.strategy.split(data, target_column)
    
# Example usage:
if __name__ == "__main__":
    data = pd.DataFrame({
        'feature1': [1, 2, 3, 4, 5],
        'feature2': [5, 4, 3, 2, 1],
        'target': [0, 1, 0, 1, 0]
    })
    
    strategy = SimpleTrainTestSplittingStrategy(test_size=0.2, random_state=42)
    splitter = DataSplitter(strategy)
    
    X_train, X_test, y_train, y_test = splitter.split(data, target_column='target')
    
    print("X_train:\n", X_train)
    print("X_test:\n", X_test)
    print("y_train:\n", y_train)
    print("y_test:\n", y_test)