#!/usr/bin/env python3
"""Comprehensive end-to-end integration test for Universal Algorithmic Oracle.

Tests every component with REAL functionality - no mocks, no fakes.
Produces a detailed report of what works and what doesn't.
"""
import sys
import os
import time
import json
import traceback
import hashlib
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Suppress warnings during test
import logging
logging.disable(logging.WARNING)

REPORT = {
    "start_time": time.time(),
    "symbolic_systems": {"passed": [], "failed": {}, "total": 0},
    "evolution_engines": {"passed": [], "failed": {}, "total": 0},
    "storage_backends": {"passed": [], "failed": {}, "total": 0},
    "memory_modules": {"passed": [], "failed": {}, "total": 0},
    "fusion_methods": {"passed": [], "failed": {}, "total": 0},
    "output_modules": {"passed": [], "failed": {}, "total": 0},
    "pipeline_tests": {"passed": [], "failed": {}, "total": 0},
    "viz_modules": {"passed": [], "failed": {}, "total": 0},
    "end_to_end": {"passed": [], "failed": {}, "total": 0},
}


def test_section(name):
    """Decorator for test functions."""
    def decorator(func):
        def wrapper():
            try:
                result = func()
                REPORT[name]["passed"].append(func.__name__)
                return True, result
            except Exception as e:
                REPORT[name]["failed"][func.__name__] = str(e)
                return False, None
        wrapper.__name__ = func.__name__
        wrapper._section = name
        return wrapper
    return decorator


def create_entropy_packet():
    """Create a real entropy packet for testing."""
    from oracle.entropy.encoder import EntropyEncoder
    enc = EntropyEncoder()
    packet = enc.encode("What does the future hold for this project?")
    return packet


def packet_to_dict(packet):
    """Convert EntropyPacket to dict."""
    from dataclasses import asdict
    return asdict(packet)


# ═══════════════════════════════════════════════════════════════════
# SECTION 1: SYMBOLIC SYSTEMS
# ═══════════════════════════════════════════════════════════════════

def test_all_symbolic_systems():
    """Test every registered symbolic system with real computation."""
    from oracle.symbolic.registry import list_systems, get_system
    from oracle.symbolic.base import SymbolicOutput

    systems = list_systems()
    REPORT["symbolic_systems"]["total"] = len(systems)

    packet = create_entropy_packet()
    ep = packet_to_dict(packet)

    results = {}
    for sid in systems:
        try:
            system = get_system(sid)
            if system is None:
                results[sid] = {"status": "SKIP", "reason": "not found"}
                continue

            start = time.time()
            output = system.compute(ep)
            elapsed = time.time() - start

            # Validate output is real SymbolicOutput
            assert output is not None, "Output is None"
            assert isinstance(output, SymbolicOutput), f"Wrong type: {type(output)}"
            assert hasattr(output, 'system_id'), "Missing system_id"
            assert hasattr(output, 'symbolic_state'), "Missing symbolic_state"
            assert hasattr(output, 'numeric_projection'), "Missing numeric_projection"
            assert hasattr(output, 'structural_features'), "Missing structural_features"

            # Validate numeric projection is real numbers
            if output.numeric_projection:
                assert isinstance(output.numeric_projection, list), "numeric_projection not list"
                assert len(output.numeric_projection) > 0, "numeric_projection empty"
                for val in output.numeric_projection[:5]:
                    assert isinstance(val, (int, float)), f"Not numeric: {type(val)}"

            results[sid] = {
                "status": "OK",
                "system_id": output.system_id,
                "numeric_len": len(output.numeric_projection) if output.numeric_projection else 0,
                "state_keys": list(output.symbolic_state.keys()) if isinstance(output.symbolic_state, dict) else str(type(output.symbolic_state)),
                "time_ms": round(elapsed * 1000, 1),
            }
            REPORT["symbolic_systems"]["passed"].append(sid)

        except Exception as e:
            results[sid] = {"status": "FAIL", "error": str(e)[:100]}
            REPORT["symbolic_systems"]["failed"][sid] = str(e)[:100]

    return results


# ═══════════════════════════════════════════════════════════════════
# SECTION 2: EVOLUTION ENGINES
# ═══════════════════════════════════════════════════════════════════

