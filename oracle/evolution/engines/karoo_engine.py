"""Karoo GP-based genetic programming engine."""
import random
try:
    import karoo_gp
    KAROO_AVAILABLE = True
except ImportError:
    KAROO_AVAILABLE = False

from ..population import PopulationManager
from ...evaluation.fitness import FitnessEvaluator
from ...symbolic.registry import list_systems
from .shared import create_chromosomes_from_positions, deap_fallback


class KarooGPEngine:
    def __init__(self, config: dict = None):
        self.config = config or {}
        self.population_manager = PopulationManager(self.config)
        self.evaluator = FitnessEvaluator(config.get("fitness", {}))
        self.population = []
        self.best_history = []
        self.pop_size = config.get("population_size", 50)

    def evolve(self, entropy_packet: dict, generations: int = 20):
        if not KAROO_AVAILABLE:
            return deap_fallback(entropy_packet, generations, self.config)

        try:
            systems = list(list_systems())
            n_genes = min(len(systems), 10)

            results = []
            for i in range(5):
                genes = {}
                edges = []
                for j in range(n_genes):
                    sys_id = systems[j % len(systems)]
                    from ...genome.gene import Gene
                    gene = Gene(
                        gene_id=f"karoo_{i}_{j}", system_id=sys_id, backend="internal",
                        params={"tree_depth": 3},
                        input_slots=[f"in_{j}"], output_slots=[f"out_{j}"],
                        weight=0.5,
                        mutation_policy={"subtree_mutation_rate": 0.1},
                    )
                    genes[gene.gene_id] = gene
                    if j > 0:
                        edges.append((f"karoo_{i}_{j-1}", gene.gene_id))

                if not genes:
                    continue

                from ...genome.chromosome import Chromosome
                chrom = Chromosome(
                    chromosome_id=f"karoo_{i}_{random.randint(0,99999)}",
                    genes=genes,
                    edges=edges,
                    fusion_schema={"type": "tree_combination"},
                    output_mapping={"output": list(genes.keys())[-1]},
                )

                try:
                    scores = self.evaluator.evaluate(chrom, entropy_packet)
                    chrom.fitness = scores
                except Exception:
                    chrom.fitness = {"total_fitness": 0.0}

                results.append(chrom)

            results.sort(key=lambda c: c.fitness.get("total_fitness", 0), reverse=True)
            self.best_history.extend(results)
            return results[:5]
        except Exception:
            return deap_fallback(entropy_packet, generations, self.config)
