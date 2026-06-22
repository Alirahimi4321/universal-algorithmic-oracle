"""Island evolution scheduler."""
import time

class IslandScheduler:
    def __init__(self, config: dict = None):
        self.config = config or {}
        self.max_generations = self.config.get("max_generations", 100)
        self.convergence_threshold = self.config.get("convergence_threshold", 0.01)
        self.patience = self.config.get("patience", 10)
        self.best_fitness_history = []
        self.no_improvement_count = 0

    def should_continue(self, generation: int, best_fitness: float) -> bool:
        if generation >= self.max_generations:
            return False
        self.best_fitness_history.append(best_fitness)
        if len(self.best_fitness_history) > 1:
            improvement = abs(self.best_fitness_history[-1] - self.best_fitness_history[-2])
            if improvement < self.convergence_threshold:
                self.no_improvement_count += 1
            else:
                self.no_improvement_count = 0
        if self.no_improvement_count >= self.patience:
            return False
        return True

    def get_schedule(self, n_islands: int) -> list[dict]:
        schedule = []
        for i in range(n_islands):
            schedule.append({
                "island_id": i,
                "generations": self.max_generations,
                "convergence_threshold": self.convergence_threshold,
                "patience": self.patience,
            })
        return schedule

    def reset(self):
        self.best_fitness_history = []
        self.no_improvement_count = 0
