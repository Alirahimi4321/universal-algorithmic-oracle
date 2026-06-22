"""Deep Mutation Engine - modifies internal logic of symbolic systems."""
import random
import copy
import math
from dataclasses import dataclass, field
from typing import Any


@dataclass
class MutationPlan:
    """A plan for deep mutation of a system."""
    system_id: str
    mutation_type: str  # parameter, structure, formula, transform, hybrid
    target: str
    original_value: Any = None
    new_value: Any = None
    intensity: float = 0.1
    description: str = ""


class DeepMutationEngine:
    """Engine that can modify the internal logic of symbolic systems."""

    def __init__(self, config: dict = None):
        self.config = config or {}
        self.mutation_history: list[MutationPlan] = []
        self.successful_mutations: list[MutationPlan] = []

    def mutate_system(self, modifiable_system, intensity: float = 0.3,
                      entropy_packet: dict = None) -> "ModifiableSystem":
        """Apply deep mutation to a modifiable system."""
        from ..symbolic.modifiable import ModifiableSystem, SystemConfig, SystemParameter, FormulaEngine

        new_system = copy.deepcopy(modifiable_system)
        mutation_type = random.choices(
            ["param_shift", "formula_invention", "transform_change",
             "structure_rebuild", "hybrid_crossover", "scale_mutation"],
            weights=[0.25, 0.25, 0.15, 0.15, 0.1, 0.1]
        )[0]

        if mutation_type == "param_shift":
            new_system = self._mutate_parameters(new_system, intensity)
        elif mutation_type == "formula_invention":
            new_system = self._invent_formula(new_system, intensity)
        elif mutation_type == "transform_change":
            new_system = self._change_transforms(new_system, intensity)
        elif mutation_type == "structure_rebuild":
            new_system = self._rebuild_structure(new_system, intensity)
        elif mutation_type == "hybrid_crossover":
            new_system = self._hybrid_mutation(new_system, intensity)
        elif mutation_type == "scale_mutation":
            new_system = self._mutate_scale(new_system, intensity)

        return new_system

    def _mutate_parameters(self, system, intensity: float):
        """Deeply mutate all parameters of a system."""
        for name, param in system.config.parameters.items():
            if random.random() < intensity:
                system.config.parameters[name] = param.mutate(intensity)
        return system

    def _invent_formula(self, system, intensity: float):
        """Invent a new formula for the system."""
        from ..symbolic.modifiable import FormulaEngine

        formula_keys = list(system.config.custom_formulas.keys())
        if formula_keys and random.random() < 0.7:
            key = random.choice(formula_keys)
            old = system.config.custom_formulas[key]
            system.config.custom_formulas[key] = FormulaEngine.mutate_formula(old, intensity)
        else:
            depth = random.randint(1, 3)
            formula = FormulaEngine.random_formula(depth)
            system.config.custom_formulas[f"auto_formula_{len(formula_keys)}"] = formula
        return system

    def _change_transforms(self, system, intensity: float):
        """Change input/output transforms."""
        transforms = ["identity", "log", "sqrt", "sin", "cos",
                     "normalize", "softmax", "sigmoid", "tanh",
                     "power2", "power3", "modulo"]
        if random.random() < intensity:
            system.config.input_transform = random.choice(transforms)
        if random.random() < intensity:
            system.config.output_transform = random.choice(transforms)
        return system

    def _rebuild_structure(self, system, intensity: float):
        """Rebuild the structure of a system by adding/removing parameters."""
        if random.random() < intensity:
            new_param_name = f"custom_{random.randint(1000,9999)}"
            system.config.parameters[new_param_name] = random.choice([
                SystemParameter(new_param_name, random.uniform(-5, 5), "float", -10, 10),
                SystemParameter(new_param_name, random.randint(1, 20), "int", 1, 50),
                SystemParameter(new_param_name, random.choice([True, False]), "bool"),
            ])
        if random.random() < intensity * 0.5 and system.config.parameters:
            key = random.choice(list(system.config.parameters.keys()))
            del system.config.parameters[key]
        return system

    def _hybrid_mutation(self, system, intensity: float):
        """Combine aspects of multiple calculation methods."""
        methods = ["standard", "weighted", "resonance", "phase_shift",
                  "harmonic", "quantum", "fractal", "chaotic"]
        current = system.config.calculation_method
        others = [m for m in methods if m != current]
        if others:
            blend_with = random.choice(others)
            system.config.calculation_method = f"{current}_{blend_with}"
            system.config.combination_rules["blend_ratio"] = random.uniform(0.3, 0.7)
        return system

    def _mutate_scale(self, system, intensity: float):
        """Mutate the scale/precision of calculations."""
        for name, param in system.config.parameters.items():
            if param.param_type in ("float", "int") and random.random() < intensity:
                scale_factor = random.uniform(0.5, 2.0)
                param.value = param.value * scale_factor
                param.max_val = param.max_val * scale_factor
        return system

    def record_mutation(self, plan: MutationPlan, success: bool):
        self.mutation_history.append(plan)
        if success:
            self.successful_mutations.append(plan)

    def get_invention_stats(self) -> dict:
        return {
            "total_mutations": len(self.mutation_history),
            "successful": len(self.successful_mutations),
            "success_rate": len(self.successful_mutations) / max(len(self.mutation_history), 1),
            "mutation_types": {},
        }


from ..symbolic.modifiable import SystemParameter
