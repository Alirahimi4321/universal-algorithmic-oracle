"""DirectSearch engine: Direct search optimization methods."""
from __future__ import annotations

import random
import uuid
import logging
import numpy as np
from typing import Any

logger = logging.getLogger(__name__)

try:
    from directsearch import solve_directsearch
    HAS_DIRECTSEARCH = True
except ImportError:
    HAS_DIRECTSEARCH = False
    logger.info("directsearch not available")


class DirectSearchEngine:
    """Optimization engine using DirectSearch methods."""

    def __init__(self, config: dict | None = None) -> None:
        self.config = config or {}
        self.id = str(uuid.uuid4())[:8]

    def run(self, population_size: int = 50, generations: int = 100,
            bounds: list[tuple[float, float]] | None = None,
            **kwargs: Any) -> dict[str, Any]:
        if not HAS_DIRECTSEARCH:
            return {"error": "directsearch not available", "engine": "directsearch"}

        bounds = bounds or [(-5.0, 5.0)] * 5
        dim = len(bounds)

        def objective(x):
            return sum(xi ** 2 for xi in x)

        x0 = [random.uniform(b[0], b[1]) for b in bounds]
        maxevals = self.config.get("maxevals", population_size * generations)

        try:
            result = solve_directsearch(objective, x0, maxevals=maxevals, verbose=False)
            optimal_x = list(result.x) if hasattr(result, "x") else x0
            optimal_val = float(result.f) if hasattr(result, "f") else objective(optimal_x)

            return {
                "engine": "directsearch",
                "engine_id": self.id,
                "best_fitness": optimal_val,
                "generations_run": 1,
                "population_size": population_size,
                "optimal_x": optimal_x,
                "converged": True,
            }
        except Exception as e:
            logger.warning("directsearch engine failed: %s", e)
            return {"error": str(e), "engine": "directsearch"}
