"""Modifiable System - allows genetic algorithms to modify internal logic of symbolic systems."""
import random
import copy
import math
from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass
class SystemParameter:
    """A modifiable parameter within a symbolic system."""
    name: str
    value: Any
    param_type: str = "float"  # float, int, choice, bool, formula
    min_val: float = 0.0
    max_val: float = 100.0
    choices: list = field(default_factory=list)
    description: str = ""
    mutation_rate: float = 0.1
    mutation_scale: float = 0.1

    def mutate(self, rate: float = None) -> "SystemParameter":
        r = rate or self.mutation_rate
        if random.random() > r:
            return copy.deepcopy(self)

        p = copy.deepcopy(self)
        if self.param_type == "float":
            p.value = max(self.min_val, min(self.max_val,
                self.value * (1.0 + random.gauss(0, self.mutation_scale))))
        elif self.param_type == "int":
            delta = random.choice([-2, -1, 0, 1, 2])
            p.value = int(max(self.min_val, min(self.max_val, self.value + delta)))
        elif self.param_type == "choice":
            if self.choices:
                p.value = random.choice(self.choices)
        elif self.param_type == "bool":
            p.value = random.choice([True, False])
        elif self.param_type == "formula":
            p.value = self._mutate_formula(self.value)
        return p

    def _mutate_formula(self, formula: str) -> str:
        """Mutate a mathematical formula string."""
        ops = ['+', '-', '*', '/', '%', '**']
        parts = formula.split()
        if not parts:
            return formula
        idx = random.randint(0, len(parts) - 1)
        if parts[idx].replace('.', '').replace('-', '').isdigit():
            parts[idx] = str(float(parts[idx]) * (1.0 + random.gauss(0, 0.2)))
        elif parts[idx] in ops:
            parts[idx] = random.choice(ops)
        return ' '.join(parts)


