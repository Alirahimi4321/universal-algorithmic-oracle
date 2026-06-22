"""Nonlinear Dynamics and Chaos analysis using nolds."""
import logging
import numpy as np

logger = logging.getLogger(__name__)

HAS_NOLDS = False
try:
    import nolds
    HAS_NOLDS = True
except ImportError:
    pass


class NonlinearDynamicsAnalyzer:
    """Analyze nonlinear dynamics, chaos, and fractal dimensions."""

    def __init__(self):
        self.available = HAS_NOLDS

    def analyze(self, data: list[float], measures: list[str] = None) -> dict:
        if not self.available:
            return {"error": "nolds not available"}
        if not data or len(data) < 10:
            return {"error": "insufficient data"}
        try:
            arr = np.array(data, dtype=float)
            measures = measures or ["hurst", "dfa", "corr_dim", "lyap_e", "sampen"]
            results = {}
            if "hurst" in measures:
                try:
                    results["hurst_rs"] = float(nolds.hurst_rs(arr))
                except Exception:
                    results["hurst_rs"] = 0.0
            if "dfa" in measures:
                try:
                    results["dfa"] = float(nolds.dfa(arr))
                except Exception:
                    results["dfa"] = 0.0
            if "corr_dim" in measures:
                try:
                    results["corr_dim"] = float(nolds.corr_dim(arr, 1))
                except Exception:
                    results["corr_dim"] = 0.0
            if "lyap_e" in measures:
                try:
                    results["lyap_e"] = float(nolds.lyap_e(arr)[0]) if len(nolds.lyap_e(arr)) > 0 else 0.0
                except Exception:
                    results["lyap_e"] = 0.0
            if "sampen" in measures:
                try:
                    results["sampen"] = float(nolds.sampen(arr))
                except Exception:
                    results["sampen"] = 0.0
            results["is_chaotic"] = results.get("lyap_e", 0) > 0
            results["fractal_dimension"] = 1 + results.get("corr_dim", 0)
            results["data_length"] = len(arr)
            return results
        except Exception as e:
            return {"error": str(e)}
