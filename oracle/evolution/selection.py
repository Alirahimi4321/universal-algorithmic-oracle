"""Selection operators for evolutionary algorithms."""
import random
import math
from ..genome.chromosome import Chromosome


def _fitness_score(c: Chromosome) -> float:
    f = c.fitness
    if not f:
        return 0.0
    return f.get("composite", f.get("accuracy", 0.0))


def tournament_selection(population: list[Chromosome], tournament_size: int = 3) -> Chromosome:
    tournament = random.sample(population, min(tournament_size, len(population)))
    return max(tournament, key=_fitness_score)


def roulette_selection(population: list[Chromosome]) -> Chromosome:
    fitnesses = [max(_fitness_score(c), 0.001) for c in population]
    total = sum(fitnesses)
    pick = random.uniform(0, total)
    current = 0
    for chrom, fit in zip(population, fitnesses):
        current += fit
        if current >= pick:
            return chrom
    return population[-1]


def rank_selection(population: list[Chromosome]) -> Chromosome:
    sorted_pop = sorted(population, key=_fitness_score)
    ranks = list(range(1, len(sorted_pop) + 1))
    total = sum(ranks)
    pick = random.uniform(0, total)
    current = 0
    for i, rank in enumerate(ranks):
        current += rank
        if current >= pick:
            return sorted_pop[i]
    return sorted_pop[-1]


def elitism_select(population: list[Chromosome], elite_count: int = 2) -> list[Chromosome]:
    sorted_pop = sorted(population, key=_fitness_score, reverse=True)
    return sorted_pop[:elite_count]


def nsga_tournament_selection(population: list[Chromosome], tournament_size: int = 3) -> Chromosome:
    def nsga_key(c: Chromosome):
        rank = c.fitness.get("rank", float("inf"))
        crowding = c.fitness.get("crowding_distance", 0)
        return (rank, -crowding)
    tournament = random.sample(population, min(tournament_size, len(population)))
    return max(tournament, key=nsga_key)
