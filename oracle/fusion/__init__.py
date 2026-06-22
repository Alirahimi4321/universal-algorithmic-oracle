"""Fusion layer for combining symbolic system outputs."""
from .numeric_fusion import weighted_average_fusion, concatenation_fusion, modular_fusion, NumericFusion
from .symbolic_fusion import symbolic_state_fusion, find_dominant_element, SymbolicFusion
from .graph_fusion import merge_graphs, compute_graph_resonance
from .mapping import map_to_response, compute_confidence

__all__ = [
    "weighted_average_fusion", "concatenation_fusion", "modular_fusion",
    "symbolic_state_fusion", "find_dominant_element",
    "merge_graphs", "compute_graph_resonance",
    "map_to_response", "compute_confidence",
    "NumericFusion", "SymbolicFusion",
]
