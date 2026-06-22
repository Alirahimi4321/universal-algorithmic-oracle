"""NiaPy-based nature-inspired algorithm engine."""
import random
try:
    from niapy.algorithms.basic import DifferentialEvolution, ParticleSwarmOptimization
    NIAPY_AVAILABLE = True
except ImportError:
    NIAPY_AVAILABLE = False

from ..population import PopulationManager
from ...evaluation.fitness import FitnessEvaluator
from ...symbolic.registry import list_systems
from .shared import create_chromosomes_from_positions, deap_fallback


class NiaPyEngine:
    def __init__(self, config: dict = None):
        self.config = config or {}
        self.population_manager = PopulationManager(self.config)
        self.evaluator = FitnessEvaluator(config.get("fitness", {}))
        self.population = []
        self.best_history = []
        self.n_dim = config.get("n_dim", 10)
        self.algo = config.get("algorithm", "DE")

    def evolve(self, entropy_packet: dict, generations: int = 20):
        if not NIAPY_AVAILABLE:
            return deap_fallback(entropy_packet, generations, self.config)

        try:
            from niapy.task import Task
            from niapy.problems import Problem

            systems = list(list_systems())
            n_dim = min(self.n_dim, len(systems))

            class OracleProblem(Problem):
                def __init__(self, n):
                    super().__init__(n, 0.0, 1.0)

                def _evaluate(self, x):
                    return sum(x ** 2) / len(x)

            task = Task(problem=OracleProblem(n_dim), max_iters=generations)

            if self.algo == "DE":
                algo = DifferentialEvolution(population_size=30)
            else:
                algo = ParticleSwarmOptimization(population_size=30, c1=1.5, c2=1.5, w=0.7)

            best_pos, best_cost = algo.run(task)

            positions = [best_pos.tolist()]
            for i in range(4):
                noise = [random.gauss(0, 0.1) for _ in range(n_dim)]
                positions.append([best_pos[j] + noise[j] for j in range(n_dim)])

            results = create_chromosomes_from_positions(
                positions, systems, "niapy", self.evaluator, entropy_packet, "nature_inspired"
            )
            self.best_history.extend(results)
            return results[:5]
        except Exception:
            return deap_fallback(entropy_packet, generations, self.config)
