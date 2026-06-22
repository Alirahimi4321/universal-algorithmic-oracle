"""Gene representation for oracle components - matches document section 14.1."""
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Gene:
    gene_id: str
    system_id: str
    backend: str
    gene_type: str = "symbolic_system"
    params: dict = field(default_factory=dict)
    input_slots: list[str] = field(default_factory=list)
    output_slots: list[str] = field(default_factory=list)
    weight: float = 1.0
    mutation_policy: dict = field(default_factory=dict)

    def mutate(self, rate: float = 0.1) -> "Gene":
        import random
        new_params = self.params.copy()
        for key in new_params:
            if isinstance(new_params[key], (int, float)) and random.random() < rate:
                new_params[key] *= 1.0 + random.gauss(0, 0.1)
        return Gene(
            gene_id=self.gene_id,
            system_id=self.system_id,
            backend=self.backend,
            gene_type=self.gene_type,
            params=new_params,
            input_slots=self.input_slots[:],
            output_slots=self.output_slots[:],
            weight=self.weight * (1.0 + random.gauss(0, 0.05) if random.random() < rate else 1.0),
            mutation_policy=self.mutation_policy.copy(),
        )
