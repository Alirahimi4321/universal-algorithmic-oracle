"""Symbolic matrix generation from entropy."""
import math
import random
from typing import Tuple

def generate_symbolic_matrix(seed: int, shape: Tuple[int, int] = (4, 4)) -> list[list[float]]:
    rng = random.Random(seed)
    rows, cols = shape
    matrix = []
    for i in range(rows):
        row = []
        for j in range(cols):
            val = rng.random() * 2 - 1
            val += math.sin(seed * (i + 1) * 0.1) * 0.3
            val += math.cos(seed * (j + 1) * 0.1) * 0.3
            row.append(val)
        matrix.append(row)
    return matrix

def matrix_to_features(matrix: list[list[float]]) -> dict:
    flat = [val for row in matrix for val in row]
    
    mean_val = sum(flat) / len(flat) if flat else 0.0
    
    variance = sum((x - mean_val) ** 2 for x in flat) / len(flat) if flat else 0.0
    std_dev = math.sqrt(variance)
    
    min_val = min(flat) if flat else 0.0
    max_val = max(flat) if flat else 0.0
    
    normalized = [(x - min_val) / (max_val - min_val) if max_val != min_val else 0.5 for x in flat]
    entropy = -sum(p * math.log2(p) for p in normalized if p > 0) if normalized else 0.0
    
    return {
        "mean": mean_val,
        "std_dev": std_dev,
        "min": min_val,
        "max": max_val,
        "entropy": entropy,
        "size": len(flat),
    }
