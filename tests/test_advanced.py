"""Advanced tests - not just smoke tests. Tests real functionality per design doc."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_topological_execution():
    """Test that chromosome execution respects graph topology."""
    from oracle.genome.chromosome import Chromosome
    from oracle.genome.gene import Gene
    from oracle.entropy.encoder import EntropyEncoder

    genes = {
        'g1': Gene(gene_id='g1', system_id='gematria', backend='internal',
            params={}, input_slots=['in'], output_slots=['out'], weight=0.8, mutation_policy={}),
        'g2': Gene(gene_id='g2', system_id='iching', backend='internal',
            params={}, input_slots=['in'], output_slots=['out'], weight=0.6, mutation_policy={}),
        'g3': Gene(gene_id='g3', system_id='tarot', backend='internal',
            params={}, input_slots=['in'], output_slots=['out'], weight=0.7, mutation_policy={}),
    }
    edges = [('g1', 'g2'), ('g1', 'g3'), ('g2', 'g3')]
    chrom = Chromosome(chromosome_id='test', genes=genes, edges=edges,
                       fusion_schema={'type': 'weighted_average'},
                       output_mapping={'output': 'g3'})

    topo = chrom._topological_sort()
    assert topo.index('g1') < topo.index('g2'), "g1 must execute before g2"
    assert topo.index('g1') < topo.index('g3'), "g1 must execute before g3"
    assert topo.index('g2') < topo.index('g3'), "g2 must execute before g3"

    packet = EntropyEncoder().encode('test')
    result = chrom.execute(packet)
    assert result['oracle_confidence'] > 0, "Confidence must be > 0"
    assert '_graph_structure' in result['symbolic_state'], "Graph structure must be in output"
    print("[PASS] test_topological_execution")


def test_pure_entropy_test():
    """Test the Pure Entropy Test module (f1)."""
    from oracle.evaluation.pure_entropy_test import PureEntropyTest, PureEntropyResult
    from oracle.genome.chromosome import Chromosome
    from oracle.genome.gene import Gene
    from oracle.entropy.encoder import EntropyEncoder

    test = PureEntropyTest({"curriculum_level": 1})
    rows, cols = test.get_curriculum_dimensions()
    assert rows == 1 and cols == 1, "Level 1 should be 1x1"

    test.curriculum_level = 2
    rows, cols = test.get_curriculum_dimensions()
    assert rows == 3 and cols == 4, "Level 2 should be 3x4"

    matrix = test.generate_secret_matrix(rows, cols)
    assert len(matrix) == rows, "Matrix rows must match"
    assert all(len(r) == cols for r in matrix), "Matrix cols must match"
    assert all(0 <= v < 100 for row in matrix for v in row), "Values must be 0-99"

    genes = {f'g{i}': Gene(gene_id=f'g{i}', system_id='gematria', backend='internal',
        params={}, input_slots=[f'in_{i}'], output_slots=[f'out_{i}'],
        weight=0.5, mutation_policy={}) for i in range(3)}
    chrom = Chromosome(chromosome_id='test', genes=genes,
        edges=[('g0','g1'),('g1','g2')], fusion_schema={'type':'weighted_average'},
        output_mapping={'output':'g2'})
    packet = EntropyEncoder().encode('test')

    from oracle.evaluation.pure_entropy_test import default_oracle_predict
    result = test.evaluate_oracle(chrom, packet, default_oracle_predict)
    assert isinstance(result, PureEntropyResult), "Result must be PureEntropyResult"
    assert result.mae >= 0, "MAE must be non-negative"
    assert result.rmse >= 0, "RMSE must be non-negative"

    fitness = test.fitness_from_result(result)
    assert 0.0 <= fitness <= 1.0, "Fitness must be between 0 and 1"
    print("[PASS] test_pure_entropy_test")


def test_historical_blind_test():
    """Test the Historical Blind Test module (f2)."""
    from oracle.evaluation.historical_blind_test import (
        HistoricalBlindTest, HistoricalTestPacket, HistoricalTestResult
    )
    from oracle.genome.chromosome import Chromosome
    from oracle.genome.gene import Gene

    test = HistoricalBlindTest()
    stats = test.get_test_bank_stats()
    assert stats["total_tests"] >= 5, "Must have at least 5 historical tests"
    assert stats["outcomes"]["positive"] > 0, "Must have positive outcomes"
    assert stats["outcomes"]["negative"] > 0, "Must have negative outcomes"

    genes = {f'g{i}': Gene(gene_id=f'g{i}', system_id='gematria', backend='internal',
        params={}, input_slots=[f'in_{i}'], output_slots=[f'out_{i}'],
        weight=0.5, mutation_policy={}) for i in range(2)}
    chrom = Chromosome(chromosome_id='test', genes=genes,
        edges=[], fusion_schema={'type':'weighted_average'},
        output_mapping={'output': 'g1'})

    from oracle.evaluation.historical_blind_test import default_oracle_prophesy
    results = test.evaluate_oracle(chrom, default_oracle_prophesy, num_tests=3)
    assert len(results) == 3, "Must return 3 results"
    assert all(isinstance(r, HistoricalTestResult) for r in results), "All must be HistoricalTestResult"
    assert all(r.prediction in [0, 1] for r in results), "Predictions must be binary"
    assert all(0 <= r.confidence <= 1 for r in results), "Confidence must be 0-1"

    accuracy = test.compute_accuracy(results)
    assert 0.0 <= accuracy <= 1.0, "Accuracy must be 0-1"
    print("[PASS] test_historical_blind_test")


def test_adaptive_rates():
    """Test the Adaptive Rate Controller."""
    from oracle.evolution.adaptive_rates import AdaptiveRateController, compute_population_diversity
    from oracle.genome.chromosome import Chromosome
    from oracle.genome.gene import Gene

    ctrl = AdaptiveRateController()
    rates = ctrl.get_rates()
    assert rates["mutation_rate"] > 0, "Mutation rate must be positive"
    assert rates["crossover_rate"] > 0, "Crossover rate must be positive"

    ctrl.update(10, 0.5, 0.8)
    rates = ctrl.get_rates()
    assert rates["mutation_rate"] > 0, "Mutation rate must be positive after update"

    genes = {f'g{i}': Gene(gene_id=f'g{i}', system_id='gematria', backend='internal',
        params={}, input_slots=[f'in_{i}'], output_slots=[f'out_{i}'],
        weight=0.5, mutation_policy={}) for i in range(3)}
    chrom = Chromosome(chromosome_id='c1', genes=genes, edges=[], fusion_schema={},
                       output_mapping={})
    diversity = compute_population_diversity([chrom])
    assert 0.0 <= diversity <= 1.0, "Diversity must be 0-1"
    print("[PASS] test_adaptive_rates")


def test_evolved_fusion():
    """Test the Evolved Fusion Tree."""
    from oracle.fusion.evolved_fusion import EvolvedFusionTree, EvolvedFusion

    tree = EvolvedFusionTree.random(depth=2)
    assert tree.tree["op"] in EvolvedFusionTree.OPERATORS, "Random tree must have valid op"

    vectors = [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]
    states = [{"element": "fire", "phase": "active"}, {"element": "water", "phase": "resting"}]
    result = tree.evaluate(vectors, states)
    assert "numeric" in result, "Result must have numeric"
    assert "symbolic" in result, "Result must have symbolic"
    assert len(result["numeric"]) > 0, "Numeric must not be empty"

    fused = EvolvedFusion({"fusion_method": "evolved"})
    result = fused.fuse(vectors, states)
    assert "numeric" in result, "EvolvedFusion result must have numeric"
    assert "symbolic" in result, "EvolvedFusion result must have symbolic"
    print("[PASS] test_evolved_fusion")


def test_fitness_with_new_tests():
    """Test fitness evaluator uses Pure Entropy and Historical tests."""
    from oracle.evaluation.fitness import FitnessEvaluator
    from oracle.genome.chromosome import Chromosome
    from oracle.genome.gene import Gene
    from oracle.entropy.encoder import EntropyEncoder

    genes = {f'g{i}': Gene(gene_id=f'g{i}', system_id='gematria', backend='internal',
        params={}, input_slots=[f'in_{i}'], output_slots=[f'out_{i}'],
        weight=0.5, mutation_policy={}) for i in range(3)}
    chrom = Chromosome(chromosome_id='test', genes=genes,
        edges=[('g0','g1'),('g1','g2')], fusion_schema={'type':'weighted_average'},
        output_mapping={'output':'g2'})
    packet = EntropyEncoder().encode('آیا این پروژه موفق می‌شود؟')

    ev = FitnessEvaluator({'use_pure_entropy': True, 'use_historical_blind': True})
    fitness = ev.evaluate(chrom, packet, generation=10)
    assert "pure_entropy_fitness" in fitness, "Must have pure_entropy_fitness"
    assert "historical_accuracy_fitness" in fitness, "Must have historical_accuracy_fitness"
    assert "total_fitness" in fitness, "Must have total_fitness"
    assert fitness["total_fitness"] > 0, "Total fitness must be positive"
    assert 0.0 <= fitness["pure_entropy_fitness"] <= 1.0, "Pure entropy fitness must be 0-1"
    assert 0.0 <= fitness["historical_accuracy_fitness"] <= 1.0, "Historical accuracy must be 0-1"
    print("[PASS] test_fitness_with_new_tests")


if __name__ == "__main__":
    test_topological_execution()
    test_pure_entropy_test()
    test_historical_blind_test()
    test_adaptive_rates()
    test_evolved_fusion()
    test_fitness_with_new_tests()
    print("\n=== ALL ADVANCED TESTS PASSED ===")