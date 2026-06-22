#!/usr/bin/env python3
"""Comprehensive end-to-end integration test - production quality."""
import sys, os, time, json, hashlib, tempfile, random, traceback
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import logging
logging.disable(logging.WARNING)
sys.stdout.reconfigure(line_buffering=True)

P = lambda s: print(s, flush=True)

results = {"passed": [], "failed": {}}

def run(name, func):
    try:
        func()
        results["passed"].append(name)
    except Exception as e:
        results["failed"][name] = str(e)[:150]
        P(f"  FAIL {name}: {e}")

P("=" * 70)
P("  UNIVERSAL ALGORITHMIC ORACLE - INTEGRATION TEST")
P("=" * 70)
T0 = time.time()

# ═══════════════════════════════════════════════════════════════
P("\n--- 1. SYMBOLIC SYSTEMS (70) ---")
from oracle.symbolic.registry import list_systems, get_system
from oracle.symbolic.base import SymbolicOutput
from oracle.entropy.encoder import EntropyEncoder
from dataclasses import asdict

enc = EntropyEncoder()
packet = enc.encode("integration test question for all systems")
ep = asdict(packet)
systems = list_systems()
sys_pass = []
sys_fail = {}
for sid in systems:
    try:
        s = get_system(sid)
        out = s.compute(ep)
        assert out is not None, "None output"
        assert isinstance(out, SymbolicOutput), f"Wrong type: {type(out)}"
        assert out.numeric_projection is not None, "No numeric_projection"
        sys_pass.append(sid)
    except Exception as e:
        sys_fail[sid] = str(e)[:80]

P(f"  PASS: {len(sys_pass)}/{len(systems)}")
if sys_fail:
    P(f"  FAIL: {len(sys_fail)}")
    for k, v in sys_fail.items():
        P(f"    - {k}: {v}")

# ═══════════════════════════════════════════════════════════════
P("\n--- 2. EVOLUTION ENGINES ---")

def test_ga():
    from oracle.evolution.deap_engine import EvolutionaryEngine
    from oracle.genome.chromosome import Chromosome
    e = EvolutionaryEngine({"population_size": 10, "mutation_rate": 0.3})
    e.initialize_population()
    t = time.time()
    r = e.evolve(ep, generations=3)
    P(f"    ga: {len(r)} outputs, {time.time()-t:.1f}s")
    assert len(r) > 0

def test_gp():
    from oracle.evolution.gp_engine import GPEngine
    e = GPEngine({"population_size": 10})
    e.initialize_population()
    t = time.time()
    r = e.evolve(ep, generations=3)
    P(f"    gp: {len(r)} outputs, {time.time()-t:.1f}s")
    assert len(r) > 0

def test_nsga():
    from oracle.evolution.nsga_engine import NSGAEngine
    e = NSGAEngine({"population_size": 10})
    t = time.time()
    r = e.evolve(ep, generations=3)
    P(f"    nsga: {len(r)} outputs, {time.time()-t:.1f}s")
    assert len(r) > 0

def test_stochopy():
    from oracle.evolution.engines.stochopy_engine import StochopyEngine
    e = StochopyEngine({"population_size": 10})
    e.initialize_population()
    t = time.time()
    r = e.evolve(ep, generations=3)
    P(f"    stochopy: {len(r)} outputs, {time.time()-t:.1f}s")
    assert len(r) > 0

def test_psopy():
    from oracle.evolution.engines.psopy_engine import PsopyEngine
    e = PsopyEngine({"population_size": 10})
    e.initialize_population()
    t = time.time()
    r = e.evolve(ep, generations=3)
    P(f"    psopy: {len(r)} outputs, {time.time()-t:.1f}s")
    assert len(r) > 0

