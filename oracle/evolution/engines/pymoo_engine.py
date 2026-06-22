"""pymoo-based NSGA-II engine."""
import random
try:
    from pymoo.algorithms.moo.nsga2 import NSGA2
    from pymoo.core.problem import Problem
    from pymoo.optimize import minimize
    from pymoo.operators.crossover.sbx import SBX
    from pymoo.operators.mutation.pm import PM
    from pymoo.operators.sampling.lhs import LHS
    PYMOO_AVAILABLE = True
except ImportError:
    PYMOO_AVAILABLE = False

from ..population import PopulationManager
from ...evaluation.fitness import FitnessEvaluator
from ...symbolic.registry import list_systems
from .shared import create_chromosomes_from_positions, deap_fallback


class OracleProblem(Problem):
    def __init__(self, n_var=10, n_obj=2):
        super().__init__(n_var=n_var, n_obj=n_obj, xl=0.0, xu=1.0)

    def _evaluate(self, X, out, *args, **kwargs):
        F = []
        for x in X:
            f1 = sum((xi - 0.5) ** 2 for xi in x) / len(x)
            f2 = sum(abs(xi - 0.5) for xi in x) / len(x)
            F.append([f1, f2])
        out["F"] = F


class PyMOOEngine:
    def __init__(self, config: dict = None):
        self.config = config or {}
        self.population_manager = PopulationManager(self.config)
        self.evaluator = FitnessEvaluator(config.get("fitness", {}))
        self.population = []
        self.best_history = []
        self.n_var = self.config.get("n_var", 10)
        self.pop_size = self.config.get("population_size", 30)

    def evolve(self, entropy_packet: dict, generations: int = 20):
        if not PYMOO_AVAILABLE:
            return deap_fallback(entropy_packet, generations, self.config)

        try:
            systems = list(list_systems())
            n_var = min(self.n_var, len(systems))

            problem = OracleProblem(n_var=n_var)
            algorithm = NSGA2(
                pop_size=self.pop_size,
                sampling=LHS(),
                crossover=SBX(prob=0.9, eta=15),
                mutation=PM(eta=20),
            )
            res = minimize(problem, algorithm, ('n_gen', generations), seed=42, verbose=False)

            positions = []
            for x in res.X[:5]:
                positions.append(x.tolist() if hasattr(x, 'tolist') else list(x))

            results = create_chromosomes_from_positions(
                positions, systems, "nsga", self.evaluator, entropy_packet
            )

            for i, chrom in enumerate(results):
                if i < len(res.F):
                    chrom.fitness["mo_objective_1"] = float(res.F[i][0])
                    chrom.fitness["mo_objective_2"] = float(res.F[i][1])

            self.best_history.extend(results)
            return results[:5]
        except Exception:
            return deap_fallback(entropy_packet, generations, self.config)
