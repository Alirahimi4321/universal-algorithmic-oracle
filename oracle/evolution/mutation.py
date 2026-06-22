"""Mutation operators for evolutionary oracle - matches document section 17."""
import random
import copy
from ..genome.chromosome import Chromosome
from ..genome.gene import Gene
from .deep_mutation import DeepMutationEngine
from .progressive_difficulty import ProgressiveDifficulty


def param_mutation(chromosome: Chromosome, rate: float = 0.1) -> Chromosome:
    new_genes = {}
    for gid, gene in chromosome.genes.items():
        new_params = gene.params.copy()
        for key in new_params:
            if isinstance(new_params[key], (int, float)) and random.random() < rate:
                new_params[key] *= 1.0 + random.gauss(0, 0.1)
        new_genes[gid] = Gene(
            gene_id=gene.gene_id,
            system_id=gene.system_id,
            backend=gene.backend,
            gene_type=gene.gene_type,
            params=new_params,
            input_slots=gene.input_slots[:],
            output_slots=gene.output_slots[:],
            weight=gene.weight,
            mutation_policy=gene.mutation_policy.copy(),
        )

    return Chromosome(
        chromosome_id=chromosome.chromosome_id,
        genes=new_genes,
        edges=chromosome.edges[:],
        fusion_schema=chromosome.fusion_schema.copy(),
        fusion_rules=chromosome.fusion_rules[:],
        output_mapping=chromosome.output_mapping.copy(),
        fitness=chromosome.fitness.copy() if isinstance(chromosome.fitness, dict) else {},
        system_configs=copy.deepcopy(chromosome.system_configs),
        custom_formulas=chromosome.custom_formulas.copy(),
        invented_methods=chromosome.invented_methods[:],
    )


def structural_mutation(chromosome: Chromosome, rate: float = 0.1) -> Chromosome:
    new_genes = {gid: Gene(
        gene_id=g.gene_id, system_id=g.system_id, backend=g.backend,
        gene_type=g.gene_type, params=g.params.copy(),
        input_slots=g.input_slots[:], output_slots=g.output_slots[:],
        weight=g.weight, mutation_policy=g.mutation_policy.copy(),
    ) for gid, g in chromosome.genes.items()}

    new_edges = chromosome.edges[:]

    if random.random() < rate and len(new_genes) > 1:
        ids = list(new_genes.keys())
        idx = random.choice(ids)
        systems = ["iching", "gematria", "tarot", "astrology", "numerology",
                    "bazi", "ziwei", "qimen", "runes", "geomancy"]
        new_sys = random.choice(systems)
        new_genes[idx] = Gene(
            gene_id=new_genes[idx].gene_id, system_id=new_sys,
            backend=new_genes[idx].backend, gene_type="symbolic_system",
            params=new_genes[idx].params.copy(),
            input_slots=new_genes[idx].input_slots[:],
            output_slots=new_genes[idx].output_slots[:],
            weight=random.random(),
            mutation_policy=new_genes[idx].mutation_policy.copy(),
        )

    if random.random() < rate and len(new_genes) >= 2:
        ids = list(new_genes.keys())
        src, dst = random.sample(ids, 2)
        edge = (src, dst)
        if edge not in new_edges:
            new_edges.append(edge)

    return Chromosome(
        chromosome_id=chromosome.chromosome_id,
        genes=new_genes,
        edges=new_edges,
        fusion_schema=chromosome.fusion_schema.copy(),
        fusion_rules=chromosome.fusion_rules[:],
        output_mapping=chromosome.output_mapping.copy(),
        fitness=chromosome.fitness.copy() if isinstance(chromosome.fitness, dict) else {},
        system_configs=copy.deepcopy(chromosome.system_configs),
        custom_formulas=chromosome.custom_formulas.copy(),
        invented_methods=chromosome.invented_methods[:],
    )


