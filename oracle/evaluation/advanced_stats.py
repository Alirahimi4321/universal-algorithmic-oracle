"""Advanced statistical analysis for oracle evaluation."""
import logging
import math
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    np = None
    HAS_NUMPY = False
    logger.info("numpy not available for advanced stats")

try:
    from scipy import stats as sp_stats
    from scipy.stats import (
        entropy as sp_entropy,
        pearsonr,
        spearmanr,
        shapiro,
        kstest,
        norm,
        expon,
        uniform,
    )
    HAS_SCIPY = True
except ImportError:
    sp_stats = None
    HAS_SCIPY = False
    logger.info("scipy not available, using fallback implementations")


class AdvancedStats:
    """Advanced statistical analysis methods for fitness and entropy data."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        config = config or {}
        self.bin_count = config.get("bin_count", 20)
        self.distribution_candidates = config.get("distributions", ["norm", "expon", "uniform"])

    def shannon_entropy(self, data: list, base: float = 2.0) -> float:
        """Compute Shannon entropy of a dataset.

        Parameters
        ----------
        data : list
            Input data (numeric values).
        base : float
            Logarithm base (2 for bits, e for nats).

        Returns
        -------
        float
            Shannon entropy value.
        """
        if data is None or (hasattr(data, '__len__') and len(data) < 2) or (not hasattr(data, '__len__') and not data):
            return 0.0

        if HAS_SCIPY and HAS_NUMPY:
            try:
                arr = np.array(data, dtype=np.float64)
                counts, _ = np.histogram(arr, bins=min(self.bin_count, len(arr)), density=False)
                counts = counts[counts > 0]
                probs = counts / counts.sum()
                return float(sp_entropy(probs, base=base))
            except Exception as e:
                logger.warning("scipy entropy failed, using fallback: %s", e)

        return self._fallback_entropy(data, base)

    @staticmethod
    def _fallback_entropy(data: list, base: float = 2.0) -> float:
        """Fallback entropy calculation without scipy."""
        import math

        counts = {}
        for val in data:
            key = round(float(val), 6)
            counts[key] = counts.get(key, 0) + 1

        total = len(data)
        entropy = 0.0
        for count in counts.values():
            p = count / total
            if p > 0:
                entropy -= p * math.log(p) / math.log(base)
        return entropy

    def kl_divergence(self, p: list, q: list, base: float = 2.0) -> float:
        """Compute KL divergence D_KL(P || Q).

        Parameters
        ----------
        p : list
            Distribution P (discrete probability or sample data).
        q : list
            Distribution Q.
        base : float
            Logarithm base.

        Returns
        -------
        float
            KL divergence value.
        """
        if not p or not q:
            return 0.0

        if HAS_SCIPY and HAS_NUMPY:
            try:
                p_arr = np.array(p, dtype=np.float64)
                q_arr = np.array(q, dtype=np.float64)

                if p_arr.ndim == 1 and q_arr.ndim == 1 and len(p_arr) == len(q_arr):
                    p_hist, _ = np.histogram(p_arr, bins=self.bin_count, density=True)
                    q_hist, _ = np.histogram(q_arr, bins=self.bin_count, density=True)
                else:
                    p_hist, _ = np.histogram(p_arr, bins=min(self.bin_count, max(len(p_arr), 2)), density=True)
                    q_hist, _ = np.histogram(q_arr, bins=min(self.bin_count, max(len(q_arr), 2)), density=True)
                    max_bins = max(len(p_hist), len(q_hist))
                    p_hist = np.pad(p_hist, (0, max_bins - len(p_hist)))
                    q_hist = np.pad(q_hist, (0, max_bins - len(q_hist)))

                eps = 1e-10
                p_hist = p_hist + eps
                q_hist = q_hist + eps
                p_hist = p_hist / p_hist.sum()
                q_hist = q_hist / q_hist.sum()

                return float(np.sum(p_hist * np.log(p_hist / q_hist) / np.log(base)))
            except Exception as e:
                logger.warning("scipy KL divergence failed: %s", e)

        return self._fallback_kl_divergence(p, q, base)

    @staticmethod
    def _fallback_kl_divergence(p: list, q: list, base: float = 2.0) -> float:
        """Fallback KL divergence."""
        import math

        if not p or not q:
            return 0.0

        eps = 1e-10
        all_vals = p + q
        max_val = max(all_vals) + eps
        min_val = min(all_vals)
        n_bins = 20
        bin_width = (max_val - min_val) / n_bins if max_val > min_val else 1.0

        p_hist = [0.0] * n_bins
        q_hist = [0.0] * n_bins
        for val in p:
            idx = min(int((val - min_val) / bin_width), n_bins - 1)
            p_hist[idx] += 1
        for val in q:
            idx = min(int((val - min_val) / bin_width), n_bins - 1)
            q_hist[idx] += 1

        p_total = sum(p_hist) or 1.0
        q_total = sum(q_hist) or 1.0
        p_hist = [(c / p_total) + eps for c in p_hist]
        q_hist = [(c / q_total) + eps for c in q_hist]

        p_sum = sum(p_hist)
        q_sum = sum(q_hist)
        p_hist = [v / p_sum for v in p_hist]
        q_hist = [v / q_sum for v in q_hist]

        kl = 0.0
        for pi, qi in zip(p_hist, q_hist):
            if pi > 0 and qi > 0:
                kl += pi * math.log(pi / qi) / math.log(base)
        return kl

    def correlation_analysis(self, data1: list, data2: list) -> Dict[str, float]:
        """Compute Pearson and Spearman correlations.

        Parameters
        ----------
        data1 : list
            First dataset.
        data2 : list
            Second dataset.

        Returns
        -------
        dict
            Dictionary with 'pearson' and 'spearman' correlation coefficients and p-values.
        """
        if not data1 or not data2 or len(data1) != len(data2) or len(data1) < 3:
            return {
                "pearson_r": 0.0, "pearson_p": 1.0,
                "spearman_r": 0.0, "spearman_p": 1.0,
            }

        if HAS_SCIPY and HAS_NUMPY:
            try:
                arr1 = np.array(data1, dtype=np.float64)
                arr2 = np.array(data2, dtype=np.float64)
                pr, pp = pearsonr(arr1, arr2)
                sr, sp = spearmanr(arr1, arr2)
                return {
                    "pearson_r": float(pr),
                    "pearson_p": float(pp),
                    "spearman_r": float(sr),
                    "spearman_p": float(sp),
                }
            except Exception as e:
                logger.warning("scipy correlation failed: %s", e)

        return self._fallback_correlation(data1, data2)

    @staticmethod
    def _fallback_correlation(data1: list, data2: list) -> Dict[str, float]:
        """Fallback correlation computation."""
        import math

        n = len(data1)
        if n < 3:
            return {"pearson_r": 0.0, "pearson_p": 1.0, "spearman_r": 0.0, "spearman_p": 1.0}

        mean1 = sum(data1) / n
        mean2 = sum(data2) / n

        var1 = sum((x - mean1) ** 2 for x in data1)
        var2 = sum((x - mean2) ** 2 for x in data2)
        cov = sum((x - mean1) * (y - mean2) for x, y in zip(data1, data2))

        denom = math.sqrt(var1 * var2)
        pearson_r = cov / denom if denom > 0 else 0.0

        def _rank(lst):
            sorted_idx = sorted(range(len(lst)), key=lambda i: lst[i])
            ranks = [0.0] * len(lst)
            for rank, idx in enumerate(sorted_idx, 1):
                ranks[idx] = rank
            return ranks

        r1 = _rank(data1)
        r2 = _rank(data2)
        mean_r1 = sum(r1) / n
        mean_r2 = sum(r2) / n
        var_r1 = sum((x - mean_r1) ** 2 for x in r1)
        var_r2 = sum((x - mean_r2) ** 2 for x in r2)
        cov_r = sum((x - mean_r1) * (y - mean_r2) for x, y in zip(r1, r2))
        denom_r = math.sqrt(var_r1 * var_r2)
        spearman_r = cov_r / denom_r if denom_r > 0 else 0.0

        return {
            "pearson_r": pearson_r,
            "pearson_p": 0.05 if abs(pearson_r) > 0.5 else 0.5,
            "spearman_r": spearman_r,
            "spearman_p": 0.05 if abs(spearman_r) > 0.5 else 0.5,
        }

    def distribution_fit(self, data: list) -> Dict[str, Any]:
        """Fit candidate distributions to data.

        Parameters
        ----------
        data : list
            Input data.

        Returns
        -------
        dict
            Results for each candidate distribution with parameters and goodness-of-fit.
        """
        if not data or len(data) < 3:
            return {"error": "insufficient data", "fits": {}}

        if HAS_SCIPY and HAS_NUMPY:
            try:
                return self._scipy_distribution_fit(data)
            except Exception as e:
                logger.warning("scipy distribution fit failed: %s", e)

        return self._fallback_distribution_fit(data)

    def _scipy_distribution_fit(self, data: list) -> Dict[str, Any]:
        """Fit distributions using scipy.stats."""
        arr = np.array(data, dtype=np.float64)
        results = {}

        dist_map = {
            "norm": norm,
            "expon": expon,
            "uniform": uniform,
        }

        for dist_name in self.distribution_candidates:
            dist = dist_map.get(dist_name)
            if dist is None:
                continue
            try:
                params = dist.fit(arr)
                ks_stat, ks_p = kstest(arr, dist_name, args=params)
                results[dist_name] = {
                    "params": [float(p) for p in params],
                    "ks_statistic": float(ks_stat),
                    "ks_p_value": float(ks_p),
                    "aic": self._compute_aic(arr, dist, params),
                }
            except Exception as e:
                logger.warning("Fit failed for %s: %s", dist_name, e)
                results[dist_name] = {"error": str(e)}

        best = min(
            ((k, v) for k, v in results.items() if "ks_statistic" in v),
            key=lambda x: x[1]["ks_statistic"],
            default=None,
        )
        best_name = best[0] if best else None

        return {
            "best_fit": best_name,
            "fits": results,
        }

    def _compute_aic(self, data: np.ndarray, dist, params: tuple) -> float:
        """Compute Akaike Information Criterion for a fitted distribution."""
        try:
            log_likelihood = np.sum(dist.logpdf(data, *params))
            k = len(params)
            n = len(data)
            aic = 2 * k - 2 * log_likelihood
            if n > 40:
                aic += (2 * k * (k + 1)) / (n - k - 1)
            return float(aic)
        except Exception:
            return float("inf")

    def _fallback_distribution_fit(self, data: list) -> Dict[str, Any]:
        """Fallback distribution fitting using basic statistics."""
        import math

        n = len(data)
        mean = sum(data) / n
        variance = sum((x - mean) ** 2 for x in data) / n
        std = math.sqrt(variance) if variance > 0 else 1.0
        skewness = sum(((x - mean) / std) ** 3 for x in data) / n if std > 0 else 0.0

        sorted_data = sorted(data)
        min_val = sorted_data[0]
        max_val = sorted_data[-1]

        norm_params = {"mean": mean, "std": std}
        expon_params = {"loc": min_val, "scale": mean - min_val if mean > min_val else 1.0}
        uniform_params = {"loc": min_val, "scale": max_val - min_val if max_val > min_val else 1.0}

        best = "norm"
        if abs(skewness) > 1.0:
            best = "expon"

        return {
            "best_fit": best,
            "fits": {
                "norm": {"params": [norm_params["mean"], norm_params["std"]], "skewness": skewness},
                "expon": {"params": [expon_params["loc"], expon_params["scale"]]},
                "uniform": {"params": [uniform_params["loc"], uniform_params["scale"]]},
            },
            "basic_stats": {
                "mean": mean,
                "variance": variance,
                "std": std,
                "skewness": skewness,
                "min": min_val,
                "max": max_val,
            },
        }

    def get_stats(self) -> Dict[str, Any]:
        """Return analysis capability summary."""
        return {
            "scipy_available": HAS_SCIPY,
            "numpy_available": HAS_NUMPY,
            "bin_count": self.bin_count,
            "distributions": self.distribution_candidates,
        }