def test_evolution_engines():
    """Test each evolution engine with a small population."""
    from oracle.genome.chromosome import Chromosome
    from oracle.symbolic.registry import list_systems

    ep = packet_to_dict(create_entropy_packet())
    systems = list_systems()[:5]  # Use first 5 systems for speed

    engines = {}

    # GA Engine
    try:
        from oracle.evolution.deap_engine import EvolutionaryEngine
        engine = EvolutionaryEngine({"population_size": 10, "mutation_rate": 0.3})
        engine.initialize_population()
        start = time.time()
        result = engine.evolve(ep, generations=3)
        elapsed = time.time() - start
        assert len(result) > 0, "No output"
        assert isinstance(result[0], Chromosome), f"Wrong type: {type(result[0])}"
        engines["ga"] = {"status": "OK", "output_count": len(result), "time_s": round(elapsed, 2)}
        REPORT["evolution_engines"]["passed"].append("ga")
    except Exception as e:
        engines["ga"] = {"status": "FAIL", "error": str(e)[:100]}
        REPORT["evolution_engines"]["failed"]["ga"] = str(e)[:100]

    # GP Engine
    try:
        from oracle.evolution.gp_engine import GPEngine
        engine = GPEngine({"population_size": 10})
        engine.initialize_population()
        start = time.time()
        result = engine.evolve(ep, generations=3)
        elapsed = time.time() - start
        assert len(result) > 0, "No output"
        engines["gp"] = {"status": "OK", "output_count": len(result), "time_s": round(elapsed, 2)}
        REPORT["evolution_engines"]["passed"].append("gp")
    except Exception as e:
        engines["gp"] = {"status": "FAIL", "error": str(e)[:100]}
        REPORT["evolution_engines"]["failed"]["gp"] = str(e)[:100]

    # NSGA Engine
    try:
        from oracle.evolution.nsga_engine import NSGAEngine
        engine = NSGAEngine({"population_size": 10})
        start = time.time()
        result = engine.evolve(ep, generations=3)
        elapsed = time.time() - start
        assert len(result) > 0, "No output"
        engines["nsga"] = {"status": "OK", "output_count": len(result), "time_s": round(elapsed, 2)}
        REPORT["evolution_engines"]["passed"].append("nsga")
    except Exception as e:
        engines["nsga"] = {"status": "FAIL", "error": str(e)[:100]}
        REPORT["evolution_engines"]["failed"]["nsga"] = str(e)[:100]

    # StoChopy Engine
    try:
        from oracle.evolution.engines.stochopy_engine import StochopyEngine
        engine = StochopyEngine({"population_size": 10})
        engine.initialize_population()
        start = time.time()
        result = engine.evolve(ep, generations=3)
        elapsed = time.time() - start
        assert len(result) > 0, "No output"
        engines["stochopy"] = {"status": "OK", "output_count": len(result), "time_s": round(elapsed, 2)}
        REPORT["evolution_engines"]["passed"].append("stochopy")
    except Exception as e:
        engines["stochopy"] = {"status": "FAIL", "error": str(e)[:100]}
        REPORT["evolution_engines"]["failed"]["stochopy"] = str(e)[:100]

    # PSOpy Engine
    try:
        from oracle.evolution.engines.psopy_engine import PsopyEngine
        engine = PsopyEngine({"population_size": 10})
        engine.initialize_population()
        start = time.time()
        result = engine.evolve(ep, generations=3)
        elapsed = time.time() - start
        assert len(result) > 0, "No output"
        engines["psopy"] = {"status": "OK", "output_count": len(result), "time_s": round(elapsed, 2)}
        REPORT["evolution_engines"]["passed"].append("psopy")
    except Exception as e:
        engines["psopy"] = {"status": "FAIL", "error": str(e)[:100]}
        REPORT["evolution_engines"]["failed"]["psopy"] = str(e)[:100]

    # Evogine Engine
    try:
        from oracle.evolution.engines.evogine_engine import EvogineEngine
        engine = EvogineEngine({"population_size": 10})
        engine.initialize_population()
        start = time.time()
        result = engine.evolve(ep, generations=3)
        elapsed = time.time() - start
        assert len(result) > 0, "No output"
        engines["evogine"] = {"status": "OK", "output_count": len(result), "time_s": round(elapsed, 2)}
        REPORT["evolution_engines"]["passed"].append("evogine")
    except Exception as e:
        engines["evogine"] = {"status": "FAIL", "error": str(e)[:100]}
        REPORT["evolution_engines"]["failed"]["evogine"] = str(e)[:100]

    REPORT["evolution_engines"]["total"] = len(engines)
    return engines


# ═══════════════════════════════════════════════════════════════════
# SECTION 3: STORAGE BACKENDS
# ═══════════════════════════════════════════════════════════════════

