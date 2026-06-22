"""Evolution strategy base class and imports for concrete engines."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any

# Existing utility imports (kept for backward compatibility)
from .mutation import param_mutation, structural_mutation
from .crossover import uniform_crossover
from .islands import MigrationManager, IslandScheduler
from .meta_selector import MetaOracleSelector

from .parallel_evaluator import ParallelEvaluator
from .neural_evaluator import NeuralEvaluator

__all__ = [
    "EvolutionStrategy",
    "param_mutation",
    "structural_mutation",
    "uniform_crossover",
    "MigrationManager",
    "IslandScheduler",
    "MetaOracleSelector",
    "ParallelEvaluator",
    "NeuralEvaluator",
]


class EvolutionStrategy(ABC):
    """Abstract base for all evolutionary engines.

    Concrete engines (GA, GP, NSGA, etc.) must implement:
    * ``initialize_population`` – create the initial pool of genomes.
    * ``evolve`` – run the evolution for a given number of generations and
      return a list of best genomes (ordered by fitness).
    * ``best_history`` – a list that records the best genome of each generation.
    """

    def __init__(self, config: Dict[str, Any] | None = None):
        self.config = config or {}
        self.population: List[Any] = []
        self.best_history: List[Any] = []

    @abstractmethod
    def initialize_population(self) -> None:
        """Create the initial population and store it in ``self.population``."""

    @abstractmethod
    def evolve(self, ep_dict: Dict[str, Any], generations: int) -> List[Any]:
        """Run the evolutionary loop.

        Parameters
        ----------
        ep_dict: dict
            The encoded entropy packet dictionary.
        generations: int
            Number of generations to run.

        Returns
        -------
        List[Any]
            List of genomes ordered from best to worst.
        """

    def _record_best(self, best) -> None:
        """Utility to store the best genome of the current generation."""
        self.best_history.append(best)
