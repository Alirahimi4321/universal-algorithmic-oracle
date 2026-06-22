"""Structural expansion engine for oracle chromosomes."""
import random
import copy
from ..genome.chromosome import Chromosome
from ..genome.gene import Gene
from ..symbolic.registry import list_systems


def expand_chromosome(chromosome: Chromosome, rate: float = 0.1) -> Chromosome:
    if random.random() > rate:
        return chromosome

    systems = list_systems()
    if not systems:
        return chromosome

    new_system = random.choice(systems)
    new_gene = Gene(
        gene_id=f"exp_{random.randint(0, 99999)}",
        system_id=new_system,
        backend="internal",
        params={},
        input_slots=["input_exp"],
        output_slots=["output_exp"],
        weight=random.uniform(0.1, 1.0),
        mutation_policy={"param_mutation_rate": 0.1, "structural_mutation_rate": 0.05},
    )

    new_genes = copy.deepcopy(chromosome.genes)
    new_genes[new_gene.gene_id] = new_gene
    new_edges = list(chromosome.edges)
    if chromosome.genes:
        last_id = list(chromosome.genes.keys())[-1]
        new_edges.append((last_id, new_gene.gene_id))

    return Chromosome(
        chromosome_id=chromosome.chromosome_id,
        genes=new_genes,
        edges=new_edges,
        fusion_schema=copy.deepcopy(chromosome.fusion_schema),
        output_mapping=copy.deepcopy(chromosome.output_mapping),
        fitness=copy.deepcopy(chromosome.fitness),
    )


def contract_chromosome(chromosome: Chromosome, rate: float = 0.1) -> Chromosome:
    if random.random() > rate or len(chromosome.genes) <= 2:
        return chromosome

    ids = list(chromosome.genes.keys())
    remove_id = random.choice(ids)
    new_genes = {k: copy.deepcopy(v) for k, v in chromosome.genes.items() if k != remove_id}
    new_edges = [(f, t) for f, t in chromosome.edges if f != remove_id and t != remove_id]

    return Chromosome(
        chromosome_id=chromosome.chromosome_id,
        genes=new_genes,
        edges=new_edges,
        fusion_schema=copy.deepcopy(chromosome.fusion_schema),
        output_mapping=copy.deepcopy(chromosome.output_mapping),
        fitness=copy.deepcopy(chromosome.fitness),
    )


def add_connection(chromosome: Chromosome, rate: float = 0.1) -> Chromosome:
    if random.random() > rate or len(chromosome.genes) < 2:
        return chromosome

    ids = list(chromosome.genes.keys())
    g1, g2 = random.sample(ids, 2)
    new_edge = (g1, g2)

    if new_edge not in chromosome.edges:
        new_edges = list(chromosome.edges) + [new_edge]
        return Chromosome(
            chromosome_id=chromosome.chromosome_id,
            genes=copy.deepcopy(chromosome.genes),
            edges=new_edges,
            fusion_schema=copy.deepcopy(chromosome.fusion_schema),
            output_mapping=copy.deepcopy(chromosome.output_mapping),
            fitness=copy.deepcopy(chromosome.fitness),
        )
    return chromosome
