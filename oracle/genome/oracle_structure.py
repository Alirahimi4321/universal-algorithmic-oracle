"""Oracle Structure - represents an evolved oracle configuration."""
import hashlib
import time
from dataclasses import dataclass, field
from ..genome.chromosome import Chromosome


@dataclass
class OracleStructure:
    oracle_id: str
    chromosome: Chromosome
    lineage: list[str] = field(default_factory=list)
    symbolic_systems: list[str] = field(default_factory=list)
    execution_plan: list[dict] = field(default_factory=list)
    final_mapping: dict = field(default_factory=dict)
    confidence_model: dict = field(default_factory=dict)
    explanation_trace: list[dict] = field(default_factory=list)
    graph_hash: str = ""
    created_at: float = 0.0

    def __post_init__(self):
        if not self.created_at:
            self.created_at = time.time()
        if not self.graph_hash:
            self.graph_hash = self._compute_hash()

    def _compute_hash(self) -> str:
        data = {
            "oracle_id": self.oracle_id,
            "genes": {gid: g.__dict__ for gid, g in self.chromosome.genes.items()},
            "edges": self.chromosome.edges,
            "fusion": self.chromosome.fusion_schema,
        }
        return hashlib.sha256(str(data).encode()).hexdigest()[:16]

    def to_dict(self) -> dict:
        return {
            "oracle_id": self.oracle_id,
            "lineage": self.lineage,
            "symbolic_systems": self.symbolic_systems,
            "execution_plan": self.execution_plan,
            "final_mapping": self.final_mapping,
            "confidence_model": self.confidence_model,
            "explanation_trace": self.explanation_trace,
            "graph_hash": self.graph_hash,
            "created_at": self.created_at,
            "chromosome": self.chromosome.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "OracleStructure":
        return cls(
            oracle_id=data.get("oracle_id", ""),
            chromosome=Chromosome.from_dict(data.get("chromosome", {})),
            lineage=data.get("lineage", []),
            symbolic_systems=data.get("symbolic_systems", []),
            execution_plan=data.get("execution_plan", []),
            final_mapping=data.get("final_mapping", {}),
            confidence_model=data.get("confidence_model", {}),
            explanation_trace=data.get("explanation_trace", []),
            graph_hash=data.get("graph_hash", ""),
            created_at=data.get("created_at", 0.0),
        )

    @classmethod
    def from_chromosome(cls, chromosome: Chromosome) -> "OracleStructure":
        systems = list(set(g.system_id for g in chromosome.gene_list))
        return cls(
            oracle_id=f"oracle_{chromosome.chromosome_id}",
            chromosome=chromosome,
            symbolic_systems=systems,
            execution_plan=[
                {"step": i, "system": g.system_id, "weight": g.weight}
                for i, g in enumerate(chromosome.gene_list)
            ],
            confidence_model={
                "avg_weight": sum(g.weight for g in chromosome.gene_list) / max(len(chromosome.genes), 1),
                "system_diversity": len(set(g.system_id for g in chromosome.gene_list)) / max(len(chromosome.genes), 1),
            },
        )
