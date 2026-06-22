"""Antropy wrapper: Entropy and complexity measures for time-series."""
import time
import logging
import numpy as np

logger = logging.getLogger(__name__)

HAS_ANTROPY = False
try:
    from antropy import (
        perm_entropy, spectral_entropy, svd_entropy,
        app_entropy, sample_entropy, lziv_complexity,
        num_zerocross, hjorth_params,
        petrosian_fd, katz_fd, higuchi_fd, detrended_fluctuation,
    )
    HAS_ANTROPY = True
except ImportError:
    pass


class AntropyAnalyzer:
    """Time-series entropy and complexity analysis using antropy."""

    def __init__(self):
        self.available = HAS_ANTROPY

    def analyze(self, data: dict) -> dict:
        seed = data.get("seed", int(time.time()))
        series = data.get("series")

        if not self.available:
            return {"error": "antropy not available"}

        try:
            if series is None:
                np.random.seed(seed % (2 ** 31))
                series = np.random.randn(256).tolist()
            x = np.array(series, dtype=float)
            sf = data.get("sf", 100)

            measures = {}
            try: measures["perm_entropy"] = float(perm_entropy(x, normalize=True))
            except Exception: measures["perm_entropy"] = 0.0
            try: measures["spectral_entropy"] = float(spectral_entropy(x, sf=sf, normalize=True))
            except Exception: measures["spectral_entropy"] = 0.0
            try: measures["svd_entropy"] = float(svd_entropy(x, normalize=True))
            except Exception: measures["svd_entropy"] = 0.0
            try: measures["app_entropy"] = float(app_entropy(x))
            except Exception: measures["app_entropy"] = 0.0
            try: measures["sample_entropy"] = float(sample_entropy(x))
            except Exception: measures["sample_entropy"] = 0.0
            try: measures["lziv_complexity"] = float(lziv_complexity(x > np.mean(x), normalize=True))
            except Exception: measures["lziv_complexity"] = 0.0
            try: measures["petrosian_fd"] = float(petrosian_fd(x))
            except Exception: measures["petrosian_fd"] = 0.0
            try: measures["katz_fd"] = float(katz_fd(x))
            except Exception: measures["katz_fd"] = 0.0
            try: measures["higuchi_fd"] = float(higuchi_fd(x))
            except Exception: measures["higuchi_fd"] = 0.0
            try: measures["dfa"] = float(detrended_fluctuation(x))
            except Exception: measures["dfa"] = 0.0

            return {
                "length": len(x),
                "mean": float(np.mean(x)),
                "std": float(np.std(x)),
                "entropy_measures": measures,
                "numeric_projection": [
                    measures.get("perm_entropy", 0) * 100,
                    measures.get("spectral_entropy", 0) * 100,
                    measures.get("svd_entropy", 0) * 100,
                    measures.get("app_entropy", 0) * 100,
                    measures.get("sample_entropy", 0) * 100,
                    measures.get("lziv_complexity", 0) * 100,
                    measures.get("petrosian_fd", 0) * 100,
                    measures.get("katz_fd", 0) * 100,
                    measures.get("higuchi_fd", 0) * 100,
                    measures.get("dfa", 0) * 100,
                ],
            }
        except Exception as e:
            logger.warning("antropy analyze failed: %s", e)
            return {"error": str(e)}
