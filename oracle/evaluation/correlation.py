"""System correlation analysis using infomeasure and divergence libraries."""
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
    import infomeasure as im
    HAS_INFOMEASURE = True
except ImportError:
    HAS_INFOMEASURE = False
    logger.info("infomeasure not available, using internal correlation")

try:
    import divergence as div
    HAS_DIVERGENCE = True
except ImportError:
    HAS_DIVERGENCE = False
    logger.info("divergence not available, using internal correlation")


class SystemCorrelationAnalyzer:
    """Analyzes correlations between symbolic system outputs using information theory."""

    def __init__(self) -> None:
        self.correlation_cache: dict[tuple[bytes, bytes], dict[str, float]] = {}

    def compute_mutual_information(self, x: 'np.ndarray', y: 'np.ndarray') -> float:
        """Compute mutual information between two system outputs."""
        if not HAS_NUMPY:
            logger.warning("numpy not available for MI computation")
            return 0.0
            
        if HAS_INFOMEASURE:
            try:
                return float(im.mutual_information(x, y, approach='ksg'))
            except Exception as e:
                logger.warning(f"infomeasure MI failed: {e}")

        if HAS_DIVERGENCE:
            try:
                return float(div.mutual_information(x, y))
            except Exception as e:
                logger.warning(f"divergence MI failed: {e}")

        return self._fallback_correlation(x, y)

    def compute_transfer_entropy(self, source: 'np.ndarray', target: 'np.ndarray') -> float:
        """Compute transfer entropy from source to target (directed information flow)."""
        if not HAS_NUMPY:
            logger.warning("numpy not available for TE computation")
            return 0.0
            
        if HAS_INFOMEASURE:
            try:
                return float(im.transfer_entropy(source, target, approach='ksg'))
            except Exception as e:
                logger.warning(f"infomeasure TE failed: {e}")

        if HAS_DIVERGENCE:
            try:
                return float(div.transfer_entropy(source, target))
            except Exception as e:
                logger.warning(f"divergence TE failed: {e}")

        return self._fallback_correlation(source, target)

    def compute_kl_divergence(self, p: 'np.ndarray', q: 'np.ndarray') -> float:
        """Compute KL divergence between two distributions."""
        if not HAS_NUMPY:
            logger.warning("numpy not available for KL computation")
            return 0.0
            
        if HAS_DIVERGENCE:
            try:
                return float(div.kl_divergence(p, q))
            except Exception as e:
                logger.warning(f"divergence KL failed: {e}")

        return self._fallback_kl(p, q)

    def compute_jensen_shannon(self, p: 'np.ndarray', q: 'np.ndarray') -> float:
        """Compute Jensen-Shannon divergence."""
        if not HAS_NUMPY:
            logger.warning("numpy not available for JSD computation")
            return 0.0
            
        if HAS_DIVERGENCE:
            try:
                return float(div.jensen_shannon_divergence(p, q))
            except Exception as e:
                logger.warning(f"divergence JSD failed: {e}")

        return self._fallback_jsd(p, q)

    def analyze_system_pair(self, outputs_a: list[float], outputs_b: list[float]) -> dict:
        """Comprehensive analysis of correlation between two systems."""
        if not HAS_NUMPY:
            logger.warning("numpy not available for system pair analysis")
            return {"mi": 0.0, "te_a_to_b": 0.0, "te_b_to_a": 0.0, "jsd": 0.0}
            
        a = np.array(outputs_a, dtype=np.float64)
        b = np.array(outputs_b, dtype=np.float64)

        if len(a) < 2 or len(b) < 2:
            return {"mi": 0.0, "te_a_to_b": 0.0, "te_b_to_a": 0.0, "jsd": 0.0}

        min_len = min(len(a), len(b))
        a, b = a[:min_len], b[:min_len]

        cache_key = (a.tobytes(), b.tobytes())
        if cache_key in self.correlation_cache:
            return self.correlation_cache[cache_key]

        result = {
            "mi": self.compute_mutual_information(a, b),
            "te_a_to_b": self.compute_transfer_entropy(a, b),
            "te_b_to_a": self.compute_transfer_entropy(b, a),
            "jsd": self.compute_jensen_shannon(a, b),
        }

        self.correlation_cache[cache_key] = result
        return result

    def find_independent_systems(self, system_outputs: dict[str, list[float]], threshold: float = 0.1) -> list[str]:
        """Find systems that are relatively independent (low MI with others)."""
        system_names = list(system_outputs.keys())
        avg_mi = {}

        for name in system_names:
            total_mi = 0
            count = 0
            for other_name in system_names:
                if name != other_name:
                    result = self.analyze_system_pair(
                        system_outputs[name], system_outputs[other_name]
                    )
                    total_mi += abs(result["mi"])
                    count += 1
            avg_mi[name] = total_mi / max(count, 1)

        independent = [name for name, mi in avg_mi.items() if mi < threshold]
        return independent if independent else sorted(avg_mi, key=avg_mi.get)[:3]

    def _fallback_correlation(self, x: 'np.ndarray', y: 'np.ndarray') -> float:
        """Fallback: Pearson correlation coefficient."""
        if not HAS_NUMPY:
            return 0.0
        try:
            if np.std(x) == 0 or np.std(y) == 0:
                return 0.0
            return float(np.corrcoef(x, y)[0, 1])
        except Exception as e:
            logger.warning(f"fallback correlation failed: {e}")
            return 0.0

    def _fallback_kl(self, p: 'np.ndarray', q: 'np.ndarray') -> float:
        """Fallback KL divergence estimation."""
        if not HAS_NUMPY:
            return 0.0
        try:
            eps = 1e-10
            p_hist, edges = np.histogram(p, bins=10, density=True)
            q_hist, _ = np.histogram(q, bins=edges, density=True)
            p_hist = p_hist + eps
            q_hist = q_hist + eps
            p_hist = p_hist / p_hist.sum()
            q_hist = q_hist / q_hist.sum()
            return float(np.sum(p_hist * np.log(p_hist / q_hist)))
        except Exception as e:
            logger.warning(f"fallback KL divergence failed: {e}")
            return 0.0

    def _fallback_jsd(self, p: 'np.ndarray', q: 'np.ndarray') -> float:
        """Fallback Jensen-Shannon divergence."""
        if not HAS_NUMPY:
            return 0.0
        try:
            kl_pq = self._fallback_kl(p, q)
            kl_qp = self._fallback_kl(q, p)
            return 0.5 * (kl_pq + kl_qp)
        except Exception as e:
            logger.warning(f"fallback JSD failed: {e}")
            return 0.0