@dataclass
class SystemConfig:
    """Configuration for a modifiable symbolic system."""
    system_id: str
    parameters: dict[str, SystemParameter] = field(default_factory=dict)
    calculation_method: str = "standard"
    input_transform: str = "identity"
    output_transform: str = "identity"
    combination_rules: dict = field(default_factory=dict)
    custom_formulas: dict = field(default_factory=dict)

    def get_param(self, name: str) -> Any:
        if name in self.parameters:
            return self.parameters[name].value
        return None

    def set_param(self, name: str, value: Any):
        if name in self.parameters:
            self.parameters[name].value = value

    def mutate_params(self, rate: float = 0.1) -> "SystemConfig":
        new_config = copy.deepcopy(self)
        for name, param in new_config.parameters.items():
            new_config.parameters[name] = param.mutate(rate)
        if random.random() < rate * 0.3:
            methods = ["standard", "weighted", "resonance", "phase_shift",
                      "harmonic", "quantum", "fractal", "chaotic"]
            new_config.calculation_method = random.choice(methods)
        if random.random() < rate * 0.2:
            transforms = ["identity", "log", "sqrt", "sin", "cos",
                         "normalize", "softmax", "sigmoid"]
            new_config.input_transform = random.choice(transforms)
        return new_config

    def to_dict(self) -> dict:
        return {
            "system_id": self.system_id,
            "parameters": {k: {"value": v.value, "type": v.param_type,
                              "min": v.min_val, "max": v.max_val}
                          for k, v in self.parameters.items()},
            "calculation_method": self.calculation_method,
            "input_transform": self.input_transform,
            "output_transform": self.output_transform,
            "combination_rules": self.combination_rules,
            "custom_formulas": self.custom_formulas,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "SystemConfig":
        params = {}
        for k, v in d.get("parameters", {}).items():
            params[k] = SystemParameter(
                name=k, value=v.get("value", 0),
                param_type=v.get("type", "float"),
                min_val=v.get("min", 0), max_val=v.get("max", 100))
        return cls(
            system_id=d.get("system_id", ""),
            parameters=params,
            calculation_method=d.get("calculation_method", "standard"),
            input_transform=d.get("input_transform", "identity"),
            output_transform=d.get("output_transform", "identity"),
            combination_rules=d.get("combination_rules", {}),
            custom_formulas=d.get("custom_formulas", {}),
        )


class ModifiableSystem:
    """Base class for symbolic systems that can be modified by genetic algorithms."""

    def __init__(self, base_wrapper, config: SystemConfig = None):
        self.base_wrapper = base_wrapper
        self.config = config or self._default_config()
        self.calculation_history: list[dict] = []

    def _default_config(self) -> SystemConfig:
        return SystemConfig(
            system_id=self.base_wrapper.SYSTEM_ID,
            parameters={
                "weight": SystemParameter("weight", 1.0, "float", 0.1, 5.0),
                "precision": SystemParameter("precision", 64, "int", 8, 256),
                "amplitude": SystemParameter("amplitude", 1.0, "float", 0.01, 10.0),
                "phase_offset": SystemParameter("phase_offset", 0.0, "float", 0, 6.28),
            },
        )

    def compute(self, entropy_packet: dict) -> Any:
        modified_ep = self._apply_input_transform(entropy_packet)
        params = {k: v.value for k, v in self.config.parameters.items()}
        output = self.base_wrapper.compute(modified_ep, params)
        return self._apply_output_transform(output)

    def _apply_input_transform(self, ep: dict) -> dict:
        ep = copy.deepcopy(ep)
        t = self.config.input_transform
        if "numeric_vector" in ep and ep["numeric_vector"]:
            nv = ep["numeric_vector"]
            if t == "log":
                ep["numeric_vector"] = [math.log(abs(x) + 1) for x in nv]
            elif t == "sqrt":
                ep["numeric_vector"] = [math.sqrt(abs(x)) for x in nv]
            elif t == "sin":
                ep["numeric_vector"] = [math.sin(x) for x in nv]
            elif t == "cos":
                ep["numeric_vector"] = [math.cos(x) for x in nv]
            elif t == "normalize":
                mx = max(abs(x) for x in nv) if nv else 1
                ep["numeric_vector"] = [x / mx for x in nv]
            elif t == "softmax":
                mx = max(nv)
                exps = [math.exp(x - mx) for x in nv]
                s = sum(exps)
                ep["numeric_vector"] = [e / s for e in exps]
            elif t == "sigmoid":
                ep["numeric_vector"] = [1 / (1 + math.exp(-x)) for x in nv]
        return ep

    def _apply_output_transform(self, output) -> Any:
        t = self.config.output_transform
        if hasattr(output, 'numeric_projection') and output.numeric_projection:
            nv = output.numeric_projection
            if t == "log":
                output.numeric_projection = [math.log(abs(x) + 1) for x in nv]
            elif t == "sigmoid":
                output.numeric_projection = [1 / (1 + math.exp(-x)) for x in nv]
            elif t == "normalize":
                mx = max(abs(x) for x in nv) if nv else 1
                output.numeric_projection = [x / mx for x in nv]
        return output

    def get_config(self) -> SystemConfig:
        return copy.deepcopy(self.config)

    def set_config(self, config: SystemConfig):
        self.config = copy.deepcopy(config)


class FormulaEngine:
    """Engine for creating and evaluating custom mathematical formulas."""

    OPERATORS = {
        '+': lambda a, b: a + b,
        '-': lambda a, b: a - b,
        '*': lambda a, b: a * b,
        '/': lambda a, b: a / b if b != 0 else 0,
        '%': lambda a, b: a % b if b != 0 else 0,
        '**': lambda a, b: a ** min(b, 10),
        'min': lambda a, b: min(a, b),
        'max': lambda a, b: max(a, b),
        'mod7': lambda a, b: a % 7,
        'mod12': lambda a, b: a % 12,
        'fibonacci': lambda a, b: _fib(int(abs(a)) % 20),
        'golden': lambda a, b: a * 1.618033988749895,
        'entropy_mix': lambda a, b: a * (1 + math.sin(b)),
    }

    FUNCTIONS = {
        'abs': abs,
        'sqrt': lambda x: math.sqrt(abs(x)),
        'sin': math.sin,
        'cos': math.cos,
        'log': lambda x: math.log(abs(x) + 1),
        'exp': lambda x: math.exp(min(x, 10)),
        'floor': math.floor,
        'ceil': math.ceil,
        'fibonacci': lambda x: _fib(int(abs(x)) % 20),
        'prime': lambda x: _next_prime(int(abs(x))),
        'digit_sum': lambda x: sum(int(d) for d in str(int(abs(x))) if d.isdigit()),
    }

    @staticmethod
    def evaluate(formula: str, variables: dict) -> float:
        try:
            safe_vars = {"math": math, "random": random}
            safe_vars.update(variables)
            safe_vars.update(FormulaEngine.FUNCTIONS)
            result = eval(formula, {"__builtins__": {}}, safe_vars)
            return float(result)
        except Exception:
            return 0.0

    @staticmethod
    def random_formula(depth: int = 2) -> str:
        if depth <= 0:
            return str(random.uniform(-10, 10))
        op = random.choice(list(FormulaEngine.OPERATORS.keys()))
        if random.random() < 0.5:
            return f"({FormulaEngine.random_formula(depth-1)} {op} {FormulaEngine.random_formula(depth-1)})"
        else:
            func = random.choice(list(FormulaEngine.FUNCTIONS.keys()))
            return f"{func}({FormulaEngine.random_formula(depth-1)})"

    @staticmethod
    def mutate_formula(formula: str, rate: float = 0.2) -> str:
        if random.random() > rate:
            return formula
        parts = list(formula)
        idx = random.randint(0, len(parts) - 1)
        mutation_type = random.choice(["char", "insert", "delete", "replace"])
        if mutation_type == "char" and parts[idx].isalnum():
            parts[idx] = random.choice("0123456789+-*/().abcdef")
        elif mutation_type == "insert":
            parts.insert(idx, random.choice("0123456789+-*/"))
        elif mutation_type == "delete" and len(parts) > 3:
            del parts[idx]
        elif mutation_type == "replace":
            parts[idx] = random.choice("0123456789+-*/")
        return ''.join(parts)


def _fib(n: int) -> int:
    a, b = 0, 1
    for _ in range(n):
        a, b = b, a + b
    return a


def _next_prime(n: int) -> int:
    n = max(2, int(n))
    while True:
        if all(n % i != 0 for i in range(2, int(math.sqrt(n)) + 1)):
            return n
        n += 1
