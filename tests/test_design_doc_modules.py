"""Tests for new design doc modules: experiment ledger, prospective testing,
disclaimer, oracle output, lineage graph, meta selector, version tracker."""
import sys
import os
import tempfile
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pytest


class TestExperimentLedger:
    def test_register_and_freeze(self):
        from oracle.memory.experiment_ledger import ExperimentLedger
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        try:
            ledger = ExperimentLedger(db_path)
            exp_id = ledger.register_experiment(
                question_text="Test question",
                entropy_signature="abc",
                oracle_id="orc_001",
                oracle_version="v1",
                oracle_graph_hash="hash1",
                prediction_payload={"pred": "yes"},
                time_horizon="1_week",
                domain="test",
            )
            assert exp_id is not None
            assert ledger.freeze_experiment(exp_id) is True
            assert ledger.annotate_outcome(exp_id, "success", {"actual": "yes"}) is True
            exp = ledger.get_experiment(exp_id)
            assert exp["status"] == "evaluated"
            assert exp["outcome"] == "success"
        finally:
            os.unlink(db_path)

    def test_hash_chain_integrity(self):
        from oracle.memory.experiment_ledger import ExperimentLedger
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        try:
            ledger = ExperimentLedger(db_path)
            exp_id = ledger.register_experiment(
                question_text="Integrity test",
                entropy_signature="def",
                oracle_id="orc_002",
                oracle_version="v1",
                oracle_graph_hash="hash2",
                prediction_payload={"pred": "no"},
                time_horizon="1_month",
                domain="test",
            )
            ledger.freeze_experiment(exp_id)
            ledger.annotate_outcome(exp_id, "failure")
            result = ledger.verify_experiment_integrity(exp_id)
            assert result["overall_valid"] is True
            assert result["content_valid"] is True
            assert result["chain_valid"] is True
            assert result["chain_length"] == 3
        finally:
            os.unlink(db_path)

    def test_immutable_log(self):
        from oracle.memory.experiment_ledger import ImmutableLog
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        try:
            log = ImmutableLog(db_path)
            r1 = log.append("EXP001", "action1", {"key": "value1"})
            r2 = log.append("EXP001", "action2", {"key": "value2"})
            assert r1["chain_length"] == 0
            assert r2["chain_length"] == 1
            assert r2["hash"] != r1["hash"]
            result = log.verify_chain("EXP001")
            assert result["valid"] is True
            assert result["chain_length"] == 2
        finally:
            os.unlink(db_path)


class TestProspectiveTesting:
    def test_full_lifecycle(self):
        from oracle.memory.prospective_testing import ProspectiveTestManager
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        try:
            ptm = ProspectiveTestManager(db_path)
            tid = ptm.register_test(
                question="Will it rain?",
                oracle_prediction={"rain": True},
                oracle_id="orc_003",
                oracle_version="v1",
                oracle_graph_hash="hash3",
                entropy_signature="ghi",
                time_horizon="1_day",
                domain="weather",
            )
            assert tid is not None
            assert ptm.freeze_test(tid) is True
            assert ptm.annotate_outcome(tid, "success", {"rained": True}) is True
            stats = ptm.compute_accuracy()
            assert stats["accuracy"] == 1.0
        finally:
            os.unlink(db_path)


class TestDisclaimer:
    def test_generate_disclaimer(self):
        from oracle.output.disclaimer import DisclaimerGenerator
        d = DisclaimerGenerator.generate_output_disclaimer("orc_001", 10, 0.8)
        assert "text" in d
        assert "brief" in d
        assert "content_hash" in d
        assert d["oracle_id"] == "orc_001"
        assert d["generation"] == 10
        assert d["confidence"] == 0.8
        assert len(d["text"]) > 100

    def test_risk_level(self):
        from oracle.output.disclaimer import DisclaimerGenerator
        assert DisclaimerGenerator.get_risk_level(0.9, "medical") == "CRITICAL"
        assert DisclaimerGenerator.get_risk_level(0.9, "general") == "HIGH_CONFIDENCE"
        assert DisclaimerGenerator.get_risk_level(0.5, "general") == "MODERATE"
        assert DisclaimerGenerator.get_risk_level(0.2, "general") == "LOW"


class TestLineageGraph:
    def test_add_and_render(self):
        from oracle.output.lineage_graph import LineageGraph
        graph = LineageGraph()
        graph.add_node("N1", "chr_1", 0, 0.5, [], ["gematria"], "initial")
        graph.add_node("N2", "chr_2", 1, 0.6, ["N1"], ["gematria", "iching"], "mutation")
        assert len(graph.nodes) == 2
        assert len(graph.edges) == 1
        text = graph.render_text()
        assert "N1" in text
        assert "N2" in text

    def test_stats(self):
        from oracle.output.lineage_graph import LineageGraph
        graph = LineageGraph()
        graph.add_node("N1", "chr_1", 0, 0.5)
        graph.add_node("N2", "chr_2", 1, 0.7)
        stats = graph.get_stats()
        assert stats["total_nodes"] == 2
        assert stats["max_fitness"] == 0.7
        assert stats["avg_fitness"] == 0.6


class TestMetaOracleSelector:
    def test_select(self):
        from oracle.evolution.meta_selector import MetaOracleSelector
        from oracle.genome.chromosome import Chromosome
        selector = MetaOracleSelector()
        pop = []
        for i in range(5):
            chrom = Chromosome.create_random([("gematria", "internal"), ("iching", "internal")])
            chrom.fitness = {"structural_coherence": 0.5 + i * 0.1, "response_stability": 0.5}
            pop.append(chrom)
        result = selector.select(pop, generation=1)
        assert result is not None
        assert result["score"] > 0
        assert result["rank"] == 1


class TestVersionTracker:
    def test_register_version(self):
        from oracle.memory.version_tracker import OracleVersionTracker
        from oracle.genome.chromosome import Chromosome
        with tempfile.TemporaryDirectory() as tmpdir:
            vt = OracleVersionTracker(tmpdir)
            chrom = Chromosome.create_random([("gematria", "internal")])
            chrom.fitness = {"total_fitness": 0.6}
            info = vt.register_version("orc_001", chrom, generation=0)
            assert info["version_id"] is not None
            assert info["oracle_id"] == "orc_001"
            assert info["generation"] == 0
            history = vt.get_lineage_history("orc_001")
            assert len(history) == 1
            stats = vt.get_stats()
            assert stats["total_versions"] == 1
