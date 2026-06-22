"""Anomaly Detector using PyOD for detecting unusual prediction patterns."""
from __future__ import annotations
import logging
import numpy as np
from typing import Any

logger = logging.getLogger(__name__)

try:
    from pyod.models.knn import KNN as KNNDetector
    from pyod.models.iforest import IForest
    HAS_PYOD = True
except Exception:
    HAS_PYOD = False
    logger.info("pyod not available")


class AnomalyDetector:
    """Detect anomalous patterns in symbolic system outputs and predictions."""

    def __init__(self) -> None:
        self.available = HAS_PYOD

    def detect(self, data_points: list[dict[str, float]], contamination: float = 0.1) -> dict[str, Any]:
        if not self.available:
            return {"anomalies": [], "method": "unavailable"}
        if len(data_points) < 10:
            return {"anomalies": [], "method": "insufficient_data"}
        keys = list(data_points[0].keys())
        X = np.array([[dp.get(k, 0.0) for k in keys] for dp in data_points], dtype=float)
        X = np.nan_to_num(X, nan=0.0)
        try:
            clf = IForest(contamination=contamination, random_state=42, n_estimators=50)
            clf.fit(X)
            labels = clf.labels_
            scores = clf.decision_scores_
            anomaly_indices = [i for i, l in enumerate(labels) if l == 1]
            return {
                "anomalies": anomaly_indices,
                "num_anomalies": len(anomaly_indices),
                "total_points": len(data_points),
                "anomaly_ratio": round(len(anomaly_indices) / len(data_points), 4),
                "scores": [round(float(s), 4) for s in scores],
                "alert_level": self._alert_level(len(anomaly_indices), len(data_points)),
                "method": "isolation_forest",
            }
        except Exception:
            try:
                clf = KNNDetector(n_neighbors=5, contamination=contamination)
                clf.fit(X)
                labels = clf.labels_
                scores = clf.decision_scores_
                anomaly_indices = [i for i, l in enumerate(labels) if l == 1]
                return {"anomalies": anomaly_indices, "num_anomalies": len(anomaly_indices),
                        "total_points": len(data_points), "anomaly_ratio": round(len(anomaly_indices) / len(data_points), 4),
                        "scores": [round(float(s), 4) for s in scores],
                        "alert_level": self._alert_level(len(anomaly_indices), len(data_points)), "method": "knn"}
            except Exception as e:
                return {"anomalies": [], "method": "failed", "error": str(e)}

    def detect_single(self, feature_vector: list[float], historical_data: list[list[float]]) -> dict[str, Any]:
        if not self.available or len(historical_data) < 10:
            return {"is_anomaly": False, "score": 0.0, "method": "unavailable"}
        X = np.array(historical_data, dtype=float)
        X = np.nan_to_num(X, nan=0.0)
        x = np.array([feature_vector], dtype=float)
        x = np.nan_to_num(x, nan=0.0)
        try:
            clf = KNNDetector(n_neighbors=min(5, len(X) - 1))
            clf.fit(X)
            score = float(clf.decision_function(x)[0])
            threshold = float(np.percentile(clf.decision_scores_, 90))
            return {"is_anomaly": score > threshold, "score": round(score, 4),
                    "threshold": round(threshold, 4), "method": "knn_single"}
        except Exception:
            return {"is_anomaly": False, "score": 0.0, "method": "failed"}

    def detect_prediction_anomalies(self, predictions: list[dict]) -> dict[str, Any]:
        if len(predictions) < 5:
            return {"anomalous_predictions": [], "method": "insufficient_data"}
        confidences = [p.get("oracle_confidence", 0.5) for p in predictions]
        fitness_vals = [p.get("fitness", {}).get("total_fitness", 0.5) for p in predictions]
        data = [{"confidence": c, "fitness": f} for c, f in zip(confidences, fitness_vals)]
        return self.detect(data, contamination=0.15)

    def _alert_level(self, n_anomalies: int, total: int) -> str:
        ratio = n_anomalies / max(total, 1)
        if ratio > 0.3:
            return "critical"
        if ratio > 0.2:
            return "high"
        if ratio > 0.1:
            return "medium"
        return "low"
