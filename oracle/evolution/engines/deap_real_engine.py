"""Real DEAP-based Genetic Algorithm engine using the deap library."""
from __future__ import annotations

import random
import uuid
import logging
from typing import Any

from ..mutation import ALL_MUTATIONS
from ...genome.chromosome import Chromosome
from ...genome.gene import Gene
from ...evaluation.fitness import FitnessEvaluator
from .shared import create_chromosomes_from_positions

logger = logging.getLogger(__name__)

try:
    from deap import base, creator, tools, algorithms
    HAS_DEAP = True
except ImportError:
    HAS_DEAP = False
    logger.info("deap not available")


class DeapRealEngine:
    """Evolution engine using the actual DEAP library for genetic algorithms."""

    def __init__(self, config: dict | None = None) -> None:
        config = config or {}
        self.population_size: int = config.get("population_size", 50)
        self.max_generations: int = config.get("max_generations", 200)
        self.mutation_rate: float = config.get("mutation_rate", 0.15)
        self.crossover_rate: float = config.get("crossover_rate", 0.7)
        self.tournament_size: int = config.get("tournament_size", 3)
        self.elite_count: int = config.get("elite_count", 5)
        self.crossover_alpha: float = config.get("crossover_alpha", 0.5)
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

        if not HAS_DEAP:
            return self._fallback_evolve(entropy_packet, max_gen)

        systems = list({g.system_id for c in self.population for g in c.gene_list})
        if not systems:
            from ...symbolic.registry import list_systems
            systems = list_systems()

        n_genes = min(4, len(systems))
        IND_SIZE = n_genes

        if not hasattr(creator, "FitnessMaxDeap"):
            creator.create("FitnessMaxDeap", base.Fitness, weights=(1.0,))
        if not hasattr(creator, "IndividualDeap"):
            creator.create("IndividualDeap", list, fitness=creator.FitnessMaxDeap)

        toolbox = base.Toolbox()
        toolbox.register("attr_float", random.uniform, -1.0, 1.0)
        toolbox.register("individual", tools.initRepeat, creator.IndividualDeap, toolbox.attr_float, n=IND_SIZE)
        toolbox.register("population", tools.initRepeat, list, toolbox.individual)

        def eval_func(individual):
            positions = [individual]
            chroms = create_chromosomes_from_positions(
                positions, systems[:n_genes], "deap", self.evaluator, entropy_packet
            )
            if chroms:
                return (chroms[0].fitness.get("total_fitness", 0.0),)
            return (0.0,)

        toolbox.register("evaluate", eval_func)
        toolbox.register("mate", tools.cxBlend, alpha=self.crossover_alpha)
        toolbox.register("mutate", tools.mutGaussian, mu=0, sigma=0.2, indpb=0.2)
        toolbox.register("select", tools.selTournament, tournsize=self.tournament_size)

        pop = toolbox.population(n=self.population_size)

        fitnesses = list(map(toolbox.evaluate, pop))
        for ind, fit in zip(pop, fitnesses):
            ind.fitness.values = fit

        for gen in range(max_gen):
            self.generation = gen + 1

            offspring = toolbox.select(pop, len(pop))
            offspring = list(map(toolbox.clone, offspring))

            for child1, child2 in zip(offspring[::2], offspring[1::2]):
                if random.random() < self.crossover_rate:
                    toolbox.mate(child1, child2)
                    del child1.fitness.values
                    del child2.fitness.values

            for mutant in offspring:
                if random.random() < self.mutation_rate:
                    toolbox.mutate(mutant)
                    del mutant.fitness.values

            invalid_ind = [ind for ind in offspring if not ind.fitness.valid]
            fitnesses = map(toolbox.evaluate, invalid_ind)
            for ind, fit in zip(invalid_ind, fitnesses):
                ind.fitness.values = fit

            pop[:] = offspring

            fits = [ind.fitness.values[0] for ind in pop]
            best_fit = max(fits)
            avg_fit = sum(fits) / len(fits)

            self.best_history.append({
                "generation": self.generation,
                "best_fitness": best_fit,
                "avg_fitness": avg_fit,
            })

        best_ind = tools.selBest(pop, 1)[0]
        best_chroms = create_chromosomes_from_positions(
            [best_ind], systems[:n_genes], "deap", self.evaluator, entropy_packet
        )

        if best_chroms:
            self.population = best_chroms[:self.population_size]
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
            self.best_history.append({"generation": self.generation, "best_fitness": best.fitness.get("total_fitness", 0)})

            new_population = sorted_pop[:self.elite_count]
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

    def get_best(self) -> Chromosome | None:
        if not self.population:
            return None
        return max(self.population, key=lambda c: c.fitness.get("total_fitness", 0))
