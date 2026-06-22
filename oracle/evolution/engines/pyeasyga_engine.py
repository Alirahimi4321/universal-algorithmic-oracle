"""pyeasyga-based simple GA engine."""
import random
try:
    import pyeasyga
    PYEASYGA_AVAILABLE = True
except ImportError:
    PYEASYGA_AVAILABLE = False

from ..population import PopulationManager
from ...evaluation.fitness import FitnessEvaluator
from ...symbolic.registry import list_systems
from .shared import create_chromosomes_from_positions, deap_fallback


class PyEasyGAEngine:
    def __init__(self, config: dict = None):
        self.config = config or {}
        self.population_manager = PopulationManager(self.config)
        self.evaluator = FitnessEvaluator(config.get("fitness", {}))
        self.population = []
        self.best_history = []
        self.pop_size = config.get("population_size", 50)

    def evolve(self, entropy_packet: dict, generations: int = 20):
        if not PYEASYGA_AVAILABLE:
            return deap_fallback(entropy_packet, generations, self.config)

        try:
            systems = list(list_systems())
            n_genes = min(len(systems), 10)

            def fitness_func(individual, data):
                ones = sum(individual)
                return ones

            seed_data = list(range(n_genes))
            ga = pyeasyga.GeneticAlgorithm(
                seed_data,
                population_size=self.pop_size,
                generations=generations,
                crossover_probability=0.8,
                mutation_probability=0.2,
                maximise_fitness=True,
            )
            ga.fitness_function = fitness_func
            ga.run()

            best = ga.best_individual()
            results = []
            for i in range(min(5, len(ga.last_population))):
                ind = ga.last_population[i]
                genes = {}
                edges = []
                for j, val in enumerate(ind[1]):
                    if j < len(systems):
                        from ...genome.gene import Gene
                        gene = Gene(
                            gene_id=f"easyga_{i}_{j}", system_id=systems[j], backend="internal",
                            params={"selected": bool(val)},
                            input_slots=[f"in_{j}"], output_slots=[f"out_{j}"],
                            weight=float(val),
                            mutation_policy={"flip_bit_rate": 0.1},
                        )
                        genes[gene.gene_id] = gene
                        if j > 0:
                            edges.append((f"easyga_{i}_{j-1}", gene.gene_id))

                if not genes:
                    continue

                from ...genome.chromosome import Chromosome
                chrom = Chromosome(
                    chromosome_id=f"easyga_{i}_{random.randint(0,99999)}",
                    genes=genes,
                    edges=edges,
                    fusion_schema={"type": "weighted_average"},
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