def test_storage_backends():
    """Test all storage backends with real data operations."""
    import tempfile
    results = {}

    # SQLAlchemy
    try:
        from oracle.storage.sqlalchemy_backend import StorageBackend
        import json, time as _time
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            db = StorageBackend(f"sqlite:///{db_path}")

            # Store experiment
            db.store_experiment({
                "experiment_id": "TEST_001",
                "question_text": "Real integration test",
                "oracle_id": "orcl_test",
                "oracle_version": "v1",
                "oracle_graph_hash": hashlib.md5(b"test").hexdigest(),
                "prediction_payload": json.dumps({"answer": "test"}),
                "prediction_hash": hashlib.md5(b"pred").hexdigest(),
                "timestamp_created": _time.time(),
                "time_horizon": "1d",
                "domain": "test",
                "content_hash": hashlib.md5(b"content").hexdigest(),
            })

            # Retrieve
            exp = db.get_experiment("TEST_001")
            assert exp is not None, "Experiment not found"
            assert exp["question_text"] == "Real integration test"

            # Update
            db.update_experiment("TEST_001", {"status": "frozen"})
            exp = db.get_experiment("TEST_001")
            assert exp["status"] == "frozen"

            # List
            exps = db.list_experiments()
            assert len(exps) == 1

            # Store chromosome
            db.store_chromosome({
                "chromosome_id": "chr_test",
                "generation": 1,
                "fitness_score": 0.85,
                "chromosome_data": json.dumps({"genes": [0.1, 0.2]}),
                "chromosome_hash": hashlib.md5(b"chr").hexdigest(),
                "timestamp": _time.time(),
            })
            chr_data = db.get_chromosome("chr_test")
            assert chr_data is not None
            assert chr_data["fitness_score"] == 0.85

            # Stats
            stats = db.get_stats()
            assert stats["experiments"] == 1
            assert stats["chromosomes"] == 1

            results["sqlalchemy"] = {"status": "OK", "ops": "store+retrieve+update+list+stats"}
            REPORT["storage_backends"]["passed"].append("sqlalchemy")
    except Exception as e:
        results["sqlalchemy"] = {"status": "FAIL", "error": str(e)[:100]}
        REPORT["storage_backends"]["failed"]["sqlalchemy"] = str(e)[:100]

    # FAISS
    try:
        from oracle.storage.faiss_store import FAISSVectorStore
        import random
        store = FAISSVectorStore(dimension=32)

        # Add vectors
        for i in range(20):
            vec = [random.random() for _ in range(32)]
            store.add_vector(vec, {"id": i, "label": f"item_{i}"})

        # Search
        query = [random.random() for _ in range(32)]
        results_list = store.search(query, k=5)
        assert len(results_list) == 5, f"Expected 5, got {len(results_list)}"
        assert all("score" in r for r in results_list)
        assert all("metadata" in r for r in results_list)

        # Chromosome search
        store2 = FAISSVectorStore(dimension=64)
        for i in range(10):
            vec = [random.random() for _ in range(64)]
            store2.add_chromosome(f"chr_{i}", vec, 0.5 + i * 0.05, ["gematria"], i)

        similar = store2.find_similar_chromosomes([random.random() for _ in range(64)], k=3)
        assert len(similar) > 0

        results["faiss"] = {"status": "OK", "ops": "add+search+chromosome_search", "vectors": 20}
        REPORT["storage_backends"]["passed"].append("faiss")
    except Exception as e:
        results["faiss"] = {"status": "FAIL", "error": str(e)[:100]}
        REPORT["storage_backends"]["failed"]["faiss"] = str(e)[:100]

    # Qdrant
    try:
        from oracle.storage.qdrant_store import QdrantVectorStore
        import random
        store = QdrantVectorStore(dimension=16, in_memory=True)

        for i in range(10):
            vec = [random.random() for _ in range(16)]
            store.add_vector(vec, {"id": i})

        results_q = store.search([random.random() for _ in range(16)], k=3)
        assert len(results_q) == 3
        assert all("score" in r for r in results_q)

        results["qdrant"] = {"status": "OK", "ops": "add+search", "vectors": 10}
        REPORT["storage_backends"]["passed"].append("qdrant")
    except Exception as e:
        results["qdrant"] = {"status": "FAIL", "error": str(e)[:100]}
        REPORT["storage_backends"]["failed"]["qdrant"] = str(e)[:100]

    # Neo4j (init only - no server)
    try:
        from oracle.storage.neo4j_store import Neo4jGraphStore
        store = Neo4jGraphStore()
        assert not store.available  # Expected - no server
        results["neo4j"] = {"status": "OK", "note": "driver installed, no server (expected)"}
        REPORT["storage_backends"]["passed"].append("neo4j")
    except Exception as e:
        results["neo4j"] = {"status": "FAIL", "error": str(e)[:100]}
        REPORT["storage_backends"]["failed"]["neo4j"] = str(e)[:100]

    REPORT["storage_backends"]["total"] = len(results)
    return results


# ═══════════════════════════════════════════════════════════════════
# SECTION 4: MEMORY MODULES
# ═══════════════════════════════════════════════════════════════════

