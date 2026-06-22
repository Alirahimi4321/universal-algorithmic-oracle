"""Novelty search for behavioral diversity in oracle evolution."""
import math
from ..genome.chromosome import Chromosome


def _feature_vector(c: Chromosome) -> list[float]:
    systems = sorted(set(g.system_id for g in c.gene_list))
    weights = sorted([g.weight for g in c.gene_list])
    padded = weights[:5] + [0] * (5 - len(weights[:5]))
    return [len(c.genes), len(c.edges), len(systems)] + padded


def _euclidean_distance(v1: list[float], v2: list[float]) -> float:
    max_len = max(len(v1), len(v2))
    v1 = v1 + [0] * (max_len - len(v1))
    v2 = v2 + [0] * (max_len - len(v2))
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(v1, v2)))


def compute_novelty(chromosome: Chromosome, archive: list[Chromosome], k: int = 15) -> float:
    if not archive:
        return 1.0

    query_vec = _feature_vector(chromosome)
    distances = []
    for member in archive:
        member_vec = _feature_vector(member)
        dist = _euclidean_distance(query_vec, member_vec)
        distances.append(dist)

    distances.sort()
    k_nearest = distances[:k]

    if not k_nearest:
        return 1.0

    novelty = sum(k_nearest) / len(k_nearest)
    return novelty
