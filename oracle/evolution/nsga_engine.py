"""NSGA-II Multi-Objective Optimization engine using pymoo."""
import random
import uuid
from typing import Callable
from ..genome.chromosome import Chromosome
from ..evaluation.fitness import FitnessEvaluator


class NSGAEngine:
    def __init__(self, config: dict | None = None):
        config = config or {}
        self.population_size = config.get("population_size", 50)
        self.max_generations = config.get("max_generations", 100)
        self.evaluator = FitnessEvaluator(config.get("fitness", {}))
        self.population: list[Chromosome] = []
        self.generation = 0
        self.pareto_front: list[Chromosome] = []
        self.best_history: list[dict] = []

    def evolve(
        self,
        entropy_packet: dict,
        generations: int | None = None,
        callback: Callable | None = None,
    ) -> list[Chromosome]:
        max_gen = generations or self.max_generations

        if not self.population:
            self._initialize_population()

        for gen in range(max_gen):
            self.generation = gen + 1

            objectives = []
            for chrom in self.population:
                scores = self.evaluator.evaluate(chrom, entropy_packet)
                chrom.fitness = scores
                objectives.append([
                    1.0 - scores.get("structural_coherence", 0),
                    1.0 - scores.get("oracle_confidence", 0),
                ])

            fronts = self._fast_non_dominated_sort(objectives)
            self.pareto_front = [self.population[i] for i in fronts[0]] if fronts else []

            crowding = self._crowding_distance(objectives, fronts)

            best_front = fronts[0] if fronts else []
            avg_coherence = sum(self.population[i].fitness.get("structural_coherence", 0) for i in best_front) / max(len(best_front), 1)
            avg_confidence = sum(self.population[i].fitness.get("oracle_confidence", 0) for i in best_front) / max(len(best_front), 1)

            self.best_history.append({
                "generation": self.generation,
                "pareto_size": len(self.pareto_front),
                "avg_coherence": avg_coherence,
                "avg_confidence": avg_confidence,
            })

            if callback:
                callback(self.generation, self.population, [])

            new_population = self._select(fronts, crowding)

            offspring = []
            while len(offspring) < self.population_size:
                p1 = self._tournament_select(new_population)
                p2 = self._tournament_select(new_population)
                child = p1.crossover(p2)
                child = child.mutate(0.15)
                child.generation = self.generation
                child.chromosome_id = str(uuid.uuid4())[:8]
                offspring.append(child)

            self.population = offspring[:self.population_size]

        for chrom in self.population:
            scores = self.evaluator.evaluate(chrom, entropy_packet)
            chrom.fitness = scores

        return sorted(
            self.population,
            key=lambda c: c.fitness.get("total_fitness", 0),
            reverse=True,
        )

    def _initialize_population(self):
        from ..evolution.deap_engine import AVAILABLE_SYSTEMS
        self.population = []
        for _ in range(self.population_size):
            num = random.randint(1, 4)
            systems = random.sample(AVAILABLE_SYSTEMS, num)
            chrom = Chromosome.create_random(systems)
            self.population.append(chrom)

    def _fast_non_dominated_sort(self, objectives: list[list[float]]) -> list[list[int]]:
        n = len(objectives)
        domination_count = [0] * n
        dominated_set = [[] for _ in range(n)]
        fronts = [[]]

        for i in range(n):
            for j in range(i + 1, n):
                if self._dominates(objectives[i], objectives[j]):
                    dominated_set[i].append(j)
                    domination_count[j] += 1
                elif self._dominates(objectives[j], objectives[i]):
                    dominated_set[j].append(i)
                    domination_count[i] += 1

            if domination_count[i] == 0:
                fronts[0].append(i)

        current_front = 0
        while fronts[current_front]:
            next_front = []
            for i in fronts[current_front]:
                for j in dominated_set[i]:
                    domination_count[j] -= 1
                    if domination_count[j] == 0:
                        next_front.append(j)
            current_front += 1
            fronts.append(next_front)

        return [f for f in fronts if f]

    def _dominates(self, a: list[float], b: list[float]) -> bool:
        at_least_one_better = False
        for va, vb in zip(a, b):
            if va > vb:
                return False
            if va < vb:
                at_least_one_better = True
        return at_least_one_better

    def _crowding_distance(self, objectives: list[list[float]], fronts: list[list[int]]) -> dict[int, float]:
        distances = {}
        for front in fronts:
            if len(front) <= 2:
                for idx in front:
                    distances[idx] = float("inf")
                continue

            for idx in front:
                distances[idx] = 0

            for obj_idx in range(len(objectives[0])):
                sorted_indices = sorted(front, key=lambda i: objectives[i][obj_idx])
                distances[sorted_indices[0]] = float("inf")
                distances[sorted_indices[-1]] = float("inf")

                obj_range = objectives[sorted_indices[-1]][obj_idx] - objectives[sorted_indices[0]][obj_idx]
                if obj_range == 0:
                    continue

                for k in range(1, len(sorted_indices) - 1):
                    distances[sorted_indices[k]] += (
                        objectives[sorted_indices[k + 1]][obj_idx] -
                        objectives[sorted_indices[k - 1]][obj_idx]
                    ) / obj_range

        return distances

    def _select(self, fronts: list[list[int]], crowding: dict[int, float]) -> list[Chromosome]:
        selected = []
        for front in fronts:
            front_sorted = sorted(front, key=lambda i: crowding.get(i, 0), reverse=True)
            for idx in front_sorted:
                if len(selected) < self.population_size:
                    selected.append(self.population[idx])
        return selected

    def _tournament_select(self, population: list[Chromosome]) -> Chromosome:
        candidates = random.sample(population, min(3, len(population)))
        return max(candidates, key=lambda c: c.fitness.get("total_fitness", 0))

    def get_pareto_front(self) -> list[Chromosome]:
        return self.pareto_front
