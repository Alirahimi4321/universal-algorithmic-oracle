"""Tests for genome representations."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_gene():
    from oracle.genome.gene import Gene
    gene = Gene(gene_id="g1", system_id="iching", backend="internal",
                params={}, input_slots=["in"], output_slots=["out"],
                weight=0.5, mutation_policy={"rate": 0.1})
    assert gene.gene_id == "g1"
    assert gene.system_id == "iching"
    print("[PASS] test_gene")

def test_chromosome():
    from oracle.genome.chromosome import Chromosome
    from oracle.genome.gene import Gene
    genes = [Gene(gene_id=f"g{i}", system_id="gematria", backend="internal",
                  params={}, input_slots=[f"in_{i}"], output_slots=[f"out_{i}"],
                  weight=0.5, mutation_policy={}) for i in range(3)]
    chrom = Chromosome(chromosome_id="c1", genes=genes,
                       edges=[("g0","g1"),("g1","g2")],
                       fusion_schema={"type":"weighted_average"},
                       output_mapping={"output":"out_2"})
    assert chrom.chromosome_id == "c1"
    assert len(chrom.genes) == 3
    print("[PASS] test_chromosome")

def test_graph_genome():
    from oracle.genome.graph_genome import GraphGenome
    genome = GraphGenome.random("test_genome", 4)
    assert genome.size == 4
    assert genome.depth >= 1
    print("[PASS] test_graph_genome")

if __name__ == "__main__":
    test_gene()
    test_chromosome()
    test_graph_genome()
    print("=== ALL GENOME TESTS PASSED ===")