def civilization_mutation(chromosome: Chromosome, rate: float = 0.1) -> Chromosome:
    eastern = ["bazi", "ziwei", "qimen", "lunar_calendar", "tianji_bazi"]
    western = ["astrology_western", "astrology_vedic", "skyfield_astro"]
    binary = ["iching", "geomancy", "raml", "iching_shifa"]
    letter = ["gematria", "hebrew_gematria", "numerology", "runes"]

    new_genes = {}
    for gid, gene in chromosome.genes.items():
        if random.random() < rate:
            current_family = None
            for fam, systems in [("eastern", eastern), ("western", western),
                                 ("binary", binary), ("letter", letter)]:
                if gene.system_id in systems:
                    current_family = fam
                    break
            families = ["eastern", "western", "binary", "letter"]
            new_family = random.choice([f for f in families if f != current_family] or families)
            family_map = {"eastern": eastern, "western": western, "binary": binary, "letter": letter}
            new_sys = random.choice(family_map[new_family])
            new_genes[gid] = Gene(
                gene_id=gene.gene_id, system_id=new_sys, backend=gene.backend,
                gene_type="symbolic_system", params=gene.params.copy(),
                input_slots=gene.input_slots[:], output_slots=gene.output_slots[:],
                weight=gene.weight, mutation_policy=gene.mutation_policy.copy(),
            )
        else:
            new_genes[gid] = gene

    return Chromosome(
        chromosome_id=chromosome.chromosome_id, genes=new_genes,
        edges=chromosome.edges[:], fusion_schema=chromosome.fusion_schema.copy(),
        fusion_rules=chromosome.fusion_rules[:],
        output_mapping=chromosome.output_mapping.copy(),
        fitness=chromosome.fitness.copy() if isinstance(chromosome.fitness, dict) else {},
        system_configs=copy.deepcopy(chromosome.system_configs),
        custom_formulas=chromosome.custom_formulas.copy(),
        invented_methods=chromosome.invented_methods[:],
    )


def dimensional_mutation(chromosome: Chromosome, rate: float = 0.1) -> Chromosome:
    new_genes = {}
    for gid, gene in chromosome.genes.items():
        if random.random() < rate:
            new_params = gene.params.copy()
            new_params["dimension_shift"] = random.randint(2, 8)
            new_params["state_count"] = random.choice([64, 128, 256, 1024])
            new_genes[gid] = Gene(
                gene_id=gene.gene_id, system_id=gene.system_id, backend=gene.backend,
                gene_type=gene.gene_type, params=new_params,
                input_slots=gene.input_slots[:], output_slots=gene.output_slots[:],
                weight=gene.weight, mutation_policy=gene.mutation_policy.copy(),
            )
        else:
            new_genes[gid] = gene

    return Chromosome(
        chromosome_id=chromosome.chromosome_id, genes=new_genes,
        edges=chromosome.edges[:], fusion_schema=chromosome.fusion_schema.copy(),
        fusion_rules=chromosome.fusion_rules[:],
        output_mapping=chromosome.output_mapping.copy(),
        fitness=chromosome.fitness.copy() if isinstance(chromosome.fitness, dict) else {},
        system_configs=copy.deepcopy(chromosome.system_configs),
        custom_formulas=chromosome.custom_formulas.copy(),
        invented_methods=chromosome.invented_methods[:],
    )


def rule_making_mutation(chromosome: Chromosome, rate: float = 0.1) -> Chromosome:
    new_fusion = chromosome.fusion_schema.copy()
    if random.random() < rate:
        fusion_types = ["weighted_average", "modular_resonance", "xor_fusion",
                        "tree_combination", "swarm_fusion", "rule_based"]
        new_fusion["type"] = random.choice(fusion_types)

    new_rules = chromosome.fusion_rules[:]
    if random.random() < rate:
        new_rules.append({
            "rule_id": f"rule_{random.randint(0,99999)}",
            "condition": random.choice(["diversity_high", "diversity_low", "convergence"]),
            "action": random.choice(["prune", "expand", "rewire", "freeze"]),
        })

    return Chromosome(
        chromosome_id=chromosome.chromosome_id,
        genes=copy.deepcopy(chromosome.genes),
        edges=chromosome.edges[:], fusion_schema=new_fusion,
        fusion_rules=new_rules,
        output_mapping=chromosome.output_mapping.copy(),
        fitness=chromosome.fitness.copy() if isinstance(chromosome.fitness, dict) else {},
        system_configs=copy.deepcopy(chromosome.system_configs),
        custom_formulas=chromosome.custom_formulas.copy(),
        invented_methods=chromosome.invented_methods[:],
    )


