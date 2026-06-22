"""Tree-based genome representation for Genetic Programming."""
import uuid
import copy
import random
from dataclasses import dataclass, field
from typing import Any


@dataclass
class TreeNode:
    node_id: str
    node_type: str  # "system", "fusion", "transform", "input", "output"
    system_id: str = ""
    operation: str = ""
    params: dict = field(default_factory=dict)
    children: list["TreeNode"] = field(default_factory=list)
    weight: float = 1.0

    @property
    def is_leaf(self) -> bool:
        return len(self.children) == 0

    @property
    def depth(self) -> int:
        if self.is_leaf:
            return 0
        return 1 + max(c.depth for c in self.children)

    @property
    def size(self) -> int:
        return 1 + sum(c.size for c in self.children)

    def to_dict(self) -> dict:
        return {
            "node_id": self.node_id,
            "node_type": self.node_type,
            "system_id": self.system_id,
            "operation": self.operation,
            "params": self.params,
            "weight": self.weight,
            "children": [c.to_dict() for c in self.children],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "TreeNode":
        children = [cls.from_dict(c) for c in data.get("children", [])]
        return cls(
            node_id=data["node_id"],
            node_type=data["node_type"],
            system_id=data.get("system_id", ""),
            operation=data.get("operation", ""),
            params=data.get("params", {}),
            children=children,
            weight=data.get("weight", 1.0),
        )

    def copy(self) -> "TreeNode":
        return copy.deepcopy(self)


class TreeGenome:
    def __init__(self, root: TreeNode | None = None):
        self.root = root
        self.genome_id = str(uuid.uuid4())[:8]
        self.fitness: dict = {}
        self.generation: int = 0
        self.lineage_id: str = ""

    @property
    def depth(self) -> int:
        return self.root.depth if self.root else 0

    @property
    def size(self) -> int:
        return self.root.size if self.root else 0

    @property
    def gene_list(self) -> list:
        return self.get_all_system_nodes()

    def get_all_nodes(self) -> list[TreeNode]:
        nodes = []
        if self.root:
            self._traverse(self.root, nodes)
        return nodes

    def _traverse(self, node: TreeNode, result: list):
        result.append(node)
        for child in node.children:
            self._traverse(child, result)

    def get_all_leaves(self) -> list[TreeNode]:
        return [n for n in self.get_all_nodes() if n.is_leaf]

    def get_all_system_nodes(self) -> list[TreeNode]:
        return [n for n in self.get_all_nodes() if n.node_type == "system"]

    def execute(self, entropy_packet: dict) -> dict:
        if self.root is None:
            return {"fused_numeric": [], "fused_structural": {}, "oracle_confidence": 0.0}
        return self._execute_node(self.root, entropy_packet)

    def _execute_node(self, node: TreeNode, entropy_packet: dict) -> dict:
        from ..symbolic.registry import compute_system

        if node.node_type == "input":
            numeric = entropy_packet.get("numeric_vector", [])
            info_density = min(1.0, len(numeric) / 32) if numeric else 0.0
            return {
                "fused_numeric": numeric,
                "fused_structural": {},
                "oracle_confidence": 0.3 + info_density * 0.4,
            }

        if node.node_type == "system":
            try:
                result = compute_system(node.system_id, entropy_packet, node.params)
                numeric = result.numeric_projection if hasattr(result, 'numeric_projection') else []
                structural = result.structural_features if hasattr(result, 'structural_features') else {}
                has_numeric = 1.0 if numeric else 0.0
                has_structural = 1.0 if structural else 0.0
                coverage = min(1.0, len(numeric) / 10) if numeric else 0.0
                confidence = 0.4 + has_numeric * 0.2 + has_structural * 0.2 + coverage * 0.2
                return {
                    "fused_numeric": numeric,
                    "fused_structural": structural,
                    "oracle_confidence": min(0.95, confidence),
                }
            except Exception as e:
                import logging
                logging.getLogger(__name__).warning("System %s execution failed: %s", node.system_id, e)
                return {"fused_numeric": [], "fused_structural": {}, "oracle_confidence": 0.0}

        if node.node_type == "fusion":
            child_results = [self._execute_node(c, entropy_packet) for c in node.children]
            return self._fuse_results(child_results, node.operation, node.params)

        if node.node_type == "transform":
            child_result = self._execute_node(node.children[0], entropy_packet) if node.children else {}
            return self._apply_transform(child_result, node.operation, node.params)

        return {"fused_numeric": [], "fused_structural": {}, "oracle_confidence": 0.0}

    def _fuse_results(self, results: list[dict], operation: str, params: dict) -> dict:
        all_numeric = []
        all_structural = {}
        for r in results:
            all_numeric.extend(r.get("fused_numeric", []))
            all_structural.update(r.get("fused_structural", {}))

        if operation == "weighted_sum" or not operation:
            fused_numeric = all_numeric[:20] if all_numeric else []
        elif operation == "modular_resonance":
            modulus = params.get("modulus", 7)
            fused_numeric = [v % modulus for v in all_numeric[:20]] if all_numeric else []
        elif operation == "xor_fusion":
            fused_numeric = []
            for i in range(0, min(20, len(all_numeric)), 2):
                if i + 1 < len(all_numeric):
                    fused_numeric.append(int(all_numeric[i]) ^ int(all_numeric[i + 1]))
                else:
                    fused_numeric.append(int(all_numeric[i]))
        else:
            fused_numeric = all_numeric[:20] if all_numeric else []

        confidence = min(1.0, len([r for r in results if r.get("fused_numeric")]) / max(len(results), 1))

        return {
            "fused_numeric": fused_numeric,
            "fused_structural": all_structural,
            "oracle_confidence": confidence,
        }

    def _apply_transform(self, result: dict, operation: str, params: dict) -> dict:
        numeric = result.get("fused_numeric", [])
        if operation == "normalize":
            max_val = max(abs(v) for v in numeric) if numeric else 1
            result["fused_numeric"] = [v / max_val for v in numeric] if max_val > 0 else numeric
        elif operation == "modular":
            modulus = params.get("modulus", 12)
            result["fused_numeric"] = [v % modulus for v in numeric]
        elif operation == "invert":
            result["fused_numeric"] = [-v for v in numeric]
        return result

    def mutate(self, mutation_rate: float = 0.15) -> "TreeGenome":
        new_genome = self.copy()
        nodes = new_genome.get_all_nodes()

        for node in nodes:
            if random.random() < mutation_rate:
                if node.node_type == "system":
                    node.system_id = self._random_system()
                    node.params = self._mutate_params(node.params)
                elif node.node_type == "fusion":
                    node.operation = random.choice(["weighted_sum", "modular_resonance", "xor_fusion"])
                    node.params["modulus"] = random.choice([7, 9, 12, 22, 28])
                elif node.node_type == "transform":
                    node.operation = random.choice(["normalize", "modular", "invert"])

        if random.random() < mutation_rate * 0.3:
            self._random_subtree_mutation(new_genome)

        new_genome.genome_id = str(uuid.uuid4())[:8]
        new_genome.fitness = {}
        return new_genome

    def crossover(self, other: "TreeGenome") -> "TreeGenome":
        child = self.copy()
        donor = other.copy()

        child_nodes = child.get_all_nodes()
        donor_nodes = donor.get_all_nodes()

        if child_nodes and donor_nodes:
            child_point = random.choice(child_nodes)
            donor_point = random.choice(donor_nodes)

            if child_point.children and donor_point.children:
                child_point.children = donor_point.children

        child.genome_id = str(uuid.uuid4())[:8]
        child.fitness = {}
        return child

    def _random_subtree_mutation(self, genome: "TreeGenome"):
        nodes = genome.get_all_nodes()
        if not nodes:
            return
        node = random.choice(nodes)
        if node.node_type == "fusion" and len(node.children) > 0:
            new_leaf = TreeNode(
                node_id=str(uuid.uuid4())[:8],
                node_type="system",
                system_id=self._random_system(),
            )
            node.children.append(new_leaf)

    def _random_system(self) -> str:
        return random.choice(["gematria", "iching", "geomancy", "calendar"])

    def _mutate_params(self, params: dict) -> dict:
        new_params = dict(params)
        if "line_count" in new_params:
            new_params["line_count"] = random.choice([6, 7, 8, 10])
        if "modulus" in new_params:
            new_params["modulus"] = random.choice([7, 9, 12, 22, 28, 64])
        return new_params

    def to_dict(self) -> dict:
        return {
            "genome_id": self.genome_id,
            "root": self.root.to_dict() if self.root else None,
            "fitness": self.fitness,
            "generation": self.generation,
            "lineage_id": self.lineage_id,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "TreeGenome":
        root = TreeNode.from_dict(data["root"]) if data.get("root") else None
        genome = cls(root=root)
        genome.genome_id = data.get("genome_id", str(uuid.uuid4())[:8])
        genome.fitness = data.get("fitness", {})
        genome.generation = data.get("generation", 0)
        genome.lineage_id = data.get("lineage_id", "")
        return genome

    def copy(self) -> "TreeGenome":
        new = TreeGenome()
        new.genome_id = self.genome_id
        new.root = self.root.copy() if self.root else None
        new.fitness = dict(self.fitness)
        new.generation = self.generation
        new.lineage_id = self.lineage_id
        return new

    @classmethod
    def create_random(cls, max_depth: int = 3, systems: list[str] | None = None) -> "TreeGenome":
        systems = systems or ["gematria", "iching", "geomancy", "calendar"]
        root = _build_random_tree(0, max_depth, systems)
        return cls(root=root)


def _build_random_tree(depth: int, max_depth: int, systems: list[str]) -> TreeNode:
    if depth >= max_depth or (depth > 0 and random.random() < 0.3):
        return TreeNode(
            node_id=str(uuid.uuid4())[:8],
            node_type="system",
            system_id=random.choice(systems),
        )

    if random.random() < 0.6:
        children = [
            _build_random_tree(depth + 1, max_depth, systems),
            _build_random_tree(depth + 1, max_depth, systems),
        ]
        return TreeNode(
            node_id=str(uuid.uuid4())[:8],
            node_type="fusion",
            operation=random.choice(["weighted_sum", "modular_resonance"]),
            children=children,
        )
    else:
        child = _build_random_tree(depth + 1, max_depth, systems)
        return TreeNode(
            node_id=str(uuid.uuid4())[:8],
            node_type="transform",
            operation=random.choice(["normalize", "modular", "invert"]),
            children=[child],
        )
