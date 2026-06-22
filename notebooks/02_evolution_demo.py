"""Notebook 02: Evolution Demo - Run a short evolution and show results."""
import sys
import os
import time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from oracle.symbolic.registry import register_all
from oracle.evolution.deap_engine import EvolutionaryEngine
from oracle.genome.chromosome import Chromosome


def make_entropy_packet(seed: int = 42) -> dict:
    import hashlib
    h = hashlib.sha256(str(seed).encode()).hexdigest()
    numeric = [int(h[i:i+2], 16) / 255.0 for i in range(0, min(32, len(h)), 2)]
    return {
        "text": f"oracle_query_{seed}",
        "seed": seed,
        "sha_stream": h,
        "numeric_vector": numeric,
        "bit_stream": list(h),
    }


def main():
    register_all()
    print("=" * 70)
    print("  EVOLUTION DEMO - Short run with DEAP engine")
    print("=" * 70)

    config = {
        "population_size": 20,
        "max_generations": 10,
        "mutation_rate": 0.15,
        "crossover_rate": 0.7,
        "use_progressive_difficulty": True,
        "use_memory": False,
        "use_adaptive_rates": True,
        "fitness": {
            "use_pure_entropy": False,
            "use_historical_blind": False,
            "use_legacy_benchmark": False,
        },
    }

    engine = EvolutionaryEngine(config)
    systems = [
        ("gematria", "internal"),
        ("iching", "internal"),
        ("geomancy", "internal"),
        ("numerology", "internal"),
    ]

    print(f"\nConfig: pop={config['population_size']}, gen={config['max_generations']}")
    print(f"Systems: {[s[0] for s in systems]}")

    print("\nInitializing population...")
    t0 = time.time()
    pop = engine.initialize_population(systems)
    print(f"  Created {len(pop)} chromosomes in {time.time()-t0:.1f}s")

    ep = make_entropy_packet(42)
    print(f"  Entropy packet: {len(ep['numeric_vector'])} numeric, {len(ep['bit_stream'])} bits")

    print("\nRunning evolution (10 generations)...")
    t0 = time.time()
    history = []

    def track(gen, best_pop, best_hist):
        if best_pop:
            scores = [c.get_fitness_score() for c in best_pop[:5]]
            avg = sum(scores) / len(scores) if scores else 0
            history.append({"gen": gen, "avg_top5": avg, "best": max(scores) if scores else 0})

    result = engine.evolve(ep, generations=10, callback=track)
    elapsed = time.time() - t0

    print(f"\nEvolution completed in {elapsed:.1f}s")
    print(f"\n{'Gen':>5s}  {'Avg Top-5':>10s}  {'Best':>10s}")
    print("-" * 30)
    for h in history:
        print(f"{h['gen']:5d}  {h['avg_top5']:10.4f}  {h['best']:10.4f}")

    if result:
        best = result[0]
        print(f"\nBest chromosome:")
        print(f"  ID: {best.chromosome_id}")
        print(f"  Genes: {len(best.genes)}")
        print(f"  Edges: {len(best.edges)}")
        print(f"  Fitness: {best.get_fitness_score():.4f}")
        print(f"  Systems: {[g.system_id for g in best.gene_list]}")

        print(f"\nExecuting best chromosome...")
        output = best.execute(ep)
        fused = output.get("fused_numeric", [])
        conf = output.get("oracle_confidence", 0)
        print(f"  Fused numeric ({len(fused)} values): {[f'{v:.3f}' for v in fused[:8]]}")
        print(f"  Oracle confidence: {conf:.4f}")


if __name__ == "__main__":
    main()
