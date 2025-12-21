import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from abc import ABC, abstractmethod

class ModelBuilderStrategy(ABC):
    @abstractmethod
    def build_and_train_model(self, X_train: pd.DataFrame, y_train: pd.Series)->Pipeline:
        pass

class LinearRegressionStrategy(ModelBuilderStrategy):

    def __init__(self):
        self.model = None

    def build_and_train_model(self, X_train: pd.DataFrame, y_train: pd.Series)->Pipeline:
        """Build and train the linear regression model"""
        
        self.model = Pipeline(steps=[
            ('regressor', LinearRegression())
        ])
        self.model.fit(X_train, y_train)
        return self.model
    

class ClassificationStrategy(ModelBuilderStrategy):
    def __init__(self):
        self.model = None

    def build_and_train_model(self, X_train: pd.DataFrame, y_train: pd.Series)->Pipeline:
        """Build and train the classification model"""
        
        self.model = Pipeline(steps=[
            ('classifier', self.classifier)
        ])
        self.model.fit(X_train, y_train)
        return self.model
    


class ModelBuilder:
    def __init__(self, strategy: ModelBuilderStrategy):
        self.strategy = strategy

    def set_strategy(self, strategy: ModelBuilderStrategy):
        self.strategy = strategy

    def build_model(self, X_train: pd.DataFrame, y_train: pd.Series)->Pipeline:
        return self.strategy.build_and_train_model(X_train, y_train)
    

if __name__ == "__main__":
    # Example usage
    data = pd.DataFrame({
        'feature1': np.random.rand(100),
        'feature2': np.random.rand(100),
        'salary': np.random.rand(100) * 100000
    })
    
    X = data[['feature1', 'feature2']]
    y = data['salary']
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # Build and train regression model
    regression_strategy = LinearRegressionStrategy()
    model_builder = ModelBuilder(regression_strategy)
    regression_model = model_builder.build_model(X_train, y_train)
    
    print("Regression model trained successfully.")