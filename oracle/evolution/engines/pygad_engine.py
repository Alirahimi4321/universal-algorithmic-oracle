"""pygad-based GA engine."""
import random
try:
    import pygad
    PYGAD_AVAILABLE = True
except ImportError:
    PYGAD_AVAILABLE = False

from ..population import PopulationManager
from ...evaluation.fitness import FitnessEvaluator
from ...symbolic.registry import list_systems
from .shared import create_chromosomes_from_positions, deap_fallback


class PyGADEngine:
    def __init__(self, config: dict = None):
        self.config = config or {}
        self.population_manager = PopulationManager(self.config)
        self.evaluator = FitnessEvaluator(config.get("fitness", {}))
        self.population = []
        self.best_history = []
        self.n_dim = config.get("n_dim", 10)

    def evolve(self, entropy_packet: dict, generations: int = 20):
        if not PYGAD_AVAILABLE:
            return deap_fallback(entropy_packet, generations, self.config)

        try:
            systems = list(list_systems())
            n_dim = min(self.n_dim, len(systems))

            def fitness_func(ga_instance, solution, solution_idx):
                return 1.0 / (1.0 + sum(x ** 2 for x in solution))

            ga = pygad.GA(
                num_generations=generations,
                num_parents_mating=5,
                fitness_func=fitness_func,
                sol_per_pop=30,
                num_genes=n_dim,
                init_range_low=-1.0,
                init_range_high=1.0,
                mutation_percent_genes=20,
            )
            ga.run()
            best_solution, best_fitness, _ = ga.best_solution()

            positions = [best_solution.tolist()]
            for i in range(4):
                noise = [random.gauss(0, 0.1) for _ in range(n_dim)]
                positions.append([best_solution[j] + noise[j] for j in range(n_dim)])

            results = create_chromosomes_from_positions(
                positions, systems, "pygad", self.evaluator, entropy_packet
            )
            self.best_history.extend(results)
            return results[:5]
        except Exception:
            return deap_fallback(entropy_packet, generations, self.config)
