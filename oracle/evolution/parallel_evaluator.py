"""Parallel fitness evaluation using joblib for multi-core processing."""
import logging
import time
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)

try:
    from joblib import Parallel, delayed
    HAS_JOBLIB = True
except ImportError:
    HAS_JOBLIB = False
    logger.info("joblib not available, parallel evaluation disabled")


class ParallelEvaluator:
    """Evaluates population fitness in parallel using joblib.

    Falls back to sequential evaluation if joblib is unavailable or fails.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        config = config or {}
        self.default_n_jobs = config.get("n_jobs", -1)
        self.backend = config.get("backend", "loky")
        self.verbose = config.get("verbose", 0)
        self.evaluation_count = 0
        self.total_time = 0.0

    def evaluate_population(
        self,
        population: list,
        evaluator: Callable,
        entropy_packet: dict,
        n_jobs: int = -1,
    ) -> list:
        """Evaluate fitness for all individuals in the population.

        Parameters
        ----------
        population : list
            List of chromosome/genome objects to evaluate.
        evaluator : callable
            Function that takes (individual, entropy_packet) and returns a fitness dict.
        entropy_packet : dict
            The entropy packet to pass to the evaluator.
        n_jobs : int
            Number of parallel jobs. -1 means use all cores.

        Returns
        -------
        list
            Population with fitness scores assigned.
        """
        if not population:
            return []

        n_jobs = n_jobs if n_jobs != 0 else self.default_n_jobs
        start_time = time.time()

        if not HAS_JOBLIB:
            logger.debug("joblib unavailable, falling back to sequential evaluation")
            return self._evaluate_sequential(population, evaluator, entropy_packet)

        try:
            results = self._evaluate_parallel(population, evaluator, entropy_packet, n_jobs)
            elapsed = time.time() - start_time
            self.evaluation_count += len(population)
            self.total_time += elapsed
            logger.debug(
                "Parallel evaluation: %d individuals in %.3fs (%d jobs)",
                len(population), elapsed, abs(n_jobs),
            )
            return results
        except Exception as e:
            logger.warning(
                "Parallel evaluation failed (%s), falling back to sequential", e
            )
            return self._evaluate_sequential(population, evaluator, entropy_packet)

    def _evaluate_parallel(
        self,
        population: list,
        evaluator: Callable,
        entropy_packet: dict,
        n_jobs: int,
    ) -> list:
        """Run parallel evaluation with joblib."""
        delayed_funcs = [
            delayed(self._eval_single)(ind, evaluator, entropy_packet)
            for ind in population
        ]
        parallel = Parallel(
            n_jobs=n_jobs,
            backend=self.backend,
            verbose=self.verbose,
        )
        results = parallel(delayed_funcs)

        for ind, fitness in zip(population, results):
            ind.fitness = fitness

        return population

    def _evaluate_sequential(
        self,
        population: list,
        evaluator: Callable,
        entropy_packet: dict,
    ) -> list:
        """Sequential fallback evaluation."""
        for ind in population:
            try:
                ind.fitness = evaluator(ind, entropy_packet)
            except Exception as e:
                logger.warning("Evaluation failed for individual: %s", e)
                ind.fitness = {"total_fitness": 0.0}
        return population

    @staticmethod
    def _eval_single(individual, evaluator: Callable, entropy_packet: dict) -> dict:
        """Evaluate a single individual (used as joblib delayed target)."""
        try:
            return evaluator(individual, entropy_packet)
        except Exception as e:
            return {"total_fitness": 0.0, "error": str(e)}

    def get_stats(self) -> dict:
        """Return evaluation statistics."""
        avg_time = self.total_time / max(self.evaluation_count, 1)
        return {
            "total_evaluations": self.evaluation_count,
            "total_time": self.total_time,
            "avg_time_per_eval": avg_time,
            "joblib_available": HAS_JOBLIB,
        }