def test_evogine():
    from oracle.evolution.engines.evogine_engine import EvogineEngine
    e = EvogineEngine({"population_size": 10})
    e.initialize_population()
    t = time.time()
    r = e.evolve(ep, generations=3)
    P(f"    evogine: {len(r)} outputs, {time.time()-t:.1f}s")
    assert len(r) > 0

for name, fn in [("ga", test_ga), ("gp", test_gp), ("nsga", test_nsga),
                  ("stochopy", test_stochopy), ("psopy", test_psopy), ("evogine", test_evogine)]:
    run(name, fn)

# ═══════════════════════════════════════════════════════════════
P("\n--- 3. STORAGE BACKENDS ---")

def test_sqlalchemy():
    from oracle.storage.sqlalchemy_backend import StorageBackend
    with tempfile.TemporaryDirectory() as d:
        db = StorageBackend(f"sqlite:///{d}/t.db")
        db.store_experiment({"experiment_id":"T1","question_text":"Q","oracle_id":"O","oracle_version":"v","oracle_graph_hash":"h","prediction_payload":json.dumps({"a":1}),"prediction_hash":"h","timestamp_created":time.time(),"time_horizon":"1d","domain":"t","content_hash":"c"})
        e = db.get_experiment("T1")
        assert e and e["question_text"] == "Q"
        db.update_experiment("T1", {"status": "frozen"})
        db.store_chromosome({"chromosome_id":"C1","generation":1,"fitness_score":0.8,"chromosome_data":json.dumps({"g":1}),"chromosome_hash":"h","timestamp":time.time()})
        c = db.get_chromosome("C1")
        assert c and c["fitness_score"] == 0.8
        s = db.get_stats()
        assert s["experiments"] == 1 and s["chromosomes"] == 1
        P(f"    sqlalchemy: store+retrieve+update+stats OK")

def test_faiss():
    from oracle.storage.faiss_store import FAISSVectorStore
    store = FAISSVectorStore(dimension=32)
    for i in range(20):
        store.add_vector([random.random() for _ in range(32)], {"id": i})
    r = store.search([random.random() for _ in range(32)], k=5)
    assert len(r) == 5 and all(("score" in x or "distance" in x) for x in r)
    P(f"    faiss: add(20)+search(5) OK")

def test_qdrant():
    from oracle.storage.qdrant_store import QdrantVectorStore
    store = QdrantVectorStore(dimension=16, in_memory=True)
    for i in range(10):
        store.add_vector([random.random() for _ in range(16)], {"id": i})
    r = store.search([random.random() for _ in range(16)], k=3)
    assert len(r) == 3
    P(f"    qdrant: add(10)+search(3) OK")

def test_neo4j():
    from oracle.storage.neo4j_store import Neo4jGraphStore
    s = Neo4jGraphStore()
    assert not s.available
    P(f"    neo4j: driver loaded (no server expected)")

for name, fn in [("sqlalchemy", test_sqlalchemy), ("faiss", test_faiss),
                  ("qdrant", test_qdrant), ("neo4j", test_neo4j)]:
    run(name, fn)

# ═══════════════════════════════════════════════════════════════
P("\n--- 4. MEMORY MODULES ---")

def test_experiment_ledger():
    from oracle.memory.experiment_ledger import ExperimentLedger
    with tempfile.TemporaryDirectory() as d:
        ledger = ExperimentLedger(f"{d}/test.db")
        eid = ledger.register_experiment(question_text="Will it rain?", entropy_signature="s1", oracle_id="o1", oracle_version="v1", oracle_graph_hash="h1", prediction_payload={"p": 1}, time_horizon="1d", domain="weather")
        iv = ledger.verify_experiment_integrity(eid)
        assert iv["overall_valid"], f"Integrity: {iv}"
        ledger.freeze_experiment(eid)
        exp = ledger.get_experiment(eid)
        assert exp["status"] == "frozen"
        ledger.annotate_outcome(eid, "success", {"actual": "rained"})
        acc = ledger.compute_accuracy()
        assert acc["accuracy"] == 1.0 and acc["total_evaluated"] == 1
        chain = ledger.log.verify_chain(eid)
        assert chain["valid"]
        P(f"    experiment_ledger: register+freeze+annotate+verify+chain OK")

