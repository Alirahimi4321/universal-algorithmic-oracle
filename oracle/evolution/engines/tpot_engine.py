"""TPOT-based AutoML pipeline evolution engine."""
import random
try:
    from tpot import TPOTClassifier
    TPOT_AVAILABLE = True
except ImportError:
    TPOT_AVAILABLE = False

from ..population import PopulationManager
from ...evaluation.fitness import FitnessEvaluator
from ...symbolic.registry import list_systems
from .shared import create_chromosomes_from_positions, deap_fallback


class TpotEngine:
    def __init__(self, config: dict = None):
        self.config = config or {}
        self.population_manager = PopulationManager(self.config)
        self.evaluator = FitnessEvaluator(config.get("fitness", {}))
        self.population = []
        self.best_history = []
        self.generations = config.get("generations", 5)

    def evolve(self, entropy_packet: dict, generations: int = 20):
        if not TPOT_AVAILABLE:
            return deap_fallback(entropy_packet, generations, self.config)

        try:
            import numpy as np
            systems = list(list_systems())
            n_features = min(len(systems), 10)

            rng = np.random.RandomState(42)
            X_train = rng.rand(100, n_features)
            y_train = (X_train.sum(axis=1) > n_features / 2).astype(int)

            tpot = TPOTClassifier(
                generations=min(generations, self.generations),
                population_size=20,
                verbosity=0,
                random_state=42,
                n_jobs=1,
            )
            tpot.fit(X_train, y_train)

            pipeline_str = str(tpot.fitted_pipeline_)[:100] if hasattr(tpot, 'fitted_pipeline') else ""

            results = []
            for i in range(5):
                genes = {}
                edges = []
                for j in range(n_features):
                    sys_id = systems[j % len(systems)]
                    from ...genome.gene import Gene
                    gene = Gene(
                        gene_id=f"tpot_{i}_{j}", system_id=sys_id, backend="internal",
                        params={"pipeline": pipeline_str},
                        input_slots=[f"in_{j}"], output_slots=[f"out_{j}"],
                        weight=0.5,
                        mutation_policy={"param_mutation_rate": 0.1},
                    )
                    genes[gene.gene_id] = gene
                    if j > 0:
                        edges.append((f"tpot_{i}_{j-1}", gene.gene_id))

                if not genes:
                    continue

                from ...genome.chromosome import Chromosome
                chrom = Chromosome(
                    chromosome_id=f"tpot_{i}_{random.randint(0,99999)}",
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
