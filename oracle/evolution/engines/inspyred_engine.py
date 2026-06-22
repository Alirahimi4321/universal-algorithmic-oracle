"""inspyred-based evolutionary engine."""
import random
try:
    import inspyred
    INSPYRED_AVAILABLE = True
except ImportError:
    INSPYRED_AVAILABLE = False

from ..population import PopulationManager
from ...evaluation.fitness import FitnessEvaluator
from ...symbolic.registry import list_systems
from .shared import create_chromosomes_from_positions, deap_fallback


class InspyredEngine:
    def __init__(self, config: dict = None):
        self.config = config or {}
        self.population_manager = PopulationManager(self.config)
        self.evaluator = FitnessEvaluator(config.get("fitness", {}))
        self.population = []
        self.best_history = []
        self.pop_size = config.get("population_size", 50)

    def evolve(self, entropy_packet: dict, generations: int = 20):
        if not INSPYRED_AVAILABLE:
            return deap_fallback(entropy_packet, generations, self.config)

        try:
            systems = list(list_systems())
            n_genes = min(len(systems), 10)

            rng = random.Random(42)
            ec = inspyred.ec.GA(rng)
            ec.terminator = inspyred.ec.generators.generation_termination(generations)

            def generator(random, args):
                return [random.random() for _ in range(n_genes)]

            def evaluator(candidates, args):
                fitness = []
                for cand in candidates:
                    score = sum(cand) / len(cand)
                    diversity = len(set(int(x * 10) for x in cand)) / len(cand)
                    fitness.append(score * 0.7 + diversity * 0.3)
                return fitness

            final_pop = ec.evolve(
                generator=generator,
                evaluator=evaluator,
                pop_size=self.pop_size,
                maximize=True,
            )

            positions = []
            for ind in sorted(final_pop, key=lambda x: x.fitness, reverse=True)[:5]:
                positions.append(ind.candidate)

            results = create_chromosomes_from_positions(
                positions, systems, "inspyred", self.evaluator, entropy_packet
            )
            self.best_history.extend(results)
            return results[:5]
        except Exception:
            return deap_fallback(entropy_packet, generations, self.config)
