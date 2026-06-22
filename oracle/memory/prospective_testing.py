"""Prospective Testing Framework for controlled future-testing of oracle predictions.

Per design doc section 28: register questions before outcomes are known,
freeze predictions with immutable timestamps, annotate outcomes later.
No historical data is used for training - only prospective testing.
"""
import hashlib
import sqlite3
import time
import json
import logging
from typing import Optional
from .experiment_ledger import ExperimentLedger

logger = logging.getLogger(__name__)


class ProspectiveTestManager:
    """Manages the lifecycle of prospective tests.

    Flow:
    1. register_test: Record question + oracle prediction BEFORE outcome
    2. freeze_test: Lock prediction (immutable from this point)
    3. annotate_outcome: Record actual outcome AFTER time horizon
    4. evaluate: Compute accuracy statistics
    """

    def __init__(self, db_path: str):
        self.ledger = ExperimentLedger(db_path)

    def register_test(
        self,
        question: str,
        oracle_prediction: dict,
        oracle_id: str,
        oracle_version: str,
        oracle_graph_hash: str,
        entropy_signature: str,
        time_horizon: str,
        domain: str = "general",
    ) -> str:
        """Register a new prospective test.

        Args:
            question: The question being asked
            oracle_prediction: The oracle's prediction payload
            oracle_id: ID of the oracle structure
            oracle_version: Version of the oracle
            oracle_graph_hash: Hash of the oracle graph structure
            entropy_signature: Hash signature of the entropy packet
            time_horizon: When outcome will be known (e.g. "1_week", "3_months")
            domain: Domain of the question (e.g. "career", "geopolitical", "market")
        """
        exp_id = self.ledger.register_experiment(
            question_text=question,
            entropy_signature=entropy_signature,
            oracle_id=oracle_id,
            oracle_version=oracle_version,
            oracle_graph_hash=oracle_graph_hash,
            prediction_payload=oracle_prediction,
            time_horizon=time_horizon,
            domain=domain,
        )
        logger.info("Prospective test registered: %s", exp_id)
        return exp_id

    def freeze_test(self, experiment_id: str) -> bool:
        """Freeze a test (prediction becomes immutable)."""
        result = self.ledger.freeze_experiment(experiment_id)
        if result:
            logger.info("Prospective test frozen: %s", experiment_id)
        return result

    def annotate_outcome(
        self,
        experiment_id: str,
        outcome: str,
        actual_result: dict = None,
    ) -> bool:
        """Annotate the actual outcome after time horizon has passed.

        Args:
            experiment_id: The experiment to annotate
            outcome: One of "success", "failure", "partial", "unknown"
            actual_result: Details of what actually happened
        """
        result = self.ledger.annotate_outcome(
            experiment_id, outcome, actual_result
        )
        if result:
            logger.info("Prospective test annotated: %s -> %s", experiment_id, outcome)
        return result

    def get_test(self, experiment_id: str) -> Optional[dict]:
        """Get details of a specific test."""
        return self.ledger.get_experiment(experiment_id)

    def get_pending_tests(self) -> list[dict]:
        """Get tests waiting for outcome annotation."""
        return self.ledger.get_pending_experiments()

    def get_all_tests(self, domain: str = None) -> list[dict]:
        """Get all tests, optionally filtered by domain."""
        return self.ledger.list_experiments(domain=domain)

    def compute_accuracy(self, domain: str = None) -> dict:
        """Compute accuracy statistics."""
        if domain:
            with sqlite3.connect(self.ledger.db_path) as conn:
                cursor = conn.execute(
                    "SELECT outcome, COUNT(*) FROM experiments "
                    "WHERE status = 'evaluated' AND domain = ? GROUP BY outcome",
                    (domain,)
                )
                counts = {row[0]: row[1] for row in cursor.fetchall()}
            total = sum(counts.values())
            successes = counts.get("success", 0)
            return {
                "domain": domain,
                "total_evaluated": total,
                "successes": successes,
                "accuracy": successes / max(total, 1),
                "by_status": counts,
            }
        else:
            return self.ledger.compute_accuracy()

    def verify_integrity(self, experiment_id: str) -> dict:
        """Verify the full integrity of an experiment."""
        return self.ledger.verify_experiment_integrity(experiment_id)

    def get_domain_summary(self) -> dict:
        """Get a summary of tests by domain."""
        with sqlite3.connect(self.ledger.db_path) as conn:
            cursor = conn.execute(
                "SELECT domain, COUNT(*), status, outcome FROM experiments "
                "GROUP BY domain, status, outcome ORDER BY domain"
            )
            summary = {}
            for row in cursor.fetchall():
                domain, count, status, outcome = row
                if domain not in summary:
                    summary[domain] = {"total": 0, "by_status": {}, "by_outcome": {}}
                summary[domain]["total"] += count
                summary[domain]["by_status"][status] = (
                    summary[domain]["by_status"].get(status, 0) + count
                )
                summary[domain]["by_outcome"][outcome] = (
                    summary[domain]["by_outcome"].get(outcome, 0) + count
                )
            return summary
