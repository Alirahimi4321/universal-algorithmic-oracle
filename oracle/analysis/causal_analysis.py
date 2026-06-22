"""Causal discovery analysis using causal-learn."""
import logging
import numpy as np

logger = logging.getLogger(__name__)

HAS_CAUSAL = False
try:
    from causallearn.search.ConstraintBased.PC import pc
    from causallearn.search.ScoreBased.GES import ges
    from causallearn.graph.Graph import Graph
    HAS_CAUSAL = True
except ImportError:
    pass


class CausalAnalyzer:
    """Causal structure learning from observational data."""

    def __init__(self):
        self.available = HAS_CAUSAL

    def discover_causal_graph(self, data: np.ndarray, method: str = "pc", alpha: float = 0.05) -> dict:
        if not self.available:
            return {"error": "causal-learn not available"}
        try:
            if method == "pc":
                cg = pc(data, alpha=alpha, indep_test="fisherz", stable=True)
            elif method == "ges":
                cg = ges(data)
            else:
                return {"error": f"unknown method: {method}"}

            adj_matrix = cg.G.graph
            n_nodes = adj_matrix.shape[0]
            edges = []
            for i in range(n_nodes):
                for j in range(n_nodes):
                    if adj_matrix[i, j] == -1 and adj_matrix[j, i] == 1:
                        edges.append((i, j, "->"))
                    elif adj_matrix[i, j] == -1 and adj_matrix[j, i] == -1:
                        edges.append((i, j, "---"))
                    elif adj_matrix[i, j] == 1 and adj_matrix[j, i] == 1:
                        edges.append((i, j, "o-o"))

            return {
                "method": method,
                "n_nodes": n_nodes,
                "edges": edges,
                "adjacency_matrix": adj_matrix.tolist(),
                "p_values": cg.get_obj() if hasattr(cg, "get_obj") else None,
            }
        except Exception as e:
            logger.warning("causal-learn failed: %s", e)
            return {"error": str(e)}

    def analyze(self, data: dict) -> dict:
        X = np.array(data.get("data", [[1, 2, 3], [4, 5, 6]]))
        method = data.get("method", "pc")
        alpha = data.get("alpha", 0.05)
        return self.discover_causal_graph(X, method, alpha)
