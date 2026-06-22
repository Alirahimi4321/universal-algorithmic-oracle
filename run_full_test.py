#!/usr/bin/env python3
"""Complete integration test: ALL 70 symbolic systems + ALL 23 evolution engines."""
import sys, os, time, json, traceback, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import logging
logging.disable(logging.WARNING)
sys.stdout.reconfigure(line_buffering=True)

P = lambda s: print(s, flush=True)

P("=" * 70)
P("  COMPLETE TEST: ALL 70 SYSTEMS + ALL 23 ENGINES")
P("=" * 70)
T0 = time.time()

# ═══════════════════════════════════════════════════════════════
# PART 1: ALL 70 SYMBOLIC SYSTEMS
# ═══════════════════════════════════════════════════════════════
P("\n" + "=" * 70)
P("  PART 1: ALL 70 SYMBOLIC SYSTEMS")
P("=" * 70)

from oracle.symbolic.registry import list_systems, get_system
from oracle.symbolic.base import SymbolicOutput
from oracle.entropy.encoder import EntropyEncoder
from dataclasses import asdict

enc = EntropyEncoder()
packet = enc.encode("What does the future hold for this project and team?")
ep = asdict(packet)

systems = list_systems()
sys_results = {}
sys_pass = 0
sys_fail = 0

P(f"\nTesting {len(systems)} systems with real entropy packet...")
P(f"Question: '{packet.raw_question[:50]}...'")
P(f"Seed: {packet.seed}")
P(f"Bit stream length: {len(packet.bit_stream)}")
P(f"Numeric vector length: {len(packet.numeric_vector)}")

for i, sid in enumerate(systems):
    try:
        s = get_system(sid)
        if s is None:
            sys_results[sid] = {"status": "SKIP", "reason": "not found in registry"}
            sys_fail += 1
            P(f"  [{i+1:2d}/70] SKIP {sid}: not found")
            continue

        t = time.time()
        out = s.compute(ep)
        elapsed = time.time() - t

        # Validate it's a REAL SymbolicOutput
        assert out is not None, "Output is None"
        assert isinstance(out, SymbolicOutput), f"Wrong type: {type(out)}"

        # Validate numeric projection contains real numbers
        num_proj = out.numeric_projection
        assert num_proj is not None, "numeric_projection is None"
        assert isinstance(num_proj, list), f"numeric_projection is {type(num_proj)}"
        assert len(num_proj) > 0, "numeric_projection is empty"
        for v in num_proj[:3]:
            assert isinstance(v, (int, float)), f"Non-numeric value: {type(v)} = {v}"

        # Validate symbolic state
        sym_state = out.symbolic_state
        assert sym_state is not None, "symbolic_state is None"

        sys_results[sid] = {
            "status": "OK",
            "system_id": out.system_id,
            "numeric_len": len(num_proj),
            "sample_values": [round(float(v), 4) for v in num_proj[:3]],
            "time_ms": round(elapsed * 1000, 1),
        }
        sys_pass += 1
        P(f"  [{i+1:2d}/70] OK   {sid:30s} num[{len(num_proj):3d}] {elapsed*1000:6.1f}ms  sample={num_proj[:2]}")

    except Exception as e:
        sys_results[sid] = {"status": "FAIL", "error": str(e)[:120]}
        sys_fail += 1
        P(f"  [{i+1:2d}/70] FAIL {sid:30s} ERROR: {str(e)[:80]}")

P(f"\n{'─'*70}")
P(f"  SYMBOLIC SYSTEMS RESULT: {sys_pass}/{len(systems)} passed, {sys_fail} failed")
P(f"{'─'*70}")

# ═══════════════════════════════════════════════════════════════
# PART 2: ALL 23 EVOLUTION ENGINES
# ═══════════════════════════════════════════════════════════════
P("\n" + "=" * 70)
P("  PART 2: ALL 23 EVOLUTION ENGINES")
P("=" * 70)

from oracle.genome.chromosome import Chromosome
from oracle.symbolic.registry import list_systems as get_systems_list

engine_results = {}
eng_pass = 0
eng_fail = 0

