"""DEAP-based Genetic Algorithm engine for oracle evolution."""
import random
import uuid
from typing import Callable
from ..genome.chromosome import Chromosome
from ..genome.gene import Gene
from ..evaluation.fitness import FitnessEvaluator
from ..evaluation.benchmark import PredictionBenchmark
from ..memory.generational_memory import GenerationalMemory
from .mutation import ALL_MUTATIONS, deep_system_mutation
from .rule_invention import RuleInventionEngine
from .progressive_difficulty import ProgressiveDifficulty
from .adaptive_rates import AdaptiveRateController, compute_population_diversity


AVAILABLE_SYSTEMS = [
    ("gematria", "internal"),
    ("iching", "internal"),
    ("geomancy", "internal"),
    ("calendar", "internal"),
]


class EvolutionaryEngine:
    def __init__(self, config: dict | None = None):
        config = config or {}
        self.population_size = config.get("population_size", 50)
        self.max_generations = config.get("max_generations", 200)
        self.elite_count = config.get("elite_count", 5)
        self.tournament_size = config.get("tournament_size", 3)
        self.mutation_rate = config.get("mutation_rate", 0.15)
        self.crossover_rate = config.get("crossover_rate", 0.7)
        self.deep_mutation_rate = config.get("deep_mutation_rate", 0.1)
        self.rule_invention_rate = config.get("rule_invention_rate", 0.15)
        self.memory_injection_rate = config.get("memory_injection_rate", 0.15)
        self.evaluator = FitnessEvaluator(config.get("fitness", {}))
        self.population: list[Chromosome] = []
        self.generation = 0
        self.best_history: list[dict] = []
        self.difficulty = ProgressiveDifficulty()
        self.rule_engine = RuleInventionEngine()
        self.benchmark = PredictionBenchmark(config.get("benchmark", {}))
        self.memory = GenerationalMemory(config.get("memory", {}))
        self.use_progressive_difficulty = config.get("use_progressive_difficulty", True)
        self.use_memory = config.get("use_memory", True)
        self.validation_history: list[dict] = []
        self.adaptive_rates = AdaptiveRateController(config.get("adaptive_rates", {}))
        self.use_adaptive_rates = config.get("use_adaptive_rates", True)

    def initialize_population(self, systems: list[tuple[str, str]] | None = None) -> list[Chromosome]:
        systems = systems or AVAILABLE_SYSTEMS
        self.population = []

        if self.use_progressive_difficulty:
            params = self.difficulty.get_evolution_params()
            num_systems = params["num_systems"]
            available = self.difficulty.get_available_systems([s[0] for s in systems])
            systems = [(s, "internal") for s in available if any(s == sys[0] for sys in systems)]
            if not systems:
                systems = AVAILABLE_SYSTEMS

        for _ in range(self.population_size):
            n = random.randint(1, min(4, len(systems)))
            selected = random.sample(systems, n)
            chrom = Chromosome.create_random(selected)
            self.population.append(chrom)

        if self.use_memory:
            self.population = self.memory.inject_memory(self.population, self.population_size)

        return self.population

    def evolve(
        self,
        entropy_packet: dict,
        generations: int | None = None,
        callback: Callable[[int, list[Chromosome], list[dict]], None] | None = None,
    ) -> list[Chromosome]:
        max_gen = generations or self.max_generations

        if not self.population:
            self.initialize_population()

        for gen in range(max_gen):
            self.generation = gen + 1

            fitness_scores = []
            for chrom in self.population:
                scores = self.evaluator.evaluate(chrom, entropy_packet)
                chrom.fitness = scores
                fitness_scores.append(scores)

            sorted_pop = sorted(
                self.population,
                key=lambda c: c.fitness.get("total_fitness", 0),
                reverse=True,
            )

            best = sorted_pop[0] if sorted_pop else None
            best_fitness = best.fitness.get("total_fitness", 0) if best else 0
            best_pred_accuracy = best.fitness.get("prediction_accuracy", 0) if best else 0

            self.best_history.append({
                "generation": self.generation,
                "best_fitness": best_fitness,
                "best_prediction_accuracy": best_pred_accuracy,
                "avg_fitness": sum(s.get("total_fitness", 0) for s in fitness_scores) / max(len(fitness_scores), 1),
                "difficulty_level": self.difficulty.current_level,
                "benchmark_difficulty": self.benchmark.difficulty_level,
                "benchmark_avg_accuracy": self.benchmark.get_avg_accuracy(),
            })

            if callback:
                callback(self.generation, self.population, fitness_scores)

            if self.use_adaptive_rates:
                diversity = compute_population_diversity(self.population)
                self.adaptive_rates.update(self.generation, best_fitness, diversity)
                current_rates = self.adaptive_rates.get_rates()
                effective_crossover_rate = current_rates["crossover_rate"]
                effective_mutation_rate = current_rates["mutation_rate"]
            else:
                effective_crossover_rate = self.crossover_rate
                effective_mutation_rate = self.mutation_rate

            new_population = sorted_pop[: self.elite_count]

            while len(new_population) < self.population_size:
                if random.random() < effective_crossover_rate:
                    parent1 = self._tournament_select(sorted_pop)
                    parent2 = self._tournament_select(sorted_pop)
                    child = parent1.crossover(parent2)
                else:
                    parent = self._tournament_select(sorted_pop)
                    child = Chromosome.from_dict(parent.to_dict())

                mutation_type = random.choices(
                    ["standard", "deep", "rule"],
                    weights=[0.6, 0.25, 0.15]
                )[0]

                if mutation_type == "deep":
                    child = deep_system_mutation(
                        child, self.deep_mutation_rate,
                        self.difficulty if self.use_progressive_difficulty else None
                    )
                elif mutation_type == "rule":
                    child = self.rule_engine.invent_rules(child)
                else:
                    mut_fn = random.choice(ALL_MUTATIONS)
                    child = mut_fn(child, effective_mutation_rate)

                child.generation = self.generation
                child.chromosome_id = str(uuid.uuid4())[:8]
                new_population.append(child)

            if self.use_memory and random.random() < self.memory_injection_rate:
                new_population = self.memory.inject_memory(new_population, self.population_size)

            self.population = new_population[: self.population_size]

            if self.use_progressive_difficulty and best:
                self.difficulty.record_attempt(
                    success=best_fitness > 0.5,
                    confidence=best.fitness.get("oracle_confidence", 0),
                    fitness=best_fitness,
                )

            if self.use_memory and best:
                self.memory.remember(best, self.generation,
                                    self.difficulty.current_level,
                                    self.benchmark.get_avg_accuracy())

            if self.generation % 3 == 0 or self.generation == max_gen:
                self._run_validation(best, entropy_packet)

            if self.use_memory and self.generation % 5 == 0:
                self.memory.save_snapshot(
                    self.generation, self.population,
                    self.difficulty.current_level,
                    self.benchmark.get_avg_accuracy(),
                )

        fitness_scores = []
        for chrom in self.population:
            scores = self.evaluator.evaluate(chrom, entropy_packet)
            chrom.fitness = scores
            fitness_scores.append(scores)

        return sorted(
            self.population,
            key=lambda c: c.fitness.get("total_fitness", 0),
            reverse=True,
        )

    def _run_validation(self, best_chromosome: Chromosome, entropy_packet: dict):
        """Run a validation benchmark against the best chromosome."""
        if best_chromosome is None:
            return

        target_numbers = self.benchmark.generate_target_numbers()

        try:
            exec_result = best_chromosome.execute(entropy_packet)
            fused_numeric = exec_result.get("fused_numeric", [])
        except Exception:
            fused_numeric = []

        predictions = []
        import math, hashlib
        for i in range(len(target_numbers)):
            if i < len(fused_numeric):
                val = fused_numeric[i]
                normalized = (math.sin(val * 12.9898 + i * 78.233) + 1) / 2
                predictions.append(normalized * self.benchmark.num_range[1])
            else:
                seed = entropy_packet.get("seed", 42)
                sha = entropy_packet.get("sha_stream", "0")
                hash_val = int(hashlib.md5(f"{sha}_{i}_{seed}".encode()).hexdigest()[:8], 16)
                predictions.append((hash_val % 10000) / 10000.0 * self.benchmark.num_range[1])

        precision = self.benchmark.get_number_precision()
        predictions = [round(p, precision) for p in predictions]

        result = self.benchmark.validate_prediction(predictions, target_numbers)

        self.validation_history.append({
            "generation": self.generation,
            "accuracy": result.accuracy,
            "error": result.error,
            "difficulty": self.benchmark.difficulty_level,
            "num_numbers": len(target_numbers),
            "target": target_numbers[:5],
            "predicted": predictions[:5],
        })

    def _tournament_select(self, population: list[Chromosome]) -> Chromosome:
        candidates = random.sample(population, min(self.tournament_size, len(population)))
        return max(candidates, key=lambda c: c.fitness.get("total_fitness", 0))

    def get_best(self) -> Chromosome | None:
        if not self.population:
            return None
        return max(self.population, key=lambda c: c.fitness.get("total_fitness", 0))

    def get_elite(self, count: int = 5) -> list[Chromosome]:
        sorted_pop = sorted(
            self.population,
            key=lambda c: c.fitness.get("total_fitness", 0),
            reverse=True,
        )
        return sorted_pop[:count]

    def get_validation_report(self) -> dict:
        if not self.validation_history:
            return {"message": "No validation runs yet"}
        accuracies = [v["accuracy"] for v in self.validation_history]
        report = {
            "total_validations": len(self.validation_history),
            "avg_accuracy": sum(accuracies) / len(accuracies),
            "best_accuracy": max(accuracies),
            "worst_accuracy": min(accuracies),
            "current_benchmark_difficulty": self.benchmark.difficulty_level,
            "recent_validations": self.validation_history[-5:],
        }
        if self.use_memory:
            report["memory_report"] = self.memory.get_memory_report()
        return report
