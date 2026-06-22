"""Crossover operators for evolutionary oracle - matches document section 18."""
import random
import copy
from ..genome.chromosome import Chromosome
from ..genome.gene import Gene


def uniform_crossover(parent1: Chromosome, parent2: Chromosome, rate: float = 0.5) -> tuple[Chromosome, Chromosome]:
    genes1, genes2 = {}, {}
    all_ids = set(parent1.genes.keys()) | set(parent2.genes.keys())

    for gid in all_ids:
        if random.random() < rate:
            if gid in parent1.genes:
                genes2[gid] = copy.deepcopy(parent1.genes[gid])
            if gid in parent2.genes:
                genes1[gid] = copy.deepcopy(parent2.genes[gid])
        else:
            if gid in parent1.genes:
                genes1[gid] = copy.deepcopy(parent1.genes[gid])
            if gid in parent2.genes:
                genes2[gid] = copy.deepcopy(parent2.genes[gid])

    child1 = Chromosome(
        chromosome_id="", genes=genes1,
        edges=parent1.edges[:] if random.random() < 0.5 else parent2.edges[:],
        fusion_schema=random.choice([parent1.fusion_schema, parent2.fusion_schema]).copy(),
        output_mapping=random.choice([parent1.output_mapping, parent2.output_mapping]).copy(),
    )
    child2 = Chromosome(
        chromosome_id="", genes=genes2,
        edges=parent2.edges[:] if random.random() < 0.5 else parent1.edges[:],
        fusion_schema=random.choice([parent2.fusion_schema, parent1.fusion_schema]).copy(),
        output_mapping=random.choice([parent2.output_mapping, parent1.output_mapping]).copy(),
    )
    return child1, child2


def subgraph_crossover(parent1: Chromosome, parent2: Chromosome) -> tuple[Chromosome, Chromosome]:
    child1_genes = copy.deepcopy(parent1.genes)
    child2_genes = copy.deepcopy(parent2.genes)

    if parent1.edges and parent2.edges:
        subgraph1 = random.sample(parent1.edges, min(2, len(parent1.edges)))
        subgraph2 = random.sample(parent2.edges, min(2, len(parent2.edges)))

        for src, dst in subgraph1:
            if src in child2_genes and dst in child2_genes:
                child2_genes[dst] = copy.deepcopy(child1_genes.get(src, child2_genes[dst]))
        for src, dst in subgraph2:
            if src in child1_genes and dst in child1_genes:
                child1_genes[dst] = copy.deepcopy(child2_genes.get(src, child1_genes[dst]))

    return (
        Chromosome(chromosome_id="", genes=child1_genes, edges=parent1.edges[:],
                   fusion_schema=parent1.fusion_schema.copy()),
        Chromosome(chromosome_id="", genes=child2_genes, edges=parent2.edges[:],
                   fusion_schema=parent2.fusion_schema.copy()),
    )


def civilization_crossover(parent1: Chromosome, parent2: Chromosome) -> tuple[Chromosome, Chromosome]:
    eastern = ["bazi", "ziwei", "qimen", "lunar_calendar"]
    western = ["astrology_western", "astrology_vedic", "skyfield_astro"]
    binary = ["iching", "geomancy", "raml"]

    def get_family(sys_id):
        for fam, systems in [("eastern", eastern), ("western", western), ("binary", binary)]:
            if sys_id in systems:
                return fam
        return "other"

    child1_genes = {}
    child2_genes = {}
    for gid, gene in parent1.genes.items():
        if get_family(gene.system_id) == "eastern" and gid in parent2.genes:
            child1_genes[gid] = copy.deepcopy(parent2.genes[gid])
        else:
            child1_genes[gid] = copy.deepcopy(gene)
    for gid, gene in parent2.genes.items():
        if get_family(gene.system_id) == "western" and gid in parent1.genes:
            child2_genes[gid] = copy.deepcopy(parent1.genes[gid])
        else:
            child2_genes[gid] = copy.deepcopy(gene)

    return (
        Chromosome(chromosome_id="", genes=child1_genes, edges=parent1.edges[:]),
        Chromosome(chromosome_id="", genes=child2_genes, edges=parent2.edges[:]),
    )


def rule_based_crossover(parent1: Chromosome, parent2: Chromosome) -> tuple[Chromosome, Chromosome]:
    child1_genes = copy.deepcopy(parent1.genes)
    child2_genes = copy.deepcopy(parent2.genes)

    p1_rules = parent1.fusion_rules or [{"type": "weighted_average"}]
    p2_rules = parent2.fusion_rules or [{"type": "weighted_average"}]

    new_fusion1 = parent1.fusion_schema.copy()
    new_fusion1["applied_rules"] = [r.get("rule_id", "default") for r in p1_rules[:2]]
    new_fusion2 = parent2.fusion_schema.copy()
    new_fusion2["applied_rules"] = [r.get("rule_id", "default") for r in p2_rules[:2]]

    return (
        Chromosome(chromosome_id="", genes=child1_genes, edges=parent1.edges[:],
                   fusion_schema=new_fusion1),
        Chromosome(chromosome_id="", genes=child2_genes, edges=parent2.edges[:],
                   fusion_schema=new_fusion2),
    )


def memory_based_crossover(parent1: Chromosome, parent2: Chromosome) -> tuple[Chromosome, Chromosome]:
    child1_genes = copy.deepcopy(parent1.genes)
    child2_genes = copy.deepcopy(parent2.genes)

    child1_links = list(set(parent1.memory_links + parent2.memory_links[:2]))
    child2_links = list(set(parent2.memory_links + parent1.memory_links[:2]))

    return (
        Chromosome(chromosome_id="", genes=child1_genes, edges=parent1.edges[:],
                   memory_links=child1_links),
        Chromosome(chromosome_id="", genes=child2_genes, edges=parent2.edges[:],
                   memory_links=child2_links),
    )


ALL_CROSSOVERS = [
    uniform_crossover, subgraph_crossover, civilization_crossover,
    rule_based_crossover, memory_based_crossover,
]
