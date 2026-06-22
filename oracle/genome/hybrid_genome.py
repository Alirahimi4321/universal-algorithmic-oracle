"""Hybrid Genome - combines linear, tree, and graph representations."""
import random
import hashlib
from dataclasses import dataclass, field
from ..genome.gene import Gene
from ..genome.chromosome import Chromosome


@dataclass
class HybridGenome:
    genome_id: str
    linear_part: list[Gene] = field(default_factory=list)
    tree_root: dict = field(default_factory=dict)
    graph_edges: list[tuple[str, str]] = field(default_factory=list)
    fusion_weights: dict = field(default_factory=dict)
    fitness: dict = field(default_factory=dict)

    def to_chromosome(self) -> Chromosome:
        genes = {}
        for g in self.linear_part:
            genes[g.gene_id] = g
        if self.tree_root:
            self._extract_genes_from_tree(self.tree_root, genes)
        return Chromosome(
            chromosome_id=self.genome_id,
            genes=genes,
            edges=self.graph_edges,
            fusion_schema={"type": "hybrid", "weights": self.fusion_weights},
        )

    def _extract_genes_from_tree(self, node: dict, genes: dict):
        if "gene" in node:
            g = node["gene"]
            genes[g.gene_id] = g
        for child in node.get("children", []):
            self._extract_genes_from_tree(child, genes)

    @classmethod
    def from_chromosome(cls, chrom: Chromosome) -> "HybridGenome":
        genes_list = chrom.gene_list
        return cls(
            genome_id=chrom.chromosome_id,
            linear_part=genes_list[:len(genes_list)//2],
            tree_root={"gene": genes_list[0] if genes_list else None,
                       "children": [{"gene": g} for g in genes_list[len(genes_list)//2:]]},
            graph_edges=chrom.edges[:],
        )

    @classmethod
    def create_random(cls, systems: list[str] = None) -> "HybridGenome":
        if systems is None:
            from ..symbolic.registry import list_systems
            systems = list(list_systems())[:6]

        linear_genes = []
        tree_children = []
        for i, sys_id in enumerate(systems):
            gene = Gene(
                gene_id=hashlib.md5(f"hybrid_{sys_id}_{i}_{random.random()}".encode()).hexdigest()[:8],
                system_id=sys_id, backend="internal", gene_type="symbolic_system",
                params={}, input_slots=[f"in_{i}"], output_slots=[f"out_{i}"],
                weight=random.uniform(0.1, 1.0),
                mutation_policy={"param_mutation_rate": 0.1},
            )
            if i % 2 == 0:
                linear_genes.append(gene)
            else:
                tree_children.append({"gene": gene})

        tree_root = {
            "gene": linear_genes[0] if linear_genes else None,
            "children": tree_children,
        }

        edges = [(linear_genes[i].gene_id, linear_genes[i+1].gene_id)
                 for i in range(len(linear_genes)-1)]

        return cls(
            genome_id=hashlib.md5(f"hybrid_{random.random()}".encode()).hexdigest()[:8],
            linear_part=linear_genes,
            tree_root=tree_root,
            graph_edges=edges,
        )