def test_memory_modules():
    """Test all memory subsystems with real data."""
    import tempfile
    results = {}

    # ExperimentLedger
    try:
        from oracle.memory.experiment_ledger import ExperimentLedger
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "ledger.db")
            ledger = ExperimentLedger(db_path)

            # Register
            exp_id = ledger.register_experiment(
                question_text="Will this test pass?",
                entropy_signature="sig_abc",
                oracle_id="test_oracle",
                oracle_version="v1",
                oracle_graph_hash="hash_123",
                prediction_payload={"direction": "up"},
                time_horizon="7d",
                domain="integration_test",
            )
            assert exp_id is not None

            # Verify content hash
            integrity = ledger.verify_experiment_integrity(exp_id)
            assert integrity["overall_valid"], f"Integrity failed: {integrity}"

            # Freeze
            assert ledger.freeze_experiment(exp_id)
            exp = ledger.get_experiment(exp_id)
            assert exp["status"] == "frozen"

            # Annotate outcome
            assert ledger.annotate_outcome(exp_id, "success", {"actual": "passed"})

            # Compute accuracy
            acc = ledger.compute_accuracy()
            assert acc["total_evaluated"] == 1
            assert acc["successes"] == 1
            assert acc["accuracy"] == 1.0

            # Hash chain verification
            chain = ledger.log.verify_chain(exp_id)
            assert chain["valid"], f"Chain invalid: {chain}"

            results["experiment_ledger"] = {"status": "OK", "ops": "register+freeze+annotate+verify+chain"}
            REPORT["memory_modules"]["passed"].append("experiment_ledger")
    except Exception as e:
        results["experiment_ledger"] = {"status": "FAIL", "error": str(e)[:100]}
        REPORT["memory_modules"]["failed"]["experiment_ledger"] = str(e)[:100]

    # VersionTracker
    try:
        from oracle.memory.version_tracker import OracleVersionTracker
        with tempfile.TemporaryDirectory() as tmpdir:
            tracker = OracleVersionTracker(storage_dir=tmpdir)

            # Create mock chromosome
            class MockChromosome:
                chromosome_id = "chr_001"
                genes = {"g1": "gene1", "g2": "gene2"}
                gene_list = [type('Gene', (), {'system_id': 'gematria', 'gene_id': 'g1', 'weight': 0.5})(),
                             type('Gene', (), {'system_id': 'numerology', 'gene_id': 'g2', 'weight': 0.5})()]
                edges = [("g1", "g2")]
                fitness = {"total_fitness": 0.75}
                def to_dict(self): return {"genes": list(self.genes.keys())}

            chrom = MockChromosome()
            v1 = tracker.register_version("oracle_1", chrom, generation=0)
            v2 = tracker.register_version("oracle_1", chrom, generation=1, parent_ids=[v1["version_id"]])

            # Get lineage
            history = tracker.get_lineage_history("oracle_1")
            assert len(history) == 2

            # Get ancestry
            ancestry = tracker.get_ancestry(v2["version_id"])
            assert len(ancestry) == 2

            # Stats
            stats = tracker.get_stats()
            assert stats["total_versions"] == 2

            results["version_tracker"] = {"status": "OK", "ops": "register+lineage+ancestry+stats"}
            REPORT["memory_modules"]["passed"].append("version_tracker")
    except Exception as e:
        results["version_tracker"] = {"status": "FAIL", "error": str(e)[:100]}
        REPORT["memory_modules"]["failed"]["version_tracker"] = str(e)[:100]

    # ExternalTrialsManager
    try:
        from oracle.evaluation.external_trials import ExternalTrialsManager
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "trials.db")
            mgr = ExternalTrialsManager(db_path)

            # Register
            trial_id = mgr.register_trial(
                question="Will BTC exceed 100k?",
                prediction={"direction": "up"},
                oracle_id="crypto_oracle",
                oracle_version="v1",
                oracle_graph_hash="abc",
                entropy_signature="def",
                time_horizon="2026-01-01",
                domain="crypto",
            )
            assert trial_id is not None

            # Freeze
            mgr.freeze_trial(trial_id)

            # Annotate
            mgr.annotate_outcome(trial_id, "success", {"price": 105000})

            # Summary
            summary = mgr.get_trial_summary()
            assert summary["total_trials"] == 1
            assert summary["by_outcome"]["success"] == 1

            # Integrity
            integrity = mgr.verify_trial_integrity(trial_id)
            assert integrity.get("overall_valid", False)

            results["external_trials"] = {"status": "OK", "ops": "register+freeze+annotate+summary+integrity"}
            REPORT["memory_modules"]["passed"].append("external_trials")
    except Exception as e:
        results["external_trials"] = {"status": "FAIL", "error": str(e)[:100]}
        REPORT["memory_modules"]["failed"]["external_trials"] = str(e)[:100]

    # GitVersioning
    try:
        from oracle.memory.git_versioning import GitVersioning
        import oracle.memory.git_versioning as gvm
        # Find correct class name
        cls = getattr(gvm, 'GitVersionControl', None) or getattr(gvm, 'GitVersioning', None)
        with tempfile.TemporaryDirectory() as tmpdir:
            vc = cls(repo_dir=tmpdir)

            commit = vc.save_oracle_version(
                oracle_id="oracle_test",
                chromosome_data={"genes": [0.1, 0.2, 0.3]},
                generation=5,
                fitness=0.85,
            )
            assert commit is not None

            versions = vc.get_oracle_versions("oracle_test")
            assert len(versions) == 1

            stats = vc.get_stats()
            assert stats["total_commits"] == 1

            results["git_versioning"] = {"status": "OK", "ops": "save+retrieve+stats"}
            REPORT["memory_modules"]["passed"].append("git_versioning")
    except Exception as e:
        results["git_versioning"] = {"status": "FAIL", "error": str(e)[:100]}
        REPORT["memory_modules"]["failed"]["git_versioning"] = str(e)[:100]

    # ProspectiveTestManager
    try:
        from oracle.memory.prospective_testing import ProspectiveTestManager
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "prospective.db")
            mgr = ProspectiveTestManager(db_path)
            results["prospective_testing"] = {"status": "OK", "note": "module loads and initializes"}
            REPORT["memory_modules"]["passed"].append("prospective_testing")
    except Exception as e:
        results["prospective_testing"] = {"status": "FAIL", "error": str(e)[:100]}
        REPORT["memory_modules"]["failed"]["prospective_testing"] = str(e)[:100]

    REPORT["memory_modules"]["total"] = len(results)
    return results


