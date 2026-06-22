"""Mealpy-based metaheuristic engine."""
import random
try:
    from mealpy import PSO, GA
    MEALPY_AVAILABLE = True
except ImportError:
    MEALPY_AVAILABLE = False

from ..population import PopulationManager
from ...evaluation.fitness import FitnessEvaluator
from ...symbolic.registry import list_systems
from .shared import create_chromosomes_from_positions, deap_fallback


class MealpyEngine:
    def __init__(self, config: dict = None):
        self.config = config or {}
        self.population_manager = PopulationManager(self.config)
        self.evaluator = FitnessEvaluator(config.get("fitness", {}))
        self.population = []
        self.best_history = []
        self.n_dim = self.config.get("n_dim", 10)

    def _objective(self, x):
        return sum((xi - 0.5) ** 2 for xi in x) / len(x)

    def evolve(self, entropy_packet: dict, generations: int = 20):
        if not MEALPY_AVAILABLE:
            return deap_fallback(entropy_packet, generations, self.config)

        try:
            systems = list(list_systems())
            n_dim = min(self.n_dim, len(systems))

            problem = {"obj_func": self._objective, "bounds": [[0, 1]] * n_dim, "minmax": "min", "log_to": None}
            model = PSO(epoch=generations, pop_size=20, c1=2.05, c2=2.05, w=0.4)
            best_position, best_fitness = model.solve(problem)

            positions = [best_position.tolist() if hasattr(best_position, 'tolist') else list(best_position)]
            for i in range(4):
                noise = [random.gauss(0, 0.1) for _ in range(n_dim)]
                positions.append([positions[0][j] + noise[j] for j in range(n_dim)])

            results = create_chromosomes_from_positions(
                positions, systems, "mealpy", self.evaluator, entropy_packet
            )
            self.best_history.extend(results)
            return results[:5]
        except Exception:
            return deap_fallback(entropy_packet, generations, self.config)
