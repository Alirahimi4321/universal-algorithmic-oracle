"""Adaptive Mutation/Crossover Rate Controller per design doc section on premature convergence."""
import math


class AdaptiveRateController:
    """
    Adjusts mutation_rate and crossover_rate dynamically based on:
    1. Population diversity (Shannon entropy of system_ids)
    2. Fitness stagnation (consecutive generations without improvement)
    3. Generation progress (schedule-based decay/boost)
    
    Per design doc: prevents premature convergence while allowing exploitation.
    """

    def __init__(self, config: dict = None):
        config = config or {}
        self.base_mutation_rate = config.get("mutation_rate", 0.15)
        self.base_crossover_rate = config.get("crossover_rate", 0.7)
        self.min_mutation_rate = config.get("min_mutation_rate", 0.05)
        self.max_mutation_rate = config.get("max_mutation_rate", 0.5)
        self.min_crossover_rate = config.get("min_crossover_rate", 0.4)
        self.max_crossover_rate = config.get("max_crossover_rate", 0.95)

        self.stagnation_window = config.get("stagnation_window", 15)
        self.diversity_threshold = config.get("diversity_threshold", 0.3)

        self.current_mutation_rate = self.base_mutation_rate
        self.current_crossover_rate = self.base_crossover_rate
        self.fitness_history: list[float] = []
        self.diversity_history: list[float] = []

    def update(self, generation: int, best_fitness: float, diversity: float):
        """Update rates based on current state."""
        self.fitness_history.append(best_fitness)
        self.diversity_history.append(diversity)

        stagnation = self._detect_stagnation()
        low_diversity = diversity < self.diversity_threshold

        if stagnation or low_diversity:
            boost = 1.0 + min(2.0, self._stagnation_severity() + (0.5 if low_diversity else 0.0))
            self.current_mutation_rate = min(self.max_mutation_rate, self.base_mutation_rate * boost)
            self.current_crossover_rate = max(self.min_crossover_rate, self.base_crossover_rate * 0.8)
        else:
            decay = max(0.5, 1.0 - generation * 0.001)
            self.current_mutation_rate = max(self.min_mutation_rate, self.base_mutation_rate * decay)
            self.current_crossover_rate = min(self.max_crossover_rate, self.base_crossover_rate)

    def _detect_stagnation(self) -> bool:
        if len(self.fitness_history) < self.stagnation_window:
            return False
        recent = self.fitness_history[-self.stagnation_window:]
        improvement = max(recent) - min(recent)
        return improvement < 0.01

    def _stagnation_severity(self) -> float:
        if len(self.fitness_history) < self.stagnation_window:
            return 0.0
        recent = self.fitness_history[-self.stagnation_window:]
        improvement = max(recent) - min(recent)
        return max(0.0, 1.0 - improvement * 10)

    def get_rates(self) -> dict:
        return {
            "mutation_rate": self.current_mutation_rate,
            "crossover_rate": self.current_crossover_rate,
            "stagnation_detected": self._detect_stagnation(),
            "diversity": self.diversity_history[-1] if self.diversity_history else 0.5,
        }

    def to_dict(self) -> dict:
        return {
            "base_mutation_rate": self.base_mutation_rate,
            "base_crossover_rate": self.base_crossover_rate,
            "current_mutation_rate": self.current_mutation_rate,
            "current_crossover_rate": self.current_crossover_rate,
            "stagnation_window": self.stagnation_window,
            "diversity_threshold": self.diversity_threshold,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "AdaptiveRateController":
        ctrl = cls(config=d)
        ctrl.current_mutation_rate = d.get("current_mutation_rate", ctrl.base_mutation_rate)
        ctrl.current_crossover_rate = d.get("current_crossover_rate", ctrl.base_crossover_rate)
        return ctrl


def compute_population_diversity(population: list) -> float:
    """Shannon entropy of system_id distribution in population."""
    import math
    system_counts = {}
    total_genes = 0
    for chrom in population:
        for gene in chrom.gene_list if hasattr(chrom, 'gene_list') else []:
            sys_id = gene.system_id
            system_counts[sys_id] = system_counts.get(sys_id, 0) + 1
            total_genes += 1
    if total_genes == 0:
        return 0.0
    entropy = 0.0
    for count in system_counts.values():
        p = count / total_genes
        if p > 0:
            entropy -= p * math.log2(p)
    max_entropy = math.log2(max(len(system_counts), 1))
    return entropy / max_entropy if max_entropy > 0 else 0.0