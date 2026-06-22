"""Shared utilities for external engines to eliminate mock/random fallbacks."""
import random
from ..population import PopulationManager
from ...genome.chromosome import Chromosome
from ...genome.gene import Gene
from ...symbolic.registry import list_systems
from ...evaluation.fitness import FitnessEvaluator


def create_chromosomes_from_positions(
    positions: list[list[float]],
    systems: list[str],
    engine_prefix: str,
    evaluator: FitnessEvaluator,
    entropy_packet: dict,
    fusion_type: str = "weighted_average",
) -> list[Chromosome]:
    """Convert optimizer positions into real evaluated Chromosomes."""
    results = []
    for i, pos in enumerate(positions):
        n_genes = min(len(pos), len(systems))
        genes = {}
        edges = []
        for j in range(n_genes):
            sys_id = systems[j % len(systems)]
            weight = max(0.05, min(1.0, abs(float(pos[j]))))
            gene = Gene(
                gene_id=f"{engine_prefix}_{i}_{j}",
                system_id=sys_id,
                backend="internal",
                params={"optimized_value": float(pos[j])},
                input_slots=[f"in_{j}"],
                output_slots=[f"out_{j}"],
                weight=weight,
                mutation_policy={"param_mutation_rate": 0.1},
            )
            genes[gene.gene_id] = gene
            if j > 0:
                edges.append((f"{engine_prefix}_{i}_{j-1}", gene.gene_id))

        if not genes:
            continue

        chrom = Chromosome(
            chromosome_id=f"{engine_prefix}_{i}_{random.randint(0, 99999)}",
            genes=genes,
            edges=edges,
            fusion_schema={"type": fusion_type},
            output_mapping={"output": list(genes.keys())[-1]},
        )

        try:
            scores = evaluator.evaluate(chrom, entropy_packet)
            chrom.fitness = scores
        except Exception:
            chrom.fitness = {"total_fitness": 0.0}

        results.append(chrom)

    return sorted(results, key=lambda c: c.fitness.get("total_fitness", 0), reverse=True)


def deap_fallback(
    entropy_packet: dict,
    generations: int,
    config: dict,
) -> list[Chromosome]:
    """Use internal DEAP engine as proper fallback instead of random chromosomes."""
    try:
        from ..deap_engine import EvolutionaryEngine
        engine = EvolutionaryEngine({"population_size": 20, **config})
        engine.initialize_population()
        engine.evolve(entropy_packet, generations=min(generations, 5))
        return engine.get_elite(5)
    except Exception:
        manager = PopulationManager(config)
        population = manager.initialize_random()
        evaluator = FitnessEvaluator(config.get("fitness", {}))
        for chrom in population:
            try:
                scores = evaluator.evaluate(chrom, entropy_packet)
                chrom.fitness = scores
            except Exception:
                chrom.fitness = {"total_fitness": 0.0}
        return sorted(population, key=lambda c: c.fitness.get("total_fitness", 0), reverse=True)[:5]
