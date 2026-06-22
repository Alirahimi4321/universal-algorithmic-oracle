"""Quality-Diversity optimization using pyribs MAP-Elites."""
from __future__ import annotations
import logging
import numpy as np
from typing import Any

logger = logging.getLogger(__name__)

try:
    from ribs.archives import GridArchive
    from ribs.emitters import GaussianEmitter
    from ribs.schedulers import Scheduler
    HAS_RIBS = True
except Exception:
    HAS_RIBS = False


class QualityDiversityOptimizer:
    """MAP-Elites based quality-diversity search for oracle strategies."""

    def __init__(self) -> None:
        self.available = HAS_RIBS

    def search(self, solution_dim: int = 5, behavior_dims: tuple = (20, 20),
               behavior_ranges: tuple = ((-1.0, 1.0), (-1.0, 1.0)),
               num_emitters: int = 3, sigma: float = 0.1, batch_size: int = 32,
               iterations: int = 100, objective_fn=None) -> dict[str, Any]:
        if not self.available:
            return {"method": "unavailable", "archive_size": 0}
        try:
            archive = GridArchive(dims=list(behavior_dims), ranges=list(behavior_ranges), solution_dim=solution_dim)
            bounds = [(-1.0, 1.0)] * solution_dim
            initial_solutions = [np.random.randn(solution_dim) for _ in range(num_emitters * batch_size)]
            emitters = [GaussianEmitter(archive, sigma=sigma, initial_solutions=initial_solutions,
                         batch_size=batch_size, bounds=bounds, seed=i) for i in range(num_emitters)]
            scheduler = Scheduler(archive, emitters)
            for _ in range(iterations):
                sols = scheduler.ask()
                if objective_fn is not None:
                    objs = [objective_fn(s) for s in sols]
                else:
                    objs = [float(np.random.rand()) for _ in sols]
                bcs = [s[:2] if len(s) >= 2 else [0, 0] for s in sols]
                scheduler.tell(objs, bcs)
            return {"archive_size": len(archive), "method": "map_elites",
                    "best_obj": round(float(archive.stats.obj_max) if len(archive) > 0 else 0, 4),
                    "coverage": round(float(len(archive) / max(np.prod(behavior_dims), 1)), 4)}
        except Exception as e:
            return {"method": "failed", "error": str(e)}

    def discover_diverse_oracles(self, systems: list[str], iterations: int = 50) -> dict[str, Any]:
        if not self.available:
            return {"solutions": [], "method": "unavailable"}
        def objective(solution):
            weights = np.abs(solution)
            weights = weights / max(np.sum(weights), 1e-10)
            return float(-np.std(weights) + np.mean(weights))
        result = self.search(solution_dim=len(systems), behavior_dims=(min(20, len(systems)), min(20, len(systems))),
                            behavior_ranges=((-1.0, 1.0),) * 2, iterations=iterations, objective_fn=objective)
        return {"method": "quality_diversity", "archive_size": result.get("archive_size", 0),
                "coverage": result.get("coverage", 0), "best_obj": result.get("best_obj", 0)}
