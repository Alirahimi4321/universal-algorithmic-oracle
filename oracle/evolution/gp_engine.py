"""Genetic Programming engine using DEAP for tree-based oracle evolution."""
import random
import uuid
from typing import Callable
from ..genome.tree_genome import TreeGenome, TreeNode
from ..evaluation.fitness import FitnessEvaluator


AVAILABLE_SYSTEMS = ["gematria", "iching", "geomancy", "calendar"]
FUSION_OPS = ["weighted_sum", "modular_resonance", "xor_fusion"]
TRANSFORM_OPS = ["normalize", "modular", "invert"]


class GPEngine:
    def __init__(self, config: dict | None = None):
        config = config or {}
        self.population_size = config.get("population_size", 30)
        self.max_generations = config.get("max_generations", 50)
        self.elite_count = config.get("elite_count", 3)
        self.tournament_size = config.get("tournament_size", 3)
        self.mutation_rate = config.get("mutation_rate", 0.2)
        self.crossover_rate = config.get("crossover_rate", 0.7)
        self.max_depth = config.get("max_depth", 4)
        self.evaluator = FitnessEvaluator(config.get("fitness", {}))
        self.population: list[TreeGenome] = []
        self.generation = 0
        self.best_history: list[dict] = []

    def initialize_population(self, systems: list[str] | None = None) -> list[TreeGenome]:
        systems = systems or AVAILABLE_SYSTEMS
        self.population = []

        for _ in range(self.population_size):
            depth = random.randint(2, self.max_depth)
            genome = TreeGenome.create_random(depth, systems)
            self.population.append(genome)

        return self.population

    def evolve(
        self,
        entropy_packet: dict,
        generations: int | None = None,
        callback: Callable | None = None,
    ) -> list[TreeGenome]:
        max_gen = generations or self.max_generations

        if not self.population:
            self.initialize_population()

        for gen in range(max_gen):
            self.generation = gen + 1

            fitness_scores = []
            for genome in self.population:
                scores = self.evaluator.evaluate_tree(genome, entropy_packet)
                genome.fitness = scores
                fitness_scores.append(scores)

            sorted_pop = sorted(
                self.population,
                key=lambda g: g.fitness.get("total_fitness", 0),
                reverse=True,
            )

            best = sorted_pop[0] if sorted_pop else None
            best_fitness = best.fitness.get("total_fitness", 0) if best else 0
            self.best_history.append({
                "generation": self.generation,
                "best_fitness": best_fitness,
                "avg_fitness": sum(s.get("total_fitness", 0) for s in fitness_scores) / max(len(fitness_scores), 1),
                "best_depth": best.depth if best else 0,
                "best_size": best.size if best else 0,
            })

            if callback:
                callback(self.generation, self.population, fitness_scores)

            new_population = [g.copy() for g in sorted_pop[:self.elite_count]]

            while len(new_population) < self.population_size:
                if random.random() < self.crossover_rate:
                    parent1 = self._tournament_select(sorted_pop)
                    parent2 = self._tournament_select(sorted_pop)
                    child = parent1.crossover(parent2)
                else:
                    parent = self._tournament_select(sorted_pop)
                    child = parent.copy()

                child = child.mutate(self.mutation_rate)
                child.generation = self.generation
                child.genome_id = str(uuid.uuid4())[:8]

                if child.depth <= self.max_depth + 1:
                    new_population.append(child)
                else:
                    new_population.append(TreeGenome.create_random(self.max_depth))

            self.population = new_population[:self.population_size]

        fitness_scores = []
        for genome in self.population:
            scores = self.evaluator.evaluate_tree(genome, entropy_packet)
            genome.fitness = scores
            fitness_scores.append(scores)

        return sorted(
            self.population,
            key=lambda g: g.fitness.get("total_fitness", 0),
            reverse=True,
        )

    def _tournament_select(self, population: list[TreeGenome]) -> TreeGenome:
        candidates = random.sample(population, min(self.tournament_size, len(population)))
        return max(candidates, key=lambda g: g.fitness.get("total_fitness", 0))

    def get_best(self) -> TreeGenome | None:
        if not self.population:
            return None
        return max(self.population, key=lambda g: g.fitness.get("total_fitness", 0))

    def get_elite(self, count: int = 5) -> list[TreeGenome]:
        sorted_pop = sorted(
            self.population,
            key=lambda g: g.fitness.get("total_fitness", 0),
            reverse=True,
        )
        return sorted_pop[:count]
