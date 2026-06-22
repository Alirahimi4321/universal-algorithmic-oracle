"""geneticalgorithm2-based optimization engine."""
import random
try:
    from geneticalgorithm2 import geneticalgorithm2 as ga2
    GA2_AVAILABLE = True
except ImportError:
    GA2_AVAILABLE = False

from ..population import PopulationManager
from ...evaluation.fitness import FitnessEvaluator
from ...symbolic.registry import list_systems
from .shared import create_chromosomes_from_positions, deap_fallback


class GeneticAlgorithm2Engine:
    def __init__(self, config: dict = None):
        self.config = config or {}
        self.population_manager = PopulationManager(self.config)
        self.evaluator = FitnessEvaluator(config.get("fitness", {}))
        self.population = []
        self.best_history = []
        self.n_var = self.config.get("n_var", 10)
        self.max_num_iteration = self.config.get("max_num_iteration", 50)

    def evolve(self, entropy_packet: dict, generations: int = 20):
        if not GA2_AVAILABLE:
            return deap_fallback(entropy_packet, generations, self.config)

        try:
            systems = list(list_systems())
            n_var = min(self.n_var, len(systems))

            def fitness_func(X):
                score = sum(X) / len(X)
                diversity = len(set(int(x * 10) for x in X)) / len(X)
                return -(score * 0.7 + diversity * 0.3)

            varbound = [[0.0, 1.0]] * n_var
            vartype = [[0, 1]] * n_var
            model = ga2(
                fitness_function=fitness_func,
                variable_type_mixed=vartype,
                variable_boundaries=varbound,
                max_num_iteration=min(generations, self.max_num_iteration),
                population_size=20,
                algorithm_parameters={
                    'max_num_iteration': min(generations, self.max_num_iteration),
                    'population_size': 20,
                    'mutation_probability': 0.1,
                    'elit_ratio': 0.1,
                    'crossover_probability': 0.7,
                    'parents_portion': 0.3,
                    'crossover_type': 'uniform',
                    'max_iteration_without_improv': None,
                },
            )
            model.run()
            best_vars = model.result['best_variable']

            positions = [best_vars.tolist() if hasattr(best_vars, 'tolist') else list(best_vars)]
            for i in range(4):
                noise = [random.gauss(0, 0.1) for _ in range(n_var)]
                positions.append([positions[0][j] + noise[j] for j in range(n_var)])

            results = create_chromosomes_from_positions(
                positions, systems, "ga2", self.evaluator, entropy_packet
            )
            self.best_history.extend(results)
            return results[:5]
        except Exception:
            return deap_fallback(entropy_packet, generations, self.config)
