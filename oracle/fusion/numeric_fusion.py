"""Numeric fusion of symbolic system outputs."""
import math

def weighted_average_fusion(vectors: list[list[float]], weights: list[float] = None) -> list[float]:
    if not vectors:
        return []
    if weights is None:
        weights = [1.0 / len(vectors)] * len(vectors)
    max_len = max(len(v) for v in vectors)
    result = [0.0] * max_len
    for vec, w in zip(vectors, weights):
        for i in range(max_len):
            val = vec[i] if i < len(vec) else 0.0
            result[i] += val * w
    return result

def concatenation_fusion(vectors: list[list[float]]) -> list[float]:
    result = []
    for vec in vectors:
        result.extend(vec)
    return result

def modular_fusion(vectors: list[list[float]], modulus: int = 7) -> list[float]:
    if not vectors:
        return []
    max_len = max(len(v) for v in vectors)
    result = [0.0] * max_len
    for vec in vectors:
        for i in range(max_len):
            val = vec[i] if i < len(vec) else 0.0
            result[i] = (result[i] + val) % modulus
    return result

def alternating_fusion(vectors: list[list[float]]) -> list[float]:
    if not vectors:
        return []
    result = []
    max_len = max(len(v) for v in vectors)
    for i in range(max_len):
        for j, vec in enumerate(vectors):
            if i < len(vec):
                result.append(vec[i])
    return result

def resonance_fusion(vectors: list[list[float]]) -> list[float]:
    if not vectors or len(vectors) < 2:
        return vectors[0] if vectors else []
    max_len = max(len(v) for v in vectors)
    result = [0.0] * max_len
    for i in range(max_len):
        vals = [v[i] if i < len(v) else 0.0 for v in vectors]
        mean_val = sum(vals) / len(vals)
        variance = sum((x - mean_val) ** 2 for x in vals) / len(vals)
        result[i] = mean_val * (1.0 + math.sqrt(variance))
    return result


class NumericFusion:
    def __init__(self, method: str = "weighted_average"):
        self.method = method

    def fuse(self, vectors: list[list[float]], weights: list[float] = None) -> list[float]:
        if self.method == "weighted_average":
            return weighted_average_fusion(vectors, weights)
        elif self.method == "concatenation":
            return concatenation_fusion(vectors)
        elif self.method == "modular":
            return modular_fusion(vectors)
        elif self.method == "alternating":
            return alternating_fusion(vectors)
        elif self.method == "resonance":
            return resonance_fusion(vectors)
        return weighted_average_fusion(vectors, weights)
