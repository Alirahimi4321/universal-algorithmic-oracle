"""Cross-system convergence/resonance evaluation."""
from ..symbolic.registry import compute_system


def evaluate_convergence(chromosome, entropy_packet: dict) -> float:
    """Evaluate how much different symbolic systems converge to similar states."""
    genes = list(chromosome.genes.values()) if isinstance(chromosome.genes, dict) else list(chromosome.genes)

    if len(genes) < 2:
        return 0.0

    results = []
    for gene in genes:
        try:
            result = compute_system(gene.system_id, entropy_packet, gene.params)
            results.append(result.numeric_projection)
        except Exception:
            continue

    if len(results) < 2:
        return 0.0

    agreement_scores = []
    for i in range(len(results)):
        for j in range(i + 1, len(results)):
            r1, r2 = results[i], results[j]
            max_len = max(len(r1), len(r2))
            v1 = r1 + [0] * (max_len - len(r1))
            v2 = r2 + [0] * (max_len - len(r2))

            norm1 = sum(abs(x) for x in v1)
            norm2 = sum(abs(x) for x in v2)

            if norm1 == 0 or norm2 == 0:
                agreement_scores.append(0.0)
                continue

            v1_norm = [x / norm1 for x in v1]
            v2_norm = [x / norm2 for x in v2]

            cosine = sum(a * b for a, b in zip(v1_norm, v2_norm))
            agreement_scores.append(max(0, cosine))

    return sum(agreement_scores) / len(agreement_scores) if agreement_scores else 0.0
