"""External Trials system for real-world prospective testing.

Per design doc section 28: controlled prospective testing with outcome tracking.
"""
import json
import time
import hashlib
import logging
from typing import Optional
from ..memory.experiment_ledger import ExperimentLedger

logger = logging.getLogger(__name__)


class ExternalTrialsManager:
    """Manages external prospective trials for oracle validation.

    Lifecycle:
    1. Register trial with question + prediction
    2. Freeze trial (prediction is immutable)
    3. Wait for outcome
    4. Annotate outcome
    5. Compute accuracy across trials
    """

    def __init__(self, db_path: str):
        self.ledger = ExperimentLedger(db_path)

    def register_trial(
        self,
        question: str,
        prediction: dict,
        oracle_id: str,
        oracle_version: str,
        oracle_graph_hash: str,
        entropy_signature: str,
        time_horizon: str,
        domain: str = "general",
        difficulty: str = "medium",
        binary_question: bool = True,
    ) -> str:
        """Register a new external trial BEFORE outcome is known.

        Args:
            question: The prediction question
            prediction: Oracle's prediction
            oracle_id: Oracle structure ID
            oracle_version: Oracle version string
            oracle_graph_hash: Hash of oracle graph
            entropy_signature: Entropy packet hash
            time_horizon: When outcome will be known
            domain: Question domain
            difficulty: Trial difficulty
            binary_question: Whether outcome is binary (yes/no)
        """
        enriched_prediction = {
            "prediction": prediction,
            "binary_question": binary_question,
            "difficulty": difficulty,
            "oracle_id": oracle_id,
        }

        exp_id = self.ledger.register_experiment(
            question_text=question,
            entropy_signature=entropy_signature,
            oracle_id=oracle_id,
            oracle_version=oracle_version,
            oracle_graph_hash=oracle_graph_hash,
            prediction_payload=enriched_prediction,
            time_horizon=time_horizon,
            domain=domain,
        )

        logger.info("External trial registered: %s", exp_id)
        return exp_id

    def freeze_trial(self, trial_id: str) -> bool:
        """Freeze trial - prediction becomes immutable."""
        result = self.ledger.freeze_experiment(trial_id)
        if result:
            logger.info("External trial frozen: %s", trial_id)
        return result

    def annotate_outcome(
        self,
        trial_id: str,
        outcome: str,
        actual_result: dict = None,
        confidence_score: float = None,
    ) -> bool:
        """Annotate the actual outcome.

        Args:
            trial_id: Trial to annotate
            outcome: "success", "failure", "partial", "unknown"
            actual_result: What actually happened
            confidence_score: How confident we are in the outcome
        """
        details = {
            "actual_result": actual_result or {},
            "confidence_score": confidence_score,
            "annotation_timestamp": time.time(),
        }

        result = self.ledger.annotate_outcome(trial_id, outcome, details)
        if result:
            logger.info("External trial annotated: %s -> %s", trial_id, outcome)
        return result

    def get_trial(self, trial_id: str) -> Optional[dict]:
        """Get trial details."""
        return self.ledger.get_experiment(trial_id)

    def get_pending_trials(self) -> list[dict]:
        """Get trials waiting for outcome annotation."""
        return self.ledger.get_pending_experiments()

    def get_completed_trials(self, domain: str = None) -> list[dict]:
        """Get completed trials."""
        return self.ledger.list_experiments(status="evaluated", domain=domain)

    def compute_domain_accuracy(self, domain: str = None) -> dict:
        """Compute accuracy by domain."""
        if domain:
            with __import__('sqlite3').connect(self.ledger.db_path) as conn:
                cursor = conn.execute(
                    "SELECT outcome, COUNT(*) FROM experiments "
                    "WHERE status = 'evaluated' AND domain = ? GROUP BY outcome",
                    (domain,)
                )
                counts = {row[0]: row[1] for row in cursor.fetchall()}
        else:
            return self.ledger.compute_accuracy()

        total = sum(counts.values())
        successes = counts.get("success", 0)
        return {
            "domain": domain,
            "total_evaluated": total,
            "successes": successes,
            "accuracy": successes / max(total, 1),
            "by_outcome": counts,
        }

    def compute_overall_accuracy(self) -> dict:
        """Compute overall accuracy across all domains."""
        return self.ledger.compute_accuracy()

    def get_trial_summary(self) -> dict:
        """Get a comprehensive summary of all trials."""
        all_trials = self.ledger.list_experiments()
        by_domain = {}
        by_status = {"registered": 0, "frozen": 0, "evaluated": 0}
        by_outcome = {"pending": 0, "success": 0, "failure": 0, "partial": 0, "unknown": 0}

        for trial in all_trials:
            domain = trial.get("domain", "general")
            status = trial.get("status", "unknown")
            outcome = trial.get("outcome", "pending")

            by_domain[domain] = by_domain.get(domain, 0) + 1
            by_status[status] = by_status.get(status, 0) + 1
            by_outcome[outcome] = by_outcome.get(outcome, 0) + 1

        evaluated = by_status.get("evaluated", 0)
        successes = by_outcome.get("success", 0)

        return {
            "total_trials": len(all_trials),
            "by_domain": by_domain,
            "by_status": by_status,
            "by_outcome": by_outcome,
            "accuracy": successes / max(evaluated, 1),
            "evaluation_rate": evaluated / max(len(all_trials), 1),
        }

    def verify_trial_integrity(self, trial_id: str) -> dict:
        """Verify the full integrity of a trial."""
        return self.ledger.verify_experiment_integrity(trial_id)
