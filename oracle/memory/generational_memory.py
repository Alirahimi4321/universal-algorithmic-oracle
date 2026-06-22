"""Generational Memory - loads and uses experience from previous generations."""
import random
import copy
import json
import time
from typing import Any
from ..genome.chromosome import Chromosome
from .chromosome_archive import ChromosomeArchive


class GenerationalMemory:
    """Memory system that learns from previous generations' successes."""

    def __init__(self, config: dict = None):
        config = config or {}
        self.archive = ChromosomeArchive(config.get("archive_path", "data/generational_memory.db"))
        self.memory_size = config.get("memory_size", 20)
        self.injection_rate = config.get("injection_rate", 0.15)
        self.learning_rate = config.get("learning_rate", 0.3)
        self.experience_weights: dict[str, float] = {}
        self.successful_patterns: list[dict] = []
        self.total_injections = 0
        self.total_successes = 0

    def remember(self, chromosome: Chromosome, generation: int,
                 difficulty_level: int = 1, benchmark_accuracy: float = 0.0):
        """Remember a successful chromosome."""
        score = chromosome.fitness.get("total_fitness", 0) if isinstance(chromosome.fitness, dict) else 0
        pred_acc = chromosome.fitness.get("prediction_accuracy", 0) if isinstance(chromosome.fitness, dict) else 0

        if score > 0.4 or pred_acc > 0.3:
            self.archive.save_best(chromosome, generation, difficulty_level, benchmark_accuracy)

            pattern = self._extract_pattern(chromosome)
            self.successful_patterns.append(pattern)

            self._update_experience_weights(chromosome, score)

    def recall(self, n: int = 5) -> list[dict]:
        """Recall the best chromosomes from memory."""
        return self.archive.get_best(n=n)

    def get_seed_chromosomes(self, count: int = 3) -> list[dict]:
        """Get seed chromosomes from previous successful evolutions."""
        best = self.archive.get_best(n=self.memory_size)
        if not best:
            return []

        selected = random.sample(best, min(count, len(best)))
        return [chrom["chromosome_data"] for chrom in selected]

    def inject_memory(self, population: list[Chromosome], target_size: int) -> list[Chromosome]:
        """Inject memory chromosomes into the population."""
        if random.random() > self.injection_rate:
            return population

        seed_data = self.get_seed_chromosomes(count=max(1, target_size // 5))
        if not seed_data:
            return population

        new_pop = population[:]
        for data in seed_data:
            try:
                chrom = Chromosome.from_dict(data)
                chrom.chromosome_id = f"memory_{chrom.chromosome_id[:8]}"
                chrom.generation = 0
                chrom.fitness = {}

                chrom = self._mutate_memory_chromosome(chrom)
                new_pop.append(chrom)
                self.total_injections += 1
            except Exception:
                continue

        return new_pop[:target_size]

    def _mutate_memory_chromosome(self, chrom: Chromosome) -> Chromosome:
        """Slightly mutate a memory chromosome to adapt to new context."""
        from ..evolution.mutation import param_mutation, deep_system_mutation

        if random.random() < 0.5:
            return param_mutation(chrom, rate=0.1)
        else:
            return deep_system_mutation(chrom, rate=0.05)

    def _extract_pattern(self, chrom: Chromosome) -> dict:
        """Extract successful patterns from a chromosome."""
        systems = [g.system_id for g in chrom.gene_list]
        weights = [g.weight for g in chrom.gene_list]
        return {
            "systems": systems,
            "avg_weight": sum(weights) / len(weights) if weights else 0,
            "gene_count": len(chrom.genes),
            "fusion_type": chrom.fusion_schema.get("type", "unknown"),
            "rule_count": len(chrom.fusion_rules),
            "config_count": len(chrom.system_configs),
            "formula_count": len(chrom.custom_formulas),
        }

    def _update_experience_weights(self, chrom: Chromosome, score: float):
        """Update which systems and patterns lead to success."""
        for gene in chrom.gene_list:
            sys_id = gene.system_id
            if sys_id not in self.experience_weights:
                self.experience_weights[sys_id] = 0.0
            self.experience_weights[sys_id] += score * self.learning_rate

        for system_id in self.experience_weights:
            self.experience_weights[system_id] *= 0.95

    def get_system_preferences(self) -> dict[str, float]:
        """Get which systems are preferred based on experience."""
        if not self.experience_weights:
            return {}
        total = sum(abs(v) for v in self.experience_weights.values())
        if total == 0:
            return {}
        return {k: abs(v) / total for k, v in self.experience_weights.items()}

    def get_pattern_insights(self) -> dict:
        """Get insights from successful patterns."""
        if not self.successful_patterns:
            return {"message": "No patterns recorded yet"}

        system_counts = {}
        for pattern in self.successful_patterns:
            for sys in pattern["systems"]:
                system_counts[sys] = system_counts.get(sys, 0) + 1

        most_common = sorted(system_counts.items(), key=lambda x: x[1], reverse=True)[:10]

        avg_gene_count = sum(p["gene_count"] for p in self.successful_patterns) / len(self.successful_patterns)
        avg_rules = sum(p["rule_count"] for p in self.successful_patterns) / len(self.successful_patterns)

        return {
            "total_patterns": len(self.successful_patterns),
            "most_successful_systems": most_common,
            "avg_gene_count": avg_gene_count,
            "avg_rule_count": avg_rules,
            "system_preferences": self.get_system_preferences(),
        }

    def save_snapshot(self, generation: int, population: list[Chromosome],
                      difficulty_level: int = 1, benchmark_accuracy: float = 0.0):
        """Save a snapshot of the current population state."""
        if not population:
            return

        best = max(population, key=lambda c: c.fitness.get("total_fitness", 0) if isinstance(c.fitness, dict) else 0)
        best_fitness = best.fitness.get("total_fitness", 0) if isinstance(best.fitness, dict) else 0
        avg_fitness = sum(
            c.fitness.get("total_fitness", 0) if isinstance(c.fitness, dict) else 0
            for c in population
        ) / len(population)
        best_pred = best.fitness.get("prediction_accuracy", 0) if isinstance(best.fitness, dict) else 0

        best_id = self.archive.save_best(best, generation, difficulty_level, benchmark_accuracy)

        self.archive.save_generation_snapshot(
            generation=generation,
            best_fitness=best_fitness,
            avg_fitness=avg_fitness,
            best_prediction_accuracy=best_pred,
            difficulty_level=difficulty_level,
            benchmark_accuracy=benchmark_accuracy,
            population_size=len(population),
            best_chromosome_id=best_id,
            snapshot_data={"patterns": len(self.successful_patterns)},
        )

    def get_memory_report(self) -> dict:
        """Get a report of the memory system."""
        archive_stats = self.archive.get_stats()
        pattern_insights = self.get_pattern_insights()
        return {
            "archive_stats": archive_stats,
            "pattern_insights": pattern_insights,
            "total_injections": self.total_injections,
            "injection_rate": self.injection_rate,
            "experience_weights_count": len(self.experience_weights),
        }

    def to_dict(self) -> dict:
        return {
            "experience_weights": self.experience_weights,
            "successful_patterns": self.successful_patterns[-20:],
            "total_injections": self.total_injections,
            "archive": self.archive.to_dict(),
        }

    @classmethod
    def from_dict(cls, d: dict, config: dict = None) -> "GenerationalMemory":
        mem = cls(config)
        mem.experience_weights = d.get("experience_weights", {})
        mem.successful_patterns = d.get("successful_patterns", [])
        mem.total_injections = d.get("total_injections", 0)
        return mem
