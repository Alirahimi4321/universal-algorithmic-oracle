"""Information Theory measures using infomeasure."""
import logging
import numpy as np

logger = logging.getLogger(__name__)

HAS_INFOMEASURE = False
try:
    import infomeasure as im
    HAS_INFOMEASURE = True
except ImportError:
    pass


class InformationMeasureAnalyzer:
    """Compute entropy, mutual information, and transfer entropy."""

    def __init__(self):
        self.available = HAS_INFOMEASURE

    def compute_entropy(self, data: list, measure: str = "shannon") -> dict:
        if not self.available:
            return {"error": "infomeasure not available"}
        if not data:
            return {"error": "empty data"}
        try:
            h_val = im.h(data, base=measure)
            return {"entropy": float(h_val), "measure": measure, "data_length": len(data)}
        except Exception as e:
            return {"error": str(e)}

    def compute_mutual_information(self, x: list, y: list) -> dict:
        if not self.available:
            return {"error": "infomeasure not available"}
        try:
            mi_val = im.mi(x, y)
            return {"mutual_information": float(mi_val), "x_length": len(x), "y_length": len(y)}
        except Exception as e:
            return {"error": str(e)}

    def compute_transfer_entropy(self, source: list, target: list) -> dict:
        if not self.available:
            return {"error": "infomeasure not available"}
        try:
            te_val = im.te(source, target)
            return {"transfer_entropy": float(te_val), "source_length": len(source), "target_length": len(target)}
        except Exception as e:
            return {"error": str(e)}

    def full_analysis(self, x: list, y: list) -> dict:
        results = {}
        try:
            results["entropy_x"] = self.compute_entropy(x)
            results["entropy_y"] = self.compute_entropy(y)
            results["mutual_information"] = self.compute_mutual_information(x, y)
            results["transfer_xy"] = self.compute_transfer_entropy(x, y)
            results["transfer_yx"] = self.compute_transfer_entropy(y, x)
        except Exception as e:
            results["error"] = str(e)
        return results
