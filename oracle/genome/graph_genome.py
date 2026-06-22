"""Graph-based genome representation with real execution capability."""
import random
import hashlib
from dataclasses import dataclass, field
from .gene import Gene
from .chromosome import Chromosome


@dataclass
class GraphGenome:
    genome_id: str
    nodes: list[Gene] = field(default_factory=list)
    edges: list[tuple[str, str]] = field(default_factory=list)
    size: int = 0
    depth: int = 1
    fitness: dict = field(default_factory=dict)

    @classmethod
    def random(cls, genome_id: str, n_nodes: int = 4) -> "GraphGenome":
        systems = ["iching", "gematria", "tarot", "astrology", "numerology",
                    "bazi", "geomancy", "calendar", "runes", "lenormand"]
        nodes = []
        for i in range(n_nodes):
            gene = Gene(
                gene_id=f"node_{i}",
                system_id=random.choice(systems),
                backend="internal",
                params={},
                input_slots=[f"in_{i}"],
                output_slots=[f"out_{i}"],
                weight=random.uniform(0.3, 0.9),
                mutation_policy={"param_mutation_rate": 0.1, "structural_mutation_rate": 0.05},
            )
            nodes.append(gene)

        edges = []
        for i in range(1, n_nodes):
            parent = random.randint(0, i - 1)
            edges.append((f"node_{parent}", f"node_{i}"))

        if n_nodes > 2 and random.random() < 0.3:
            a, b = random.sample(range(n_nodes), 2)
            edge = (f"node_{a}", f"node_{b}")
            if edge not in edges and edge[0] != edge[1]:
                edges.append(edge)

        depth = cls._compute_depth(nodes, edges)

        return cls(
            genome_id=genome_id,
            nodes=nodes,
            edges=edges,
            size=n_nodes,
            depth=depth,
        )

    @staticmethod
    def _compute_depth(nodes: list, edges: list) -> int:
        if not nodes:
            return 0
        adj = {}
        for node in nodes:
            adj[node.gene_id] = []
        for src, dst in edges:
            if src in adj:
                adj[src].append(dst)

        in_degree = {node.gene_id: 0 for node in nodes}
        for src, dst in edges:
            if dst in in_degree:
                in_degree[dst] += 1

        queue = [nid for nid, deg in in_degree.items() if deg == 0]
        depth = 0
        visited = 0
        while queue:
            next_queue = []
            for nid in queue:
                visited += 1
                for child in adj.get(nid, []):
                    in_degree[child] -= 1
                    if in_degree[child] == 0:
                        next_queue.append(child)
            if next_queue:
                depth += 1
            queue = next_queue

        if visited < len(nodes):
            depth += 1

        return max(1, depth)

    def execute(self, entropy_packet: dict) -> dict:
        from ..symbolic.registry import compute_system

        if not self.nodes:
            return {"fused_numeric": [], "fused_structural": {}, "oracle_confidence": 0.0}

        node_outputs = {}
        adj = {node.gene_id: [] for node in self.nodes}
        for src, dst in self.edges:
            if src in adj:
                adj[src].append(dst)

        in_degree = {node.gene_id: 0 for node in self.nodes}
        for src, dst in self.edges:
            if dst in in_degree:
                in_degree[dst] += 1

        sorted_nodes = []
        queue = [nid for nid, deg in in_degree.items() if deg == 0]
        while queue:
            nid = queue.pop(0)
            sorted_nodes.append(nid)
            for child in adj.get(nid, []):
                in_degree[child] -= 1
                if in_degree[child] == 0:
                    queue.append(child)

        for node_id in sorted_nodes:
            node = next((n for n in self.nodes if n.gene_id == node_id), None)
            if node is None:
                continue

            input_data = []
            for src, dst in self.edges:
                if dst == node_id and src in node_outputs:
                    input_data.extend(node_outputs[src].get("fused_numeric", []))

            if not input_data:
                input_data = entropy_packet.get("numeric_vector", [])

            try:
                result = compute_system(node.system_id, entropy_packet, node.params)
                numeric = result.numeric_projection if hasattr(result, 'numeric_projection') else []
                structural = result.structural_features if hasattr(result, 'structural_features') else {}

                if input_data and numeric:
                    weighted = []
                    for i in range(min(len(input_data), len(numeric))):
                        weighted.append(input_data[i] * node.weight + numeric[i] * (1 - node.weight))
                    numeric = weighted

                coverage = min(1.0, len(numeric) / 10) if numeric else 0.0
                confidence = 0.4 + coverage * 0.4 + node.weight * 0.2

                node_outputs[node_id] = {
                    "fused_numeric": numeric,
                    "fused_structural": structural,
                    "oracle_confidence": min(0.95, confidence),
                }
            except Exception as e:
                import logging
                logging.getLogger(__name__).warning("Graph node %s (%s) failed: %s", node_id, node.system_id, e)
                node_outputs[node_id] = {
                    "fused_numeric": input_data[:10] if input_data else [],
                    "fused_structural": {},
                    "oracle_confidence": 0.1,
                }

        output_nodes = [n for n in self.nodes if not adj.get(n.gene_id, [])]
        if not output_nodes:
            output_nodes = self.nodes[-1:]

        best_node = max(output_nodes, key=lambda n: node_outputs.get(n.gene_id, {}).get("oracle_confidence", 0))
        return node_outputs.get(best_node.gene_id, {"fused_numeric": [], "fused_structural": {}, "oracle_confidence": 0.0})

    def to_chromosome(self) -> Chromosome:
        genes = {}
        for node in self.nodes:
            genes[node.gene_id] = node

        output_node = self.nodes[-1] if self.nodes else None
        return Chromosome(
            chromosome_id=self.genome_id,
            genes=genes,
            edges=self.edges,
            fusion_schema={"type": "graph_fusion"},
            output_mapping={"output": output_node.output_slots[0] if output_node else ""},
        )

    def copy(self) -> "GraphGenome":
        import copy
        new = GraphGenome(
            genome_id=self.genome_id,
            nodes=copy.deepcopy(self.nodes),
            edges=list(self.edges),
            size=self.size,
            depth=self.depth,
            fitness=dict(self.fitness),
        )
        return new

    def mutate(self, mutation_rate: float = 0.15) -> "GraphGenome":
        new_genome = self.copy()
        for node in new_genome.nodes:
            if random.random() < mutation_rate:
                systems = ["iching", "gematria", "tarot", "astrology", "numerology",
                           "bazi", "geomancy", "calendar", "runes", "lenormand"]
                node.system_id = random.choice(systems)
                node.weight = random.uniform(0.3, 0.9)

        if random.random() < mutation_rate * 0.3 and len(new_genome.nodes) > 2:
            a, b = random.sample(range(len(new_genome.nodes)), 2)
            edge = (new_genome.nodes[a].gene_id, new_genome.nodes[b].gene_id)
            if edge not in new_genome.edges:
                new_genome.edges.append(edge)

        new_genome.depth = self._compute_depth(new_genome.nodes, new_genome.edges)
        new_genome.fitness = {}
        return new_genome

    def crossover(self, other: "GraphGenome") -> "GraphGenome":
        child = self.copy()
        donor = other.copy()

        if child.nodes and donor.nodes:
            crossover_point = random.randint(1, len(child.nodes) - 1)
            donor_subset = donor.nodes[:min(crossover_point, len(donor.nodes))]
            for i, node in enumerate(donor_subset):
                if i < len(child.nodes):
                    child.nodes[i].system_id = node.system_id
                    child.nodes[i].weight = node.weight

        child.depth = self._compute_depth(child.nodes, child.edges)
        child.fitness = {}
        return child
