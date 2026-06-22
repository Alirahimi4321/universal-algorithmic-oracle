"""XGBoost prediction model."""
import logging
import numpy as np

logger = logging.getLogger(__name__)

HAS_XGB = False
try:
    import xgboost as xgb
    HAS_XGB = True
except ImportError:
    pass


class XGBoostPredictor:
    """XGBoost-based prediction and classification."""

    def __init__(self):
        self.available = HAS_XGB

    def train_predict(self, X_train: np.ndarray, y_train: np.ndarray,
                      X_test: np.ndarray = None, task: str = "classification") -> dict:
        if not self.available:
            return {"error": "xgboost not available"}
        try:
            if task == "classification":
                model = xgb.XGBClassifier(
                    n_estimators=100, max_depth=6, learning_rate=0.1,
                    use_label_encoder=False, eval_metric="mlogloss",
                )
            else:
                model = xgb.XGBRegressor(n_estimators=100, max_depth=6, learning_rate=0.1)

            model.fit(X_train, y_train)
            predictions = model.predict(X_test if X_test is not None else X_train)
            importance = dict(zip(
                range(X_train.shape[1]),
                model.feature_importances_.tolist(),
            ))

            return {
                "predictions": predictions.tolist(),
                "feature_importance": importance,
                "num_features": X_train.shape[1],
                "task": task,
            }
        except Exception as e:
            logger.warning("xgboost failed: %s", e)
            return {"error": str(e)}

    def analyze(self, data: dict) -> dict:
        X = np.array(data.get("X", [[1, 2], [3, 4]]))
        y = np.array(data.get("y", [0, 1]))
        X_test = np.array(data.get("X_test")) if data.get("X_test") else None
        task = data.get("task", "classification")
        return self.train_predict(X, y, X_test, task)
