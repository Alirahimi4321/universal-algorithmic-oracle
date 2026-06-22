"""pyMetaheuristic-based engine - 400+ real optimization algorithms."""
import logging
import math
import random
try:
    import pymetaheuristic as pm
    PYMETAHEURISTIC_AVAILABLE = True
except ImportError:
    PYMETAHEURISTIC_AVAILABLE = False

from ..population import PopulationManager
from ...evaluation.fitness import FitnessEvaluator
from ...symbolic.registry import list_systems
from ...genome.gene import Gene
from ...genome.chromosome import Chromosome
from .shared import create_chromosomes_from_positions, deap_fallback

logger = logging.getLogger(__name__)

AVAILABLE_ALGORITHMS = [
    "pso", "ga", "de", "sa", "aco", "gwo", "woa", "sca",
    "mfo", "ffa", "bbo", "cmaes", "tso", "eo", "jso",
    "shade", "lshade", "jade", "sade", "mbo", "spo", "soa",
]


class PyMetaheuristicEngine:
    """Engine using pymetaheuristic's 400+ optimization algorithms."""

    def __init__(self, config: dict = None):
        self.config = config or {}
        self.population_manager = PopulationManager(self.config)
        self.evaluator = FitnessEvaluator(config.get("fitness", {}))
        self.population = []
        self.best_history = []
        self.n_dim = config.get("n_dim", 10)
        self.algorithm = config.get("algorithm", "pso")
        self.max_steps = config.get("max_steps", 20)
        self._cached_entropy = None
        self._cached_systems = None
        self._cached_numeric = None

    def _lightweight_fitness(self, position):
        """Fast fitness without full chromosome evaluation - uses numeric vector similarity."""
        numeric = self._cached_numeric
        if numeric is None or not position:
            return 0.0

        n = min(len(position), len(numeric))
        if n == 0:
            return 0.0

        total = 0.0
        for i in range(n):
            diff = abs(float(position[i]) - (numeric[i] % 100) / 100.0)
            total += math.exp(-diff * 3)

        diversity = len(set(round(p, 2) for p in position)) / max(len(position), 1)
        stability = 1.0 - min(1.0, sum(abs(position[i] - position[i-1]) for i in range(1, len(position))) / max(len(position), 1))

        return (total / n) * 0.6 + diversity * 0.2 + stability * 0.2

    def _target_function(self, position, entropy_packet, systems, engine_prefix):
        """Fast target function using lightweight fitness for optimizer, full eval for top candidates."""
        return self._lightweight_fitness(position)

    def evolve(self, entropy_packet: dict, generations: int = 20):
        if not PYMETAHEURISTIC_AVAILABLE:
            return deap_fallback(entropy_packet, generations, self.config)

        try:
            systems = list(list_systems())
            if not systems:
                return deap_fallback(entropy_packet, generations, self.config)

            self._cached_entropy = entropy_packet
            self._cached_systems = systems
            self._cached_numeric = entropy_packet.get("numeric_vector", [])

            n_dim = min(self.n_dim, len(systems))
            algorithm = self.algorithm if self.algorithm in AVAILABLE_ALGORITHMS else "pso"

            import functools
            target_fn = functools.partial(
                self._target_function,
                entropy_packet=entropy_packet,
                systems=systems,
                engine_prefix="pmh",
            )

            optimizer = pm.create_optimizer(
                algorithm=algorithm,
                target_function=target_fn,
                min_values=[-1.0] * n_dim,
                max_values=[1.0] * n_dim,
                objective="max",
                max_steps=self.max_steps,
                seed=random.randint(0, 99999),
                verbose=False,
            )

            result = optimizer.run()
            best_position = result.best_solution() if hasattr(result, 'best_solution') else None

            positions = []
            if best_position is not None:
                positions.append(best_position)
            if hasattr(result, 'population') and result.population is not None:
                pop = result.population
                if hasattr(pop, 'position') and pop.position is not None:
                    positions.extend(pop.position[:4])

            if not positions:
                return deap_fallback(entropy_packet, generations, self.config)

            return create_chromosomes_from_positions(
                positions, systems, "pmh", self.evaluator, entropy_packet,
            )

        except Exception as e:
            logger.warning("pymetaheuristic engine failed: %s, using DEAP fallback", e)
            return deap_fallback(entropy_packet, generations, self.config)