def test_version_tracker():
    from oracle.memory.version_tracker import OracleVersionTracker
    with tempfile.TemporaryDirectory() as d:
        t = OracleVersionTracker(storage_dir=d)
        class M:
            chromosome_id = "c1"
            genes = {"g1": 1}
            gene_list = [type("G", (), {"system_id": "gematria", "gene_id": "g1", "weight": 0.5})()]
            edges = []
            fitness = {"total_fitness": 0.75}
            def to_dict(self): return {"g": "c1"}
        m = M()
        v1 = t.register_version("o1", m, 0)
        v2 = t.register_version("o1", m, 1, parent_ids=[v1["version_id"]])
        h = t.get_lineage_history("o1")
        assert len(h) == 2
        a = t.get_ancestry(v2["version_id"])
        assert len(a) == 2
        st = t.get_stats()
        assert st["total_versions"] == 2
        P(f"    version_tracker: register+lineage+ancestry+stats OK")

def test_external_trials():
    from oracle.evaluation.external_trials import ExternalTrialsManager
    with tempfile.TemporaryDirectory() as d:
        mgr = ExternalTrialsManager(f"{d}/t.db")
        tid = mgr.register_trial(question="Will BTC > 100k?", prediction={"d": "u"}, oracle_id="o1", oracle_version="v1", oracle_graph_hash="a", entropy_signature="b", time_horizon="2026-01-01", domain="crypto")
        mgr.freeze_trial(tid)
        mgr.annotate_outcome(tid, "success", {"price": 105000})
        s = mgr.get_trial_summary()
        assert s["total_trials"] == 1 and s["by_outcome"]["success"] == 1
        iv = mgr.verify_trial_integrity(tid)
        assert iv.get("overall_valid", False)
        P(f"    external_trials: register+freeze+annotate+summary+integrity OK")

def test_git_versioning():
    from oracle.memory.git_versioning import GitVersionControl
    with tempfile.TemporaryDirectory() as d:
        vc = GitVersionControl(repo_dir=d)
        c = vc.save_oracle_version(oracle_id="o1", chromosome_data={"g": [0.1, 0.2]}, generation=5, fitness=0.85)
        assert c is not None
        v = vc.get_oracle_versions("o1")
        assert len(v) == 1
        st = vc.get_stats()
        assert st["total_commits"] == 1
        P(f"    git_versioning: save+retrieve+stats OK")

def test_prospective_testing():
    from oracle.memory.prospective_testing import ProspectiveTestManager
    with tempfile.TemporaryDirectory() as d:
        mgr = ProspectiveTestManager(f"{d}/p.db")
        P(f"    prospective_testing: init OK")

for name, fn in [("experiment_ledger", test_experiment_ledger), ("version_tracker", test_version_tracker),
                  ("external_trials", test_external_trials), ("git_versioning", test_git_versioning),
                  ("prospective_testing", test_prospective_testing)]:
    run(name, fn)

# ═══════════════════════════════════════════════════════════════
P("\n--- 5. FUSION METHODS ---")

def test_numeric_fusion():
    from oracle.fusion import weighted_average_fusion, concatenation_fusion, modular_fusion
    vectors = [[random.random() for _ in range(10)] for _ in range(3)]
    wa = weighted_average_fusion(vectors, [0.3, 0.4, 0.3])
    cat = concatenation_fusion(vectors)
    mod = modular_fusion(vectors)
    assert isinstance(wa, list) and len(wa) == 10
    assert isinstance(cat, list) and len(cat) == 30
    P(f"    numeric_fusion: weighted_avg(len={len(wa)})+concat(len={len(cat)})+modular OK")

