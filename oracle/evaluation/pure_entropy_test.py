"""Pure Entropy Test (f1) - mathematical entropy prediction challenge per design doc section 16.2."""
import secrets
import numpy as np
import hashlib
from dataclasses import dataclass
from typing import Callable
from ..genome.chromosome import Chromosome


@dataclass
class PureEntropyResult:
    """Result of pure entropy test."""
    target_matrix: list[list[int]]
    predicted_matrix: list[list[float]]
    mae: float
    rmse: float
    difficulty_level: int
    curriculum_rows: int
    curriculum_cols: int


class PureEntropyTest:
    """
    Pure Entropy Test - the mathematical oracle challenge.
    
    Per design doc section 16.2:
    - Level 1 (gen 1-50): single digit 0-9
    - Level 2 (gen 51-200): multi-digit sequences in matrix
    - Level 3 (gen 200+): longer sequences, higher dimensions
    """
    
    def __init__(self, config: dict = None):
        config = config or {}
        self.difficulty_level = config.get("difficulty_level", 1)
        self.curriculum_level = config.get("curriculum_level", 1)
        
    def get_curriculum_dimensions(self) -> tuple[int, int]:
        """Get matrix dimensions based on curriculum level (section 16.2.2)."""
        if self.curriculum_level <= 1:
            return 1, 1  # Level 1: single digit
        elif self.curriculum_level <= 2:
            return 3, 4  # Level 2: 3x4 matrix
        else:
            return 5, 5  # Level 3: 5x5 matrix
    
    def generate_secret_matrix(self, rows: int, cols: int) -> list[list[int]]:
        """Generate cryptographically secure random matrix (section 16.2.1)."""
        return [[secrets.randbelow(100) for _ in range(cols)] for _ in range(rows)]
    
    def evaluate_oracle(
        self, 
        chromosome: Chromosome, 
        entropy_packet: dict,
        oracle_predict_fn: Callable
    ) -> PureEntropyResult:
        """
        Evaluate chromosome on pure entropy test.
        
        Args:
            chromosome: The evolved oracle structure
            entropy_packet: Input entropy for this test
            oracle_predict_fn: Function(oracle, rows, cols) -> predicted matrix
        """
        rows, cols = self.get_curriculum_dimensions()
        target = self.generate_secret_matrix(rows, cols)
        
        # Oracle predicts WITHOUT seeing the target matrix
        predicted = oracle_predict_fn(chromosome, entropy_packet, rows, cols)
        
        # Compute metrics
        mae = self._compute_mae(target, predicted)
        rmse = self._compute_rmse(target, predicted)
        
        return PureEntropyResult(
            target_matrix=target,
            predicted_matrix=predicted,
            mae=mae,
            rmse=rmse,
            difficulty_level=self.difficulty_level,
            curriculum_rows=rows,
            curriculum_cols=cols
        )
    
    def _compute_mae(self, target: list[list[int]], predicted: list[list[float]]) -> float:
        """Mean Absolute Error - per design doc f1 formula."""
        errors = []
        for i, row in enumerate(target):
            for j, val in enumerate(row):
                pred = predicted[i][j] if i < len(predicted) and j < len(predicted[i]) else 0.0
                errors.append(abs(val - pred))
        return sum(errors) / len(errors) if errors else 100.0
    
    def _compute_rmse(self, target: list[list[int]], predicted: list[list[float]]) -> float:
        """Root Mean Square Error."""
        errors = []
        for i, row in enumerate(target):
            for j, val in enumerate(row):
                pred = predicted[i][j] if i < len(predicted) and j < len(predicted[i]) else 0.0
                errors.append((val - pred) ** 2)
        return (sum(errors) / len(errors)) ** 0.5 if errors else 100.0
    
    def fitness_from_result(self, result: PureEntropyResult) -> float:
        """
        Convert test result to fitness (0.0 to 1.0).
        Lower MAE = higher fitness.
        """
        # Normalize: perfect prediction = 1.0, random guess ~ 0.0
        # Max possible MAE ~ 50 (range 0-100)
        max_mae = 50.0
        fitness = max(0.0, 1.0 - (result.mae / max_mae))
        return fitness
    
    def advance_curriculum(self, generation: int):
        """Advance curriculum based on generation (section 16.2.2)."""
        if generation <= 50:
            self.curriculum_level = 1
        elif generation <= 200:
            self.curriculum_level = 2
        else:
            self.curriculum_level = 3


def default_oracle_predict(
    chromosome: Chromosome, 
    entropy_packet: dict, 
    rows: int, 
    cols: int
) -> list[list[float]]:
    """
    Default prediction function using chromosome execution.
    The oracle must predict without access to target.
    """
    exec_result = chromosome.execute(entropy_packet)
    fused = exec_result.get("fused_numeric", [])
    
    # Use fused numeric output to generate predictions
    predictions = []
    for i in range(rows):
        row = []
        for j in range(cols):
            idx = (i * cols + j) % max(len(fused), 1)
            base_val = fused[idx] if fused else 0.5
            # Scale to 0-100 range
            pred = (math.sin(base_val * 12.9898 + idx * 78.233) + 1) / 2 * 100
            row.append(pred)
        predictions.append(row)
    
    return predictions


import math