"""Chaos and dynamical systems analysis using nolds, pynamicalsys, pyenfra."""
from __future__ import annotations

import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    np = None
    HAS_NUMPY = False
    logger.info("numpy not available")

try:
    import nolds
    HAS_NOLDS = True
except ImportError:
    HAS_NOLDS = False
    logger.info("nolds not available")

try:
    from pynamicalsys import LyapunovExponent
    HAS_PYNAMICALSYS = True
except ImportError:
    HAS_PYNAMICALSYS = False
    logger.info("pynamicalsys not available")

try:
    import pyenfra
    HAS_PYENFRA = True
except ImportError:
    HAS_PYENFRA = False
    logger.info("pyenfra not available")


class ChaosAnalyzer:
    """Analyzes chaotic dynamics in system outputs using multiple libraries."""

    def __init__(self) -> None:
        self.cache: dict[tuple[str, bytes, ...], float] = {}

    def lyapunov_exponent(self, timeseries: 'np.ndarray', embedding_dim: int = 3, tau: int = 1) -> float:
        """Compute largest Lyapunov exponent. Positive = chaotic."""
        if not HAS_NUMPY:
            logger.warning("numpy not available for Lyapunov computation")
            return 0.0
            
        try:
            ts = np.asarray(timeseries, dtype=np.float64)
            if len(ts) < 20:
                return 0.0

            cache_key = ("lyap", ts.tobytes(), embedding_dim, tau)
            if cache_key in self.cache:
                return self.cache[cache_key]

            result = 0.0

            if HAS_NOLDS:
                try:
                    result = float(nolds.lyap_r(ts, emb=embedding_dim, tau=tau))
                    self.cache[cache_key] = result
                    return result
                except Exception as e:
                    logger.warning(f"nolds lyap_r failed: {e}")

            if HAS_PYNAMICALSYS:
                try:
                    le = LyapunovExponent()
                    spectrum = le.compute(ts, embedding_dimension=embedding_dim, time_delay=tau)
                    result = float(spectrum[0]) if len(spectrum) > 0 else 0.0
                    self.cache[cache_key] = result
                    return result
                except Exception as e:
                    logger.warning(f"pynamicalsys lyapunov failed: {e}")

            return result
        except Exception as e:
            logger.warning("lyapunov computation failed: %s", e)
            return 0.0

    def hurst_exponent(self, timeseries: 'np.ndarray') -> float:
        """Compute Hurst exponent. H>0.5 = persistent, H<0.5 = anti-persistent."""
        if not HAS_NUMPY:
            logger.warning("numpy not available for Hurst computation")
            return 0.5
            
        try:
            ts = np.asarray(timeseries, dtype=np.float64)
            if len(ts) < 20:
                return 0.5

            cache_key = ("hurst", ts.tobytes())
            if cache_key in self.cache:
                return self.cache[cache_key]

            result = 0.5

            if HAS_NOLDS:
                try:
                    result = float(nolds.hurst_rs(ts))
                    self.cache[cache_key] = result
                    return result
                except Exception as e:
                    logger.warning(f"nolds hurst failed: {e}")

            return result
        except Exception as e:
            logger.warning("hurst computation failed: %s", e)
            return 0.5

    def sample_entropy(self, timeseries: 'np.ndarray', emb_dim: int = 2, tolerance: float = 0.2) -> float:
        """Compute sample entropy. Lower = more regular, higher = more complex."""
        if not HAS_NUMPY:
            logger.warning("numpy not available for sample entropy computation")
            return 0.0
            
        try:
            ts = np.asarray(timeseries, dtype=np.float64)
            if len(ts) < 30:
                return 0.0

            cache_key = ("sampen", ts.tobytes(), emb_dim, tolerance)
            if cache_key in self.cache:
                return self.cache[cache_key]

            result = 0.0

            if HAS_NOLDS:
                try:
                    result = float(nolds.sampen(ts, emb_dim=emb_dim, tolerance=tolerance))
                    self.cache[cache_key] = result
                    return result
                except Exception as e:
                    logger.warning(f"nolds sampen failed: {e}")

            return result
        except Exception as e:
            logger.warning("sample entropy computation failed: %s", e)
            return 0.0

    def correlation_dimension(self, timeseries: 'np.ndarray', emb_dim: int = 2, tau: int = 1) -> float:
        """Estimate correlation dimension. Measure of fractal complexity."""
        if not HAS_NUMPY:
            logger.warning("numpy not available for correlation dimension computation")
            return 0.0
            
        try:
            ts = np.asarray(timeseries, dtype=np.float64)
            if len(ts) < 50:
                return 0.0

            cache_key = ("corr_dim", ts.tobytes(), emb_dim, tau)
            if cache_key in self.cache:
                return self.cache[cache_key]

            result = 0.0

            if HAS_NOLDS:
                try:
                    result = float(nolds.corr_dim(ts, emb_dim))
                    self.cache[cache_key] = result
                    return result
                except Exception as e:
                    logger.warning(f"nolds corr_dim failed: {e}")

            return result
        except Exception as e:
            logger.warning("correlation dimension computation failed: %s", e)
            return 0.0

    def dfa_exponent(self, timeseries: 'np.ndarray') -> float:
        """Detrended Fluctuation Analysis exponent. Long-range correlations."""
        if not HAS_NUMPY:
            logger.warning("numpy not available for DFA computation")
            return 0.5
            
        try:
            ts = np.asarray(timeseries, dtype=np.float64)
            if len(ts) < 50:
                return 0.5

            cache_key = ("dfa", ts.tobytes())
            if cache_key in self.cache:
                return self.cache[cache_key]

            result = 0.5

            if HAS_PYENFRA:
                try:
                    result = float(pyenfra.functions.dfa(ts))
                    self.cache[cache_key] = result
                    return result
                except Exception as e:
                    logger.warning(f"pyenfra dfa failed: {e}")

            return result
        except Exception as e:
            logger.warning("DFA computation failed: %s", e)
            return 0.5

    def full_analysis(self, timeseries: 'np.ndarray') -> dict[str, Any]:
        """Run complete chaos analysis on a timeseries."""
        if not HAS_NUMPY:
            logger.warning("numpy not available for full chaos analysis")
            return {"error": "numpy not available"}
            
        try:
            ts = np.asarray(timeseries, dtype=np.float64)
            return {
                "lyapunov": self.lyapunov_exponent(ts),
                "hurst": self.hurst_exponent(ts),
                "sample_entropy": self.sample_entropy(ts),
                "correlation_dim": self.correlation_dimension(ts),
                "dfa": self.dfa_exponent(ts),
                "is_chaotic": self.lyapunov_exponent(ts) > 0,
                "is_persistent": self.hurst_exponent(ts) > 0.5,
            }
        except Exception as e:
            logger.warning("full chaos analysis failed: %s", e)
            return {"error": str(e)}

    def analyze_system_dynamics(self, system_outputs: dict[str, list[float]]) -> dict[str, dict[str, Any]]:
        """Analyze chaotic dynamics across multiple system outputs."""
        if not HAS_NUMPY:
            logger.warning("numpy not available for system dynamics analysis")
            return {"error": "numpy not available"}
            
        try:
            results = {}
            for name, output in system_outputs.items():
                ts = np.array(output, dtype=np.float64)
                if len(ts) >= 20:
                    results[name] = self.full_analysis(ts)
                else:
                    results[name] = {"error": "insufficient data"}
            return results
        except Exception as e:
            logger.warning("system dynamics analysis failed: %s", e)
            return {"error": str(e)}