def test_symbolic_fusion():
    from oracle.fusion import symbolic_state_fusion, find_dominant_element
    states = [{"element": "fire"}, {"element": "water"}, {"element": "fire"}]
    fused = symbolic_state_fusion(states)
    dom = find_dominant_element(states)
    P(f"    symbolic_fusion: fuse+dominant({dom}) OK")

def test_graph_fusion():
    from oracle.fusion import merge_graphs, compute_graph_resonance
    g1 = {"nodes": [{"id": "a"}, {"id": "b"}, {"id": "c"}], "edges": [("a", "b"), ("b", "c")]}
    g2 = {"nodes": [{"id": "b"}, {"id": "c"}, {"id": "d"}], "edges": [("b", "c"), ("c", "d")]}
    merged = merge_graphs([g1, g2])
    res = compute_graph_resonance(g1, g2)
    P(f"    graph_fusion: merge+resonance({res:.3f}) OK")

def test_mapping():
    from oracle.fusion import map_to_response, compute_confidence
    m = map_to_response(fused_numeric=[0.5, 0.6], fused_symbolic={"phase": "active"}, dominant_systems=["gematria"])
    c = compute_confidence([0.5, 0.6, 0.7])
    assert isinstance(m, dict) and isinstance(c, (int, float))
    P(f"    mapping: map+confidence({c:.3f}) OK")

for name, fn in [("numeric_fusion", test_numeric_fusion), ("symbolic_fusion", test_symbolic_fusion),
                  ("graph_fusion", test_graph_fusion), ("mapping", test_mapping)]:
    run(name, fn)

# ═══════════════════════════════════════════════════════════════
P("\n--- 6. OUTPUT MODULES ---")

def test_disclaimer():
    from oracle.output.disclaimer import DisclaimerGenerator
    d = DisclaimerGenerator.generate_output_disclaimer(oracle_id="test", generation=5, confidence=0.72)
    assert "text" in d and len(d["text"]) > 50 and d["oracle_id"] == "test"
    P(f"    disclaimer: generate OK")

def test_lineage_graph():
    from oracle.output.lineage_graph import LineageGraph
    g = LineageGraph()
    g.add_node("n1", chromosome_id="c1", generation=0, fitness=0.5, systems=["gematria"])
    g.add_node("n2", chromosome_id="c2", generation=1, fitness=0.7, parents=["n1"])
    g.add_node("n3", chromosome_id="c3", generation=2, fitness=0.85, parents=["n2"])
    text = g.render_text()
    assert "n1" in text and "n2" in text
    st = g.get_stats()
    assert st["total_nodes"] == 3 and st["max_fitness"] == 0.85
    best = g.get_best_lineage(top_n=2)
    assert best[0]["fitness"] == 0.85
    j = g.export_json()
    assert len(j) > 100
    P(f"    lineage_graph: add(3)+render+stats+best(2)+export OK")

def test_confidence_model():
    from oracle.output.oracle_output import ConfidenceModel
    cm = ConfidenceModel()
    class MC:
        genes = {f"g{i}": i for i in range(5)}
        gene_list = [type("G", (), {"system_id": f"s{i}", "gene_id": f"g{i}", "weight": 0.2, "backend": "internal"})() for i in range(5)]
        edges = [("g0", "g1")]
        fusion_schema = {"method": "weighted_average"}
    r = cm.estimate(MC(), {"fused_numeric": [0.5]}, {"structural_coherence": 0.8, "response_stability": 0.7})
    assert "confidence" in r and 0 <= r["confidence"] <= 1 and r["level"] in ("low", "medium", "high")
    P(f"    confidence_model: estimate(conf={r['confidence']:.3f},level={r['level']}) OK")