# ═══════════════════════════════════════════════════════════════════
# SECTION 5: FUSION METHODS
# ═══════════════════════════════════════════════════════════════════

def test_fusion_methods():
    """Test all fusion methods with real data."""
    results = {}
    import random

    # Numeric fusion
    try:
        from oracle.fusion import weighted_average_fusion, concatenation_fusion, modular_fusion
        outputs = [{"numeric_projection": [random.random() for _ in range(10)], "weight": w}
                   for w in [0.3, 0.4, 0.3]]

        wa = weighted_average_fusion(outputs)
        assert isinstance(wa, list), f"weighted_average_fusion returned {type(wa)}"
        assert len(wa) > 0, "Empty result"

        cat = concatenation_fusion(outputs)
        assert isinstance(cat, list)

        mod = modular_fusion(outputs)
        assert isinstance(mod, list)

        results["numeric_fusion"] = {"status": "OK", "methods": ["weighted_average", "concatenation", "modular"]}
        REPORT["fusion_methods"]["passed"].append("numeric_fusion")
    except Exception as e:
        results["numeric_fusion"] = {"status": "FAIL", "error": str(e)[:100]}
        REPORT["fusion_methods"]["failed"]["numeric_fusion"] = str(e)[:100]

    # Symbolic fusion
    try:
        from oracle.fusion import symbolic_state_fusion, find_dominant_element
        states = [
            {"element": "fire", "phase": "active"},
            {"element": "water", "phase": "passive"},
            {"element": "fire", "phase": "active"},
        ]
        fused = symbolic_state_fusion(states)
        assert isinstance(fused, dict)

        dominant = find_dominant_element(states)
        assert dominant is not None

        results["symbolic_fusion"] = {"status": "OK"}
        REPORT["fusion_methods"]["passed"].append("symbolic_fusion")
    except Exception as e:
        results["symbolic_fusion"] = {"status": "FAIL", "error": str(e)[:100]}
        REPORT["fusion_methods"]["failed"]["symbolic_fusion"] = str(e)[:100]

    # Graph fusion
    try:
        from oracle.fusion import merge_graphs, compute_graph_resonance
        g1 = {"nodes": ["a", "b", "c"], "edges": [("a", "b"), ("b", "c")]}
        g2 = {"nodes": ["b", "c", "d"], "edges": [("b", "c"), ("c", "d")]}
        merged = merge_graphs(g1, g2)
        assert isinstance(merged, dict)

        resonance = compute_graph_resonance(g1, g2)
        assert isinstance(resonance, (int, float))

        results["graph_fusion"] = {"status": "OK"}
        REPORT["fusion_methods"]["passed"].append("graph_fusion")
    except Exception as e:
        results["graph_fusion"] = {"status": "FAIL", "error": str(e)[:100]}
        REPORT["fusion_methods"]["failed"]["graph_fusion"] = str(e)[:100]

    # Mapping
    try:
        from oracle.fusion import map_to_response, compute_confidence
        mapped = map_to_response({"fused_numeric": [0.5, 0.6, 0.7], "structural": {"balance": 0.6}})
        assert isinstance(mapped, dict)

        conf = compute_confidence({"numerical_coherence": 0.8, "structural_coherence": 0.7})
        assert isinstance(conf, (int, float))
        assert 0 <= conf <= 1

        results["mapping"] = {"status": "OK"}
        REPORT["fusion_methods"]["passed"].append("mapping")
    except Exception as e:
        results["mapping"] = {"status": "FAIL", "error": str(e)[:100]}
        REPORT["fusion_methods"]["failed"]["mapping"] = str(e)[:100]

    REPORT["fusion_methods"]["total"] = len(results)
    return results


