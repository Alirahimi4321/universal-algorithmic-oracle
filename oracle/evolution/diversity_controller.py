"""Diversity controller for evolutionary oracle - maintains population diversity."""
import random
import math
from ..genome.chromosome import Chromosome


class DiversityController:
    def __init__(self, config: dict = None):
        config = config or {}
        self.target_diversity = config.get("target_diversity", 0.6)
        self.min_diversity = config.get("min_diversity", 0.3)

    def measure_diversity(self, population: list[Chromosome]) -> float:
        if len(population) < 2:
            return 1.0

        system_sets = [set(g.system_id for g in chrom.gene_list) for chrom in population]
        all_systems = set()
        for s in system_sets:
            all_systems.update(s)

        if not all_systems:
            return 0.0

        presence_count = {sys: 0 for sys in all_systems}
        for s in system_sets:
            for sys in s:
                presence_count[sys] += 1

        frequencies = [presence_count[sys] / len(population) for sys in all_systems]
        entropy = -sum(f * math.log2(f + 1e-10) for f in frequencies if f > 0)
        max_entropy = math.log2(len(all_systems)) if all_systems else 1.0

        return entropy / max_entropy if max_entropy > 0 else 0.0

    def control(self, population: list[Chromosome]) -> list[Chromosome]:
        diversity = self.measure_diversity(population)

        if diversity < self.min_diversity:
            n_inject = max(1, len(population) // 5)
            for _ in range(n_inject):
                random.shuffle(population)
                weakest_idx = min(range(len(population)),
                                  key=lambda i: population[i].get_fitness_score())
                new_chrom = Chromosome.create_random()
                population[weakest_idx] = new_chrom

        elif diversity > self.target_diversity + 0.2:
            system_counts = {}
            for chrom in population:
                for g in chrom.gene_list:
                    system_counts[g.system_id] = system_counts.get(g.system_id, 0) + 1

            if system_counts:
                rare_system = min(system_counts, key=system_counts.get)
                for i, chrom in enumerate(population[:len(population)//3]):
                    if random.random() < 0.3:
                        genes = chrom.genes.copy()
                        if genes:
                            target_gene_id = list(genes.keys())[0]
                            genes[target_gene_id] = Chromosome.create_random([(rare_system, "internal")]).gene_list[0]
                            population[i] = Chromosome(
                                chromosome_id=chrom.chromosome_id,
                                genes=genes, edges=chrom.edges[:],
                                fusion_schema=chrom.fusion_schema.copy(),
                            )

        return population
