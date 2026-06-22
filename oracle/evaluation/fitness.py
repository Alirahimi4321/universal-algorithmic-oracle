"""Fitness evaluator - 10-dimension multi-objective fitness per design doc sections 16 & 20."""
import hashlib
import math
import logging
from ..genome.chromosome import Chromosome
from .benchmark import PredictionBenchmark
from .pure_entropy_test import PureEntropyTest, default_oracle_predict
from .historical_blind_test import HistoricalBlindTest, default_oracle_prophesy

logger = logging.getLogger(__name__)


class FitnessEvaluator:
    """Multi-objective fitness evaluator with Pure Entropy Test (f1) and Historical Blind Test (f2)."""

    DIMENSIONS = [
        "structural_coherence", "response_stability", "symbolic_convergence",
        "novelty_score", "complexity_penalty", "tradition_escape",
        "entropy_utilization", "oracle_confidence",
        "pure_entropy_fitness",
        "historical_accuracy_fitness",
    ]

    def __init__(self, config: dict = None):
        config = config or {}
        self.weights = config.get("weights", {})
        if not self.weights:
            default_w = 1.0 / len(self.DIMENSIONS)
            self.weights = {d: default_w for d in self.DIMENSIONS}

        self.pure_entropy_test = PureEntropyTest(config.get("pure_entropy_test", {}))
        self.historical_blind_test = HistoricalBlindTest(
            test_bank=config.get("historical_test_bank"),
            config=config.get("historical_blind_test", {})
        )
        self.benchmark = PredictionBenchmark(config.get("benchmark", {}))

        self.use_pure_entropy = config.get("use_pure_entropy", True)
        self.use_historical_blind = config.get("use_historical_blind", True)
        self.use_legacy_benchmark = config.get("use_legacy_benchmark", False)

    def evaluate(self, chromosome: Chromosome, entropy_packet: dict = None, generation: int = 0) -> dict:
        if not chromosome.genes:
            return {d: 0.0 for d in self.DIMENSIONS} | {"total_fitness": 0.0}

        self.pure_entropy_test.advance_curriculum(generation)

        scores = {}
        scores["structural_coherence"] = self._eval_structural_coherence(chromosome)
        scores["response_stability"] = self._eval_response_stability(chromosome)
        scores["symbolic_convergence"] = self._eval_symbolic_convergence(chromosome)
        scores["novelty_score"] = self._eval_novelty(chromosome)
        scores["complexity_penalty"] = self._eval_complexity_penalty(chromosome)
        scores["tradition_escape"] = self._eval_tradition_escape(chromosome)
        scores["entropy_utilization"] = self._eval_entropy_utilization(chromosome, entropy_packet)
        scores["oracle_confidence"] = self._eval_oracle_confidence(chromosome)

        if self.use_pure_entropy and entropy_packet:
            scores["pure_entropy_fitness"] = self._eval_pure_entropy(chromosome, entropy_packet)
        else:
            scores["pure_entropy_fitness"] = 0.0

        if self.use_historical_blind:
            scores["historical_accuracy_fitness"] = self._eval_historical_blind(chromosome)
        else:
            scores["historical_accuracy_fitness"] = 0.0

        if self.use_legacy_benchmark and entropy_packet:
            scores["legacy_prediction_accuracy"] = self._eval_prediction_accuracy(chromosome, entropy_packet)
        else:
            scores["legacy_prediction_accuracy"] = 0.0

        total = 0.0
        for d in self.DIMENSIONS:
            total += scores.get(d, 0.0) * self.weights.get(d, 1.0 / len(self.DIMENSIONS))

        if self.use_legacy_benchmark:
            total += scores["legacy_prediction_accuracy"] * self.weights.get("legacy_prediction_accuracy", 0.0)

        scores["total_fitness"] = total
        return scores

    def _eval_pure_entropy(self, chromosome: Chromosome, entropy_packet: dict) -> float:
        try:
            result = self.pure_entropy_test.evaluate_oracle(
                chromosome, entropy_packet, default_oracle_predict
            )
            return self.pure_entropy_test.fitness_from_result(result)
        except Exception as e:
            logger.warning("Pure entropy evaluation failed: %s", e)
            return 0.0

    def _eval_historical_blind(self, chromosome: Chromosome) -> float:
        try:
            results = self.historical_blind_test.evaluate_oracle(
                chromosome, default_oracle_prophesy
            )
            return self.historical_blind_test.fitness_from_results(results)
        except Exception as e:
            logger.warning("Historical blind evaluation failed: %s", e)
            return 0.0

    def _eval_prediction_accuracy(self, chrom: Chromosome, entropy_packet: dict) -> float:
        target_numbers = self.benchmark.generate_target_numbers()
        predictions = self._extract_predictions(chrom, entropy_packet, len(target_numbers))
        result = self.benchmark.validate_prediction(predictions, target_numbers)
        return result.accuracy

    def _extract_predictions(self, chrom: Chromosome, entropy_packet: dict, n: int) -> list[float]:
        try:
            exec_result = chrom.execute(entropy_packet)
            fused_numeric = exec_result.get("fused_numeric", [])
        except Exception as e:
            logger.warning("Chromosome execution failed for predictions: %s", e)
            fused_numeric = []

        predictions = []
        for i in range(n):
            if i < len(fused_numeric):
                val = fused_numeric[i]
                normalized = max(0.0, min(1.0, (math.tanh(val) + 1) / 2))
                predictions.append(normalized * self.benchmark.num_range[1])
            else:
                val = (entropy_packet.get("seed", 42) * (i + 1) * 2654435761) % 10000
                predictions.append((val / 10000.0) * self.benchmark.num_range[1])

        precision = self.benchmark.get_number_precision()
        return [round(p, precision) for p in predictions]

    def _eval_structural_coherence(self, chrom: Chromosome) -> float:
        n_genes = len(chrom.genes)
        n_edges = len(chrom.edges)
        if n_genes == 0:
            return 0.0
        max_edges = n_genes * (n_genes - 1)
        edge_density = n_edges / max_edges if max_edges > 0 else 0
        weights = [g.weight for g in chrom.gene_list]
        weight_balance = 1.0 - (max(weights) - min(weights)) if len(weights) > 1 else 1.0
        has_output = 1.0 if chrom.output_mapping.get("output") else 0.0
        return min(1.0, edge_density * 0.3 + weight_balance * 0.3 + min(n_genes / 5, 1.0) * 0.2 + has_output * 0.2)

    def _eval_response_stability(self, chrom: Chromosome) -> float:
        if not chrom.genes:
            return 0.0
        unique_backends = len(set(g.backend for g in chrom.gene_list))
        total = len(chrom.genes)
        weight_std = self._weight_std(chrom)
        stability_bonus = max(0.0, 1.0 - weight_std)
        return min(1.0, unique_backends / max(total, 1) * 0.4 + stability_bonus * 0.3 + 0.3)

    def _eval_symbolic_convergence(self, chrom: Chromosome) -> float:
        if not chrom.genes:
            return 0.0
        system_ids = [g.system_id for g in chrom.gene_list]
        unique_systems = len(set(system_ids))
        total = len(system_ids)
        if total == 0:
            return 0.0
        dominant_count = max(system_ids.count(s) for s in set(system_ids))
        dominance = dominant_count / total
        return min(1.0, unique_systems / max(total, 1) * 0.5 + dominance * 0.3 + 0.2)

    def _eval_novelty(self, chrom: Chromosome) -> float:
        gene_types = [g.gene_type for g in chrom.gene_list]
        unique_types = len(set(gene_types))
        type_diversity = unique_types / max(len(gene_types), 1)
        has_anti_traditional = any(g.params.get("anti_traditional") for g in chrom.gene_list)
        system_ids = [g.system_id for g in chrom.gene_list]
        cross_civilization = len(set(system_ids)) > 1
        novelty = type_diversity * 0.4 + (0.3 if has_anti_traditional else 0.0) + (0.3 if cross_civilization else 0.0)
        return min(1.0, novelty)

    def _eval_complexity_penalty(self, chrom: Chromosome) -> float:
        n_genes = len(chrom.genes)
        depth = chrom.depth
        n_edges = len(chrom.edges)
        complexity = n_genes * 0.3 + depth * 0.3 + n_edges * 0.4
        return max(0.0, 1.0 - complexity / 20)

    def _eval_tradition_escape(self, chrom: Chromosome) -> float:
        if not chrom.genes:
            return 0.0
        anti_traditional_count = sum(1 for g in chrom.gene_list if g.params.get("anti_traditional"))
        system_ids = [g.system_id for g in chrom.gene_list]
        cross_civilization = len(set(system_ids)) > 1
        has_transform = any(g.gene_type == "transform" for g in chrom.gene_list)
        score = anti_traditional_count / len(chrom.genes) * 0.3
        score += 0.3 if cross_civilization else 0.0
        score += 0.3 if has_transform else 0.0
        score += 0.1 if len(chrom.genes) > 3 else 0.0
        return min(1.0, score)

    def _eval_entropy_utilization(self, chrom: Chromosome, entropy_packet: dict = None) -> float:
        if not entropy_packet:
            return 0.0
        numeric_vector = entropy_packet.get("numeric_vector", [])
        bit_stream = entropy_packet.get("bit_stream", [])
        entropy_bits = len(numeric_vector) + len(bit_stream)
        n_genes = len(chrom.genes)
        if n_genes == 0:
            return 0.0
        utilization = min(1.0, entropy_bits / (n_genes * 10))
        return utilization

    def _eval_oracle_confidence(self, chrom: Chromosome) -> float:
        if not chrom.genes:
            return 0.0
        weights = [g.weight for g in chrom.gene_list]
        avg_weight = sum(weights) / len(weights) if weights else 0.0
        weight_variance = sum((w - avg_weight) ** 2 for w in weights) / len(weights) if weights else 0.0
        consistency = 1.0 - min(weight_variance, 1.0)
        n_genes_factor = min(len(chrom.genes) / 5, 1.0)
        return consistency * 0.5 + min(avg_weight, 1.0) * 0.3 + n_genes_factor * 0.2

    def _weight_std(self, chrom: Chromosome) -> float:
        weights = [g.weight for g in chrom.gene_list]
        if len(weights) < 2:
            return 0.0
        avg = sum(weights) / len(weights)
        variance = sum((w - avg) ** 2 for w in weights) / len(weights)
        return math.sqrt(variance)

    def evaluate_tree(self, genome, entropy_packet: dict = None, generation: int = 0) -> dict:
        from ..genome.tree_genome import TreeGenome

        if not isinstance(genome, TreeGenome) or genome.root is None:
            return {d: 0.0 for d in self.DIMENSIONS} | {"total_fitness": 0.0}

        scores = {}

        try:
            exec_result = genome.execute(entropy_packet) if entropy_packet else {}
            fused_numeric = exec_result.get("fused_numeric", [])
            oracle_conf = exec_result.get("oracle_confidence", 0.0)
        except Exception as e:
            logger.warning("TreeGenome execution failed: %s", e)
            fused_numeric = []
            oracle_conf = 0.0

        scores["structural_coherence"] = self._eval_tree_structural(genome)
        scores["response_stability"] = self._eval_tree_stability(genome)
        scores["symbolic_convergence"] = self._eval_tree_convergence(genome)
        scores["novelty_score"] = self._eval_tree_novelty(genome)
        scores["complexity_penalty"] = self._eval_tree_complexity(genome)
        scores["tradition_escape"] = self._eval_tree_tradition_escape(genome)
        scores["entropy_utilization"] = self._eval_tree_entropy_utilization(genome, entropy_packet)
        scores["oracle_confidence"] = min(1.0, max(0.0, oracle_conf))

        if self.use_pure_entropy and entropy_packet:
            scores["pure_entropy_fitness"] = self._eval_pure_entropy_tree(genome, entropy_packet)
        else:
            scores["pure_entropy_fitness"] = 0.0

        if self.use_historical_blind:
            scores["historical_accuracy_fitness"] = self._eval_historical_blind_tree(genome)
        else:
            scores["historical_accuracy_fitness"] = 0.0

        total = sum(scores.get(d, 0.0) * self.weights.get(d, 1.0 / len(self.DIMENSIONS)) for d in self.DIMENSIONS)
        scores["total_fitness"] = total
        return scores

    def _eval_tree_structural(self, genome) -> float:
        nodes = genome.get_all_nodes()
        if not nodes:
            return 0.0
        system_nodes = [n for n in nodes if n.node_type == "system"]
        fusion_nodes = [n for n in nodes if n.node_type == "fusion"]
        depth_score = 1.0 - min(genome.depth / 6, 1.0)
        balance_score = min(len(system_nodes) / max(len(fusion_nodes) + 1, 1), 3.0) / 3.0
        type_diversity = len(set(n.node_type for n in nodes)) / 4.0
        return min(1.0, depth_score * 0.3 + balance_score * 0.3 + type_diversity * 0.4)

    def _eval_tree_stability(self, genome) -> float:
        system_nodes = genome.get_all_system_nodes()
        if not system_nodes:
            return 0.0
        unique_systems = len(set(n.system_id for n in system_nodes))
        total = len(system_nodes)
        return min(1.0, unique_systems / max(total, 1) * 0.5 + 0.5)

    def _eval_tree_convergence(self, genome) -> float:
        system_nodes = genome.get_all_system_nodes()
        if not system_nodes:
            return 0.0
        system_ids = [n.system_id for n in system_nodes]
        unique = len(set(system_ids))
        return min(1.0, unique / max(len(system_ids), 1) * 0.6 + 0.4)

    def _eval_tree_novelty(self, genome) -> float:
        all_nodes = genome.get_all_nodes()
        if not all_nodes:
            return 0.0
        unique_ops = len(set(n.operation for n in all_nodes if n.operation))
        unique_systems = len(set(n.system_id for n in all_nodes if n.system_id))
        has_transform = any(n.node_type == "transform" for n in all_nodes)
        has_xor = any(n.operation == "xor_fusion" for n in all_nodes)
        novelty = (unique_ops * 0.2 + unique_systems * 0.2 +
                   (0.3 if has_transform else 0.0) + (0.3 if has_xor else 0.0))
        return min(1.0, novelty)

    def _eval_tree_complexity(self, genome) -> float:
        n_nodes = genome.size
        depth = genome.depth
        complexity = n_nodes * 0.2 + depth * 0.3
        return max(0.0, 1.0 - complexity / 15)

    def _eval_tree_tradition_escape(self, genome) -> float:
        system_nodes = genome.get_all_system_nodes()
        all_nodes = genome.get_all_nodes()
        if not system_nodes:
            return 0.0
        unique_systems = set(n.system_id for n in system_nodes)
        cross_civilization = len(unique_systems) > 1
        has_transform = any(n.node_type == "transform" for n in all_nodes)
        has_xor = any(n.operation == "xor_fusion" for n in all_nodes)
        score = 0.0
        score += 0.3 if cross_civilization else 0.0
        score += 0.3 if has_transform else 0.0
        score += 0.4 if has_xor else 0.0
        return min(1.0, score)

    def _eval_tree_entropy_utilization(self, genome, entropy_packet: dict = None) -> float:
        if not entropy_packet:
            return 0.0
        numeric_vector = entropy_packet.get("numeric_vector", [])
        bit_stream = entropy_packet.get("bit_stream", [])
        entropy_bits = len(numeric_vector) + len(bit_stream)
        n_system = len(genome.get_all_system_nodes())
        if n_system == 0:
            return 0.0
        return min(1.0, entropy_bits / (n_system * 10))

    def _eval_pure_entropy_tree(self, genome, entropy_packet: dict) -> float:
        try:
            def tree_predict(ep, chrom):
                result = genome.execute(ep)
                fused = result.get("fused_numeric", [])
                return [v % 100 for v in fused] if fused else [0]

            result = self.pure_entropy_test.evaluate_oracle(
                genome, entropy_packet, tree_predict
            )
            return self.pure_entropy_test.fitness_from_result(result)
        except Exception as e:
            logger.warning("Tree pure entropy evaluation failed: %s", e)
            return 0.0

    def _eval_historical_blind_tree(self, genome) -> float:
        try:
            def tree_prophesy(chrom):
                try:
                    ep = {"text": "test", "sha_stream": "0", "numeric_vector": [0.5]}
                    result = genome.execute(ep)
                    fused = result.get("fused_numeric", [])
                    return fused[0] if fused else 0.5
                except Exception as e:
                    logger.warning("Tree prophesy failed: %s", e)
                    return 0.5

            results = self.historical_blind_test.evaluate_oracle(
                genome, tree_prophesy
            )
            return self.historical_blind_test.fitness_from_results(results)
        except Exception as e:
            logger.warning("Tree historical blind evaluation failed: %s", e)
            return 0.0
