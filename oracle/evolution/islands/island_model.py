"""Island Model for parallel evolution of different symbolic system families."""
import random
import uuid
from typing import Callable
from ...genome.chromosome import Chromosome
from ..deap_engine import EvolutionaryEngine
from ...evaluation.fitness import FitnessEvaluator


ISLAND_FAMILIES = {
    "western": [("gematria", "internal"), ("calendar", "internal")],
    "eastern": [("iching", "internal"), ("calendar", "internal")],
    "binary": [("iching", "internal"), ("geomancy", "internal")],
    "letter_number": [("gematria", "internal"), ("numerology", "internal")],
    "hybrid": [("gematria", "internal"), ("iching", "internal"), ("geomancy", "internal")],
}


class Island:
    def __init__(self, island_id: str, systems: list[tuple[str, str]], config: dict | None = None):
        self.island_id = island_id
        self.systems = systems
        self.config = config or {}
        self.engine = EvolutionaryEngine(self.config)
        self.engine.population_size = self.config.get("population_size", 20)
        self.migrants: list[Chromosome] = []

    def initialize(self):
        self.engine.initialize_population(self.systems)

    def evolve(self, entropy_packet: dict, generations: int = 10):
        self.engine.evolve(entropy_packet, generations=generations)

    def get_migrants(self, count: int = 3) -> list[Chromosome]:
        return self.engine.get_elite(count)

    def receive_migrants(self, migrants: list[Chromosome]):
        self.migrants.extend(migrants)
        if len(self.engine.population) > 0:
            worst = sorted(
                self.engine.population,
                key=lambda c: c.fitness.get("total_fitness", 0),
            )[:len(migrants)]
            for w in worst:
                if migrants:
                    idx = self.engine.population.index(w)
                    self.engine.population[idx] = migrants.pop(0)

    def get_best(self) -> Chromosome | None:
        return self.engine.get_best()

    def get_population(self) -> list[Chromosome]:
        return self.engine.population


class IslandModel:
    def __init__(self, config: dict | None = None):
        config = config or {}
        self.config = config
        self.num_islands = config.get("num_islands", 4)
        self.migration_interval = config.get("migration_interval", 10)
        self.migration_rate = config.get("migration_rate", 0.1)
        self.islands: list[Island] = []
        self.generation = 0
        self.evaluator = FitnessEvaluator(config.get("fitness", {}))
        self.best_history: list[dict] = []

    def initialize(self):
        families = list(ISLAND_FAMILIES.keys())
        for i in range(self.num_islands):
            family = families[i % len(families)]
            systems = ISLAND_FAMILIES[family]
            island = Island(
                island_id=f"island_{family}",
                systems=systems,
                config=self.config,
            )
            island.initialize()
            self.islands.append(island)

    def evolve(
        self,
        entropy_packet: dict,
        generations: int = 50,
        callback: Callable | None = None,
    ) -> list[Chromosome]:
        for gen in range(generations):
            self.generation = gen + 1

            for island in self.islands:
                island.evolve(entropy_packet, generations=1)

            if self.generation % self.migration_interval == 0:
                self._migrate()

            best_per_island = []
            for island in self.islands:
                best = island.get_best()
                if best:
                    best_per_island.append(best)

            if best_per_island:
                avg_fitness = sum(
                    b.fitness.get("total_fitness", 0) for b in best_per_island
                ) / len(best_per_island)
                self.best_history.append({
                    "generation": self.generation,
                    "avg_best_fitness": avg_fitness,
                    "island_count": len(self.islands),
                })

            if callback:
                all_pop = []
                for island in self.islands:
                    all_pop.extend(island.get_population())
                callback(self.generation, all_pop, [])

        all_population = []
        for island in self.islands:
            all_population.extend(island.get_population())

        return sorted(
            all_population,
            key=lambda c: c.fitness.get("total_fitness", 0),
            reverse=True,
        )

    def _migrate(self):
        migrants_per_island = max(1, int(len(self.islands[0].get_population()) * self.migration_rate))

        all_migrants = []
        for island in self.islands:
            migrants = island.get_migrants(migrants_per_island)
            all_migrants.append(migrants)

        for i, island in enumerate(self.islands):
            incoming = []
            for j, migrant_list in enumerate(all_migrants):
                if i != j and migrant_list:
                    incoming.append(migrant_list[0])
            island.receive_migrants(incoming[:migrants_per_island])

    def get_best_global(self) -> Chromosome | None:
        best = None
        for island in self.islands:
            island_best = island.get_best()
            if island_best and (best is None or
                island_best.fitness.get("total_fitness", 0) > best.fitness.get("total_fitness", 0)):
                best = island_best
        return best

    def get_all_population(self) -> list[Chromosome]:
        all_pop = []
        for island in self.islands:
            all_pop.extend(island.get_population())
        return all_pop
