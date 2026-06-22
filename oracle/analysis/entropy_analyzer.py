"""Advanced Entropy Analysis using antropy for complexity measures."""
from __future__ import annotations
import logging
import numpy as np
from typing import Any

logger = logging.getLogger(__name__)

try:
    import antropy as ant
    HAS_ANTROPY = True
except Exception:
    HAS_ANTROPY = False

try:
    import pywt
    HAS_PYWT = True
except Exception:
    HAS_PYWT = False


class EntropyAnalyzer:
    """Compute advanced entropy and complexity measures for time series."""

    def __init__(self) -> None:
        self.antropy_available = HAS_ANTROPY
        self.wavelet_available = HAS_PYWT

    def full_analysis(self, data: list[float]) -> dict[str, Any]:
        signal = np.array(data, dtype=float)
        result: dict[str, Any] = {"data_points": len(signal)}
        if self.antropy_available:
            try:
                result["permutation_entropy"] = round(float(ant.perm_entropy(signal, order=3, normalize=True)), 4)
            except Exception:
                result["permutation_entropy"] = None
            try:
                result["spectral_entropy"] = round(float(ant.spectral_entropy(signal, normalize=True)), 4)
            except Exception:
                result["spectral_entropy"] = None
            try:
                result["svd_entropy"] = round(float(ant.svd_entropy(signal, normalize=True)), 4)
            except Exception:
                result["svd_entropy"] = None
            try:
                result["sample_entropy"] = round(float(ant.sample_entropy(signal, order=2)), 4)
            except Exception:
                result["sample_entropy"] = None
            try:
                result["approximate_entropy"] = round(float(ant.app_entropy(signal, order=2)), 4)
            except Exception:
                result["approximate_entropy"] = None
            try:
                result["lempel_ziv"] = round(float(ant.lziv_complexity(signal > np.mean(signal))), 4)
            except Exception:
                result["lempel_ziv"] = None
            try:
                result["hjorth_activity"] = round(float(ant.hjorth_params(signal)[0]), 4)
                result["hjorth_mobility"] = round(float(ant.hjorth_params(signal)[1]), 4)
                result["hjorth_complexity"] = round(float(ant.hjorth_params(signal)[2]), 4)
            except Exception:
                pass
            try:
                result["dfa"] = round(float(ant.detrended_fluctuation(signal)), 4)
            except Exception:
                result["dfa"] = None
            try:
                result["higuchi_fd"] = round(float(ant.higuchi_fd(signal)), 4)
            except Exception:
                result["higuchi_fd"] = None
        if self.wavelet_available:
            try:
                cA, cD = pywt.dwt(signal, "haar")
                result["wavelet_energy_ratio"] = round(float(np.sum(cA**2) / max(np.sum(cD**2), 1e-10)), 4)
                result["wavelet_detail_energy"] = round(float(np.sum(cD**2)), 4)
            except Exception:
                pass
        result["complexity_score"] = self._complexity_score(result)
        return result

    def _complexity_score(self, metrics: dict) -> float:
        score = 0.5
        pe = metrics.get("permutation_entropy")
        if pe is not None:
            score += (pe - 0.5) * 0.2
        se = metrics.get("sample_entropy")
        if se is not None:
            score += min(0.2, se / 10.0)
        dfa = metrics.get("dfa")
        if dfa is not None:
            score += (dfa - 0.5) * 0.1
        return round(min(1.0, max(0.0, score)), 4)

    def compare_series(self, data1: list[float], data2: list[float]) -> dict[str, Any]:
        a1 = self.full_analysis(data1)
        a2 = self.full_analysis(data2)
        similarities = {}
        for key in ["permutation_entropy", "spectral_entropy", "sample_entropy", "dfa"]:
            if a1.get(key) is not None and a2.get(key) is not None:
                diff = abs(a1[key] - a2[key])
                similarities[key] = round(1.0 - min(diff, 1.0), 4)
        avg_sim = np.mean(list(similarities.values())) if similarities else 0.5
        return {"similarities": similarities, "overall_similarity": round(float(avg_sim), 4)}
