"""evosax-based evolution strategies engine."""
import random
try:
    from evosax import OpenES, SimpleGA, CMA_ES
    EVOSAX_AVAILABLE = True
except ImportError:
    EVOSAX_AVAILABLE = False

from ..population import PopulationManager
from ...evaluation.fitness import FitnessEvaluator
from ...symbolic.registry import list_systems
from .shared import create_chromosomes_from_positions, deap_fallback


class EvosaxEngine:
    def __init__(self, config: dict = None):
        self.config = config or {}
        self.population_manager = PopulationManager(self.config)
        self.evaluator = FitnessEvaluator(config.get("fitness", {}))
        self.population = []
        self.best_history = []
        self.n_dim = config.get("n_dim", 10)
        self.algo = config.get("algorithm", "OpenES")

    def evolve(self, entropy_packet: dict, generations: int = 20):
        if not EVOSAX_AVAILABLE:
            return deap_fallback(entropy_packet, generations, self.config)

        try:
            import jax
            import jax.numpy as jnp
            systems = list(list_systems())
            n_dim = min(self.n_dim, len(systems))

            def objective(params):
                return jnp.sum(params ** 2) / n_dim

            if self.algo == "OpenES":
                strategy = OpenES(pop_size=30, n_dim=n_dim, maximize=False)
            elif self.algo == "SimpleGA":
                strategy = SimpleGA(pop_size=30, n_dim=n_dim, maximize=False)
            else:
                strategy = CMA_ES(pop_size=30, n_dim=n_dim, maximize=False)

            key = jax.random.PRNGKey(42)
            state = strategy.init_params()
            for gen in range(generations):
                key, subkey = jax.random.split(key)
                keys = jax.random.split(subkey, 30)
                offspring = strategy.ask(keys, state)
                fitness = jnp.array([objective(ind) for ind in offspring])
                state = strategy.tell(offspring, fitness, state)

            best_params = strategy.best_params(state)

            positions = []
            for i in range(5):
                noise = [random.gauss(0, 0.05) for _ in range(n_dim)]
                positions.append([float(best_params[j]) + noise[j] for j in range(n_dim)])

            results = create_chromosomes_from_positions(
                positions, systems, "evosax", self.evaluator, entropy_packet, "evolution_strategy"
            )
            self.best_history.extend(results)
            return results[:5]
        except Exception:
            return deap_fallback(entropy_packet, generations, self.config)
