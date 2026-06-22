"""Complexity control - penalizes overly complex or overly simple structures."""


def evaluate_complexity(chromosome, target_complexity: float = 0.5) -> float:
    """Evaluate structural complexity and penalize deviation from target.
    Returns float 0.0-1.0 where 1.0 is optimally complex.
    """
    genes = list(chromosome.genes.values()) if isinstance(chromosome.genes, dict) else list(chromosome.genes)
    edges = chromosome.edges

    if not genes:
        return 0.0

    n_genes = len(genes)
    n_edges = len(edges)
    system_diversity = len(set(g.system_id for g in genes)) / n_genes if n_genes > 0 else 0
    param_complexity = sum(len(g.params) for g in genes) / n_genes if n_genes > 0 else 0

    raw_complexity = (n_genes * 0.2 + n_edges * 0.1 + system_diversity * 0.3 + min(param_complexity / 10, 1.0) * 0.4)

    normalized = min(raw_complexity / 2.0, 1.0)

    deviation = abs(normalized - target_complexity)
    score = 1.0 - deviation

    return max(0.0, min(1.0, score))
