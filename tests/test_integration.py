"""Integration tests - runs the full pipeline end to end."""
import os
import sys
import json
import time
import tempfile

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


class TestFullPipeline:
    """Test the full oracle pipeline from question to output."""

    def test_import_all_modules(self):
        """All core modules import without error."""
        from oracle import OraclePipeline
        from oracle.symbolic.registry import list_systems, get_system
        from oracle.evolution.deap_engine import EvolutionaryEngine
        from oracle.evolution.gp_engine import GPEngine
        from oracle.evolution.nsga_engine import NSGAEngine
        from oracle.evaluation.fitness import FitnessEvaluator
        from oracle.memory.archive import EvolutionaryMemory
        from oracle.memory.experiment_ledger import ExperimentLedger
        from oracle.memory.version_tracker import OracleVersionTracker
        from oracle.output.oracle_output import OracleOutput, OracleOutputBuilder
        from oracle.output.disclaimer import DisclaimerGenerator
        from oracle.output.lineage_graph import LineageGraph
        from oracle.entropy.encoder import EntropyEncoder
        from oracle.fusion import weighted_average_fusion, NumericFusion
        from oracle.storage.sqlalchemy_backend import StorageBackend
        from oracle.storage.faiss_store import FAISSVectorStore
        from oracle.storage.qdrant_store import QdrantVectorStore
        from oracle.storage.neo4j_store import Neo4jGraphStore
        from oracle.viz.lineage_visualizer import GraphicalLineageVisualizer
        from oracle.memory.git_versioning import GitVersionControl
        from oracle.evaluation.external_trials import ExternalTrialsManager
        from oracle.evolution.meta_selector import MetaOracleSelector
        from oracle.memory.prospective_testing import ProspectiveTestManager

    def test_registry_has_systems(self):
        """Registry has at least 50 systems registered."""
        from oracle.symbolic.registry import list_systems
        systems = list_systems()
        assert len(systems) >= 50, f"Only {len(systems)} systems registered"

    def test_pipeline_ask_ga(self):
        """Full pipeline: ask question with GA engine."""
        from oracle import OraclePipeline
        pipeline = OraclePipeline()
        output = pipeline.ask("Will this project succeed?", generations=2)
        assert output is not None
        assert output.answer
        assert output.oracle_confidence >= 0
        assert output.dominant_systems is not None

    def test_pipeline_ask_gp(self):
        """Full pipeline: ask question with GP engine."""
        from oracle import OraclePipeline
        pipeline = OraclePipeline()
        output = pipeline.ask_tree("What does the future hold?", generations=2)
        assert output is not None
        assert output.answer

    def test_output_to_dict(self):
        """OracleOutput serializes to dict correctly."""
        from oracle import OraclePipeline
        pipeline = OraclePipeline()
        output = pipeline.ask("Test question", generations=2)
        d = output.to_dict()
        assert isinstance(d, dict)
        assert "answer" in d
        assert "oracle_confidence" in d
        assert "dominant_systems" in d
        assert "output_hash" in d
        assert "disclaimer" in d

    def test_output_hash_is_consistent(self):
        """Same output produces same hash."""
        from oracle import OraclePipeline
        from oracle.output.oracle_output import OracleOutputBuilder
        pipeline = OraclePipeline()
        output = pipeline.ask("Hash test", generations=2)
        hash1 = output.output_hash
        hash2 = output.output_hash
        assert hash1 == hash2
        assert len(hash1) == 16

    def test_disclaimer_generated(self):
        """Disclaimer is generated with required fields."""
        from oracle.output.disclaimer import DisclaimerGenerator
        disclaimer = DisclaimerGenerator.generate_output_disclaimer(
            oracle_id="test", generation=1, confidence=0.5
        )
        assert "text" in disclaimer
        assert "confidence" in disclaimer
        assert disclaimer["oracle_id"] == "test"

    def test_lineage_graph_render(self, tmp_path):
        """Lineage graph can render to file."""
        from oracle.output.lineage_graph import LineageGraph
        graph = LineageGraph()
        graph.add_node("n1", chromosome_id="chr1", generation=0, fitness=0.5)
        graph.add_node("n2", chromosome_id="chr2", generation=1, fitness=0.7, parents=["n1"])
        text = graph.render_text()
        assert "n1" in text
        assert "n2" in text
        stats = graph.get_stats()
        assert stats["total_nodes"] == 2


