"""Wavelet Analysis using PyWavelets for multi-scale signal decomposition."""
from __future__ import annotations
import logging
import numpy as np
from typing import Any

logger = logging.getLogger(__name__)

try:
    import pywt
    HAS_PYWT = True
except Exception:
    HAS_PYWT = False


class WaveletAnalyzer:
    """Multi-scale signal analysis using wavelet transforms."""

    def __init__(self) -> None:
        self.available = HAS_PYWT

    def decompose(self, data: list[float], wavelet: str = "haar", level: int = None) -> dict[str, Any]:
        if not self.available:
            return {"method": "unavailable"}
        signal = np.array(data, dtype=float)
        try:
            coeffs = pywt.wavedec(signal, wavelet, level=level)
            result = {"wavelet": wavelet, "num_levels": len(coeffs), "level_details": []}
            for i, c in enumerate(coeffs):
                result["level_details"].append({"level": i, "length": len(c), "energy": round(float(np.sum(c**2)), 4),
                                                "mean": round(float(np.mean(c)), 4), "std": round(float(np.std(c)), 4)})
            energies = [np.sum(c**2) for c in coeffs]
            total = sum(energies)
            result["energy_distribution"] = [round(float(e / max(total, 1e-10)), 4) for e in energies]
            result["approximation_energy"] = round(float(energies[0] / max(total, 1e-10)), 4)
            result["detail_energy"] = round(float(sum(energies[1:]) / max(total, 1e-10)), 4)
            return result
        except Exception as e:
            return {"method": "failed", "error": str(e)}

    def denoise(self, data: list[float], wavelet: str = "db4", threshold_mode: str = "soft") -> dict[str, Any]:
        if not self.available:
            return {"denoised": data, "method": "unavailable"}
        signal = np.array(data, dtype=float)
        try:
            coeffs = pywt.wavedec(signal, wavelet, level=3)
            sigma = np.median(np.abs(coeffs[-1])) / 0.6745
            threshold = sigma * np.sqrt(2 * np.log(len(signal)))
            denoised_coeffs = [coeffs[0]]
            for c in coeffs[1:]:
                if threshold_mode == "soft":
                    denoised = pywt.threshold(c, threshold, mode="soft")
                else:
                    denoised = pywt.threshold(c, threshold, mode="hard")
                denoised_coeffs.append(denoised)
            denoised_signal = pywt.waverec(denoised_coeffs, wavelet)[:len(signal)]
            noise_removed = float(np.mean(np.abs(signal - denoised_signal)))
            return {"denoised": denoised_signal.tolist(), "noise_removed": round(noise_removed, 4),
                    "method": f"wavelet_{threshold_mode}", "wavelet": wavelet}
        except Exception as e:
            return {"denoised": data, "method": "failed", "error": str(e)}

    def extract_features(self, data: list[float]) -> dict[str, Any]:
        if not self.available:
            return {"features": [], "method": "unavailable"}
        decomp = self.decompose(data, wavelet="db4", level=3)
        if decomp.get("method") == "failed":
            return {"features": [], "method": "decomposition_failed"}
        features = []
        for detail in decomp.get("level_details", []):
            features.extend([detail["energy"], detail["mean"], detail["std"]])
        features.append(decomp.get("approximation_energy", 0))
        features.append(decomp.get("detail_energy", 0))
        return {"features": features, "num_features": len(features), "method": "wavelet_db4"}
