"""Tests for crossover operators."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_uniform_crossover():
    from oracle.evolution.crossover import uniform_crossover
    from oracle.genome.chromosome import Chromosome
    from oracle.genome.gene import Gene
    g1 = {f"a{i}": Gene(gene_id=f"a{i}", system_id="gematria", backend="internal",
               params={}, input_slots=[f"in_{i}"], output_slots=[f"out_{i}"],
               weight=0.5, mutation_policy={}) for i in range(3)}
    g2 = {f"b{i}": Gene(gene_id=f"b{i}", system_id="iching", backend="internal",
               params={}, input_slots=[f"in_{i}"], output_slots=[f"out_{i}"],
               weight=0.5, mutation_policy={}) for i in range(3)}
    p1 = Chromosome(chromosome_id="p1", genes=g1, edges=[], fusion_schema={}, output_mapping={})
    p2 = Chromosome(chromosome_id="p2", genes=g2, edges=[], fusion_schema={}, output_mapping={})
    c1, c2 = uniform_crossover(p1, p2, rate=0.5)
    assert c1.chromosome_id != "p1"
    assert c2.chromosome_id != "p2"
    print("[PASS] test_uniform_crossover")

if __name__ == "__main__":
    test_uniform_crossover()
    print("=== ALL CROSSOVER TESTS PASSED ===")