class TestStorageIntegration:
    """Test storage backends with real data."""

    def test_sqlalchemy_full_cycle(self):
        """SQLAlchemy: create, query, update experiment."""
        from oracle.storage.sqlalchemy_backend import StorageBackend
        import json, time
        db = StorageBackend("sqlite:///:memory:")
        db.store_experiment({
            "experiment_id": "INT_001",
            "question_text": "Will rain tomorrow?",
            "oracle_id": "orcl1",
            "oracle_version": "v1",
            "oracle_graph_hash": "abc",
            "prediction_payload": json.dumps({"yes": True}),
            "prediction_hash": "h1",
            "timestamp_created": time.time(),
            "time_horizon": "1d",
            "domain": "weather",
            "content_hash": "ch1",
        })
        exp = db.get_experiment("INT_001")
        assert exp is not None
        assert exp["question_text"] == "Will rain tomorrow?"
        db.update_experiment("INT_001", {"status": "frozen"})
        exp = db.get_experiment("INT_001")
        assert exp["status"] == "frozen"
        stats = db.get_stats()
        assert stats["experiments"] == 1

    def test_faiss_similarity_search(self):
        """FAISS: vectors stored and similar ones found."""
        from oracle.storage.faiss_store import FAISSVectorStore
        import random
        store = FAISSVectorStore(dimension=32)
        base = [random.random() for _ in range(32)]
        similar = [v + random.random() * 0.01 for v in base]
        different = [random.random() for _ in range(32)]
        store.add_vector(base, {"label": "base"})
        store.add_vector(similar, {"label": "similar"})
        store.add_vector(different, {"label": "different"})
        results = store.search(base, k=2)
        assert len(results) >= 2
        assert results[0]["metadata"]["label"] == "base"

    def test_qdrant_in_memory(self):
        """Qdrant: in-memory vector operations work."""
        from oracle.storage.qdrant_store import QdrantVectorStore
        import random
        store = QdrantVectorStore(dimension=16, in_memory=True)
        vec = [random.random() for _ in range(16)]
        store.add_vector(vec, {"test": True})
        results = store.search(vec, k=1)
        assert len(results) == 1
        assert results[0]["metadata"]["test"] is True

    def test_neo4j_init(self):
        """Neo4j: init without server doesn't crash."""
        from oracle.storage.neo4j_store import Neo4jGraphStore
        store = Neo4jGraphStore()
        assert not store.available


