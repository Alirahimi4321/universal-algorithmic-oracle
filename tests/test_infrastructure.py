"""Tests for infrastructure modules: SQLAlchemy, FAISS, Qdrant, Neo4j, viz, git, trials."""
import os
import json
import time
import tempfile
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# SQLAlchemy
from oracle.storage.sqlalchemy_backend import StorageBackend

# FAISS
from oracle.storage.faiss_store import FAISSVectorStore

# Qdrant
from oracle.storage.qdrant_store import QdrantVectorStore

# Neo4j
from oracle.storage.neo4j_store import Neo4jGraphStore

# Viz
from oracle.viz.lineage_visualizer import GraphicalLineageVisualizer

# Git
from oracle.memory.git_versioning import GitVersionControl

# Trials
from oracle.evaluation.external_trials import ExternalTrialsManager


# ─── SQLAlchemy ──────────────────────────────────────────────────────────────

class TestSQLAlchemyBackend:
    def test_init_sqlite(self):
        db = StorageBackend("sqlite:///:memory:")
        stats = db.get_stats()
        assert stats["experiments"] == 0

    def test_experiment_lifecycle(self):
        db = StorageBackend("sqlite:///:memory:")
        data = {
            "experiment_id": "exp_001",
            "question_text": "Will it rain?",
            "oracle_id": "test_oracle",
            "oracle_version": "v1",
            "oracle_graph_hash": "abc",
            "prediction_payload": json.dumps({"prediction": "yes"}),
            "prediction_hash": "hash1",
            "timestamp_created": time.time(),
            "time_horizon": "1 day",
            "content_hash": "c_hash",
        }
        db.store_experiment(data)
        exp = db.get_experiment("exp_001")
        assert exp is not None
        assert exp["status"] == "registered"
        db.update_experiment("exp_001", {"status": "frozen"})
        exp = db.get_experiment("exp_001")
        assert exp["status"] == "frozen"

    def test_chromosome_roundtrip(self):
        db = StorageBackend("sqlite:///:memory:")
        data = {
            "chromosome_id": "chr1",
            "generation": 1,
            "fitness_score": 0.75,
            "chromosome_data": json.dumps({"genes": [0.1, 0.2]}),
            "chromosome_hash": "hash1",
            "timestamp": time.time(),
        }
        db.store_chromosome(data)
        chrom = db.get_chromosome("chr1")
        assert chrom is not None
        assert chrom["fitness_score"] == 0.75


# ─── FAISS ───────────────────────────────────────────────────────────────────

class TestFAISSVectorStore:
    def test_init(self):
        store = FAISSVectorStore(dimension=64)
        assert store.available
        assert store.dimension == 64

    def test_add_and_search(self):
        store = FAISSVectorStore(dimension=32)
        import random
        vec1 = [random.random() for _ in range(32)]
        vec2 = [random.random() for _ in range(32)]
        store.add_vector(vec1, {"label": "a"})
        store.add_vector(vec2, {"label": "b"})
        results = store.search(vec1, k=1)
        assert len(results) >= 1
        assert results[0]["metadata"]["label"] == "a"

    def test_persistence(self, tmp_path):
        path = str(tmp_path / "test_faiss")
        store = FAISSVectorStore(dimension=16, storage_dir=path)
        import random
        vec = [random.random() for _ in range(16)]
        store.add_vector(vec, {"id": 1})
        store2 = FAISSVectorStore(dimension=16, storage_dir=path)
        assert store2.index is not None


# ─── Qdrant (in-memory) ─────────────────────────────────────────────────────

class TestQdrantVectorStore:
    def test_init_in_memory(self):
        store = QdrantVectorStore(dimension=32, in_memory=True)
        assert store.available

    def test_add_and_search(self):
        store = QdrantVectorStore(dimension=16, in_memory=True)
        import random
        vec = [random.random() for _ in range(16)]
        store.add_vector(vec, {"label": "test"})
        results = store.search(vec, k=1)
        assert len(results) == 1
        assert results[0]["metadata"]["label"] == "test"


# ─── Neo4j (init only, no server) ──────────────────────────────────────────

class TestNeo4jGraphStore:
    def test_init_unavailable(self):
        store = Neo4jGraphStore()
        assert not store.available


# ─── Visualization ──────────────────────────────────────────────────────────

class TestVisualization:
    def test_render_lineage(self, tmp_path):
        viz = GraphicalLineageVisualizer(output_dir=str(tmp_path))
        nodes = {
            "n1": {"generation": 0, "fitness": 0.5},
            "n2": {"generation": 1, "fitness": 0.7},
        }
        edges = [{"from": "n1", "to": "n2"}]
        path = viz.render_lineage(nodes, edges, output_file="test.png")
        assert path is not None
        assert os.path.exists(path)

    def test_render_fitness_history(self, tmp_path):
        viz = GraphicalLineageVisualizer(output_dir=str(tmp_path))
        history = [{"generation": i, "avg_best_fitness": 0.5 + i * 0.05} for i in range(10)]
        path = viz.render_fitness_history(history, output_file="fitness.png")
        assert path is not None
        assert os.path.exists(path)

    def test_render_system_distribution(self, tmp_path):
        viz = GraphicalLineageVisualizer(output_dir=str(tmp_path))
        usage = {"astrology": 50, "divination": 30, "calendars": 20}
        path = viz.render_system_distribution(usage, output_file="dist.png")
        assert path is not None
        assert os.path.exists(path)


# ─── Git Versioning ─────────────────────────────────────────────────────────

class TestGitVersioning:
    def test_init(self, tmp_path):
        vc = GitVersionControl(repo_dir=str(tmp_path / "git_test"))
        assert vc.available

    def test_save_and_retrieve(self, tmp_path):
        vc = GitVersionControl(repo_dir=str(tmp_path / "git_test"))
        commit = vc.save_oracle_version(
            oracle_id="oracle_1",
            chromosome_data={"genes": [0.1, 0.2]},
            generation=1,
            fitness=0.75,
        )
        assert commit is not None
        versions = vc.get_oracle_versions("oracle_1")
        assert len(versions) >= 1


# ─── External Trials ────────────────────────────────────────────────────────

class TestExternalTrials:
    def test_trial_lifecycle(self, tmp_path):
        db_path = str(tmp_path / "trials_test.db")
        mgr = ExternalTrialsManager(db_path)
        trial_id = mgr.register_trial(
            question="Will BTC be above 100k on 2026-01-01?",
            prediction={"direction": "up"},
            oracle_id="test_oracle",
            oracle_version="v1",
            oracle_graph_hash="abc123",
            entropy_signature="def456",
            time_horizon="2026-01-01",
            domain="crypto",
        )
        assert trial_id is not None
        mgr.freeze_trial(trial_id)
        trial = mgr.get_trial(trial_id)
        assert trial["status"] == "frozen"
        mgr.annotate_outcome(trial_id, "success", {"btc_price": 105000})
        summary = mgr.get_trial_summary()
        assert summary["total_trials"] == 1
