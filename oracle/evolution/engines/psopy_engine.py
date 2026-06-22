"""PSO engine using psopy - fast Particle Swarm Optimization."""
from __future__ import annotations

import random
import uuid
import logging
import numpy as np
from typing import Any

from ..mutation import ALL_MUTATIONS
from ...genome.chromosome import Chromosome
from ...evaluation.fitness import FitnessEvaluator
from .shared import create_chromosomes_from_positions

logger = logging.getLogger(__name__)

try:
    import psopy
    from psopy import minimize as psopy_minimize
    HAS_PSOPY = True
except ImportError:
    HAS_PSOPY = False
    logger.info("psopy not available")


class PsopyEngine:
    """Particle Swarm Optimization engine using psopy."""

    def __init__(self, config: dict | None = None) -> None:
        config = config or {}
        self.population_size: int = config.get("population_size", 30)
        self.max_generations: int = config.get("max_generations", 100)
        self.mutation_rate: float = config.get("mutation_rate", 0.15)
        self.inertia_weight: float = config.get("inertia_weight", 0.7)
        self.cognitive_weight: float = config.get("cognitive_weight", 1.5)
        self.social_weight: float = config.get("social_weight", 1.5)
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

        if not HAS_PSOPY:
            return self._fallback_evolve(entropy_packet, max_gen)

        systems = list({g.system_id for c in self.population for g in c.gene_list})
        if not systems:
            from ...symbolic.registry import list_systems
            systems = list_systems()

        n_genes = min(4, len(systems))
        best_chromosomes = []

        def objective(x):
            positions = [x.tolist() if hasattr(x, 'tolist') else list(x)]
            chroms = create_chromosomes_from_positions(
                positions, systems[:n_genes], "psopy", self.evaluator, entropy_packet
            )
            if chroms:
                best_chromosomes.append(chroms[0])
                return -chroms[0].fitness.get("total_fitness", 0.0)
            return 0.0

        try:
            lb = np.full(n_genes, -1.0)
            ub = np.full(n_genes, 1.0)
            constraints = psopy.gen_confunc(lb, ub)
            x0 = np.random.uniform(-1.0, 1.0, (min(self.population_size, 20), n_genes))

            result = psopy_minimize(
                objective, x0,
                constraints,
                options={
                    "max_iter": max_gen,
                    "vel_strategy": 2,
                    "lt": self.inertia_weight,
                    "gt": self.cognitive_weight,
                    "pt": self.social_weight,
                },
            )
        except Exception as e:
            logger.warning("psopy minimize failed: %s", e)
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
