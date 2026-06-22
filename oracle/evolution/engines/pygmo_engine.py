"""PyGMO-based island model engine."""
import random
try:
    import pygmo as pg
    PYGMO_AVAILABLE = True
except ImportError:
    PYGMO_AVAILABLE = False

from ..population import PopulationManager
from ...evaluation.fitness import FitnessEvaluator
from ...symbolic.registry import list_systems
from .shared import create_chromosomes_from_positions, deap_fallback


class SimpleProblem:
    def __init__(self, n=10):
        self.n = n
        self.lb = [0.0] * n
        self.ub = [1.0] * n

    def fitness(self, x):
        f1 = sum((xi - 0.5) ** 2 for xi in x) / len(x)
        f2 = sum(abs(xi - 0.5) for xi in x) / len(x)
        return [f1, f2]

    def get_bounds(self):
        return (self.lb, self.ub)

    def get_nobj(self):
        return 2


class PyGMOEngine:
    def __init__(self, config: dict = None):
        self.config = config or {}
        self.population_manager = PopulationManager(self.config)
        self.evaluator = FitnessEvaluator(config.get("fitness", {}))
        self.population = []
        self.best_history = []
        self.n_islands = self.config.get("n_islands", 4)
        self.pop_size = self.config.get("population_size", 20)

    def evolve(self, entropy_packet: dict, generations: int = 20):
        if not PYGMO_AVAILABLE:
            return deap_fallback(entropy_packet, generations, self.config)

        try:
            systems = list(list_systems())
            n_dim = min(10, len(systems))

            prob = pg.problem(SimpleProblem(n=n_dim))
            islands = []
            for i in range(self.n_islands):
                algo = pg.algorithm(pg.nsga2(gen=max(generations // self.n_islands, 5)))
                isl = pg.island(algo=algo, prob=prob, size=self.pop_size)
                islands.append(isl)

            archi = pg.archipelago(islands)
            archi.evolve(n_gen=generations)
            archi.wait()

            positions = []
            for isl in archi:
                pop = isl.population
                for j in range(min(2, len(pop))):
                    x = pop.get_x()[j]
                    positions.append(x.tolist() if hasattr(x, 'tolist') else list(x))

            results = create_chromosomes_from_positions(
                positions[:5], systems, "pygmo", self.evaluator, entropy_packet
            )
            self.best_history.extend(results)
            return results[:5]
        except Exception:
            return deap_fallback(entropy_packet, generations, self.config)
