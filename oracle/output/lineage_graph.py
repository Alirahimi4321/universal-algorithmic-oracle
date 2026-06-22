"""Visual lineage graph for oracle evolution tracking.

Generates text-based and structured lineage representations.
Per design doc section 21.1: Oracle Archive, Lineage Graph, Mutation Bank.
"""
import json
import time
import hashlib
from typing import Optional


class LineageGraph:
    """Tracks and visualizes oracle lineage and evolution history."""

    def __init__(self):
        self.nodes = {}
        self.edges = []
        self.metadata = {}

    def add_node(
        self,
        node_id: str,
        chromosome_id: str,
        generation: int,
        fitness: float,
        parents: list[str] = None,
        systems: list[str] = None,
        mutation_type: str = "initial",
    ):
        """Add a node to the lineage graph."""
        self.nodes[node_id] = {
            "chromosome_id": chromosome_id,
            "generation": generation,
            "fitness": fitness,
            "parents": parents or [],
            "systems": systems or [],
            "mutation_type": mutation_type,
            "timestamp": time.time(),
        }
        for parent_id in (parents or []):
            self.edges.append({"from": parent_id, "to": node_id, "type": mutation_type})

    def get_node(self, node_id: str) -> Optional[dict]:
        return self.nodes.get(node_id)

    def get_children(self, node_id: str) -> list[str]:
        return [e["to"] for e in self.edges if e["from"] == node_id]

    def get_parents(self, node_id: str) -> list[str]:
        return [e["from"] for e in self.edges if e["to"] == node_id]

    def get_generation_range(self, gen_min: int, gen_max: int) -> list[dict]:
        return [
            {"id": nid, **node}
            for nid, node in self.nodes.items()
            if gen_min <= node["generation"] <= gen_max
        ]

    def get_best_lineage(self, top_n: int = 5) -> list[dict]:
        """Get the top N best nodes by fitness."""
        sorted_nodes = sorted(
            self.nodes.items(),
            key=lambda x: x[1]["fitness"],
            reverse=True,
        )
        return [{"id": nid, **node} for nid, node in sorted_nodes[:top_n]]

    def render_text(self, root_id: str = None, max_depth: int = 3) -> str:
        """Render text-based lineage visualization."""
        lines = ["=== ORACLE LINEAGE GRAPH ===", ""]

        if root_id:
            roots = [root_id]
        else:
            roots = [nid for nid, node in self.nodes.items() if not node["parents"]]

        for root in roots:
            lines.extend(self._render_subtree(root, 0, max_depth, set()))

        lines.append(f"\nTotal nodes: {len(self.nodes)}")
        lines.append(f"Total edges: {len(self.edges)}")
        return "\n".join(lines)

    def _render_subtree(self, node_id: str, depth: int, max_depth: int, visited: set) -> list[str]:
        if depth > max_depth or node_id in visited:
            return ["  " * depth + f"  ... ({node_id[:8]})"]
        visited.add(node_id)
        node = self.nodes.get(node_id)
        if not node:
            return []

        indent = "  " * depth
        lines = [
            f"{indent}[{node_id[:8]}] gen={node['generation']} "
            f"fitness={node['fitness']:.3f} "
            f"systems={node['systems'][:3]} "
            f"({node['mutation_type']})"
        ]

        children = self.get_children(node_id)
        for child in children[:5]:
            lines.extend(self._render_subtree(child, depth + 1, max_depth, visited))
        if len(children) > 5:
            lines.append(f"{indent}  ... +{len(children) - 5} more children")

        return lines

    def to_dict(self) -> dict:
        return {
            "nodes": self.nodes,
            "edges": self.edges,
            "metadata": self.metadata,
            "stats": self.get_stats(),
        }

    def get_stats(self) -> dict:
        if not self.nodes:
            return {"total_nodes": 0, "total_edges": 0}

        fitnesses = [n["fitness"] for n in self.nodes.values()]
        generations = [n["generation"] for n in self.nodes.values()]
        all_systems = set()
        for node in self.nodes.values():
            all_systems.update(node["systems"])

        return {
            "total_nodes": len(self.nodes),
            "total_edges": len(self.edges),
            "avg_fitness": sum(fitnesses) / len(fitnesses),
            "max_fitness": max(fitnesses),
            "min_fitness": min(fitnesses),
            "min_generation": min(generations),
            "max_generation": max(generations),
            "unique_systems": len(all_systems),
            "system_list": sorted(all_systems),
        }

    def export_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, default=str)


class LineageTracker:
    """High-level tracker that connects with chromosome archive."""

    def __init__(self):
        self.graph = LineageGraph()
        self._counter = 0

    def record_chromosome(
        self,
        chromosome,
        fitness: float,
        generation: int,
        parent_ids: list[str] = None,
        mutation_type: str = "evolution",
    ) -> str:
        """Record a chromosome in the lineage graph."""
        self._counter += 1
        node_id = f"N{self._counter:06d}"
        chrom_id = getattr(chromosome, 'chromosome_id', f"chr_{self._counter}")
        systems = [g.system_id for g in chromosome.gene_list] if hasattr(chromosome, 'gene_list') else []

        self.graph.add_node(
            node_id=node_id,
            chromosome_id=chrom_id,
            generation=generation,
            fitness=fitness,
            parents=parent_ids or [],
            systems=systems,
            mutation_type=mutation_type,
        )
        return node_id

    def get_summary(self) -> dict:
        return self.graph.get_stats()

    def render(self, max_depth: int = 3) -> str:
        return self.graph.render_text(max_depth=max_depth)
