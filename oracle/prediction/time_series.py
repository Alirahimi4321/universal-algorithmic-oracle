"""Time Series Predictor using sktime and darts for trend forecasting."""
from __future__ import annotations
import logging
import numpy as np
from typing import Any

logger = logging.getLogger(__name__)

try:
    from sktime.forecasting.naive import NaiveForecaster
    from sktime.forecasting.exp_smoothing import ExponentialSmoothing
    from sktime.forecasting.arima import AutoARIMA
    HAS_SKTIME = True
except Exception:
    HAS_SKTIME = False
    logger.info("sktime not available")

try:
    from darts import TimeSeries
    from darts.models import NaiveSeasonal, AutoARIMA as DartsAutoARIMA
    HAS_DARTS = True
except Exception:
    HAS_DARTS = False
    logger.info("darts not available")


class TimeSeriesPredictor:
    """Predict future trends using time series forecasting."""

    def __init__(self) -> None:
        self.sktime_available = HAS_SKTIME
        self.darts_available = HAS_DARTS

    def predict(self, data: list[float], horizon: int = 5, method: str = "auto") -> dict[str, Any]:
        if len(data) < 5:
            return {"forecast": [], "trend": "insufficient_data", "method": "none"}
        arr = np.array(data, dtype=float)
        if method == "auto" or method == "sktime":
            return self._predict_sktime(arr, horizon)
        elif method == "darts":
            return self._predict_darts(arr, horizon)
        return self._predict_sktime(arr, horizon)

    def _predict_sktime(self, arr: np.ndarray, horizon: int) -> dict[str, Any]:
        if not self.sktime_available:
            return self._predict_simple(arr, horizon)
        try:
            forecaster = AutoARIMA(start_p=1, max_p=3, start_q=1, max_q=3, suppress_warnings=True, stepwise=True)
            forecaster.fit(arr)
            pred = forecaster.predict(fh=list(range(1, horizon + 1)))
            forecast = pred.tolist() if hasattr(pred, "tolist") else list(pred)
            trend = self._compute_trend(arr, np.array(forecast))
            return {"forecast": [round(float(f), 4) for f in forecast], "trend": trend,
                    "method": "AutoARIMA", "data_points": len(arr)}
        except Exception:
            try:
                forecaster = NaiveForecaster(strategy="mean")
                forecaster.fit(arr)
                pred = forecaster.predict(fh=list(range(1, horizon + 1)))
                forecast = pred.tolist() if hasattr(pred, "tolist") else list(pred)
                trend = self._compute_trend(arr, np.array(forecast))
                return {"forecast": [round(float(f), 4) for f in forecast], "trend": trend,
                        "method": "NaiveForecaster", "data_points": len(arr)}
            except Exception as e:
                return self._predict_simple(arr, horizon)

    def _predict_darts(self, arr: np.ndarray, horizon: int) -> dict[str, Any]:
        if not self.darts_available:
            return self._predict_simple(arr, horizon)
        try:
            ts = TimeSeries.from_values(arr)
            model = NaiveSeasonal(K=1)
            model.fit(ts)
            pred = model.predict(horizon)
            forecast = pred.values().flatten().tolist()
            trend = self._compute_trend(arr, np.array(forecast))
            return {"forecast": [round(float(f), 4) for f in forecast], "trend": trend,
                    "method": "NaiveSeasonal", "data_points": len(arr)}
        except Exception as e:
            return self._predict_simple(arr, horizon)

    def _predict_simple(self, arr: np.ndarray, horizon: int) -> dict[str, Any]:
        mean = float(np.mean(arr[-5:]))
        std = float(np.std(arr[-5:])) if len(arr) > 1 else 0.0
        forecast = [round(mean + std * np.sin(i * 0.5), 4) for i in range(horizon)]
        trend = "stable"
        if len(arr) >= 3:
            recent_slope = (arr[-1] - arr[-3]) / 2
            trend = "up" if recent_slope > 0.01 else ("down" if recent_slope < -0.01 else "stable")
        return {"forecast": forecast, "trend": trend, "method": "simple_moving_average", "data_points": len(arr)}

    def _compute_trend(self, historical: np.ndarray, forecast: np.ndarray) -> str:
        if len(forecast) == 0:
            return "unknown"
        hist_slope = (historical[-1] - historical[max(0, len(historical)-3)]) / max(3, len(historical))
        fc_slope = (forecast[-1] - forecast[0]) / max(len(forecast), 1)
        combined = hist_slope * 0.6 + fc_slope * 0.4
        if combined > 0.02:
            return "up"
        elif combined < -0.02:
            return "down"
        return "stable"

    def analyze_fitness_history(self, fitness_values: list[float]) -> dict[str, Any]:
        if len(fitness_values) < 3:
            return {"trend": "insufficient", "prediction": None}
        result = self.predict(fitness_values, horizon=3)
        return {"trend": result["trend"], "forecast": result["forecast"],
                "current_fitness": fitness_values[-1], "method": result["method"]}
