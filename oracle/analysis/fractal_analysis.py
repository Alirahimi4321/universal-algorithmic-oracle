"""Fractal analysis wrapper using fractek."""
import logging
import numpy as np

logger = logging.getLogger(__name__)

HAS_FRACTEK = False
try:
    from fractek.dimension_calculations.box_counting import box_counting, calc_dimension
    HAS_FRACTEK = True
except ImportError:
    pass


class FractalAnalyzer:
    """Fractal dimension analysis using box-counting method."""

    def __init__(self):
        self.available = HAS_FRACTEK

    def compute_fractal_dimension(self, data: list[float]) -> dict:
        if not self.available:
            return {"error": "fractek not available"}
        if not data or len(data) < 4:
            return {"error": "insufficient data"}
        try:
            arr = np.array(data, dtype=float)
            # Normalize to [0,1]
            arr = (arr - arr.min()) / (arr.max() - arr.min() + 1e-10)
            # Create 2D representation
            size = int(np.sqrt(len(arr)))
            if size < 2:
                return {"error": "data too small for 2D"}
            img = arr[:size*size].reshape(size, size)
            counts = box_counting(img)
            dimension = calc_dimension(counts) if counts else 0
            return {
                "fractal_dimension": float(dimension),
                "box_counts": counts if isinstance(counts, list) else [],
                "data_length": len(data),
            }
        except Exception as e:
            return {"error": str(e)}