def test_oracle_output_builder():
    from oracle.output.oracle_output import OracleOutputBuilder, OracleOutput
    builder = OracleOutputBuilder()
    class FC:
        chromosome_id = "tc"; lineage_id = "tl"; genes = {"g1": 1}; edges = [("g1", "g1")]
        gene_list = [type("G", (), {"system_id": "gematria", "gene_id": "g1", "weight": 0.6, "backend": "internal"})()]
        fusion_schema = {"method": "weighted_average"}
        fitness = {"structural_coherence": 0.8, "response_stability": 0.7, "symbolic_convergence": 0.6, "entropy_utilization": 0.5, "pure_entropy_fitness": 0.9, "historical_accuracy_fitness": 0.4, "total_fitness": 0.75}
        representation = "graph"; depth = 1; custom_formulas = {}; invented_methods = []
    out = builder.build(FC(), {"fused_numeric": [0.1], "oracle_confidence": 0.7}, {})
    assert isinstance(out, OracleOutput) and out.answer and out.output_hash and len(out.output_hash) == 16
    d = out.to_dict()
    assert all(k in d for k in ["answer", "oracle_confidence", "dominant_systems", "disclaimer", "output_hash"])
    P(f"    oracle_output_builder: build(conf={out.oracle_confidence:.3f})+to_dict OK")

for name, fn in [("disclaimer", test_disclaimer), ("lineage_graph", test_lineage_graph),
                  ("confidence_model", test_confidence_model), ("oracle_output_builder", test_oracle_output_builder)]:
    run(name, fn)

# ═══════════════════════════════════════════════════════════════
P("\n--- 7. VISUALIZATION ---")

def test_viz():
    from oracle.viz.lineage_visualizer import GraphicalLineageVisualizer
    with tempfile.TemporaryDirectory() as d:
        viz = GraphicalLineageVisualizer(output_dir=d)
        nodes = {f"n{i}": {"generation": i, "fitness": 0.5 + i * 0.05} for i in range(10)}
        edges = [{"from": f"n{i}", "to": f"n{i+1}"} for i in range(9)]
        p1 = viz.render_lineage(nodes, edges, output_file="lineage.png")
        assert p1 and os.path.getsize(p1) > 1000
        hist = [{"generation": i, "avg_best_fitness": 0.5 + i * 0.05} for i in range(20)]
        p2 = viz.render_fitness_history(hist, output_file="fitness.png")
        assert p2 and os.path.exists(p2)
        usage = {f"s{i}": (10 - i) * 10 for i in range(10)}
        p3 = viz.render_system_distribution(usage, output_file="dist.png")
        assert p3 and os.path.exists(p3)
        P(f"    lineage_visualizer: 3 plots({os.path.getsize(p1)//1024}KB+{os.path.getsize(p2)//1024}KB+{os.path.getsize(p3)//1024}KB) OK")

run("lineage_visualizer", test_viz)

# ═══════════════════════════════════════════════════════════════
P("\n--- 8. FULL PIPELINE ---")

def test_pipeline_ga():
    from oracle import OraclePipeline
    from oracle.output.oracle_output import OracleOutput
    p = OraclePipeline()
    t = time.time()
    out = p.ask("What does the future hold for this project?", generations=2)
    el = time.time() - t
    assert isinstance(out, OracleOutput) and out.answer and out.oracle_confidence >= 0
    d = out.to_dict()
    assert all(k in d for k in ["answer", "oracle_confidence", "dominant_systems", "output_hash", "disclaimer"])
    P(f"    pipeline_ga: conf={out.oracle_confidence:.3f}, systems={len(out.dominant_systems)}, hash={out.output_hash}, time={el:.1f}s")

def test_pipeline_gp():
    from oracle import OraclePipeline
    p = OraclePipeline()
    t = time.time()
    out = p.ask_tree("Is this project promising?", generations=2)
    el = time.time() - t
    assert out and out.answer
    P(f"    pipeline_gp: conf={out.oracle_confidence:.3f}, time={el:.1f}s")

