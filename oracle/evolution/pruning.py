"""Pruning engine for evolutionary oracle - removes low-fitness genes."""
import random
from ..genome.chromosome import Chromosome


class PruningEngine:
    def __init__(self, config: dict = None):
        config = config or {}
        self.prune_threshold = config.get("prune_threshold", 0.2)
        self.min_genes = config.get("min_genes", 2)

    def prune(self, chromosome: Chromosome) -> Chromosome:
        if len(chromosome.genes) <= self.min_genes:
            return chromosome

        gene_fitness = {}
        for gid, gene in chromosome.genes.items():
            gene_fitness[gid] = gene.weight * random.uniform(0.5, 1.5)

        sorted_genes = sorted(gene_fitness.items(), key=lambda x: x[1])
        to_remove = []
        for gid, fitness in sorted_genes:
            if fitness < self.prune_threshold and len(chromosome.genes) - len(to_remove) > self.min_genes:
                to_remove.append(gid)

        new_genes = {gid: g for gid, g in chromosome.genes.items() if gid not in to_remove}
        new_edges = [(s, d) for s, d in chromosome.edges if s in new_genes and d in new_genes]

        return Chromosome(
            chromosome_id=chromosome.chromosome_id,
            genes=new_genes,
            edges=new_edges,
            fusion_schema=chromosome.fusion_schema.copy(),
            output_mapping=chromosome.output_mapping.copy(),
            fitness=chromosome.fitness.copy(),
            metadata=chromosome.metadata.copy(),
        )
