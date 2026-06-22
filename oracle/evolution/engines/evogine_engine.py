"""Evogine-based optimization engine: GA, CMA-ES, DE, Island Model, NSGA-II/III, MAP-Elites."""
from __future__ import annotations

import random
import uuid
import logging
import numpy as np
from typing import Any

from ..mutation import ALL_MUTATIONS
from ...genome.chromosome import Chromosome
from ...genome.gene import Gene
from ...evaluation.fitness import FitnessEvaluator
from .shared import create_chromosomes_from_positions

logger = logging.getLogger(__name__)

try:
    from evogine import GeneticAlgorithm, CMAESOptimizer, DEOptimizer, IslandModel, MultiObjectiveGA, MAPElites
    from evogine.genes import FloatRange, IntRange, ChoiceList
    HAS_EVOGINE = True
except ImportError:
    HAS_EVOGINE = False
    logger.info("evogine not available")


class EvogineEngine:
    """Optimization engine using evogine (GA, CMA-ES, DE, Island, NSGA, MAP-Elites)."""

    METHODS: list[str] = ["ga", "cmaes", "de", "island", "nsga", "mapelites"]

    def __init__(self, config: dict | None = None) -> None:
        config = config or {}
        self.population_size: int = config.get("population_size", 30)
        self.max_generations: int = config.get("max_generations", 100)
        self.method: str = config.get("method", "ga")
        self.mutation_rate: float = config.get("mutation_rate", 0.15)
        self.evaluator: FitnessEvaluator = FitnessEvaluator(config.get("fitness", {}))
        self.population: list[Chromosome] = []
        self.generation: int = 0
        self.best_history: list[dict[str, Any]] = []

    def initialize_population(self, systems: list[tuple[str, str]] | None = None) -> list[Chromosome]:
        from ...symbolic.registry import list_systems
        if systems is None:
            all_sys = list_systems()
            systems = [(s, "internal") for s in random.sample(all_sys, min(4, len(all_sys)))]

        self.population = []
        for _ in range(self.population_size):
            n = random.randint(1, min(4, len(systems)))
            selected = random.sample(systems, n)
            chrom = Chromosome.create_random(selected)
            self.population.append(chrom)
        return self.population

    def evolve(self, entropy_packet: dict, generations: int | None = None) -> list[Chromosome]:
        max_gen = generations or self.max_generations

        if not self.population:
            self.initialize_population()

        if not HAS_EVOGINE:
            return self._fallback_evolve(entropy_packet, max_gen)

        systems = list({g.system_id for c in self.population for g in c.gene_list})
        if not systems:
            from ...symbolic.registry import list_systems
            systems = list_systems()

        n_genes = min(4, len(systems))
        best_chromosomes = []

        def fitness_func(individual):
            x = np.array(individual)
            positions = [x.tolist()]
            chroms = create_chromosomes_from_positions(
                positions, systems[:n_genes], "evogine", self.evaluator, entropy_packet
            )
            if chroms:
                best_chromosomes.append(chroms[0])
                return chroms[0].fitness.get("total_fitness", 0.0)
            return 0.0

        try:
            gene_defs = [FloatRange(-1.0, 1.0) for _ in range(n_genes)]

            if self.method == "cmaes":
                optimizer = CMAESOptimizer(fitness_func, gene_defs, population_size=min(self.population_size, 20))
            elif self.method == "de":
                optimizer = DEOptimizer(fitness_func, gene_defs, population_size=min(self.population_size, 20))
            elif self.method == "island":
                optimizer = IslandModel(fitness_func, gene_defs, population_size=min(self.population_size, 20))
            elif self.method == "nsga":
                optimizer = MultiObjectiveGA(fitness_func, gene_defs, population_size=min(self.population_size, 20))
            elif self.method == "mapelites":
                optimizer = MAPElites(fitness_func, gene_defs, population_size=min(self.population_size, 20))
            else:
                optimizer = GeneticAlgorithm(fitness_func, gene_defs, population_size=min(self.population_size, 20))

            result = optimizer.run(generations=max_gen)
        except Exception as e:
            logger.warning("evogine optimization failed: %s", e)
            return self._fallback_evolve(entropy_packet, max_gen)

        for gen in range(max_gen):
            self.generation = gen + 1
            if best_chromosomes:
                self.best_history.append({
                    "generation": self.generation,
                    "best_fitness": best_chromosomes[-1].fitness.get("total_fitness", 0),
                    "avg_fitness": np.mean([c.fitness.get("total_fitness", 0) for c in self.population]),
                })

        if best_chromosomes:
            best_chromosomes.sort(key=lambda c: c.fitness.get("total_fitness", 0), reverse=True)
            self.population = best_chromosomes[:self.population_size]

        return sorted(self.population, key=lambda c: c.fitness.get("total_fitness", 0), reverse=True)

    def _fallback_evolve(self, entropy_packet: dict, max_gen: int) -> list[Chromosome]:
        for gen in range(max_gen):
            self.generation = gen + 1
            fitness_scores = []
            for chrom in self.population:
                scores = self.evaluator.evaluate(chrom, entropy_packet)
                chrom.fitness = scores
                fitness_scores.append(scores)

            sorted_pop = sorted(self.population, key=lambda c: c.fitness.get("total_fitness", 0), reverse=True)
            best = sorted_pop[0]
            self.best_history.append({"generation": self.generation, "best_fitness": best.fitness.get("total_fitness", 0), "avg_fitness": sum(s.get("total_fitness", 0) for s in fitness_scores) / max(len(fitness_scores), 1)})

            new_population = sorted_pop[:3]
            while len(new_population) < self.population_size:
                parent = random.choice(sorted_pop[:max(5, len(sorted_pop) // 2)])
                child = Chromosome.from_dict(parent.to_dict())
                mut_fn = random.choice(ALL_MUTATIONS)
                child = mut_fn(child, self.mutation_rate)
                child.generation = self.generation
                child.chromosome_id = str(uuid.uuid4())[:8]
                new_population.append(child)
            self.population = new_population[:self.population_size]

        fitness_scores = []
        for chrom in self.population:
            scores = self.evaluator.evaluate(chrom, entropy_packet)
            chrom.fitness = scores
            fitness_scores.append(scores)
        return sorted(self.population, key=lambda c: c.fitness.get("total_fitness", 0), reverse=True)