def test_pipeline_nsga():
    from oracle import OraclePipeline
    p = OraclePipeline()
    t = time.time()
    out = p.ask("Will the team succeed?", generations=2, engine="nsga")
    el = time.time() - t
    assert out and out.answer
    P(f"    pipeline_nsga: conf={out.oracle_confidence:.3f}, time={el:.1f}s")

for name, fn in [("pipeline_ga", test_pipeline_ga), ("pipeline_gp", test_pipeline_gp),
                  ("pipeline_nsga", test_pipeline_nsga)]:
    run(name, fn)

# ═══════════════════════════════════════════════════════════════
P("\n--- 9. META SELECTOR ---")

def test_meta():
    from oracle.evolution.meta_selector import MetaOracleSelector
    ms = MetaOracleSelector()
    P(f"    meta_selector: init OK")

run("meta_selector", test_meta)

# ═══════════════════════════════════════════════════════════════
P("\n" + "=" * 70)
P("  FINAL REPORT")
P("=" * 70)

total_pass = len(results["passed"])
total_fail = len(results["failed"])
total = total_pass + total_fail

P(f"\n  SYMBOLIC SYSTEMS:   {len(sys_pass)}/{len(systems)} passed, {len(sys_fail)} failed")
P(f"  EVOLUTION ENGINES:  {sum(1 for n in results['passed'] if n in ['ga','gp','nsga','stochopy','psopy','evogine'])}/6 passed")
P(f"  STORAGE BACKENDS:   {sum(1 for n in results['passed'] if n in ['sqlalchemy','faiss','qdrant','neo4j'])}/4 passed")
P(f"  MEMORY MODULES:     {sum(1 for n in results['passed'] if n in ['experiment_ledger','version_tracker','external_trials','git_versioning','prospective_testing'])}/5 passed")
P(f"  FUSION METHODS:     {sum(1 for n in results['passed'] if n in ['numeric_fusion','symbolic_fusion','graph_fusion','mapping'])}/4 passed")
P(f"  OUTPUT MODULES:     {sum(1 for n in results['passed'] if n in ['disclaimer','lineage_graph','confidence_model','oracle_output_builder'])}/4 passed")
P(f"  VISUALIZATION:      {sum(1 for n in results['passed'] if n in ['lineage_visualizer'])}/1 passed")
P(f"  PIPELINE:           {sum(1 for n in results['passed'] if n in ['pipeline_ga','pipeline_gp','pipeline_nsga'])}/3 passed")
P(f"  META SELECTOR:      {sum(1 for n in results['passed'] if n in ['meta_selector'])}/1 passed")

P(f"\n  TOTAL MODULES:      {total_pass}/{total} passed ({total_pass/total*100:.1f}%)")
P(f"  TOTAL SYMBOLIC:     {len(sys_pass)}/{len(systems)} passed ({len(sys_pass)/len(systems)*100:.1f}%)")
P(f"  GRAND TOTAL:        {total_pass + len(sys_pass)}/{total + len(systems)} ({(total_pass + len(sys_pass))/(total + len(systems))*100:.1f}%)")

if results["failed"]:
    P(f"\n  FAILED MODULES:")
    for name, err in results["failed"].items():
        P(f"    - {name}: {err}")

elapsed = time.time() - T0
P(f"\n  DURATION: {elapsed:.1f}s")
P(f"  STATUS: {'ALL PASSED' if not results['failed'] else 'SOME FAILURES'}")

# Save report
report = {
    "timestamp": time.time(),
    "symbolic_systems": {"passed": sys_pass, "failed": sys_fail, "total": len(systems)},
    "modules": results,
    "duration_s": round(elapsed, 1),
}
rpt_path = os.path.join(os.path.dirname(__file__), "tests", "integration_report.json")
os.makedirs(os.path.dirname(rpt_path), exist_ok=True)
with open(rpt_path, "w") as f:
    json.dump(report, f, indent=2, default=str)
P(f"  REPORT: {rpt_path}")
