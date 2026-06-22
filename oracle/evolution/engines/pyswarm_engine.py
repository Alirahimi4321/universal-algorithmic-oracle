"""pyswarms-based swarm intelligence engine."""
import random
try:
    import pyswarms as ps
    PSWARMS_AVAILABLE = True
except ImportError:
    PSWARMS_AVAILABLE = False

from ..population import PopulationManager
from ...evaluation.fitness import FitnessEvaluator
from ...symbolic.registry import list_systems
from .shared import create_chromosomes_from_positions, deap_fallback


class PySwarmEngine:
    def __init__(self, config: dict = None):
        self.config = config or {}
        self.population_manager = PopulationManager(self.config)
        self.evaluator = FitnessEvaluator(config.get("fitness", {}))
        self.population = []
        self.best_history = []
        self.n_particles = config.get("n_particles", 30)
        self.n_dim = config.get("n_dim", 10)

    def evolve(self, entropy_packet: dict, generations: int = 20):
        if not PSWARMS_AVAILABLE:
            return deap_fallback(entropy_packet, generations, self.config)

        try:
            systems = list(list_systems())
            n_dim = min(self.n_dim, len(systems))

            def objective(x):
                return [sum(row ** 2) / len(row) for row in x]

            options = {'c1': 1.5, 'c2': 1.5, 'w': 0.7}
            optimizer = ps.single.GlobalBestPSO(
                n_particles=self.n_particles,
                dimensions=n_dim,
                options=options,
            )
            cost, best_pos = optimizer.optimize(objective, iters=generations)

            positions = []
            for i in range(5):
                noise = [random.gauss(0, 0.1) for _ in range(n_dim)]
                positions.append([best_pos[j] + noise[j] for j in range(n_dim)])

            results = create_chromosomes_from_positions(
                positions, systems, "swarm", self.evaluator, entropy_packet, "swarm_fusion"
            )
            self.best_history.extend(results)
            return results[:5]
        except Exception:
            return deap_fallback(entropy_packet, generations, self.config)
