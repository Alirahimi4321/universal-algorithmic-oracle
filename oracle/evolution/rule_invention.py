"""Advanced Rule Invention Engine - creates new calculation methods and rules."""
import random
import hashlib
import math
from ..genome.chromosome import Chromosome
from ..symbolic.modifiable import FormulaEngine, SystemParameter, SystemConfig


class RuleInventionEngine:
    """Engine that invents new rules, formulas, and calculation methods."""

    RULE_TEMPLATES = [
        {"condition": "diversity_high", "action": "expand", "params": {"max_expansion": 3}},
        {"condition": "diversity_low", "action": "mutate_civilization", "params": {"mutation_rate": 0.3}},
        {"condition": "convergence", "action": "freeze_best", "params": {"freeze_count": 2}},
        {"condition": "stagnation", "action": "inject_random", "params": {"injection_rate": 0.2}},
        {"condition": "overfitting", "action": "prune_weak", "params": {"prune_threshold": 0.3}},
        {"condition": "exploration", "action": "cross_civilization", "params": {"cross_rate": 0.4}},
        {"condition": "breakthrough", "action": "amplify_signal", "params": {"amplification": 2.0}},
        {"condition": "noise", "action": "filter_output", "params": {"filter_strength": 0.5}},
        {"condition": "phase_shift", "action": "rotate_dimensions", "params": {"rotation_angle": 0.5}},
        {"condition": "resonance", "action": "sync_systems", "params": {"sync_rate": 0.3}},
    ]

    CALCULATION_METHODS = [
        "weighted_average", "resonance", "phase_shift", "harmonic",
        "quantum_interference", "fractal_iteration", "chaotic_attractor",
        "neural_resonance", "symbolic_algebra", "probabilistic_fusion",
        "entropy_maximization", "information_theoretic", "topological_mapping",
        "group_theory", "category_theory", "graph_isomorphism",
    ]

    COMBINATION_STRATEGIES = [
        "union", "intersection", "difference", "symmetric_difference",
        "weighted_merge", "hierarchical_blend", "recursive_fusion",
        "cross_civilization_transfer", "dimensional_projection",
        "symbolic_substitution", "formula_composition", "rule_chaining",
    ]

    def __init__(self, config: dict = None):
        config = config or {}
        self.max_rules = config.get("max_rules", 20)
        self.invention_rate = config.get("invention_rate", 0.15)
        self.formula_depth = config.get("formula_depth", 3)
        self.invented_rules: list[dict] = []
        self.invented_formulas: list[dict] = []
        self.invented_methods: list[dict] = []

    def invent_rules(self, chromosome: Chromosome) -> Chromosome:
        if random.random() > self.invention_rate:
            return chromosome

        existing_rules = chromosome.fusion_rules[:]
        if len(existing_rules) >= self.max_rules:
            existing_rules = existing_rules[-self.max_rules + 2:]

        invention_type = random.choices(
            ["rule", "formula", "method", "strategy", "hybrid"],
            weights=[0.25, 0.25, 0.2, 0.15, 0.15]
        )[0]

        if invention_type == "rule":
            new_rule = self._invent_rule(chromosome)
            self.invented_rules.append(new_rule)
        elif invention_type == "formula":
            new_rule = self._invent_formula_rule(chromosome)
            self.invented_formulas.append(new_rule)
        elif invention_type == "method":
            new_rule = self._invent_method(chromosome)
            self.invented_methods.append(new_rule)
        elif invention_type == "strategy":
            new_rule = self._invent_strategy(chromosome)
        else:
            new_rule = self._invent_hybrid(chromosome)

        return Chromosome(
            chromosome_id=chromosome.chromosome_id,
            genes=chromosome.genes.copy(),
            edges=chromosome.edges[:],
            fusion_schema=chromosome.fusion_schema.copy(),
            fusion_rules=existing_rules + [new_rule],
            output_mapping=chromosome.output_mapping.copy(),
            fitness=chromosome.fitness.copy(),
            metadata=chromosome.metadata.copy(),
        )

    def _invent_rule(self, chromosome: Chromosome) -> dict:
        template = random.choice(self.RULE_TEMPLATES)
        condition = self._mutate_condition(template["condition"])
        action = self._mutate_action(template["action"])
        params = self._mutate_params(template["params"])
        return {
            "rule_id": hashlib.md5(f"rule_{random.random()}".encode()).hexdigest()[:8],
            "type": "invented",
            "condition": condition,
            "action": action,
            "params": params,
            "priority": random.uniform(0.1, 1.0),
            "generation": chromosome.generation,
            "formula": FormulaEngine.random_formula(random.randint(1, self.formula_depth)),
            "source": "rule_invention",
        }

    def _invent_formula_rule(self, chromosome: Chromosome) -> dict:
        formula = FormulaEngine.random_formula(random.randint(1, self.formula_depth))
        input_vars = random.sample(["x", "y", "z", "t", "n", "h", "s", "e"],
                                   random.randint(1, 4))
        return {
            "rule_id": hashlib.md5(f"formula_{random.random()}".encode()).hexdigest()[:8],
            "type": "formula",
            "condition": "always",
            "action": "apply_formula",
            "params": {
                "formula": formula,
                "input_variables": input_vars,
                "output_variable": random.choice(["result", "score", "weight", "confidence"]),
            },
            "priority": random.uniform(0.2, 0.8),
            "generation": chromosome.generation,
            "formula": formula,
            "source": "formula_invention",
        }

    def _invent_method(self, chromosome: Chromosome) -> dict:
        method = random.choice(self.CALCULATION_METHODS)
        return {
            "rule_id": hashlib.md5(f"method_{random.random()}".encode()).hexdigest()[:8],
            "type": "method",
            "condition": "diversity_moderate",
            "action": "use_method",
            "params": {
                "method": method,
                "parameters": {k: random.uniform(0.1, 2.0) for k in
                              random.sample(["alpha", "beta", "gamma", "delta",
                                           "epsilon", "zeta", "eta", "theta"], 3)},
            },
            "priority": random.uniform(0.3, 0.9),
            "generation": chromosome.generation,
            "source": "method_invention",
        }

    def _invent_strategy(self, chromosome: Chromosome) -> dict:
        strategy = random.choice(self.COMBINATION_STRATEGIES)
        return {
            "rule_id": hashlib.md5(f"strategy_{random.random()}".encode()).hexdigest()[:8],
            "type": "strategy",
            "condition": "always",
            "action": "combine_systems",
            "params": {
                "strategy": strategy,
                "blend_ratio": random.uniform(0.2, 0.8),
                "recursion_depth": random.randint(1, 3),
                "system_subset": random.randint(2, min(5, max(2, len(chromosome.genes)))),
            },
            "priority": random.uniform(0.4, 0.9),
            "generation": chromosome.generation,
            "source": "strategy_invention",
        }

    def _invent_hybrid(self, chromosome: Chromosome) -> dict:
        rules = [self._invent_rule(chromosome),
                self._invent_formula_rule(chromosome),
                self._invent_method(chromosome)]
        selected = random.sample(rules, min(2, len(rules)))
        return {
            "rule_id": hashlib.md5(f"hybrid_{random.random()}".encode()).hexdigest()[:8],
            "type": "hybrid",
            "condition": "always",
            "action": "apply_hybrid",
            "params": {
                "sub_rules": selected,
                "combination": random.choice(["sequential", "parallel", "conditional"]),
            },
            "priority": random.uniform(0.5, 1.0),
            "generation": chromosome.generation,
            "source": "hybrid_invention",
        }

    def _mutate_condition(self, condition: str) -> str:
        conditions = ["always", "diversity_high", "diversity_low", "diversity_moderate",
                     "convergence", "stagnation", "overfitting", "exploration",
                     "breakthrough", "noise", "phase_shift", "resonance"]
        if random.random() < 0.3:
            return random.choice(conditions)
        return condition

    def _mutate_action(self, action: str) -> str:
        actions = ["expand", "mutate_civilization", "freeze_best", "inject_random",
                  "prune_weak", "cross_civilization", "amplify_signal",
                  "filter_output", "rotate_dimensions", "sync_systems",
                  "apply_formula", "use_method", "combine_systems"]
        if random.random() < 0.3:
            return random.choice(actions)
        return action

    def _mutate_params(self, params: dict) -> dict:
        new_params = params.copy()
        for key in new_params:
            if isinstance(new_params[key], (int, float)):
                new_params[key] = new_params[key] * (1.0 + random.gauss(0, 0.2))
            elif isinstance(new_params[key], bool):
                if random.random() < 0.3:
                    new_params[key] = not new_params[key]
        return new_params

    def get_invention_stats(self) -> dict:
        return {
            "total_invented": len(self.invented_rules) + len(self.invented_formulas) + len(self.invented_methods),
            "rules": len(self.invented_rules),
            "formulas": len(self.invented_formulas),
            "methods": len(self.invented_methods),
        }
