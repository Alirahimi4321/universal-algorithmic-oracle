"""Neural network based fitness evaluation using PyTorch."""
import logging
import math
import random
import time
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

try:
    import torch
    import torch.nn as nn
    import torch.optim as optim
    HAS_TORCH = True
except ImportError:
    nn = None
    optim = None
    HAS_TORCH = False
    logger.info("torch not available, neural evaluator will use random fallback")


if HAS_TORCH:
    class _FitnessNet(nn.Module):
        """Simple feedforward network for fitness prediction."""

        def __init__(self, input_dim: int, hidden_dim: int = 64, output_dim: int = 1):
            super().__init__()
            self.net = nn.Sequential(
                nn.Linear(input_dim, hidden_dim),
                nn.ReLU(),
                nn.Linear(hidden_dim, hidden_dim // 2),
                nn.ReLU(),
                nn.Linear(hidden_dim // 2, output_dim),
                nn.Sigmoid(),
            )

        def forward(self, x):
            return self.net(x)
else:
    _FitnessNet = None


class NeuralEvaluator:
    """Neural network based fitness evaluator.

    Trains a small feedforward network on chromosome-to-fitness examples,
    then predicts fitness for new chromosomes. Falls back to random scoring
    if torch is unavailable.
    """

    DEFAULT_INPUT_DIM = 32
    DEFAULT_HIDDEN_DIM = 64
    LEARNING_RATE = 0.001
    EPOCHS_PER_BATCH = 10
    MIN_EXAMPLES = 5

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        config = config or {}
        self.input_dim = config.get("input_dim", self.DEFAULT_INPUT_DIM)
        self.hidden_dim = config.get("hidden_dim", self.DEFAULT_HIDDEN_DIM)
        self.lr = config.get("learning_rate", self.LEARNING_RATE)
        self.epochs_per_batch = config.get("epochs_per_batch", self.EPOCHS_PER_BATCH)
        self.min_examples = config.get("min_examples", self.MIN_EXAMPLES)

        self._model = None
        self._optimizer = None
        self._training_data: List[Dict[str, Any]] = []
        self._trained = False
        self._train_count = 0
        self._predict_count = 0

        if HAS_TORCH:
            try:
                self._model = _FitnessNet(self.input_dim, self.hidden_dim)
                self._optimizer = optim.Adam(self._model.parameters(), lr=self.lr)
                logger.info("NeuralEvaluator initialized with input_dim=%d", self.input_dim)
            except Exception as e:
                logger.error("Failed to initialize neural network: %s", e)
                self._model = None

    def _chromosome_to_tensor(self, chromosome) -> Optional[Any]:
        """Convert a chromosome to a fixed-size feature tensor."""
        if not HAS_TORCH:
            return None

        features = []

        genes = chromosome.gene_list if hasattr(chromosome, "gene_list") else []
        n_genes = len(genes)
        features.append(n_genes / 10.0)

        if hasattr(chromosome, "genes") and isinstance(chromosome.genes, dict):
            system_ids = [g.system_id for g in chromosome.genes.values()]
        elif genes:
            system_ids = [g.system_id for g in genes]
        else:
            system_ids = []

        unique_systems = len(set(system_ids))
        features.append(unique_systems / 5.0)
        features.append(1.0 if unique_systems > 1 else 0.0)

        if hasattr(chromosome, "edges"):
            features.append(len(chromosome.edges) / 20.0)
        else:
            features.append(0.0)

        depth = getattr(chromosome, "depth", 0)
        features.append(depth / 6.0)

        if genes:
            weights = [g.weight for g in genes]
            avg_w = sum(weights) / len(weights) if weights else 0.0
            std_w = (
                math.sqrt(sum((w - avg_w) ** 2 for w in weights) / len(weights))
                if len(weights) > 1
                else 0.0
            )
            features.append(avg_w)
            features.append(std_w)
            features.append(min(weights) if weights else 0.0)
            features.append(max(weights) if weights else 0.0)
        else:
            features.extend([0.0, 0.0, 0.0, 0.0])

        gene_types = [g.gene_type for g in genes] if genes else []
        unique_types = len(set(gene_types))
        features.append(unique_types / 4.0)

        has_transform = 1.0 if any(t == "transform" for t in gene_types) else 0.0
        features.append(has_transform)

        backends = [g.backend for g in genes] if genes else []
        unique_backends = len(set(backends))
        features.append(unique_backends / 3.0)

        fitness = getattr(chromosome, "fitness", {})
        if isinstance(fitness, dict):
            for key in [
                "structural_coherence", "response_stability",
                "symbolic_convergence", "novelty_score",
            ]:
                features.append(fitness.get(key, 0.0))
        else:
            features.extend([0.0, 0.0, 0.0, 0.0])

        system_hash = hash(tuple(sorted(system_ids))) if system_ids else 0
        features.append((system_hash % 1000) / 1000.0)

        gene_hash = hash(tuple(sorted(gene_types))) if gene_types else 0
        features.append((gene_hash % 1000) / 1000.0)

        while len(features) < self.input_dim:
            features.append(0.0)

        features = features[: self.input_dim]

        tensor = torch.tensor(features, dtype=torch.float32)
        return tensor.unsqueeze(0)

    def train(self, examples: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Train the neural network on chromosome-fitness examples.

        Parameters
        ----------
        examples : list of dict
            Each dict has 'chromosome' and 'fitness' keys.
            'fitness' should be a float or a dict with 'total_fitness'.

        Returns
        -------
        dict
            Training results with loss and status.
        """
        if not HAS_TORCH or self._model is None:
            return {"status": "skipped", "reason": "torch unavailable"}

        self._training_data.extend(examples)

        valid = []
        for ex in self._training_data:
            chrom = ex.get("chromosome")
            fitness = ex.get("fitness")
            if chrom is None or fitness is None:
                continue
            target = fitness.get("total_fitness", 0.0) if isinstance(fitness, dict) else float(fitness)
            tensor = self._chromosome_to_tensor(chrom)
            if tensor is not None:
                valid.append((tensor, target))

        if len(valid) < self.min_examples:
            return {
                "status": "insufficient_data",
                "collected": len(valid),
                "required": self.min_examples,
            }

        inputs = torch.cat([v[0] for v in valid])
        targets = torch.tensor([[v[1]] for v in valid], dtype=torch.float32)

        self._model.train()
        total_loss = 0.0
        for epoch in range(self.epochs_per_batch):
            self._optimizer.zero_grad()
            predictions = self._model(inputs)
            loss = nn.functional.mse_loss(predictions, targets)
            loss.backward()
            self._optimizer.step()
            total_loss += loss.item()

        self._trained = True
        self._train_count += len(valid)
        avg_loss = total_loss / self.epochs_per_batch

        logger.info(
            "NeuralEvaluator trained: %d examples, avg_loss=%.6f",
            len(valid), avg_loss,
        )
        return {
            "status": "trained",
            "examples": len(valid),
            "avg_loss": avg_loss,
            "total_trained": self._train_count,
        }

    def predict(self, chromosome) -> float:
        """Predict fitness score for a chromosome.

        Parameters
        ----------
        chromosome
            Chromosome/genome object.

        Returns
        -------
        float
            Predicted fitness score in [0, 1].
        """
        self._predict_count += 1

        if not HAS_TORCH or self._model is None:
            return self._random_predict(chromosome)

        if not self._trained:
            return self._random_predict(chromosome)

        tensor = self._chromosome_to_tensor(chromosome)
        if tensor is None:
            return self._random_predict(chromosome)

        try:
            self._model.eval()
            with torch.no_grad():
                prediction = self._model(tensor)
            score = float(prediction.item())
            return max(0.0, min(1.0, score))
        except Exception as e:
            logger.warning("Neural prediction failed: %s, using random fallback", e)
            return self._random_predict(chromosome)

    @staticmethod
    def _random_predict(chromosome) -> float:
        """Deterministic random prediction based on chromosome features."""
        genes = chromosome.gene_list if hasattr(chromosome, "gene_list") else []
        n_genes = len(genes)

        h = hash(str(getattr(chromosome, "chromosome_id", "")) + str(n_genes))
        base = (h % 10000) / 10000.0

        weight_bonus = 0.0
        if genes:
            weights = [g.weight for g in genes]
            avg_w = sum(weights) / len(weights)
            weight_bonus = avg_w * 0.2

        return max(0.0, min(1.0, base * 0.7 + weight_bonus + 0.15))

    def get_stats(self) -> Dict[str, Any]:
        """Return evaluator statistics."""
        return {
            "torch_available": HAS_TORCH,
            "model_initialized": self._model is not None,
            "trained": self._trained,
            "training_examples": len(self._training_data),
            "total_trained": self._train_count,
            "total_predicted": self._predict_count,
            "input_dim": self.input_dim,
            "hidden_dim": self.hidden_dim,
        }

    def save_model(self, path: str) -> bool:
        """Save model weights to disk."""
        if not HAS_TORCH or self._model is None:
            return False
        try:
            import os
            os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
            torch.save(self._model.state_dict(), path)
            logger.info("Model saved to %s", path)
            return True
        except Exception as e:
            logger.error("Failed to save model: %s", e)
            return False

    def load_model(self, path: str) -> bool:
        """Load model weights from disk."""
        if not HAS_TORCH or self._model is None:
            return False
        try:
            try:
                state_dict = torch.load(path, map_location="cpu", weights_only=True)
            except TypeError:
                state_dict = torch.load(path, map_location="cpu")
            self._model.load_state_dict(state_dict)
            self._trained = True
            logger.info("Model loaded from %s", path)
            return True
        except Exception as e:
            logger.error("Failed to load model: %s", e)
            return False
