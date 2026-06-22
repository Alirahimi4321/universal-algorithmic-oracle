"""Causal Discovery Engine using causal-learn to find causal relationships between symbolic systems."""
from __future__ import annotations
import logging
import numpy as np
from typing import Any

logger = logging.getLogger(__name__)

try:
    from causallearn.search.ConstraintBased.PC import pc as pc_algorithm
    from causallearn.search.ScoreBased.GES import ges as ges_algorithm
    HAS_CAUSAL = True
except Exception:
    HAS_CAUSAL = False


class CausalDiscoveryEngine:
    """Discover causal relationships between symbolic system outputs."""

    def __init__(self) -> None:
        self.available = HAS_CAUSAL

    def discover(self, system_outputs: dict[str, list[float]], alpha: float = 0.05) -> dict[str, Any]:
        if not self.available:
            return {"causal_graph": [], "direct_causes": {}, "method": "unavailable"}
        systems = list(system_outputs.keys())
        if len(systems) < 3:
            return {"causal_graph": [], "direct_causes": {}, "method": "insufficient_data"}
        min_len = min(len(v) for v in system_outputs.values())
        data = np.column_stack([system_outputs[s][:min_len] for s in systems])
        data = np.nan_to_num(data, nan=0.0)
        if data.shape[0] < data.shape[1]:
            data = np.tile(data, (max(2, data.shape[1] // data.shape[0] + 1), 1))[:max(10, data.shape[1])]
        try:
            cg = pc_algorithm(data, alpha=alpha, verbose=False)
            adj_matrix = cg.G.graph
            causal_graph = []
            direct_causes = {s: [] for s in systems}
            for i in range(len(systems)):
                for j in range(len(systems)):
                    if i != j and adj_matrix[i, j] == -1 and adj_matrix[j, i] == 1:
                        causal_graph.append({"cause": systems[i], "effect": systems[j]})
                        direct_causes[systems[j]].append(systems[i])
            return {"causal_graph": causal_graph, "direct_causes": direct_causes,
                    "num_edges": len(causal_graph), "method": "pc_algorithm", "alpha": alpha}
        except Exception as e:
            return {"causal_graph": [], "direct_causes": {}, "method": "failed", "error": str(e)}

    def discover_with_ges(self, system_outputs: dict[str, list[float]]) -> dict[str, Any]:
        if not self.available:
            return {"causal_graph": [], "method": "unavailable"}
        systems = list(system_outputs.keys())
        min_len = min(len(v) for v in system_outputs.values())
        data = np.column_stack([system_outputs[s][:min_len] for s in systems])
        data = np.nan_to_num(data, nan=0.0)
        try:
            cg = ges_algorithm(data, verbose=False)
            adj_matrix = cg.G.graph
            causal_graph = []
            for i in range(len(systems)):
                for j in range(len(systems)):
                    if i != j and adj_matrix[i, j] == -1 and adj_matrix[j, i] == 1:
                        causal_graph.append({"cause": systems[i], "effect": systems[j]})
            return {"causal_graph": causal_graph, "num_edges": len(causal_graph), "method": "ges"}
        except Exception as e:
            return {"causal_graph": [], "method": "failed", "error": str(e)}
