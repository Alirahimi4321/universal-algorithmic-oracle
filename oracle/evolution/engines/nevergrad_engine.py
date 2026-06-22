"""Nevergrad-based optimization engine."""
import random
try:
    import nevergrad as ng
    NEVERGRAD_AVAILABLE = True
except ImportError:
    NEVERGRAD_AVAILABLE = False

from ..population import PopulationManager
from ...evaluation.fitness import FitnessEvaluator
from ...symbolic.registry import list_systems
from .shared import create_chromosomes_from_positions, deap_fallback


class NevergradEngine:
    def __init__(self, config: dict = None):
        self.config = config or {}
        self.population_manager = PopulationManager(self.config)
        self.evaluator = FitnessEvaluator(config.get("fitness", {}))
        self.population = []
        self.best_history = []
        self.n_dim = self.config.get("n_dim", 10)
        self.budget = self.config.get("budget", 100)

    def _objective(self, x):
        return sum((xi - 0.5) ** 2 for xi in x) / len(x)

    def evolve(self, entropy_packet: dict, generations: int = 20):
        if not NEVERGRAD_AVAILABLE:
            return deap_fallback(entropy_packet, generations, self.config)

        try:
            systems = list(list_systems())
            n_dim = min(self.n_dim, len(systems))

            instrum = ng.p.Array(shape=(n_dim,), lower=0.0, upper=1.0)
            optimizer = ng.optimizers.OnePlusOne(parametrization=instrum, budget=self.budget)

            for _ in range(generations):
                x = optimizer.ask()
                loss = self._objective(x.value)
                optimizer.tell(x, loss)

            recommendation = optimizer.provide_recommendation()
            best_x = recommendation.value

            positions = [best_x.tolist()]
            for i in range(4):
                noise = [random.gauss(0, 0.05) for _ in range(n_dim)]
                positions.append([best_x[j] + noise[j] for j in range(n_dim)])

            results = create_chromosomes_from_positions(
                positions, systems, "nevergrad", self.evaluator, entropy_packet
            )
            self.best_history.extend(results)
            return results[:5]
        except Exception:
            return deap_fallback(entropy_packet, generations, self.config)