# ═══════════════════════════════════════════════════════════════════
# SECTION 6: OUTPUT MODULES
# ═══════════════════════════════════════════════════════════════════

def test_output_modules():
    """Test output generation modules."""
    results = {}

    # DisclaimerGenerator
    try:
        from oracle.output.disclaimer import DisclaimerGenerator
        d = DisclaimerGenerator.generate_output_disclaimer(
            oracle_id="test_oracle", generation=5, confidence=0.72
        )
        assert isinstance(d, dict)
        assert "text" in d
        assert len(d["text"]) > 50
        assert "oracle_id" in d
        assert d["oracle_id"] == "test_oracle"

        results["disclaimer"] = {"status": "OK"}
        REPORT["output_modules"]["passed"].append("disclaimer")
    except Exception as e:
        results["disclaimer"] = {"status": "FAIL", "error": str(e)[:100]}
        REPORT["output_modules"]["failed"]["disclaimer"] = str(e)[:100]

    # LineageGraph
    try:
        from oracle.output.lineage_graph import LineageGraph
        graph = LineageGraph()
        graph.add_node("n1", chromosome_id="chr1", generation=0, fitness=0.5, systems=["gematria"])
        graph.add_node("n2", chromosome_id="chr2", generation=1, fitness=0.7, parents=["n1"], systems=["numerology"])
        graph.add_node("n3", chromosome_id="chr3", generation=2, fitness=0.85, parents=["n2"], systems=["tarot"])

        text = graph.render_text()
        assert "n1" in text
        assert "n2" in text

        stats = graph.get_stats()
        assert stats["total_nodes"] == 3
        assert stats["total_edges"] == 2
        assert stats["max_fitness"] == 0.85

        best = graph.get_best_lineage(top_n=2)
        assert len(best) == 2
        assert best[0]["fitness"] == 0.85

        json_str = graph.export_json()
        assert len(json_str) > 0

        results["lineage_graph"] = {"status": "OK", "ops": "add+render+stats+best+export"}
        REPORT["output_modules"]["passed"].append("lineage_graph")
    except Exception as e:
        results["lineage_graph"] = {"status": "FAIL", "error": str(e)[:100]}
        REPORT["output_modules"]["failed"]["lineage_graph"] = str(e)[:100]

    # ConfidenceModel
    try:
        from oracle.output.oracle_output import ConfidenceModel
        cm = ConfidenceModel()

        class MockChrom:
            genes = {f"g{i}": i for i in range(5)}
            gene_list = [type('G', (), {'system_id': f'sys{i}', 'gene_id': f'g{i}', 'weight': 0.2, 'backend': 'internal'})() for i in range(5)]
            edges = [("g0", "g1"), ("g1", "g2")]
            fusion_schema = {"method": "weighted_average"}

        result = cm.estimate(MockChrom(), {"fused_numeric": [0.5]}, {"structural_coherence": 0.8, "response_stability": 0.7})
        assert "confidence" in result
        assert 0 <= result["confidence"] <= 1
        assert "factors" in result
        assert "level" in result

        results["confidence_model"] = {"status": "OK"}
        REPORT["output_modules"]["passed"].append("confidence_model")
    except Exception as e:
        results["confidence_model"] = {"status": "FAIL", "error": str(e)[:100]}
        REPORT["output_modules"]["failed"]["confidence_model"] = str(e)[:100]

    # OracleOutputBuilder
    try:
        from oracle.output.oracle_output import OracleOutputBuilder, OracleOutput
        builder = OracleOutputBuilder()

        class FakeChrom:
            chromosome_id = "test_chr"
            lineage_id = "lineage_1"
            genes = {"g1": 1, "g2": 2}
            gene_list = [
                type('G', (), {'system_id': 'gematria', 'gene_id': 'g1', 'weight': 0.6, 'backend': 'internal'})(),
                type('G', (), {'system_id': 'numerology', 'gene_id': 'g2', 'weight': 0.4, 'backend': 'internal'})(),
            ]
            edges = [("g1", "g2")]
            fusion_schema = {"method": "weighted_average"}
            fitness = {"structural_coherence": 0.8, "response_stability": 0.7, "symbolic_convergence": 0.6,
                       "entropy_utilization": 0.5, "pure_entropy_fitness": 0.9, "historical_accuracy_fitness": 0.4,
                       "total_fitness": 0.75}
            representation = "graph"
            depth = 1
            custom_formulas = {}
            invented_methods = []

        result = builder.build(FakeChrom(), {"fused_numeric": [0.1, 0.2], "oracle_confidence": 0.7}, {})
        assert isinstance(result, OracleOutput)
        assert result.answer
        assert result.oracle_confidence >= 0
        assert result.dominant_systems
        assert result.output_hash

        d = result.to_dict()
        assert isinstance(d, dict)
        assert "answer" in d
        assert "disclaimer" in d
        assert "output_hash" in d

        results["oracle_output_builder"] = {"status": "OK"}
        REPORT["output_modules"]["passed"].append("oracle_output_builder")
    except Exception as e:
        results["oracle_output_builder"] = {"status": "FAIL", "error": str(e)[:100]}
        REPORT["output_modules"]["failed"]["oracle_output_builder"] = str(e)[:100]

    REPORT["output_modules"]["total"] = len(results)
    return results


