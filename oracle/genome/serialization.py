"""Serialization/deserialization for genomes and chromosomes."""
import json
import time
from .gene import Gene
from .chromosome import Chromosome

def serialize_gene(gene: Gene) -> dict:
    return {
        "gene_id": gene.gene_id,
        "system_id": gene.system_id,
        "backend": gene.backend,
        "params": gene.params,
        "input_slots": gene.input_slots,
        "output_slots": gene.output_slots,
        "weight": gene.weight,
        "mutation_policy": gene.mutation_policy,
    }

def deserialize_gene(data: dict) -> Gene:
    return Gene(
        gene_id=data["gene_id"],
        system_id=data["system_id"],
        backend=data.get("backend", "internal"),
        params=data.get("params", {}),
        input_slots=data.get("input_slots", []),
        output_slots=data.get("output_slots", []),
        weight=data.get("weight", 0.5),
        mutation_policy=data.get("mutation_policy", {}),
    )

def serialize_chromosome(chromosome: Chromosome) -> dict:
    genes_dict = chromosome.genes
    if isinstance(genes_dict, dict):
        genes_serialized = {k: serialize_gene(v) for k, v in genes_dict.items()}
    else:
        genes_serialized = {g.gene_id: serialize_gene(g) for g in genes_dict}
    
    return {
        "chromosome_id": chromosome.chromosome_id,
        "genes": genes_serialized,
        "edges": chromosome.edges,
        "fusion_schema": chromosome.fusion_schema,
        "output_mapping": chromosome.output_mapping,
        "fitness": chromosome.fitness,
        "metadata": getattr(chromosome, 'metadata', {}),
        "timestamp": time.time(),
    }

def deserialize_chromosome(data: dict) -> Chromosome:
    genes = {k: deserialize_gene(v) for k, v in data.get("genes", {}).items()}
    return Chromosome(
        chromosome_id=data["chromosome_id"],
        genes=genes,
        edges=data.get("edges", []),
        fusion_schema=data.get("fusion_schema", {"type": "weighted_average"}),
        output_mapping=data.get("output_mapping", {}),
        fitness=data.get("fitness"),
    )

def serialize_population(population: list[Chromosome]) -> str:
    return json.dumps([serialize_chromosome(c) for c in population], indent=2, default=str)

def deserialize_population(data_str: str) -> list[Chromosome]:
    data = json.loads(data_str)
    return [deserialize_chromosome(c) for c in data]

def save_to_file(chromosome: Chromosome, filepath: str):
    with open(filepath, "w") as f:
        json.dump(serialize_chromosome(chromosome), f, indent=2, default=str)

def load_from_file(filepath: str) -> Chromosome:
    with open(filepath) as f:
        return deserialize_chromosome(json.load(f))
