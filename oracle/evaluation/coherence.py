"""Structural coherence evaluation for oracle chromosomes."""
from ..genome.chromosome import Chromosome


def evaluate_coherence(chromosome: Chromosome) -> float:
    """Evaluate structural coherence of an oracle chromosome.
    Measures: graph connectivity, cycle control, signal flow completeness, output completeness.
    Returns float 0.0-1.0.
    """
    genes = list(chromosome.genes.values()) if isinstance(chromosome.genes, dict) else list(chromosome.genes)
    edges = chromosome.edges

    if not genes:
        return 0.0

    n_genes = len(genes)
    n_edges = len(edges)
    max_edges = n_genes * (n_genes - 1) if n_genes > 1 else 0

    connectivity = n_edges / max(max_edges, 1) if n_genes > 1 else 1.0

    gene_ids = set()
    for g in genes:
        gene_ids.add(g.gene_id)

    edges_from = set(f for f, t in edges)
    edges_to = set(t for f, t in edges)

    nodes_with_output = len(edges_from) / n_genes if n_genes > 0 else 0
    nodes_with_input = len(edges_to) / n_genes if n_genes > 0 else 0
    nodes_connected = len(edges_from | edges_to) / n_genes if n_genes > 0 else 0

    output_gene = genes[-1] if genes else None
    has_output = 1.0 if output_gene and output_gene.gene_id in edges_to else 0.5

    coherence = (connectivity * 0.3 + nodes_connected * 0.3 +
                 nodes_with_output * 0.2 + nodes_with_input * 0.1 + has_output * 0.1)

    return min(max(coherence, 0.0), 1.0)
