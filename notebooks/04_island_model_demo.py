"""Notebook 04: Island Model Demo - Parallel evolution with migration."""
import sys
import os
import time
import hashlib
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from oracle.symbolic.registry import register_all
from oracle.evolution.islands.island_model import IslandModel, ISLAND_FAMILIES
from oracle.evolution.islands.migration import MigrationManager
from oracle.evolution.islands.scheduler import IslandScheduler


def make_entropy_packet(seed: int = 42) -> dict:
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
    print("  ISLAND MODEL DEMO - Parallel Evolution with Migration")
    print("=" * 70)

    print(f"\nIsland families defined: {list(ISLAND_FAMILIES.keys())}")
    for name, systems in ISLAND_FAMILIES.items():
        print(f"  {name:18s}: {[s[0] for s in systems]}")

    print("\n--- MigrationManager test ---")
    mm = MigrationManager({"migration_rate": 0.2, "migration_interval": 3, "topology": "ring"})
    print(f"  Topology: {mm.topology}")
    print(f"  Rate: {mm.migration_rate}, Interval: {mm.migration_interval}")

    print("\n--- IslandScheduler test ---")
    sched = IslandScheduler({"max_generations": 30, "convergence_threshold": 0.01, "patience": 5})
    for gen in [1, 10, 20, 29, 30]:
        cont = sched.should_continue(gen, 0.5 - gen * 0.01)
        print(f"  Gen {gen:2d}: should_continue={cont}")

    print("\n--- IslandModel instantiation ---")
    config = {
        "num_islands": 3,
        "migration_interval": 5,
        "migration_rate": 0.1,
        "population_size": 10,
        "fitness": {
            "use_pure_entropy": False,
            "use_historical_blind": False,
            "use_legacy_benchmark": False,
        },
    }
    model = IslandModel(config)
    print(f"  Num islands: {model.num_islands}")
    print(f"  Migration interval: {model.migration_interval}")
    print(f"  Migration rate: {model.migration_rate}")

    print("\nInitializing islands...")
    t0 = time.time()
    model.initialize()
    print(f"  Created {len(model.islands)} islands in {time.time()-t0:.1f}s")
    for island in model.islands:
        print(f"    {island.island_id}: systems={[s[0] for s in island.systems]}, pop={len(island.get_population())}")

    print("\nRunning 15 generations...")
    ep = make_entropy_packet(42)
    t0 = time.time()
    result = model.evolve(ep, generations=15)
    elapsed = time.time() - t0
    print(f"  Completed in {elapsed:.1f}s")

    print(f"\nResults:")
    print(f"  Best global: {model.get_best_global()}")
    if model.get_best_global():
        best = model.get_best_global()
        print(f"    ID: {best.chromosome_id}")
        print(f"    Fitness: {best.get_fitness_score():.4f}")
        print(f"    Systems: {[g.system_id for g in best.gene_list]}")

    if model.best_history:
        print(f"\n  Fitness history:")
        for h in model.best_history:
            print(f"    Gen {h['generation']:2d}: avg_best={h['avg_best_fitness']:.4f}")


if __name__ == "__main__":
    main()
