"""Statistical analysis using statsmodels."""
import logging
import numpy as np

logger = logging.getLogger(__name__)

HAS_STATSMODELS = False
try:
    import statsmodels.api as sm
    from statsmodels.tsa.arima.model import ARIMA
    from statsmodels.stats.outliers_influence import variance_inflation_factor
    HAS_STATSMODELS = True
except ImportError:
    pass


class StatsAnalyzer:
    """Statistical modeling and time series analysis."""

    def __init__(self):
        self.available = HAS_STATSMODELS

    def linear_regression(self, X: np.ndarray, y: np.ndarray) -> dict:
        if not self.available:
            return {"error": "statsmodels not available"}
        try:
            X_const = sm.add_constant(X)
            model = sm.OLS(y, X_const).fit()
            return {
                "r_squared": float(model.rsquared),
                "adj_r_squared": float(model.rsquared_adj),
                "f_statistic": float(model.fvalue),
                "p_values": model.pvalues.tolist(),
                "coefficients": model.params.tolist(),
                "aic": float(model.aic),
                "bic": float(model.bic),
            }
        except Exception as e:
            return {"error": str(e)}

    def arima_forecast(self, series: list[float], order: tuple = (1, 1, 1), steps: int = 5) -> dict:
        if not self.available:
            return {"error": "statsmodels not available"}
        try:
            model = ARIMA(series, order=order)
            fitted = model.fit()
            forecast = fitted.forecast(steps=steps)
            return {
                "forecast": forecast.tolist(),
                "aic": float(fitted.aic),
                "bic": float(fitted.bic),
                "order": list(order),
            }
        except Exception as e:
            return {"error": str(e)}

    def analyze(self, data: dict) -> dict:
        method = data.get("method", "regression")
        if method == "regression":
            X = np.array(data.get("X", [[1], [2], [3]]))
            y = np.array(data.get("y", [1, 2, 3]))
            return self.linear_regression(X, y)
        elif method == "arima":
            series = data.get("series", [1, 2, 3, 4, 5])
            order = tuple(data.get("order", [1, 1, 1]))
            steps = data.get("steps", 5)
            return self.arima_forecast(series, order, steps)
        return {"error": "unknown method"}
