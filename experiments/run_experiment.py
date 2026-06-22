"""Run a complete experiment: baseline collection, evolution, and analysis."""
import sys
import os
import json
import time
import hashlib
from datetime import datetime
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from oracle.symbolic.registry import register_all, list_systems, get_system
from oracle.evolution.deap_engine import EvolutionaryEngine


EXPERIMENT_DIR = os.path.join(os.path.dirname(__file__), 'data')
RESULTS_DIR = os.path.join(os.path.dirname(__file__), 'results')
os.makedirs(RESULTS_DIR, exist_ok=True)


def make_entropy_packet(seed: int = 42) -> dict:
    h = hashlib.sha256(str(seed).encode()).hexdigest()
    numeric = [int(h[i:i+2], 16) / 255.0 for i in range(0, min(32, len(h)), 2)]
    return {
        "text": f"experiment_{seed}",
        "seed": seed,
        "sha_stream": h,
        "numeric_vector": numeric,
        "bit_stream": list(h),
    }


def run_baseline_experiment(n_queries: int = 20) -> dict:
    print(f"\n{'='*60}")
    print(f"  BASELINE EXPERIMENT: {n_queries} queries across all systems")
    print(f"{'='*60}")

    results = {}
    systems = list_systems()
    for sys_id in sorted(systems):
        wrapper = get_system(sys_id)
        if not wrapper:
            continue
        times = []
        successes = 0
        for q in range(n_queries):
            ep = make_entropy_packet(seed=q * 17 + 7)
            t0 = time.time()
            try:
                result = wrapper.compute(ep)
                elapsed = time.time() - t0
                times.append(elapsed)
                successes += 1
            except Exception:
                times.append(None)
        if times:
            valid_times = [t for t in times if t is not None]
            avg_time = sum(valid_times) / len(valid_times) if valid_times else 0
            results[sys_id] = {
                "success_rate": successes / n_queries,
                "avg_time_ms": avg_time * 1000,
                "total_queries": n_queries,
            }
            print(f"  {sys_id:30s}: {successes:2d}/{n_queries} ok, {avg_time*1000:6.1f}ms avg")

    return results


def run_evolution_experiment(config: dict = None) -> dict:
    print(f"\n{'='*60}")
    print(f"  EVOLUTION EXPERIMENT")
    print(f"{'='*60}")

    config = config or {
        "population_size": 25,
        "max_generations": 15,
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
        ("tarot", "internal"),
    ]

    print(f"  Pop={config['population_size']}, Gen={config['max_generations']}")
    print(f"  Systems: {[s[0] for s in systems]}")

    t0 = time.time()
    engine.initialize_population(systems)
    print(f"  Population initialized: {len(engine.population)} chromosomes")

    ep = make_entropy_packet(42)
    history = []

    def track(gen, best_pop, hist):
        if best_pop:
            scores = [c.get_fitness_score() for c in best_pop[:5]]
            avg = sum(scores) / len(scores) if scores else 0
            best = max(scores) if scores else 0
            history.append({"gen": gen, "avg_top5": avg, "best": best})

    engine.evolve(ep, generations=config["max_generations"], callback=track)
    elapsed = time.time() - t0
    print(f"  Evolution completed in {elapsed:.1f}s")

    result = {
        "config": config,
        "history": history,
        "elapsed_seconds": elapsed,
        "final_pop_size": len(engine.population),
    }

    if history:
        print(f"\n  {'Gen':>5s}  {'Avg Top-5':>10s}  {'Best':>10s}")
        print(f"  {'-'*28}")
        for h in history:
            print(f"  {h['gen']:5d}  {h['avg_top5']:10.4f}  {h['best']:10.4f}")

        best_chrom = sorted(engine.population, key=lambda c: c.get_fitness_score(), reverse=True)[0]
        result["best_chromosome"] = {
            "id": best_chrom.chromosome_id,
            "fitness": best_chrom.get_fitness_score(),
            "genes": len(best_chrom.genes),
            "systems": [g.system_id for g in best_chrom.gene_list],
        }

        print(f"\n  Best chromosome: {best_chrom.chromosome_id}")
        print(f"  Fitness: {best_chrom.get_fitness_score():.4f}")
        print(f"  Systems: {[g.system_id for g in best_chrom.gene_list]}")

    return result


def main():
    register_all()
    print("=" * 70)
    print("  UNIVERSAL ALGORITHMIC ORACLE - Experiment Runner")
    print(f"  {datetime.now().isoformat()}")
    print("=" * 70)

    baseline_results = run_baseline_experiment(10)
    evolution_results = run_evolution_experiment()

    all_results = {
        "timestamp": datetime.now().isoformat(),
        "baseline": baseline_results,
        "evolution": evolution_results,
        "registered_systems": len(list_systems()),
    }

    filepath = os.path.join(RESULTS_DIR, f"experiment_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    with open(filepath, "w") as f:
        json.dump(all_results, f, indent=2, default=str)
    print(f"\nResults saved to {filepath}")

    print(f"\n{'='*70}")
    print(f"  EXPERIMENT SUMMARY")
    print(f"{'='*70}")
    print(f"  Systems tested: {len(baseline_results)}")
    print(f"  Avg baseline success: {sum(r['success_rate'] for r in baseline_results.values()) / max(len(baseline_results), 1) * 100:.1f}%")
    print(f"  Evolution generations: {evolution_results.get('history', [{}])[-1].get('gen', 0) if evolution_results.get('history') else 0}")
    if evolution_results.get("best_chromosome"):
        print(f"  Best fitness: {evolution_results['best_chromosome']['fitness']:.4f}")
    print(f"\nDone!")


if __name__ == "__main__":
    main()