# All 23 engine configurations
ALL_ENGINES = [
    ("deap_engine", "EvolutionaryEngine", {"population_size": 15, "mutation_rate": 0.3}),
    ("gp_engine", "GPEngine", {"population_size": 15}),
    ("nsga_engine", "NSGAEngine", {"population_size": 15}),
    ("engines.stochopy_engine", "StochopyEngine", {"population_size": 15}),
    ("engines.psopy_engine", "PsopyEngine", {"population_size": 15}),
    ("engines.evogine_engine", "EvogineEngine", {"population_size": 15}),
    ("engines.pygad_engine", "PyGADEngine", {"population_size": 15}),
    ("engines.geneticalgorithm2_engine", "GeneticAlgorithm2Engine", {"population_size": 15}),
    ("engines.pyeasyga_engine", "PyEasyGAEngine", {"population_size": 15}),
    ("engines.inspyred_engine", "InspyredEngine", {"population_size": 15}),
    ("engines.gplearn_engine", "GPlearnEngine", {"population_size": 15}),
    ("engines.tpot_engine", "TpotEngine", {"population_size": 15}),
    ("engines.nevergrad_engine", "NevergradEngine", {"population_size": 15}),
    ("engines.evosax_engine", "EvosaxEngine", {"population_size": 15}),
    ("engines.pygmo_engine", "PyGMOEngine", {"population_size": 15}),
    ("engines.pymoo_engine", "PyMOOEngine", {"population_size": 15}),
    ("engines.pyswarm_engine", "PySwarmEngine", {"population_size": 15}),
    ("engines.mealpy_engine", "MealpyEngine", {"population_size": 15}),
    ("engines.niapy_engine", "NiaPyEngine", {"population_size": 15}),
    ("engines.neat_engine", "NEATEngine", {"population_size": 15}),
    ("engines.pymetaheuristic_engine", "PyMetaheuristicEngine", {"population_size": 15}),
    ("engines.cma_engine", "CMAEngine", {"population_size": 15}),
    ("engines.bayesian_engine", "BayesianOptEngine", {"population_size": 15}),
]

P(f"\nTesting {len(ALL_ENGINES)} engines with real evolution...")
P(f"Population: 15 | Generations: 3 | Real fitness evaluation")

for i, (mod_name, cls_name, config) in enumerate(ALL_ENGINES):
    engine_name = mod_name.split(".")[-1].replace("_engine", "")
    try:
        # Dynamic import
        import importlib
        mod = importlib.import_module(f"oracle.evolution.{mod_name}")
        cls = getattr(mod, cls_name)

        t_start = time.time()
        engine = cls(config)

        # Initialize population if method exists
        if hasattr(engine, 'initialize_population'):
            engine.initialize_population()

        # Run evolution with REAL entropy packet
        result = engine.evolve(ep, generations=3)
        elapsed = time.time() - t_start

        # Validate result
        assert result is not None, "No output"
        assert isinstance(result, list), f"Output is {type(result)}, expected list"
        assert len(result) > 0, "Empty output"

        # Check if outputs are real Chromosomes
        first = result[0]
        is_chromosome = isinstance(first, Chromosome)

        # Check if fitness was computed
        has_fitness = hasattr(first, 'fitness') and first.fitness is not None
        fitness_score = 0
        if has_fitness and isinstance(first.fitness, dict):
            fitness_score = first.fitness.get("total_fitness", 0)

        engine_results[engine_name] = {
            "status": "OK",
            "outputs": len(result),
            "is_chromosome": is_chromosome,
            "has_fitness": has_fitness,
            "fitness": round(fitness_score, 4),
            "time_s": round(elapsed, 2),
            "first_type": type(first).__name__,
        }
        eng_pass += 1
        P(f"  [{i+1:2d}/23] OK   {engine_name:25s} {len(result)} outputs, "
          f"fitness={fitness_score:.4f}, type={type(first).__name__}, {elapsed:.1f}s")

    except Exception as e:
        engine_results[engine_name] = {"status": "FAIL", "error": str(e)[:120]}
        eng_fail += 1
        P(f"  [{i+1:2d}/23] FAIL {engine_name:25s} ERROR: {str(e)[:80]}")

P(f"\n{'─'*70}")
P(f"  EVOLUTION ENGINES RESULT: {eng_pass}/{len(ALL_ENGINES)} passed, {eng_fail} failed")
P(f"{'─'*70}")

# ═══════════════════════════════════════════════════════════════
# PART 3: FULL PIPELINE (3 engines)
# ═══════════════════════════════════════════════════════════════
P("\n" + "=" * 70)
P("  PART 3: FULL PIPELINE (question → answer)")
P("=" * 70)

from oracle import OraclePipeline
from oracle.output.oracle_output import OracleOutput

pipeline_results = {}
pipe_pass = 0
pipe_fail = 0

PIPELINE_TESTS = [
    ("pipeline_ga", "ga", "What does the future hold?"),
    ("pipeline_gp", "gp", "Is this project promising?"),
    ("pipeline_nsga", "nsga", "Will the team succeed?"),
]

