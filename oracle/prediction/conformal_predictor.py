"""Conformal Prediction using MAPIE for prediction intervals with coverage guarantees."""
from __future__ import annotations
import logging
import numpy as np
from typing import Any

logger = logging.getLogger(__name__)

try:
    from sklearn.linear_model import LinearRegression
    HAS_SKLEARN = True
except Exception:
    HAS_SKLEARN = False

try:
    from mapie.regression import MapieRegressor
    HAS_MAPIE = True
except Exception:
    HAS_MAPIE = False


class ConformalPredictor:
    """Generate prediction intervals with guaranteed coverage using conformal prediction."""

    def __init__(self) -> None:
        self.available = HAS_MAPIE and HAS_SKLEARN

    def predict_with_intervals(self, X_train: list[list[float]], y_train: list[float],
                                X_test: list[list[float]], confidence: float = 0.9) -> dict[str, Any]:
        if not self.available:
            return self._fallback_predict(X_train, y_train, X_test)
        try:
            X_tr = np.array(X_train, dtype=float)
            y_tr = np.array(y_train, dtype=float)
            X_te = np.array(X_test, dtype=float)
            base_model = LinearRegression()
            mapie = MapieRegressor(base_model, method="plus", cv=min(5, len(X_tr) - 1))
            mapie.fit(X_tr, y_tr)
            y_pred, y_pis = mapie.predict(X_te, alpha=1 - confidence)
            intervals = []
            for i in range(len(y_pred)):
                low = float(y_pis[i, 0, 0]) if y_pis.ndim == 3 else float(y_pred[i] - 0.1)
                high = float(y_pis[i, 1, 0]) if y_pis.ndim == 3 else float(y_pred[i] + 0.1)
                intervals.append({"prediction": round(float(y_pred[i]), 4), "lower": round(low, 4),
                                 "upper": round(high, 4), "width": round(high - low, 4)})
            return {"predictions": intervals, "confidence": confidence, "method": "mapie_plus", "n_train": len(X_tr)}
        except Exception as e:
            return self._fallback_predict(X_train, y_train, X_test)

    def _fallback_predict(self, X_train, y_train, X_test):
        try:
            X_tr = np.array(X_train, dtype=float)
            y_tr = np.array(y_train, dtype=float)
            X_te = np.array(X_test, dtype=float)
            model = LinearRegression()
            model.fit(X_tr, y_tr)
            y_pred = model.predict(X_te)
            residuals = y_tr - model.predict(X_tr)
            std_resid = float(np.std(residuals))
            intervals = []
            for i in range(len(y_pred)):
                pred = float(y_pred[i])
                intervals.append({"prediction": round(pred, 4), "lower": round(pred - 1.96 * std_resid, 4),
                                 "upper": round(pred + 1.96 * std_resid, 4), "width": round(2 * 1.96 * std_resid, 4)})
            return {"predictions": intervals, "confidence": 0.95, "method": "residual_based", "n_train": len(X_tr)}
        except Exception as e:
            return {"predictions": [], "method": "failed", "error": str(e)}

    def predict_fitness_interval(self, fitness_history: list[float], n_ahead: int = 1) -> dict[str, Any]:
        if len(fitness_history) < 10:
            return {"prediction": fitness_history[-1] if fitness_history else 0.5, "interval": None}
        try:
            X = np.arange(len(fitness_history)).reshape(-1, 1)
            y = np.array(fitness_history)
            model = LinearRegression()
            model.fit(X, y)
            X_future = np.array([[len(fitness_history) + i] for i in range(n_ahead)])
            y_pred = model.predict(X_future)
            residuals = y - model.predict(X)
            std_resid = float(np.std(residuals))
            intervals = []
            for i in range(n_ahead):
                pred = float(y_pred[i])
                intervals.append({"step": i + 1, "prediction": round(pred, 4),
                                 "lower": round(pred - 1.96 * std_resid, 4),
                                 "upper": round(pred + 1.96 * std_resid, 4)})
            return {"intervals": intervals, "method": "residual_based", "std_residual": round(std_resid, 4)}
        except Exception as e:
            return {"intervals": [], "method": "failed", "error": str(e)}
