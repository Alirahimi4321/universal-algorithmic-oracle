"""Tests for mutation operators."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_param_mutation():
    from oracle.evolution.mutation import param_mutation
    from oracle.genome.chromosome import Chromosome
    from oracle.genome.gene import Gene
    genes = {"g0": Gene(gene_id="g0", system_id="iching", backend="internal",
                  params={"weight": 0.5}, input_slots=["in"], output_slots=["out"],
                  weight=0.5, mutation_policy={"param_mutation_rate": 0.5})}
    chrom = Chromosome(chromosome_id="c1", genes=genes, edges=[],
                       fusion_schema={}, output_mapping={})
    mutated = param_mutation(chrom, rate=1.0)
    assert mutated.chromosome_id == chrom.chromosome_id
    print("[PASS] test_param_mutation")

def test_structural_mutation():
    from oracle.evolution.mutation import structural_mutation
    from oracle.genome.chromosome import Chromosome
    from oracle.genome.gene import Gene
    genes = {f"g{i}": Gene(gene_id=f"g{i}", system_id="gematria", backend="internal",
                  params={}, input_slots=[f"in_{i}"], output_slots=[f"out_{i}"],
                  weight=0.5, mutation_policy={}) for i in range(3)}
    chrom = Chromosome(chromosome_id="c1", genes=genes,
                       edges=[("g0","g1"),("g1","g2")],
                       fusion_schema={}, output_mapping={})
    mutated = structural_mutation(chrom, rate=1.0)
    assert mutated.chromosome_id == chrom.chromosome_id
    print("[PASS] test_structural_mutation")

if __name__ == "__main__":
    test_param_mutation()
    test_structural_mutation()
    print("=== ALL MUTATION TESTS PASSED ===")