for name, engine, question in PIPELINE_TESTS:
    try:
        pipeline = OraclePipeline()
        t = time.time()
        out = pipeline.ask(question, generations=2, engine=engine) if engine != "gp" else pipeline.ask_tree(question, generations=2)
        elapsed = time.time() - t

        assert isinstance(out, OracleOutput)
        assert out.answer and len(out.answer) > 10
        assert out.oracle_confidence >= 0
        assert out.dominant_systems
        assert out.output_hash

        d = out.to_dict()
        assert all(k in d for k in ["answer", "oracle_confidence", "dominant_systems", "output_hash", "disclaimer"])

        pipeline_results[name] = {
            "status": "OK",
            "confidence": round(out.oracle_confidence, 4),
            "systems": out.dominant_systems,
            "hash": out.output_hash,
            "answer_len": len(out.answer),
            "time_s": round(elapsed, 2),
        }
        pipe_pass += 1
        P(f"  OK  {name:15s} conf={out.oracle_confidence:.4f} systems={out.dominant_systems[:3]} hash={out.output_hash} {elapsed:.1f}s")

    except Exception as e:
        pipeline_results[name] = {"status": "FAIL", "error": str(e)[:200]}
        pipe_fail += 1
        P(f"  FAIL {name:15s} ERROR: {str(e)[:100]}")

P(f"\n{'─'*70}")
P(f"  PIPELINE RESULT: {pipe_pass}/{len(PIPELINE_TESTS)} passed, {pipe_fail} failed")
P(f"{'─'*70}")

# ═══════════════════════════════════════════════════════════════
# FINAL REPORT
# ═══════════════════════════════════════════════════════════════
P("\n" + "=" * 70)
P("  FINAL REPORT")
P("=" * 70)

P(f"\n  PART 1 - SYMBOLIC SYSTEMS:")
P(f"    Total:    {len(systems)}")
P(f"    Passed:   {sys_pass}")
P(f"    Failed:   {sys_fail}")
P(f"    Rate:     {sys_pass/len(systems)*100:.1f}%")

P(f"\n  PART 2 - EVOLUTION ENGINES:")
P(f"    Total:    {len(ALL_ENGINES)}")
P(f"    Passed:   {eng_pass}")
P(f"    Failed:   {eng_fail}")
P(f"    Rate:     {eng_pass/len(ALL_ENGINES)*100:.1f}%")

P(f"\n  PART 3 - FULL PIPELINE:")
P(f"    Total:    {len(PIPELINE_TESTS)}")
P(f"    Passed:   {pipe_pass}")
P(f"    Failed:   {pipe_fail}")
P(f"    Rate:     {pipe_pass/len(PIPELINE_TESTS)*100:.1f}%")

grand_total = len(systems) + len(ALL_ENGINES) + len(PIPELINE_TESTS)
grand_pass = sys_pass + eng_pass + pipe_pass
grand_fail = sys_fail + eng_fail + pipe_fail

P(f"\n  {'═'*50}")
P(f"  GRAND TOTAL: {grand_pass}/{grand_total} ({grand_pass/grand_total*100:.1f}%)")
P(f"  {'═'*50}")

if grand_fail > 0:
    P(f"\n  FAILED ITEMS:")
    for sid, r in sys_results.items():
        if r["status"] == "FAIL":
            P(f"    [SYSTEM] {sid}: {r.get('error', 'unknown')[:80]}")
    for ename, r in engine_results.items():
        if r["status"] == "FAIL":
            P(f"    [ENGINE] {ename}: {r.get('error', 'unknown')[:80]}")
    for pname, r in pipeline_results.items():
        if r["status"] == "FAIL":
            P(f"    [PIPELINE] {pname}: {r.get('error', 'unknown')[:80]}")

elapsed = time.time() - T0
P(f"\n  DURATION: {elapsed:.1f}s")
P(f"  STATUS: {'ALL PASSED ✅' if grand_fail == 0 else f'{grand_fail} FAILURES ❌'}")

# Save full report
report = {
    "timestamp": time.time(),
    "duration_s": round(elapsed, 1),
    "symbolic_systems": {"total": len(systems), "passed": sys_pass, "failed": sys_fail, "details": sys_results},
    "evolution_engines": {"total": len(ALL_ENGINES), "passed": eng_pass, "failed": eng_fail, "details": engine_results},
    "pipeline": {"total": len(PIPELINE_TESTS), "passed": pipe_pass, "failed": pipe_fail, "details": pipeline_results},
    "grand_total": {"total": grand_total, "passed": grand_pass, "failed": grand_fail},
}

rpt_path = os.path.join(os.path.dirname(__file__), "tests", "full_integration_report.json")
os.makedirs(os.path.dirname(rpt_path), exist_ok=True)
with open(rpt_path, "w") as f:
    json.dump(report, f, indent=2, default=str)
P(f"  REPORT: {rpt_path}")
