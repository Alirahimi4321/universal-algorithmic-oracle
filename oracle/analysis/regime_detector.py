"""Change Point Detection using ruptures for detecting regime shifts in oracle data."""
from __future__ import annotations
import logging
import numpy as np
from typing import Any

logger = logging.getLogger(__name__)

try:
    import ruptures as rpt
    HAS_RUPTURES = True
except Exception:
    HAS_RUPTURES = False


class RegimeDetector:
    """Detect change points and regime shifts in time series data."""

    def __init__(self) -> None:
        self.available = HAS_RUPTURES

    def detect(self, data: list[float], model: str = "rbf", method: str = "pelt",
               min_size: int = 5, penalty: float = 10.0) -> dict[str, Any]:
        if not self.available:
            return {"change_points": [], "method": "unavailable"}
        signal = np.array(data, dtype=float)
        if len(signal) < min_size * 2:
            return {"change_points": [], "num_regimes": 1, "method": "insufficient_data"}
        try:
            if method == "pelt":
                algo = rpt.Pelt(model=model, min_size=min_size)
            elif method == "binseg":
                algo = rpt.Binseg(model=model, min_size=min_size)
            elif method == "bottomup":
                algo = rpt.BottomUp(model=model, min_size=min_size)
            else:
                algo = rpt.Pelt(model=model, min_size=min_size)
            algo.fit(signal)
            bkpts = algo.predict(pen=penalty)
            regimes = []
            prev = 0
            for i, bp in enumerate(bkpts):
                segment = signal[prev:bp]
                regimes.append({"start": prev, "end": bp, "mean": round(float(np.mean(segment)), 4),
                               "std": round(float(np.std(segment)), 4)})
                prev = bp
            return {"change_points": bkpts, "num_regimes": len(regimes), "regimes": regimes,
                    "method": f"{method}_{model}"}
        except Exception as e:
            return {"change_points": [], "method": "failed", "error": str(e)}

    def detect_fitness_regimes(self, fitness_history: list[float]) -> dict[str, Any]:
        if len(fitness_history) < 10:
            return {"regimes": [], "current_regime": "stable"}
        result = self.detect(fitness_history, model="rbf", method="pelt", penalty=5.0)
        regimes = result.get("regimes", [])
        current = "stable"
        if regimes:
            last = regimes[-1]
            if last["mean"] > 0.7:
                current = "high_performance"
            elif last["mean"] < 0.3:
                current = "low_performance"
            elif last["std"] > 0.15:
                current = "volatile"
        return {"regimes": regimes, "current_regime": current, "total_regimes": len(regimes)}

    def detect_prediction_shifts(self, predictions: list[dict]) -> dict[str, Any]:
        if len(predictions) < 10:
            return {"shifts": [], "method": "insufficient_data"}
        confidences = [p.get("oracle_confidence", 0.5) for p in predictions]
        result = self.detect(confidences, model="l2", method="binseg", penalty=3.0)
        return {"shifts": result["change_points"], "num_shifts": len(result["change_points"]),
                "regimes": result.get("regimes", []), "method": result["method"]}
