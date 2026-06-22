"""Meta-Oracle Selector: selects the best oracle from a population.

Per design doc section 15.4: Meta-Oracular Selection across islands.
"""
import time
import hashlib
import json
import math
from typing import Optional


class MetaOracleSelector:
    """Selects the best oracle from a population based on multi-objective fitness."""

    def __init__(self, config: dict = None):
        config = config or {}
        self.min_confidence = config.get("min_confidence", 0.3)
        self.diversity_bonus = config.get("diversity_bonus", 0.1)
        self.history = []

    def select(
        self,
        population: list,
        generation: int = 0,
    ) -> Optional[dict]:
        """Select the best oracle from the population."""
        if not population:
            return None

        scored = []
        for chrom in population:
            score = self._score_chromosome(chrom, generation)
            if score > 0:
                scored.append((chrom, score))

        if not scored:
            return None

        scored.sort(key=lambda x: x[1], reverse=True)
        best_chrom, best_score = scored[0]

        systems = [g.system_id for g in best_chrom.gene_list] if hasattr(best_chrom, 'gene_list') else []

        result = {
            "chromosome": best_chrom,
            "score": best_score,
            "rank": 1,
            "total_evaluated": len(population),
            "total_qualified": len(scored),
            "systems": systems,
            "generation": generation,
            "timestamp": time.time(),
        }

        self.history.append({
            "generation": generation,
            "best_score": best_score,
            "population_size": len(population),
            "qualified_count": len(scored),
            "best_systems": systems[:5],
        })

        return result

    def select_diverse(
        self,
        population: list,
        n: int = 5,
        generation: int = 0,
    ) -> list[dict]:
        """Select N diverse oracles using fitness + diversity."""
        if not population:
            return []

        scored = []
        for chrom in population:
            score = self._score_chromosome(chrom, generation)
            if score > 0:
                systems = tuple(sorted(g.system_id for g in chrom.gene_list)) if hasattr(chrom, 'gene_list') else ()
                scored.append((chrom, score, systems))

        if not scored:
            return []

        scored.sort(key=lambda x: x[1], reverse=True)

        selected = []
        seen_systems = set()

        for chrom, score, systems in scored:
            diversity_key = systems
            diversity_bonus = self.diversity_bonus if diversity_key not in seen_systems else 0
            final_score = score + diversity_bonus

            selected.append({
                "chromosome": chrom,
                "score": final_score,
                "fitness_score": score,
                "diversity_bonus": diversity_bonus,
                "systems": list(systems),
                "generation": generation,
            })
            seen_systems.add(diversity_key)

            if len(selected) >= n:
                break

        return selected

    def _score_chromosome(self, chrom, generation: int = 0) -> float:
        """Score a chromosome using multi-objective fitness."""
        fitness = getattr(chrom, 'fitness', {})
        if not fitness:
            return 0.0

        weights = {
            "structural_coherence": 0.15,
            "response_stability": 0.15,
            "symbolic_convergence": 0.10,
            "novelty_score": 0.10,
            "entropy_utilization": 0.10,
            "oracle_confidence": 0.15,
            "pure_entropy_fitness": 0.15,
            "historical_accuracy_fitness": 0.10,
        }

        total = 0.0
        for key, weight in weights.items():
            total += fitness.get(key, 0) * weight

        total_fitness = fitness.get("total_fitness", 0)
        if total_fitness > total:
            total = total_fitness

        return total

    def get_pareto_front(self, population: list) -> list[dict]:
        """Find Pareto-optimal oracles (multi-objective)."""
        if not population:
            return []

        objectives = []
        for chrom in population:
            fitness = getattr(chrom, 'fitness', {})
            obj = (
                fitness.get("structural_coherence", 0),
                fitness.get("response_stability", 0),
                fitness.get("novelty_score", 0),
            )
            objectives.append((chrom, obj))

        pareto = []
        for i, (chrom_i, obj_i) in enumerate(objectives):
            dominated = False
            for j, (chrom_j, obj_j) in enumerate(objectives):
                if i != j:
                    if all(a >= b for a, b in zip(obj_j, obj_i)) and any(a > b for a, b in zip(obj_j, obj_i)):
                        dominated = True
                        break
            if not dominated:
                pareto.append({
                    "chromosome": chrom_i,
                    "objectives": {
                        "structural_coherence": obj_i[0],
                        "response_stability": obj_i[1],
                        "novelty_score": obj_i[2],
                    },
                })

        return pareto

    def get_stats(self) -> dict:
        if not self.history:
            return {"total_selections": 0}
        return {
            "total_selections": len(self.history),
            "avg_best_score": sum(h["best_score"] for h in self.history) / len(self.history),
            "max_best_score": max(h["best_score"] for h in self.history),
            "avg_population": sum(h["population_size"] for h in self.history) / len(self.history),
        }
