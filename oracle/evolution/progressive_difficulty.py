"""Progressive Difficulty Controller - makes predictions harder over time."""
import random
import math
from dataclasses import dataclass, field
from typing import Any


@dataclass
class DifficultyLevel:
    """A single difficulty level."""
    level: int
    name: str
    description: str
    num_systems_range: tuple = (2, 4)
    min_generations: int = 10
    required_confidence: float = 0.5
    entropy_complexity: float = 0.3
    allowed_domains: list = field(default_factory=lambda: ["general"])
    mutation_intensity: float = 0.2
    crossover_diversity: float = 0.3
    fitness_threshold: float = 0.6


DIFFICULTY_LEVELS = [
    DifficultyLevel(
        level=1, name="Novice",
        description="Simple predictions with few systems",
        num_systems_range=(1, 3), min_generations=5,
        required_confidence=0.3, entropy_complexity=0.2,
        allowed_domains=["general"],
        mutation_intensity=0.1, crossover_diversity=0.2, fitness_threshold=0.4,
    ),
    DifficultyLevel(
        level=2, name="Apprentice",
        description="Multi-system predictions",
        num_systems_range=(2, 5), min_generations=10,
        required_confidence=0.4, entropy_complexity=0.3,
        allowed_domains=["general", "personal"],
        mutation_intensity=0.2, crossover_diversity=0.3, fitness_threshold=0.5,
    ),
    DifficultyLevel(
        level=3, name="Adept",
        description="Cross-domain predictions",
        num_systems_range=(3, 7), min_generations=15,
        required_confidence=0.5, entropy_complexity=0.4,
        allowed_domains=["general", "personal", "financial"],
        mutation_intensity=0.3, crossover_diversity=0.4, fitness_threshold=0.6,
    ),
    DifficultyLevel(
        level=4, name="Expert",
        description="Complex multi-domain with custom formulas",
        num_systems_range=(4, 9), min_generations=20,
        required_confidence=0.6, entropy_complexity=0.5,
        allowed_domains=["general", "personal", "financial", "social"],
        mutation_intensity=0.4, crossover_diversity=0.5, fitness_threshold=0.7,
    ),
    DifficultyLevel(
        level=5, name="Master",
        description="Full system fusion with invention",
        num_systems_range=(5, 12), min_generations=30,
        required_confidence=0.7, entropy_complexity=0.6,
        allowed_domains=["general", "personal", "financial", "social", "political", "natural"],
        mutation_intensity=0.5, crossover_diversity=0.6, fitness_threshold=0.75,
    ),
    DifficultyLevel(
        level=6, name="Oracle",
        description="Maximum complexity, all systems, all domains",
        num_systems_range=(8, 20), min_generations=50,
        required_confidence=0.8, entropy_complexity=0.8,
        allowed_domains=["all"],
        mutation_intensity=0.7, crossover_diversity=0.8, fitness_threshold=0.85,
    ),
]


class ProgressiveDifficulty:
    """Controls the progressive difficulty of predictions."""

    def __init__(self, config: dict = None):
        self.config = config or {}
        self.current_level = 1
        self.levels = DIFFICULTY_LEVELS
        self.history: list[dict] = []
        self.total_questions = 0
        self.successful_predictions = 0

    def get_current_level(self) -> DifficultyLevel:
        for level in self.levels:
            if level.level == self.current_level:
                return level
        return self.levels[-1]

    def record_attempt(self, success: bool, confidence: float, fitness: float):
        self.total_questions += 1
        if success:
            self.successful_predictions += 1

        self.history.append({
            "level": self.current_level,
            "success": success,
            "confidence": confidence,
            "fitness": fitness,
            "total_questions": self.total_questions,
        })

        if self.total_questions >= 5:
            recent = self.history[-5:]
            recent_success = sum(1 for h in recent if h["success"])
            if recent_success >= 4 and confidence > 0.6:
                self._advance_level()
            elif recent_success <= 1:
                self._regress_level()

    def _advance_level(self):
        if self.current_level < len(self.levels):
            self.current_level += 1

    def _regress_level(self):
        if self.current_level > 1:
            self.current_level -= 1

    def get_evolution_params(self) -> dict:
        level = self.get_current_level()
        num_numbers = 2 + (level.level - 1) * 2  # 2, 4, 6, 8, 10, 12
        precision = 1 if level.level <= 2 else (2 if level.level <= 4 else 4)
        return {
            "difficulty_level": level.level,
            "difficulty_name": level.name,
            "num_systems": random.randint(*level.num_systems_range),
            "min_generations": level.min_generations,
            "required_confidence": level.required_confidence,
            "entropy_complexity": level.entropy_complexity,
            "allowed_domains": level.allowed_domains,
            "mutation_intensity": level.mutation_intensity,
            "crossover_diversity": level.crossover_diversity,
            "fitness_threshold": level.fitness_threshold,
            "num_numbers": num_numbers,
            "number_precision": precision,
            "target_accuracy": 0.3 + (level.level - 1) * 0.1,
        }

    def get_available_systems(self, all_systems: list[str]) -> list[str]:
        level = self.get_current_level()
        if "all" in level.allowed_domains:
            return all_systems
        available = []
        domain_map = {
            "general": ["iching", "tarot", "runes", "numerology", "gematria"],
            "personal": ["bazi", "ziwei", "astrology_western", "astrology_vedic",
                        "yaegi_kundali", "tarot", "lenormand"],
            "financial": ["numerology", "gematria", "iching", "geomancy"],
            "social": ["iching", "tarot", "numerology", "calendar"],
            "political": ["iching", "numerology", "qimen", "bazi"],
            "natural": ["calendar", "lunar_calendar", "tzolkin", "long_count"],
        }
        for domain in level.allowed_domains:
            if domain in domain_map:
                available.extend(domain_map[domain])
        return list(set(available)) if available else all_systems[:5]

    def get_progress(self) -> dict:
        level = self.get_current_level()
        return {
            "current_level": self.current_level,
            "level_name": level.name,
            "description": level.description,
            "total_questions": self.total_questions,
            "success_rate": self.successful_predictions / max(self.total_questions, 1),
            "next_level_threshold": 4,
            "questions_to_next": max(0, 5 - (self.total_questions % 5)),
        }

    def to_dict(self) -> dict:
        return {
            "current_level": self.current_level,
            "total_questions": self.total_questions,
            "successful_predictions": self.successful_predictions,
            "history": self.history[-20:],
        }

    @classmethod
    def from_dict(cls, d: dict) -> "ProgressiveDifficulty":
        pd = cls()
        pd.current_level = d.get("current_level", 1)
        pd.total_questions = d.get("total_questions", 0)
        pd.successful_predictions = d.get("successful_predictions", 0)
        pd.history = d.get("history", [])
        return pd