class TestMemoryIntegration:
    """Test memory and ledger systems together."""

    def test_experiment_ledger_with_sqlalchemy(self):
        """ExperimentLedger works with SQLAlchemy backend."""
        from oracle.memory.experiment_ledger import ExperimentLedger
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            ledger = ExperimentLedger(db_path, backend="sqlalchemy")
            exp_id = ledger.register_experiment(
                question_text="Integration test?",
                entropy_signature="sig123",
                oracle_id="test_oracle",
                oracle_version="v1",
                oracle_graph_hash="abc123",
                prediction_payload={"answer": "yes"},
                time_horizon="1 day",
                domain="test",
            )
            assert exp_id is not None
            exp = ledger.get_experiment(exp_id)
            assert exp["status"] == "registered"
            ledger.freeze_experiment(exp_id)
            exp = ledger.get_experiment(exp_id)
            assert exp["status"] == "frozen"

    def test_version_tracker_with_db(self):
        """VersionTracker can persist to SQLAlchemy."""
        from oracle.memory.version_tracker import OracleVersionTracker
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "versions.db")
            tracker = OracleVersionTracker(
                storage_dir=tmpdir,
                db_path=db_path,
            )
            assert tracker._storage is not None

    def test_git_versioning_save(self):
        """Git versioning saves and retrieves versions."""
        from oracle.memory.git_versioning import GitVersionControl
        with tempfile.TemporaryDirectory() as tmpdir:
            vc = GitVersionControl(repo_dir=tmpdir)
            commit = vc.save_oracle_version(
                oracle_id="oracle_test",
                chromosome_data={"genes": [0.1, 0.2, 0.3]},
                generation=5,
                fitness=0.85,
            )
            assert commit is not None
            versions = vc.get_oracle_versions("oracle_test")
            assert len(versions) == 1

    def test_external_trials_full_lifecycle(self):
        """External trials: register, freeze, annotate, compute accuracy."""
        from oracle.evaluation.external_trials import ExternalTrialsManager
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "trials.db")
            mgr = ExternalTrialsManager(db_path)
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
            mgr.freeze_trial(trial_id)
            mgr.annotate_outcome(trial_id, "success", {"price": 105000})
            summary = mgr.get_trial_summary()
            assert summary["total_trials"] == 1
            assert summary["by_outcome"]["success"] == 1


class TestVisualizationIntegration:
    """Test visualization with real data."""

    def test_lineage_visualizer_render(self, tmp_path):
        """GraphicalLineageVisualizer produces output files."""
        from oracle.viz.lineage_visualizer import GraphicalLineageVisualizer
        viz = GraphicalLineageVisualizer(output_dir=str(tmp_path))
        nodes = {
            f"n{i}": {"generation": i, "fitness": 0.5 + i * 0.05}
            for i in range(5)
        }
        edges = [{"from": f"n{i}", "to": f"n{i+1}"} for i in range(4)]
        path = viz.render_lineage(nodes, edges, output_file="lineage.png")
        assert path is not None
        assert os.path.exists(path)

    def test_fitness_history_render(self, tmp_path):
        """Fitness history plot renders correctly."""
        from oracle.viz.lineage_visualizer import GraphicalLineageVisualizer
        viz = GraphicalLineageVisualizer(output_dir=str(tmp_path))
        history = [
            {"generation": i, "avg_best_fitness": 0.5 + i * 0.05}
            for i in range(10)
        ]
        path = viz.render_fitness_history(history, output_file="fitness.png")
        assert path is not None
        assert os.path.exists(path)


class TestEndToEnd:
    """Complete end-to-end scenarios."""

    def test_ask_and_store(self):
        """Ask question, store result, retrieve from DB."""
        from oracle import OraclePipeline
        from oracle.storage.sqlalchemy_backend import StorageBackend
        import json, time

        pipeline = OraclePipeline()
        output = pipeline.ask("End-to-end test", generations=2)

        db = StorageBackend("sqlite:///:memory:")
        db.store_experiment({
            "experiment_id": "E2E_001",
            "question_text": "End-to-end test",
            "oracle_id": output.lineage_id,
            "oracle_version": "v1",
            "oracle_graph_hash": "e2e",
            "prediction_payload": json.dumps(output.to_dict()),
            "prediction_hash": output.output_hash,
            "timestamp_created": time.time(),
            "time_horizon": "unknown",
            "content_hash": output.output_hash,
        })
        exp = db.get_experiment("E2E_001")
        assert exp is not None
        assert output.oracle_confidence > 0

    def test_multiple_questions(self):
        """Ask multiple questions without crashing."""
        from oracle import OraclePipeline
        pipeline = OraclePipeline()
        questions = [
            "Will it rain?",
            "What about the economy?",
        ]
        for q in questions:
            output = pipeline.ask(q, generations=2)
            assert output is not None
            assert output.answer
