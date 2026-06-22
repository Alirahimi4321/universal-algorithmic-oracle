"""Tests for memory modules."""
import sys, os, tempfile
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_archive():
    from oracle.memory.archive import EvolutionaryMemory
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    try:
        mem = EvolutionaryMemory(db_path)
        print("[PASS] test_archive")
    finally:
        os.unlink(db_path)

def test_mutation_bank():
    from oracle.memory.mutation_bank import MutationBank
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    try:
        bank = MutationBank(db_path)
        print("[PASS] test_mutation_bank")
    finally:
        os.unlink(db_path)

def test_experiment_ledger():
    from oracle.memory.experiment_ledger import ExperimentLedger
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    try:
        ledger = ExperimentLedger(db_path)
        print("[PASS] test_experiment_ledger")
    finally:
        os.unlink(db_path)

def test_lineage():
    from oracle.memory.lineage import LineageTracker
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    try:
        tracker = LineageTracker(db_path)
        tracker.record_birth("c1", generation=0)
        parents = tracker.get_parents("c1")
        assert parents == []
        print("[PASS] test_lineage")
    finally:
        os.unlink(db_path)

def test_fitness_history():
    from oracle.memory.fitness_history import FitnessHistory
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    try:
        history = FitnessHistory(db_path)
        history.record("c1", 0, {"score": 0.5})
        h = history.get_history("c1")
        assert len(h) == 1
        print("[PASS] test_fitness_history")
    finally:
        os.unlink(db_path)

if __name__ == "__main__":
    test_archive()
    test_mutation_bank()
    test_experiment_ledger()
    test_lineage()
    test_fitness_history()
    print("=== ALL MEMORY TESTS PASSED ===")
