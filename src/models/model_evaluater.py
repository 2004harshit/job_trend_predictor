from abc import ABC, abstractmethod
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score, accuracy_score, classification_report
from typing import Any, Dict

class ModelEvaluaterStrategy(ABC):
    @abstractmethod
    def evaluate(self, y_true: pd.Series, y_pred: pd.Series) -> Dict[str, Any]:
        pass

class RegressionEvaluaterStrategy(ModelEvaluaterStrategy):
    def evaluate(self, y_true: pd.Series, y_pred: pd.Series) -> Dict[str, Any]:
        mae = mean_absolute_error(y_true, y_pred)
        mse = mean_squared_error(y_true, y_pred)
        r2 = r2_score(y_true, y_pred)
        return {
            "Mean Absolute Error": mae,
            "Mean Squared Error": mse,
            "R^2 Score": r2
        }
    
class ClassificationEvaluaterStrategy(ModelEvaluaterStrategy):
    def evaluate(self, y_true: pd.Series, y_pred: pd.Series) -> Dict[str, Any]:
        accuracy = accuracy_score(y_true, y_pred)
        report = classification_report(y_true, y_pred, output_dict=True)
        return {
            "Accuracy": accuracy,
            "Classification Report": report
        }
    
class ModelEvaluater:
    def __init__(self, strategy: ModelEvaluaterStrategy):
        self.strategy = strategy

    def set_strategy(self, strategy: ModelEvaluaterStrategy):
        self.strategy = strategy

    def evaluate_model(self, y_true: pd.Series, y_pred: pd.Series) -> Dict[str, Any]:
        return self.strategy.evaluate(y_true, y_pred)   
    

if __name__ == "__main__":
    # Example usage
    y_true_reg = pd.Series([3.0, -0.5, 2.0, 7.0])
    y_pred_reg = pd.Series([2.5, 0.0, 2.0, 8.0])

    reg_evaluater = ModelEvaluater(RegressionEvaluaterStrategy())
    reg_metrics = reg_evaluater.evaluate_model(y_true_reg, y_pred_reg)
    print("Regression Metrics:", reg_metrics)

    y_true_clf = pd.Series([0, 1, 1, 0])
    y_pred_clf = pd.Series([0, 1, 0, 0])

    clf_evaluater = ModelEvaluater(ClassificationEvaluaterStrategy())
    clf_metrics = clf_evaluater.evaluate_model(y_true_clf, y_pred_clf)
    print("Classification Metrics:", clf_metrics)