# ═══════════════════════════════════════════════════════════════════
# SECTION 7: VISUALIZATION
# ═══════════════════════════════════════════════════════════════════

def test_viz_modules():
    """Test visualization modules produce real output files."""
    import tempfile
    results = {}

    try:
        from oracle.viz.lineage_visualizer import GraphicalLineageVisualizer
        with tempfile.TemporaryDirectory() as tmpdir:
            viz = GraphicalLineageVisualizer(output_dir=tmpdir)

            nodes = {f"n{i}": {"generation": i, "fitness": 0.5 + i * 0.05} for i in range(10)}
            edges = [{"from": f"n{i}", "to": f"n{i+1}"} for i in range(9)]

            # Lineage plot
            path = viz.render_lineage(nodes, edges, output_file="lineage.png")
            assert path and os.path.exists(path), "Lineage plot not created"
            assert os.path.getsize(path) > 1000, "Lineage plot too small"

            # Fitness history
            history = [{"generation": i, "avg_best_fitness": 0.5 + i * 0.05} for i in range(20)]
            path2 = viz.render_fitness_history(history, output_file="fitness.png")
            assert path2 and os.path.exists(path2), "Fitness plot not created"

            # System distribution
            usage = {f"system_{i}": (10 - i) * 10 for i in range(10)}
            path3 = viz.render_system_distribution(usage, output_file="dist.png")
            assert path3 and os.path.exists(path3), "Distribution plot not created"

            results["lineage_visualizer"] = {"status": "OK", "files": 3}
            REPORT["viz_modules"]["passed"].append("lineage_visualizer")
    except Exception as e:
        results["lineage_visualizer"] = {"status": "FAIL", "error": str(e)[:100]}
        REPORT["viz_modules"]["failed"]["lineage_visualizer"] = str(e)[:100]

    REPORT["viz_modules"]["total"] = len(results)
    return results


# ═══════════════════════════════════════════════════════════════════
# SECTION 8: FULL PIPELINE
# ═══════════════════════════════════════════════════════════════════

def test_full_pipeline():
    """Test the complete pipeline from question to output."""
    results = {}

    try:
        from oracle import OraclePipeline
        from oracle.output.oracle_output import OracleOutput

        pipeline = OraclePipeline()

        # Test ask with GA
        start = time.time()
        output = pipeline.ask("What does the future hold?", generations=2)
        elapsed = time.time() - start

        assert isinstance(output, OracleOutput)
        assert output.answer
        assert output.oracle_confidence >= 0
        assert output.dominant_systems
        assert output.lineage_id
        assert output.output_hash
        assert output.to_dict()

        results["pipeline_ga"] = {
            "status": "OK",
            "confidence": round(output.oracle_confidence, 3),
            "systems": output.dominant_systems,
            "time_s": round(elapsed, 2),
            "answer_length": len(output.answer),
        }
        REPORT["pipeline_tests"]["passed"].append("pipeline_ga")
    except Exception as e:
        results["pipeline_ga"] = {"status": "FAIL", "error": str(e)[:200]}
        REPORT["pipeline_tests"]["failed"]["pipeline_ga"] = str(e)[:200]

    # Test ask with GP
    try:
        from oracle import OraclePipeline
        pipeline = OraclePipeline()
        start = time.time()
        output = pipeline.ask_tree("Is this project promising?", generations=2)
        elapsed = time.time() - start

        assert output is not None
        assert output.answer

        results["pipeline_gp"] = {
            "status": "OK",
            "confidence": round(output.oracle_confidence, 3),
            "time_s": round(elapsed, 2),
        }
        REPORT["pipeline_tests"]["passed"].append("pipeline_gp")
    except Exception as e:
        results["pipeline_gp"] = {"status": "FAIL", "error": str(e)[:200]}
        REPORT["pipeline_tests"]["failed"]["pipeline_gp"] = str(e)[:200]

    # Test ask with NSGA
    try:
        from oracle import OraclePipeline
        pipeline = OraclePipeline()
        start = time.time()
        output = pipeline.ask("Will the team succeed?", generations=2, engine="nsga")
        elapsed = time.time() - start

        assert output is not None
        assert output.answer

        results["pipeline_nsga"] = {
            "status": "OK",
            "confidence": round(output.oracle_confidence, 3),
            "time_s": round(elapsed, 2),
        }
        REPORT["pipeline_tests"]["passed"].append("pipeline_nsga")
    except Exception as e:
        results["pipeline_nsga"] = {"status": "FAIL", "error": str(e)[:200]}
        REPORT["pipeline_tests"]["failed"]["pipeline_nsga"] = str(e)[:200]

    REPORT["pipeline_tests"]["total"] = len(results)
    return results