def anti_traditional_mutation(chromosome: Chromosome, rate: float = 0.1) -> Chromosome:
    new_genes = {}
    for gid, gene in chromosome.genes.items():
        if random.random() < rate:
            new_params = gene.params.copy()
            new_params["anti_traditional"] = True
            new_params["tradition_break"] = random.choice([
                "inverted_logic", "cross_civilization", "dimensional_shift",
                "rule_inversion", "entropy_maximization",
            ])
            new_genes[gid] = Gene(
                gene_id=gene.gene_id, system_id=gene.system_id, backend=gene.backend,
                gene_type="transform", params=new_params,
                input_slots=gene.input_slots[:], output_slots=gene.output_slots[:],
                weight=gene.weight * 1.2,
                mutation_policy=gene.mutation_policy.copy(),
            )
        else:
            new_genes[gid] = gene

    return Chromosome(
        chromosome_id=chromosome.chromosome_id, genes=new_genes,
        edges=chromosome.edges[:], fusion_schema=chromosome.fusion_schema.copy(),
        fusion_rules=chromosome.fusion_rules[:],
        output_mapping=chromosome.output_mapping.copy(),
        fitness=chromosome.fitness.copy() if isinstance(chromosome.fitness, dict) else {},
        system_configs=copy.deepcopy(chromosome.system_configs),
        custom_formulas=chromosome.custom_formulas.copy(),
        invented_methods=chromosome.invented_methods[:],
    )


def deep_system_mutation(chromosome: Chromosome, rate: float = 0.1,
                        difficulty: ProgressiveDifficulty = None) -> Chromosome:
    """Deep mutation that modifies internal logic of symbolic systems."""
    if random.random() > rate:
        return chromosome

    engine = DeepMutationEngine()
    intensity = difficulty.get_evolution_params()["mutation_intensity"] if difficulty else 0.3

    new_configs = copy.deepcopy(chromosome.system_configs)
    for gene in chromosome.gene_list:
        if random.random() < rate and gene.system_id not in new_configs:
            from ..symbolic.modifiable import ModifiableSystem, SystemConfig, SystemParameter
            config = SystemConfig(
                system_id=gene.system_id,
                parameters={
                    "weight": SystemParameter("weight", gene.weight, "float", 0.1, 5.0),
                    "precision": SystemParameter("precision", 64, "int", 8, 256),
                    "amplitude": SystemParameter("amplitude", 1.0, "float", 0.01, 10.0),
                    "phase_offset": SystemParameter("phase_offset", 0.0, "float", 0, 6.28),
                },
            )
            new_configs[gene.system_id] = config

        if gene.system_id in new_configs and random.random() < rate:
            old_config = new_configs[gene.system_id]
            new_configs[gene.system_id] = old_config.mutate_params(intensity)

    new_formulas = chromosome.custom_formulas.copy()
    if random.random() < rate * 0.5:
        from ..symbolic.modifiable import FormulaEngine
        formula = FormulaEngine.random_formula(random.randint(1, 3))
        new_formulas[f"deep_formula_{len(new_formulas)}"] = formula

    return Chromosome(
        chromosome_id=chromosome.chromosome_id,
        genes=copy.deepcopy(chromosome.genes),
        edges=chromosome.edges[:],
        fusion_schema=chromosome.fusion_schema.copy(),
        fusion_rules=chromosome.fusion_rules[:],
        output_mapping=chromosome.output_mapping.copy(),
        fitness=chromosome.fitness.copy() if isinstance(chromosome.fitness, dict) else {},
        system_configs=new_configs,
        custom_formulas=new_formulas,
        invented_methods=chromosome.invented_methods[:],
    )


ALL_MUTATIONS = [
    param_mutation, structural_mutation, civilization_mutation,
    dimensional_mutation, rule_making_mutation, anti_traditional_mutation,
    deep_system_mutation,
]
