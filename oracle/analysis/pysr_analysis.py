"""Symbolic Regression analysis using PySR."""
import logging
import numpy as np

logger = logging.getLogger(__name__)

HAS_PYSR = False
try:
    from pysr import PySRRegressor
    HAS_PYSR = True
except ImportError:
    pass


class SymbolicRegressionAnalyzer:
    """Discover mathematical formulas from data using PySR."""

    def __init__(self):
        self.available = HAS_PYSR

    def discover_formula(self, X: np.ndarray, y: np.ndarray, n_iterations: int = 50) -> dict:
        if not self.available:
            return {"error": "pysr not available"}
        try:
            model = PySRRegressor(
                niterations=n_iterations,
                binary_operators=["+", "-", "*", "/"],
                unary_operators=["sin", "cos", "exp", "log", "sqrt"],
                maxsize=20,
            )
            model.fit(X, y)
            equations = model.equations_
            best = equations.iloc[-1] if len(equations) > 0 else None
            return {
                "best_equation": str(best["equation"]) if best is not None else "",
                "best_loss": float(best["loss"]) if best is not None else float("inf"),
                "num_equations": len(equations),
                "all_equations": equations.to_dict("records") if len(equations) > 0 else [],
            }
        except Exception as e:
            logger.warning("pysr discover failed: %s", e)
            return {"error": str(e)}

    def analyze(self, data: dict) -> dict:
        X = np.array(data.get("X", [[1, 2], [3, 4], [5, 6]]))
        y = np.array(data.get("y", [1, 2, 3]))
        return self.discover_formula(X, y, data.get("n_iterations", 50))