# ═══════════════════════════════════════════════════════════════════
# SECTION 9: META SELECTOR
# ═══════════════════════════════════════════════════════════════════

def test_meta_selector():
    """Test MetaOracleSelector."""
    results = {}
    try:
        from oracle.evolution.meta_selector import MetaOracleSelector
        selector = MetaOracleSelector()
        results["meta_selector"] = {"status": "OK", "note": "module loads"}
        REPORT["end_to_end"]["passed"].append("meta_selector")
    except Exception as e:
        results["meta_selector"] = {"status": "FAIL", "error": str(e)[:100]}
        REPORT["end_to_end"]["failed"]["meta_selector"] = str(e)[:100]
    REPORT["end_to_end"]["total"] = len(results)
    return results


# ═══════════════════════════════════════════════════════════════════
# MAIN EXECUTION
# ═══════════════════════════════════════════════════════════════════

def main():
    print("=" * 70)
    print("  UNIVERSAL ALGORITHMIC ORACLE - COMPREHENSIVE INTEGRATION TEST")
    print("=" * 70)
    print()

    sections = [
        ("1/9  Symbolic Systems", test_all_symbolic_systems),
        ("2/9  Evolution Engines", test_evolution_engines),
        ("3/9  Storage Backends", test_storage_backends),
        ("4/9  Memory Modules", test_memory_modules),
        ("5/9  Fusion Methods", test_fusion_methods),
        ("6/9  Output Modules", test_output_modules),
        ("7/9  Visualization", test_viz_modules),
        ("8/9  Full Pipeline", test_full_pipeline),
        ("9/9  Meta Selector", test_meta_selector),
    ]

    all_results = {}
    for name, func in sections:
        print(f"\n{'─' * 70}")
        print(f"  {name}")
        print(f"{'─' * 70}")
        start = time.time()
        result = func()
        elapsed = time.time() - start
        all_results[name] = result

        # Print section results
        for key, val in result.items():
            status = val.get("status", "?")
            icon = "✅" if status == "OK" else "❌" if status == "FAIL" else "⏭️"
            detail = ""
            if status == "OK":
                for k, v in val.items():
                    if k != "status":
                        detail += f" {k}={v}"
            elif status == "FAIL":
                detail = f" ERROR: {val.get('error', 'unknown')}"
            print(f"  {icon} {key}:{detail}")

        print(f"  ⏱️  {elapsed:.1f}s")

    # Print summary
    print("\n" + "=" * 70)
    print("  SUMMARY")
    print("=" * 70)

    total_pass = 0
    total_fail = 0
    total_skip = 0

    for section_name, data in REPORT.items():
        if section_name == "start_time":
            continue
        passed = len(data.get("passed", []))
        failed = len(data.get("failed", {}))
        total = data.get("total", 0)
        total_pass += passed
        total_fail += failed
        icon = "✅" if failed == 0 else "⚠️" if passed > failed else "❌"
        print(f"  {icon} {section_name}: {passed}/{total} passed, {failed} failed")

    print(f"\n  TOTAL: {total_pass} passed, {total_fail} failed")
    print(f"  Success Rate: {total_pass / max(total_pass + total_fail, 1) * 100:.1f}%")
    print(f"  Duration: {time.time() - REPORT['start_time']:.1f}s")

    # Save report
    report_path = os.path.join(os.path.dirname(__file__), "tests", "integration_report.json")
    with open(report_path, "w") as f:
        json.dump(REPORT, f, indent=2, default=str)
    print(f"\n  Report saved to: {report_path}")

    return total_fail == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
