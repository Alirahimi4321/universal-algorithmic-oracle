"""Optuna-based Bayesian Optimizer for oracle evolution parameters."""
from __future__ import annotations
import logging
import numpy as np
from typing import Any, Callable

logger = logging.getLogger(__name__)

try:
    import optuna
    optuna.logging.set_verbosity(optuna.logging.WARNING)
    HAS_OPTUNA = True
except Exception:
    HAS_OPTUNA = False


class OptunaOptimizer:
    """Optimize oracle evolution parameters using Optuna Bayesian optimization."""

    def __init__(self) -> None:
        self.available = HAS_OPTUNA
        self._study = None

    def optimize_evolution_params(self, objective_fn: Callable, n_trials: int = 50,
                                   n_startup_trials: int = 10) -> dict[str, Any]:
        if not self.available:
            return {"best_params": {}, "best_value": None, "method": "unavailable"}
        try:
            sampler = optuna.samplers.TPESampler(n_startup_trials=n_startup_trials, seed=42)
            study = optuna.create_study(direction="maximize", sampler=sampler)
            study.optimize(objective_fn, n_trials=n_trials, show_progress_bar=False)
            self._study = study
            return {
                "best_params": study.best_params,
                "best_value": round(float(study.best_value), 6),
                "n_trials": len(study.trials),
                "method": "TPE",
                "param_importances": self._get_importances(study),
                "optimization_history": self._get_history(study),
            }
        except Exception as e:
            return {"best_params": {}, "best_value": None, "method": "failed", "error": str(e)}

    def optimize_population_params(self, fitness_fn: Callable, n_trials: int = 30) -> dict[str, Any]:
        def objective(trial):
            population_size = trial.suggest_int("population_size", 20, 100)
            mutation_rate = trial.suggest_float("mutation_rate", 0.05, 0.3)
            crossover_rate = trial.suggest_float("crossover_rate", 0.5, 0.9)
            tournament_size = trial.suggest_int("tournament_size", 2, 7)
            elite_count = trial.suggest_int("elite_count", 1, 10)
            return fitness_fn(population_size=population_size, mutation_rate=mutation_rate,
                              crossover_rate=crossover_rate, tournament_size=tournament_size, elite_count=elite_count)
        return self.optimize_evolution_params(objective, n_trials=n_trials)

    def optimize_mutation_params(self, fitness_fn: Callable, n_trials: int = 30) -> dict[str, Any]:
        def objective(trial):
            param_rate = trial.suggest_float("param_rate", 0.05, 0.3)
            structural_rate = trial.suggest_float("structural_rate", 0.05, 0.3)
            civilization_rate = trial.suggest_float("civilization_rate", 0.0, 0.2)
            deep_mutation_rate = trial.suggest_float("deep_mutation_rate", 0.0, 0.15)
            rule_invention_rate = trial.suggest_float("rule_invention_rate", 0.0, 0.2)
            return fitness_fn(param_rate=param_rate, structural_rate=structural_rate,
                              civilization_rate=civilization_rate, deep_mutation_rate=deep_mutation_rate,
                              rule_invention_rate=rule_invention_rate)
        return self.optimize_evolution_params(objective, n_trials=n_trials)

    def optimize_fitness_weights(self, fitness_fn: Callable, n_trials: int = 30) -> dict[str, Any]:
        dimensions = ["structural_coherence", "response_stability", "symbolic_convergence",
                      "novelty_score", "complexity_penalty", "tradition_escape",
                      "entropy_utilization", "oracle_confidence", "pure_entropy_fitness",
                      "historical_accuracy_fitness"]
        def objective(trial):
            weights = {d: trial.suggest_float(f"w_{d}", 0.0, 1.0) for d in dimensions}
            total = sum(weights.values())
            if total > 0:
                weights = {k: v / total for k, v in weights.items()}
            return fitness_fn(weights=weights)
        return self.optimize_evolution_params(objective, n_trials=n_trials)

    def suggest_params(self, param_space: dict[str, Any], trial_name: str = "suggest") -> dict[str, Any]:
        if not self.available:
            return {}
        study = optuna.create_study()
        def objective(trial):
            params = {}
            for name, spec in param_space.items():
                if spec["type"] == "int":
                    params[name] = trial.suggest_int(name, spec["low"], spec["high"])
                elif spec["type"] == "float":
                    params[name] = trial.suggest_float(name, spec["low"], spec["high"],
                                                        log=spec.get("log", False))
                elif spec["type"] == "categorical":
                    params[name] = trial.suggest_categorical(name, spec["choices"])
            return 0.0
        study.optimize(objective, n_trials=1)
        return study.best_params

    def _get_importances(self, study) -> dict[str, float]:
        try:
            importances = optuna.importance.get_param_importances(study)
            return {k: round(float(v), 4) for k, v in importances.items()}
        except Exception:
            return {}

    def _get_history(self, study) -> list[dict[str, Any]]:
        history = []
        for trial in study.trials[:50]:
            history.append({"number": trial.number, "value": round(float(trial.value), 6) if trial.value is not None else None,
                           "params": {k: round(float(v), 4) if isinstance(v, float) else v for k, v in trial.params.items()}})
        return history

    def compare_samplers(self, objective_fn: Callable, n_trials: int = 20) -> dict[str, Any]:
        if not self.available:
            return {"results": [], "method": "unavailable"}
        samplers = {
            "TPE": optuna.samplers.TPESampler(seed=42),
            "Random": optuna.samplers.RandomSampler(seed=42),
            "CMA-ES": optuna.samplers.CmaEsSampler(seed=42),
        }
        results = {}
        for name, sampler in samplers.items():
            try:
                study = optuna.create_study(direction="maximize", sampler=sampler)
                study.optimize(objective_fn, n_trials=n_trials, show_progress_bar=False)
                results[name] = {"best_value": round(float(study.best_value), 6), "best_params": study.best_params}
            except Exception as e:
                results[name] = {"best_value": None, "error": str(e)}
        return {"results": results, "method": "comparison"}
