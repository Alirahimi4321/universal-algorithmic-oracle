"""Tests for fitness evaluation."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_fitness():
    from oracle.evaluation.fitness import FitnessEvaluator
    from oracle.genome.chromosome import Chromosome
    from oracle.genome.gene import Gene
    genes = {f"g{i}": Gene(gene_id=f"g{i}", system_id="gematria", backend="internal",
                  params={}, input_slots=[f"in_{i}"], output_slots=[f"out_{i}"],
                  weight=0.5, mutation_policy={}) for i in range(3)}
    chrom = Chromosome(chromosome_id="c1", genes=genes,
                       edges=[("g0","g1"),("g1","g2")],
                       fusion_schema={"type":"weighted_average"},
                       output_mapping={"output":"out_2"})
    evaluator = FitnessEvaluator()
    packet = {"bit_stream": [1,0,1]*10, "seed": 42, "numeric_vector": [1,2,3],
              "normalized_text": "test", "calendar_context": {}}
    fitness = evaluator.evaluate(chrom, packet)
    assert "structural_coherence" in fitness
    assert "oracle_confidence" in fitness
    print("[PASS] test_fitness")

if __name__ == "__main__":
    test_fitness()
    print("=== ALL FITNESS TESTS PASSED ===")
