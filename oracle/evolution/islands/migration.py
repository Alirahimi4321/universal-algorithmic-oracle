"""Migration between islands in island model evolution."""
import random
from ...genome.chromosome import Chromosome

class MigrationManager:
    def __init__(self, config: dict = None):
        self.config = config or {}
        self.migration_rate = self.config.get("migration_rate", 0.1)
        self.migration_interval = self.config.get("migration_interval", 5)
        self.topology = self.config.get("topology", "ring")

    def migrate(self, islands: list[list[Chromosome]], generation: int) -> list[list[Chromosome]]:
        if generation % self.migration_interval != 0 or len(islands) < 2:
            return islands
        
        n_migrants = max(1, int(len(islands[0]) * self.migration_rate))
        
        if self.topology == "ring":
            migrated = self._ring_migration(islands, n_migrants)
        elif self.topology == "fully_connected":
            migrated = self._fully_connected_migration(islands, n_migrants)
        else:
            migrated = self._random_migration(islands, n_migrants)
        
        return migrated

    def _ring_migration(self, islands, n_migrants):
        n = len(islands)
        migrated = [list(island) for island in islands]
        for i in range(n):
            donors = sorted(migrated[i], key=lambda c: c.get_fitness_score(), reverse=True)[:n_migrants]
            migrated[(i + 1) % n].extend(donors)
        return migrated

    def _fully_connected_migration(self, islands, n_migrants):
        migrated = [list(island) for island in islands]
        for i in range(len(islands)):
            donors = sorted(migrated[i], key=lambda c: c.get_fitness_score(), reverse=True)[:n_migrants]
            for j in range(len(islands)):
                if i != j:
                    migrated[j].extend(donors[:1])
        return migrated

    def _random_migration(self, islands, n_migrants):
        migrated = [list(island) for island in islands]
        for i in range(len(islands)):
            donors = sorted(migrated[i], key=lambda c: c.get_fitness_score(), reverse=True)[:n_migrants]
            target = random.choice([j for j in range(len(islands)) if j != i])
            migrated[target].extend(donors)
        return migrated

    def select_migrants(self, island: list[Chromosome], n: int) -> list[Chromosome]:
        sorted_island = sorted(island, key=lambda c: c.get_fitness_score(), reverse=True)
        return sorted_island[:n]
