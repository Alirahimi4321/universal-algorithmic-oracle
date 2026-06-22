"""Prediction Benchmark - validates prediction accuracy using cryptographic randomness."""
import secrets
import math
import hashlib
import time
from dataclasses import dataclass, field
from typing import Any


@dataclass
class BenchmarkResult:
    """Result of a single prediction benchmark."""
    target_numbers: list[float]
    predicted_numbers: list[float]
    accuracy: float  # 0.0 to 1.0
    error: float  # lower is better
    closeness_scores: list[float]  # per-number closeness
    difficulty_level: int
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return {
            "target_numbers": self.target_numbers,
            "predicted_numbers": self.predicted_numbers,
            "accuracy": self.accuracy,
            "error": self.error,
            "closeness_scores": self.closeness_scores,
            "difficulty_level": self.difficulty_level,
            "timestamp": self.timestamp,
        }


class PredictionBenchmark:
    """Generates random numbers and validates prediction accuracy."""

    def __init__(self, config: dict = None):
        config = config or {}
        self.seed = config.get("seed", None)
        self.history: list[BenchmarkResult] = []
        self.total_tests = 0
        self.total_accuracy = 0.0
        self.difficulty_level = 1
        self.num_range = config.get("num_range", (0, 9999))
        self.max_tests_before_levelup = config.get("max_tests", 5)
        self.tests_since_levelup = 0
        self.consecutive_successes = 0
        self.target_accuracy = config.get("target_accuracy", 0.6)

    def get_num_numbers(self) -> int:
        """Number of random numbers to generate based on difficulty."""
        base = 2
        extra = (self.difficulty_level - 1) * 2
        return min(base + extra, 20)

    def get_number_precision(self) -> int:
        """Precision of numbers based on difficulty."""
        if self.difficulty_level <= 2:
            return 1  # 1 decimal place
        elif self.difficulty_level <= 4:
            return 2  # 2 decimal places
        else:
            return 4  # 4 decimal places

    def generate_target_numbers(self) -> list[float]:
        """Generate cryptographically secure random numbers as prediction targets."""
        n = self.get_num_numbers()
        precision = self.get_number_precision()
        low, high = self.num_range
        numbers = []
        for _ in range(n):
            raw = secrets.randbelow(10000)
            num = low + (raw / 10000.0) * (high - low)
            num = round(num, precision)
            numbers.append(num)
        return numbers

    def validate_prediction(self, predicted: list[float], target: list[float]) -> BenchmarkResult:
        """Validate a prediction against the target numbers."""
        if not target:
            return BenchmarkResult(
                target_numbers=[], predicted_numbers=[],
                accuracy=0.0, error=float('inf'),
                closeness_scores=[], difficulty_level=self.difficulty_level
            )

        min_len = min(len(predicted), len(target))
        if min_len == 0:
            return BenchmarkResult(
                target_numbers=target, predicted_numbers=predicted,
                accuracy=0.0, error=float('inf'),
                closeness_scores=[0.0] * len(target), difficulty_level=self.difficulty_level
            )

        target_arr = target[:min_len]
        predicted_arr = predicted[:min_len]

        max_possible_error = max(target_arr) - min(target_arr) if len(target_arr) > 1 else 1.0
        max_possible_error = max(max_possible_error, 0.01)

        closeness_scores = []
        errors = []
        for t, p in zip(target_arr, predicted_arr):
            abs_error = abs(t - p)
            relative_error = abs_error / max(abs(t), 0.01)
            normalized_error = min(abs_error / max_possible_error, 1.0)
            closeness = 1.0 - normalized_error
            closeness_scores.append(closeness)
            errors.append(relative_error)

        avg_closeness = sum(closeness_scores) / len(closeness_scores)
        avg_error = sum(errors) / len(errors)
        accuracy = avg_closeness

        if min_len < len(target):
            missing_penalty = (len(target) - min_len) / len(target)
            accuracy *= (1.0 - missing_penalty)

        result = BenchmarkResult(
            target_numbers=target,
            predicted_numbers=predicted,
            accuracy=accuracy,
            error=avg_error,
            closeness_scores=closeness_scores,
            difficulty_level=self.difficulty_level,
        )

        self.history.append(result)
        self.total_tests += 1
        self.total_accuracy += accuracy
        self.tests_since_levelup += 1

        if accuracy >= self.target_accuracy:
            self.consecutive_successes += 1
        else:
            self.consecutive_successes = 0

        self._update_difficulty()

        return result

    def _update_difficulty(self):
        """Update difficulty based on performance."""
        if self.tests_since_levelup >= self.max_tests_before_levelup:
            if self.consecutive_successes >= 3:
                self.difficulty_level = min(self.difficulty_level + 1, 10)
                self.consecutive_successes = 0
            elif self.consecutive_successes <= 1:
                self.difficulty_level = max(self.difficulty_level - 1, 1)
            self.tests_since_levelup = 0

    def get_accuracy_history(self) -> list[float]:
        return [r.accuracy for r in self.history]

    def get_avg_accuracy(self) -> float:
        return self.total_accuracy / max(self.total_tests, 1)

    def get_stats(self) -> dict:
        return {
            "total_tests": self.total_tests,
            "avg_accuracy": self.get_avg_accuracy(),
            "difficulty_level": self.difficulty_level,
            "num_numbers": self.get_num_numbers(),
            "precision": self.get_number_precision(),
            "target_accuracy": self.target_accuracy,
            "consecutive_successes": self.consecutive_successes,
            "recent_accuracies": [r.accuracy for r in self.history[-10:]],
        }

    def to_dict(self) -> dict:
        return {
            "seed": self.seed,
            "difficulty_level": self.difficulty_level,
            "total_tests": self.total_tests,
            "total_accuracy": self.total_accuracy,
            "tests_since_levelup": self.tests_since_levelup,
            "consecutive_successes": self.consecutive_successes,
            "history": [r.to_dict() for r in self.history[-50:]],
        }

    @classmethod
    def from_dict(cls, d: dict) -> "PredictionBenchmark":
        bench = cls(config={"seed": d.get("seed")})
        bench.difficulty_level = d.get("difficulty_level", 1)
        bench.total_tests = d.get("total_tests", 0)
        bench.total_accuracy = d.get("total_accuracy", 0.0)
        bench.tests_since_levelup = d.get("tests_since_levelup", 0)
        bench.consecutive_successes = d.get("consecutive_successes", 0)
        for rd in d.get("history", []):
            bench.history.append(BenchmarkResult(
                target_numbers=rd.get("target_numbers", []),
                predicted_numbers=rd.get("predicted_numbers", []),
                accuracy=rd.get("accuracy", 0.0),
                error=rd.get("error", 0.0),
                closeness_scores=rd.get("closeness_scores", []),
                difficulty_level=rd.get("difficulty_level", 1),
                timestamp=rd.get("timestamp", 0.0),
            ))
        return bench

    def predict_from_entropy(self, entropy_packet: dict, num_numbers: int = None) -> list[float]:
        """Use entropy packet to generate prediction numbers."""
        n = num_numbers or self.get_num_numbers()
        seed_val = entropy_packet.get("seed", 42)
        sha = entropy_packet.get("sha_stream", "0")
        numeric_vec = entropy_packet.get("numeric_vector", [])

        predictions = []
        for i in range(n):
            if i < len(numeric_vec):
                base = numeric_vec[i]
            else:
                base = (seed_val * (i + 1) * 31) % 10000

            hash_val = int(hashlib.md5(f"{sha}_{i}_{seed_val}".encode()).hexdigest()[:8], 16)
            combined = (base * 0.3 + (hash_val % 10000) * 0.7) / 10000.0
            predictions.append(combined * self.num_range[1])

        precision = self.get_number_precision()
        return [round(p, precision) for p in predictions]
