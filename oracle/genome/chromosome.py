"""Chromosome representation for oracle structures - matches document section 14.2."""
import random
import hashlib
import math
from dataclasses import dataclass, field
from typing import Any
from .gene import Gene


@dataclass
class Chromosome:
    chromosome_id: str
    genes: dict[str, Gene] = field(default_factory=dict)
    edges: list[tuple[str, str]] = field(default_factory=list)
    fusion_schema: dict = field(default_factory=dict)
    fusion_rules: list[dict] = field(default_factory=list)
    output_mapping: dict = field(default_factory=dict)
    fitness: dict = field(default_factory=dict)
    metadata: dict = field(default_factory=dict)
    generation: int = 0
    lineage_id: str = ""
    representation: str = "graph"
    memory_links: list[str] = field(default_factory=list)
    system_configs: dict = field(default_factory=dict)
    custom_formulas: dict = field(default_factory=dict)
    invented_methods: list = field(default_factory=list)

    @property
    def gene_list(self) -> list[Gene]:
        return list(self.genes.values())

    def get_gene(self, gene_id: str) -> Gene | None:
        return self.genes.get(gene_id)

    def add_gene(self, gene: Gene):
        self.genes[gene.gene_id] = gene

    def remove_gene(self, gene_id: str):
        if gene_id in self.genes:
            del self.genes[gene_id]

    def get_fitness_score(self) -> float:
        if isinstance(self.fitness, dict):
            return self.fitness.get("total_fitness", 0.0)
        return float(self.fitness) if self.fitness else 0.0

    def size(self) -> int:
        return len(self.genes)

    @property
    def depth(self) -> int:
        if not self.edges:
            return 1
        node_deps = {}
        for src, dst in self.edges:
            if dst not in node_deps:
                node_deps[dst] = []
            node_deps[dst].append(src)

        def get_depth(node, visited=None):
            if visited is None:
                visited = set()
            if node in visited:
                return 0
            visited.add(node)
            if node not in node_deps or not node_deps[node]:
                return 1
            return 1 + max((get_depth(dep, visited) for dep in node_deps[node]), default=0)

        all_nodes = set()
        for src, dst in self.edges:
            all_nodes.add(src)
            all_nodes.add(dst)
        if not all_nodes:
            return 1
        return max((get_depth(n) for n in all_nodes), default=1)

    def execute(self, entropy_packet: dict) -> dict:
        """Execute chromosome as a directed graph with topological data flow."""
        from ..symbolic.registry import compute_system
        from ..symbolic.modifiable import FormulaEngine, ModifiableSystem
        
        if not self.genes:
            return {"fused_numeric": [], "symbolic_state": {}, "oracle_confidence": 0.0}

        # Build adjacency list and compute topological order
        topo_order = self._topological_sort()
        if not topo_order:
            return {"fused_numeric": [], "symbolic_state": {}, "oracle_confidence": 0.0}

        # Execute genes in topological order, passing data through edges
        gene_outputs = {}
        for gene_id in topo_order:
            gene = self.genes.get(gene_id)
            if not gene:
                continue
            
            # Prepare input for this gene from upstream genes
            gene_input = self._prepare_gene_input(gene_id, gene_outputs, entropy_packet)
            
            try:
                sys_config = self.system_configs.get(gene.system_id, None)
                if sys_config:
                    wrapper = self._get_wrapper(gene.system_id)
                    if wrapper:
                        mod_sys = ModifiableSystem(wrapper, sys_config)
                        result = mod_sys.compute(gene_input)
                        gene_outputs[gene_id] = result
                        continue
                result = compute_system(gene.system_id, gene_input, gene.params)
                gene_outputs[gene_id] = result
            except Exception as e:
                import logging
                logging.getLogger(__name__).warning(
                    "Gene %s (%s) execution failed: %s", gene_id, gene.system_id, e
                )
                gene_outputs[gene_id] = None
                continue

        # Apply fusion according to output_mapping and fusion_schema
        return self._apply_graph_fusion(gene_outputs)

    def _topological_sort(self) -> list[str]:
        """Kahn's algorithm for topological sorting of genes."""
        if not self.edges:
            return list(self.genes.keys())
        
        in_degree = {gid: 0 for gid in self.genes}
        adj = {gid: [] for gid in self.genes}
        
        for src, dst in self.edges:
            if src in self.genes and dst in self.genes:
                adj[src].append(dst)
                in_degree[dst] += 1
        
        queue = [gid for gid, deg in in_degree.items() if deg == 0]
        topo = []
        
        while queue:
            node = queue.pop(0)
            topo.append(node)
            for neighbor in adj.get(node, []):
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        
        # If cycle detected, return all nodes anyway
        if len(topo) != len(self.genes):
            return list(self.genes.keys())
        return topo

    def _prepare_gene_input(self, gene_id: str, gene_outputs: dict, entropy_packet: dict) -> dict:
        """Prepare input packet for a gene from its upstream dependencies."""
        # Find upstream genes
        upstream = [src for src, dst in self.edges if dst == gene_id]
        
        # Start with entropy packet as base
        input_packet = entropy_packet.copy() if isinstance(entropy_packet, dict) else entropy_packet.__dict__.copy()
        
        # Merge upstream outputs
        for upstream_id in upstream:
            upstream_result = gene_outputs.get(upstream_id)
            if upstream_result and hasattr(upstream_result, 'symbolic_state'):
                # Merge symbolic state
                if 'upstream_symbolic' not in input_packet:
                    input_packet['upstream_symbolic'] = {}
                input_packet['upstream_symbolic'][upstream_id] = upstream_result.symbolic_state
                
                # Merge numeric projection
                if 'upstream_numeric' not in input_packet:
                    input_packet['upstream_numeric'] = {}
                input_packet['upstream_numeric'][upstream_id] = upstream_result.numeric_projection
        
        return input_packet

    def _apply_graph_fusion(self, gene_outputs: dict) -> dict:
        """Apply fusion according to graph structure and output_mapping."""
        valid_outputs = {gid: out for gid, out in gene_outputs.items() if out is not None}
        
        if not valid_outputs:
            return {"fused_numeric": [], "symbolic_state": {}, "oracle_confidence": 0.0}

        # Collect all numeric projections
        all_numeric = [out.numeric_projection for out in valid_outputs.values() if out.numeric_projection]
        all_symbolic = [out.symbolic_state for out in valid_outputs.values() if out.symbolic_state]

        # Apply fusion rules
        fused_numeric = self._apply_fusion_rules(all_numeric)

        # Merge symbolic states
        fused_symbolic = {}
        for s in all_symbolic:
            for k, v in s.items():
                if k not in fused_symbolic:
                    fused_symbolic[k] = v

        # Add graph structure info
        fused_symbolic['_graph_structure'] = {
            'nodes': list(self.genes.keys()),
            'edges': self.edges,
            'execution_order': self._topological_sort(),
            'output_mapping': self.output_mapping
        }

        # Calculate confidence based on graph structure
        weights = [self.genes[gid].weight for gid in valid_outputs.keys()]
        total_weight = sum(weights) if weights else 1.0
        confidence = min(total_weight / len(self.genes), 1.0) if self.genes else 0.0
        confidence = self._apply_custom_formulas(confidence, fused_numeric)

        return {
            "fused_numeric": fused_numeric,
            "symbolic_state": fused_symbolic,
            "oracle_confidence": confidence,
        }

    def _apply_fusion_rules(self, all_numeric: list[list[float]]) -> list[float]:
        if not all_numeric:
            return []
        max_len = max(len(n) for n in all_numeric)
        fused = []
        for i in range(max_len):
            vals = [n[i] for n in all_numeric if i < len(n)]
            fused.append(sum(vals) / len(vals) if vals else 0.0)

        for rule in self.fusion_rules:
            try:
                if rule.get("action") == "apply_formula" and "formula" in rule.get("params", {}):
                    formula = rule["params"]["formula"]
                    vars_dict = {"x": fused[0] if fused else 0, "y": fused[1] if len(fused) > 1 else 0}
                    result = FormulaEngine.evaluate(formula, vars_dict)
                    fused = [v * result for v in fused]
            except Exception:
                continue
        return fused

    def _apply_custom_formulas(self, confidence: float, fused_numeric: list[float]) -> float:
        for rule in self.fusion_rules:
            if rule.get("type") == "formula" and rule.get("action") == "apply_formula":
                try:
                    formula = rule["params"]["formula"]
                    input_vars = rule["params"].get("input_variables", ["x"])
                    vars_dict = {}
                    for i, var in enumerate(input_vars):
                        if var == "x" and fused_numeric:
                            vars_dict[var] = fused_numeric[0]
                        elif var == "y" and len(fused_numeric) > 1:
                            vars_dict[var] = fused_numeric[1]
                        elif var == "n":
                            vars_dict[var] = len(self.genes)
                        elif var == "t":
                            vars_dict[var] = self.generation
                        elif var == "h":
                            vars_dict[var] = hash(self.chromosome_id) % 100
                        elif var == "s":
                            vars_dict[var] = sum(fused_numeric[:5])
                        elif var == "e":
                            vars_dict[var] = confidence
                        else:
                            vars_dict[var] = 0.5
                    result = FormulaEngine.evaluate(formula, vars_dict)
                    confidence = 1 / (1 + math.exp(-result))
                except Exception:
                    continue
        return confidence

    def _get_wrapper(self, system_id: str):
        try:
            from ..symbolic.registry import get_system
            return get_system(system_id)
        except Exception:
            pass
        return None

    def to_dict(self) -> dict:
        return {
            "chromosome_id": self.chromosome_id,
            "genes": {gid: g.__dict__ for gid, g in self.genes.items()},
            "edges": self.edges,
            "fusion_schema": self.fusion_schema,
            "fusion_rules": self.fusion_rules,
            "output_mapping": self.output_mapping,
            "fitness": self.fitness,
            "metadata": self.metadata,
            "representation": self.representation,
            "memory_links": self.memory_links,
            "system_configs": {k: v.to_dict() for k, v in self.system_configs.items()} if self.system_configs else {},
            "custom_formulas": self.custom_formulas,
            "invented_methods": self.invented_methods,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Chromosome":
        genes_raw = data.get("genes", {})
        if isinstance(genes_raw, list):
            genes = {g["gene_id"]: Gene(**g) for g in genes_raw if "gene_id" in g}
        else:
            genes = {gid: Gene(**g) for gid, g in genes_raw.items()}
        
        system_configs = {}
        configs_raw = data.get("system_configs", {})
        if configs_raw:
            from ..symbolic.modifiable import SystemConfig
            for k, v in configs_raw.items():
                system_configs[k] = SystemConfig.from_dict(v)
        
        return cls(
            chromosome_id=data.get("chromosome_id", ""),
            genes=genes,
            edges=data.get("edges", []),
            fusion_schema=data.get("fusion_schema", {}),
            fusion_rules=data.get("fusion_rules", []),
            output_mapping=data.get("output_mapping", {}),
            fitness=data.get("fitness", {}),
            metadata=data.get("metadata", {}),
            representation=data.get("representation", "graph"),
            memory_links=data.get("memory_links", []),
            system_configs=system_configs,
            custom_formulas=data.get("custom_formulas", {}),
            invented_methods=data.get("invented_methods", []),
        )

    def crossover(self, other: "Chromosome") -> "Chromosome":
        from ..evolution.crossover import uniform_crossover
        child1, child2 = uniform_crossover(self, other, rate=0.5)
        child1.chromosome_id = hashlib.md5(f"cross_{random.random()}".encode()).hexdigest()[:8]
        return child1

    def mutate(self, rate: float = 0.1) -> "Chromosome":
        from ..evolution.mutation import param_mutation, structural_mutation
        mutated = param_mutation(self, rate=rate)
        mutated = structural_mutation(mutated, rate=rate * 0.5)
        return mutated

    @classmethod
    def create_random(cls, systems: list[tuple[str, str]] = None) -> "Chromosome":
        if systems is None:
            from ..symbolic.registry import list_systems
            all_sys = list_systems()
            n = random.randint(2, min(4, len(all_sys)))
            systems = [(s, "internal") for s in random.sample(all_sys, n)]

        genes = {}
        edges = []
        prev_id = None
        for i, (sys_id, backend) in enumerate(systems):
            gene = Gene(
                gene_id=hashlib.md5(f"{sys_id}_{i}_{random.random()}".encode()).hexdigest()[:8],
                system_id=sys_id,
                backend=backend,
                params={},
                input_slots=[f"input_{i}"],
                output_slots=[f"output_{i}"],
                weight=random.uniform(0.1, 1.0),
                mutation_policy={"param_mutation_rate": 0.1, "structural_mutation_rate": 0.05},
            )
            genes[gene.gene_id] = gene
            if prev_id:
                edges.append((prev_id, gene.gene_id))
            prev_id = gene.gene_id

        return cls(
            chromosome_id=hashlib.md5(f"chr_{random.random()}".encode()).hexdigest()[:8],
            genes=genes,
            edges=edges,
            fusion_schema={"type": "weighted_average"},
            output_mapping={"output": prev_id or "input_0"},
        )
