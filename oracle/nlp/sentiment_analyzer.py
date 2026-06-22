"""Sentiment Analyzer for oracle questions using VADER."""
from __future__ import annotations
import logging
from typing import Any

logger = logging.getLogger(__name__)

try:
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    _analyzer = SentimentIntensityAnalyzer()
    HAS_VADER = True
except Exception:
    HAS_VADER = False
    _analyzer = None


class SentimentAnalyzer:
    """Analyze question sentiment to adjust prediction confidence weighting."""

    def __init__(self) -> None:
        self.available = HAS_VADER

    def analyze(self, question: str) -> dict[str, Any]:
        if not self.available or _analyzer is None:
            return {"positive": 0.0, "negative": 0.0, "neutral": 1.0, "compound": 0.0,
                    "label": "neutral", "confidence_weight": 1.0, "emotion_intensity": 0.0}
        scores = _analyzer.polarity_scores(question)
        compound = scores["compound"]
        label = "positive" if compound >= 0.05 else ("negative" if compound <= -0.05 else "neutral")
        cw = 1.15 if abs(compound) > 0.5 else (1.08 if abs(compound) > 0.3 else (0.95 if abs(compound) < 0.1 else 1.0))
        return {"positive": round(scores["pos"], 4), "negative": round(scores["neg"], 4),
                "neutral": round(scores["neu"], 4), "compound": round(compound, 4),
                "label": label, "confidence_weight": round(cw, 4), "emotion_intensity": round(abs(compound), 4)}

    def adjust_confidence(self, base_confidence: float, question: str) -> float:
        return min(1.0, base_confidence * self.analyze(question)["confidence_weight"])
