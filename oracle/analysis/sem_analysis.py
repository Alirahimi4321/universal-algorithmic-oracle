"""SEM analysis using semopy."""
import logging
import numpy as np

logger = logging.getLogger(__name__)

HAS_SEMOPY = False
try:
    import semopy
    HAS_SEMOPY = True
except ImportError:
    pass


class SEMAnalyzer:
    """Structural Equation Modeling analysis."""

    def __init__(self):
        self.available = HAS_SEMOPY

    def fit_model(self, model_spec: str, data: dict) -> dict:
        if not self.available:
            return {"error": "semopy not available"}
        try:
            import pandas as pd
            df = pd.DataFrame(data.get("data", []))
            model = semopy.Model(model_spec)
            result = model.fit(df)

            estimates = model.inspect()
            stats = semopy.calc_stats(model)

            return {
                "estimates": estimates.to_dict("records") if hasattr(estimates, "to_dict") else str(estimates),
                "stats": {
                    "Chi-square": float(stats["Chi-square"].iloc[0]) if hasattr(stats, "iloc") else None,
                    "CFI": float(stats["CFI"].iloc[0]) if hasattr(stats, "iloc") and "CFI" in stats.columns else None,
                    "RMSEA": float(stats["RMSEA"].iloc[0]) if hasattr(stats, "iloc") and "RMSEA" in stats.columns else None,
                },
                "model_spec": model_spec,
            }
        except Exception as e:
            logger.warning("semopy failed: %s", e)
            return {"error": str(e)}

    def analyze(self, data: dict) -> dict:
        model_spec = data.get("model_spec", "y ~ x")
        return self.fit_model(model_spec, data)
