"""Population management for evolutionary engines."""
import random
import math
from ..genome.chromosome import Chromosome
from ..genome.gene import Gene
from ..symbolic.registry import list_systems


class PopulationManager:
    def __init__(self, config: dict = None):
        self.config = config or {}
        self.size = self.config.get("population_size", 50)
        self.diversity_threshold = self.config.get("diversity_threshold", 0.3)

    def initialize_random(self, num_systems: int = None) -> list[Chromosome]:
        systems = list_systems()
        if not systems:
            return []
        population = []
        for i in range(self.size):
            n_genes = random.randint(2, min(num_systems or 6, len(systems)))
            selected = random.sample(systems, min(n_genes, len(systems)))
            genes = {}
            edges = []
            for j, sys_id in enumerate(selected):
                gene = Gene(
                    gene_id=f"g{i}_{j}",
                    system_id=sys_id,
                    backend="internal",
                    params={},
                    input_slots=[f"input_{j}"],
                    output_slots=[f"output_{j}"],
                    weight=random.uniform(0.1, 1.0),
                    mutation_policy={"param_mutation_rate": 0.1, "structural_mutation_rate": 0.05},
                )
                genes[gene.gene_id] = gene
                if j > 0:
                    prev_id = f"g{i}_{j-1}"
                    edges.append((prev_id, gene.gene_id))
            chrom = Chromosome(
                chromosome_id=f"chr_{i}_{random.randint(0, 99999)}",
                genes=genes,
                edges=edges,
                fusion_schema={"type": "weighted_average"},
                output_mapping={"output": list(genes.keys())[-1] if genes else ""},
            )
            population.append(chrom)
        return population

    def measure_diversity(self, population: list[Chromosome]) -> float:
        if len(population) < 2:
            return 0.0
        system_counts = {}
        total_genes = 0
        for chrom in population:
            for gene in chrom.gene_list:
                system_counts[gene.system_id] = system_counts.get(gene.system_id, 0) + 1
                total_genes += 1
        if total_genes == 0:
            return 0.0
        probs = [count / total_genes for count in system_counts.values()]
        entropy = -sum(p * math.log2(p) for p in probs if p > 0)
        max_entropy = math.log2(len(system_counts)) if system_counts else 1
        return entropy / max_entropy if max_entropy > 0 else 0.0

    def inject_random(self, population: list[Chromosome], count: int = 5) -> list[Chromosome]:
        new_random = self.initialize_random(count)
        return population + new_random
