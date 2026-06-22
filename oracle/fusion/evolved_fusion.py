"""Evolved Fusion - fusion function itself is evolved by GA/GP per design doc section 23.1.4."""
import math
import random
from .numeric_fusion import (
    weighted_average_fusion, concatenation_fusion,
    modular_fusion, resonance_fusion
)
from .symbolic_fusion import symbolic_state_fusion, find_dominant_element, symbolic_phase_detection


class EvolvedFusionTree:
    """A tree-based fusion function that can be evolved."""

    OPERATORS = ["weighted_sum", "modular_resonance", "max_select", "harmonic_mean", "phase_blend"]
    
    def __init__(self, tree: dict = None):
        self.tree = tree or {"op": "weighted_sum", "args": []}

    def evaluate(self, numeric_vectors: list[list[float]], symbolic_states: list[dict]) -> dict:
        fused_numeric = self._eval_numeric_tree(self.tree, numeric_vectors)
        fused_symbolic = symbolic_state_fusion(symbolic_states)
        dominant = find_dominant_element(symbolic_states)
        phase = symbolic_phase_detection(symbolic_states)
        fused_symbolic["dominant_element"] = dominant
        fused_symbolic["phase"] = phase
        fused_symbolic["fusion_tree"] = self.tree
        return {"numeric": fused_numeric, "symbolic": fused_symbolic}

    def _eval_numeric_tree(self, node: dict, vectors: list[list[float]]) -> list[float]:
        op = node.get("op", "weighted_sum")
        args = node.get("args", [])

        if op == "weighted_sum":
            weights = node.get("weights", [1.0 / max(len(vectors), 1)] * len(vectors))
            return weighted_average_fusion(vectors, weights)
        elif op == "modular_resonance":
            modulus = node.get("modulus", 7)
            return modular_fusion(vectors, modulus)
        elif op == "max_select":
            return self._max_select(vectors)
        elif op == "harmonic_mean":
            return self._harmonic_mean(vectors)
        elif op == "phase_blend":
            return resonance_fusion(vectors)
        elif op == "composed":
            child_results = []
            for arg in args:
                child_results.append(self._eval_numeric_tree(arg, vectors))
            return weighted_average_fusion(child_results)
        return weighted_average_fusion(vectors)

    def _max_select(self, vectors: list[list[float]]) -> list[float]:
        if not vectors:
            return []
        max_len = max(len(v) for v in vectors)
        result = []
        for i in range(max_len):
            vals = [v[i] for v in vectors if i < len(v)]
            result.append(max(vals) if vals else 0.0)
        return result

    def _harmonic_mean(self, vectors: list[list[float]]) -> list[float]:
        if not vectors:
            return []
        max_len = max(len(v) for v in vectors)
        result = []
        for i in range(max_len):
            vals = [abs(v[i]) + 1e-10 for v in vectors if i < len(v)]
            if vals:
                result.append(len(vals) / sum(1.0 / x for x in vals))
            else:
                result.append(0.0)
        return result

    def mutate(self, intensity: float = 0.3):
        if random.random() < intensity:
            new_op = random.choice(self.OPERATORS)
            self.tree["op"] = new_op
        for arg in self.tree.get("args", []):
            if isinstance(arg, dict) and random.random() < intensity:
                EvolvedFusionTree(arg).mutate(intensity)

    @classmethod
    def random(cls, depth: int = 2) -> "EvolvedFusionTree":
        if depth <= 0:
            return cls({"op": random.choice(cls.OPERATORS), "weights": [random.random() for _ in range(5)]})
        op = random.choice(cls.OPERATORS)
        n_args = random.randint(0, 2)
        args = [cls.random(depth - 1).tree for _ in range(n_args)]
        return cls({"op": op, "args": args})


class EvolvedFusion:
    """Main evolved fusion - combines all fusion types per design doc section 23."""

    def __init__(self, config: dict = None):
        self.config = config or {}
        self.fusion_tree = EvolvedFusionTree(config.get("fusion_tree"))
        self.fusion_method = config.get("fusion_method", "evolved")

    def fuse(self, numeric_vectors: list[list[float]], symbolic_states: list[dict]) -> dict:
        if self.fusion_method == "evolved":
            return self.fusion_tree.evaluate(numeric_vectors, symbolic_states)
        elif self.fusion_method == "weighted_average":
            fused_num = weighted_average_fusion(numeric_vectors)
            fused_sym = symbolic_state_fusion(symbolic_states)
            return {"numeric": fused_num, "symbolic": fused_sym}
        elif self.fusion_method == "resonance":
            fused_num = resonance_fusion(numeric_vectors)
            fused_sym = symbolic_state_fusion(symbolic_states)
            return {"numeric": fused_num, "symbolic": fused_sym}
        return self.fusion_tree.evaluate(numeric_vectors, symbolic_states)

    def mutate_tree(self, intensity: float = 0.3):
        self.fusion_tree.mutate(intensity)
