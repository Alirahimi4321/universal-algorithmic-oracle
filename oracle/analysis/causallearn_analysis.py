"""Causal Discovery analysis using causal-learn."""
import logging
import numpy as np

logger = logging.getLogger(__name__)

HAS_CAUSALLEARN = False
try:
    import causallearn
    HAS_CAUSALLEARN = True
except ImportError:
    pass


class CausalLearnAnalyzer:
    """Causal discovery using constraint-based and score-based methods."""

    def __init__(self):
        self.available = HAS_CAUSALLEARN
        self.causal_graph = None

    def pc_algorithm(self, data: list[list[float]], alpha: float = 0.05) -> dict:
        if not self.available:
            return {"error": "causal-learn not available"}
        try:
            from causallearn.search.ConstraintBased.PC import pc
            cg = pc(np.array(data, dtype=float), alpha=alpha)
            self.causal_graph = cg
            adj_matrix = cg.G.graph if hasattr(cg, "G") else np.zeros((len(data[0]), len(data[0])))
            return {
                "adjacency_matrix": adj_matrix.tolist() if isinstance(adj_matrix, np.ndarray) else [],
                "num_edges": int(np.sum(adj_matrix != 0)) if isinstance(adj_matrix, np.ndarray) else 0,
                "method": "PC",
                "alpha": alpha,
            }
        except Exception as e:
            return {"error": str(e)}

    def ges_algorithm(self, data: list[list[float]]) -> dict:
        if not self.available:
            return {"error": "causal-learn not available"}
        try:
            from causallearn.search.ScoreBased.GES import ges
            result = ges(np.array(data, dtype=float))
            cg = result["G"] if isinstance(result, dict) else result
            return {
                "score": float(result.get("score", 0)) if isinstance(result, dict) else 0,
                "method": "GES",
            }
        except Exception as e:
            return {"error": str(e)}
