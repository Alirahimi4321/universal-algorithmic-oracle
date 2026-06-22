"""Enhanced Experiment Ledger with Merkle-style hash chain for tamper evidence.

Per design doc sections 28.1-28.3: append-only log, hash chain, immutable timestamps,
prospective testing lifecycle (register -> freeze -> evaluate).
"""
import sqlite3
import json
import time
import hashlib
import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)


class ImmutableLog:
    """Merkle-style hash chain for tamper-evident experiment logging."""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS immutable_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    experiment_id TEXT NOT NULL,
                    action TEXT NOT NULL,
                    timestamp REAL NOT NULL,
                    entry_data TEXT NOT NULL,
                    entry_hash TEXT NOT NULL,
                    prev_hash TEXT NOT NULL,
                    chain_length INTEGER NOT NULL,
                    merkle_root TEXT
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_log_experiment
                ON immutable_log(experiment_id)
            """)
            conn.commit()

    def append(self, experiment_id: str, action: str, data: dict) -> dict:
        """Append an entry to the immutable log with hash chaining."""
        entry = {
            "experiment_id": experiment_id,
            "action": action,
            "data": data,
            "timestamp": time.time(),
        }

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT entry_hash, chain_length FROM immutable_log "
                "WHERE experiment_id = ? ORDER BY id DESC LIMIT 1",
                (experiment_id,)
            )
            prev_row = cursor.fetchone()
            prev_hash = prev_row[0] if prev_row else "GENESIS"
            chain_length = (prev_row[1] + 1) if prev_row else 0

            entry_str = json.dumps(entry, sort_keys=True) + prev_hash
            entry_hash = hashlib.sha256(entry_str.encode()).hexdigest()

            conn.execute(
                "INSERT INTO immutable_log "
                "(experiment_id, action, timestamp, entry_data, entry_hash, prev_hash, chain_length) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (experiment_id, action, time.time(), json.dumps(entry),
                 entry_hash, prev_hash, chain_length)
            )
            conn.commit()

        return {"hash": entry_hash, "chain_length": chain_length}

    def verify_chain(self, experiment_id: str) -> dict:
        """Verify the hash chain integrity for an experiment."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT entry_data, entry_hash, prev_hash, chain_length "
                "FROM immutable_log WHERE experiment_id = ? ORDER BY id",
                (experiment_id,)
            )
            rows = cursor.fetchall()

        if not rows:
            return {"valid": True, "chain_length": 0, "entries": 0}

        for i, (entry_data, entry_hash, prev_hash, chain_length) in enumerate(rows):
            if i == 0:
                if prev_hash != "GENESIS":
                    return {"valid": False, "error": "First entry missing GENESIS", "at_index": i}
                if chain_length != 0:
                    return {"valid": False, "error": "First entry chain_length != 0", "at_index": i}
            else:
                if prev_hash != rows[i - 1][1]:
                    return {"valid": False, "error": "Chain broken", "at_index": i}

            entry = json.loads(entry_data)
            entry_str = json.dumps(entry, sort_keys=True) + prev_hash
            expected_hash = hashlib.sha256(entry_str.encode()).hexdigest()
            if entry_hash != expected_hash:
                return {"valid": False, "error": "Hash mismatch", "at_index": i}

        return {"valid": True, "chain_length": len(rows), "entries": len(rows)}

    def get_entries(self, experiment_id: str) -> list[dict]:
        """Get all log entries for an experiment."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT entry_data, entry_hash, chain_length "
                "FROM immutable_log WHERE experiment_id = ? ORDER BY id",
                (experiment_id,)
            )
            return [
                {"data": json.loads(row[0]), "hash": row[1], "chain_position": row[2]}
                for row in cursor.fetchall()
            ]


class ExperimentLedger:
    """Tracks experiments with proper lifecycle: register -> freeze -> evaluate.

    Per design doc section 28: experiments are registered before outcomes are known,
    outputs are frozen with hash chains, and outcomes are annotated later.
    """

    def __init__(self, db_path: str, backend: str = "sqlite"):
        """Initialize ledger.

        Args:
            db_path: Path for SQLite DB (used when backend='sqlite')
            backend: 'sqlite' for direct sqlite3, 'sqlalchemy' for ORM backend
        """
        self.db_path = db_path
        self.backend_type = backend
        self.log = ImmutableLog(db_path)

        self._use_orm = False
        self._storage = None
        if backend == "sqlalchemy":
            try:
                from oracle.storage.sqlalchemy_backend import StorageBackend
                url = f"sqlite:///{db_path}"
                self._storage = StorageBackend(url)
                self._use_orm = True
                logger.info("ExperimentLedger using SQLAlchemy backend")
            except Exception as e:
                logger.warning("Falling back to sqlite3: %s", e)

        if not self._use_orm:
            self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS experiments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    experiment_id TEXT UNIQUE NOT NULL,
                    question_text TEXT NOT NULL,
                    entropy_signature TEXT,
                    oracle_id TEXT NOT NULL,
                    oracle_version TEXT NOT NULL,
                    oracle_graph_hash TEXT NOT NULL,
                    prediction_payload TEXT NOT NULL,
                    prediction_hash TEXT NOT NULL,
                    timestamp_created REAL NOT NULL,
                    time_horizon TEXT NOT NULL,
                    domain TEXT DEFAULT 'general',
                    status TEXT DEFAULT 'registered',
                    outcome TEXT DEFAULT 'pending',
                    outcome_details TEXT,
                    outcome_timestamp REAL,
                    content_hash TEXT NOT NULL
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_exp_status ON experiments(status)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_exp_outcome ON experiments(outcome)
            """)
            conn.commit()

    def register_experiment(
        self,
        question_text: str,
        entropy_signature: str,
        oracle_id: str,
        oracle_version: str,
        oracle_graph_hash: str,
        prediction_payload: dict,
        time_horizon: str,
        domain: str = "general",
    ) -> str:
        """Register a new experiment BEFORE the outcome is known."""
        exp_id = (
            f"EXP_{int(time.time() * 1000)}_"
            f"{hashlib.sha256(question_text.encode()).hexdigest()[:8]}"
        )

        content = json.dumps({
            "question": question_text,
            "prediction": prediction_payload,
            "oracle_id": oracle_id,
            "oracle_version": oracle_version,
            "time_horizon": time_horizon,
            "domain": domain,
        }, sort_keys=True)
        content_hash = hashlib.sha256(content.encode()).hexdigest()

        prediction_hash = hashlib.sha256(
            json.dumps(prediction_payload, sort_keys=True).encode()
        ).hexdigest()

        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO experiments
                (experiment_id, question_text, entropy_signature, oracle_id,
                 oracle_version, oracle_graph_hash, prediction_payload, prediction_hash,
                 timestamp_created, time_horizon, domain, status, content_hash)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'registered', ?)
            """, (
                exp_id, question_text, entropy_signature, oracle_id,
                oracle_version, oracle_graph_hash, json.dumps(prediction_payload),
                prediction_hash, time.time(), time_horizon, domain, content_hash,
            ))
            conn.commit()

        self.log.append(exp_id, "register", {
            "question_hash": content_hash,
            "prediction_hash": prediction_hash,
            "oracle_id": oracle_id,
            "oracle_version": oracle_version,
            "time_horizon": time_horizon,
        })

        logger.info("Registered experiment %s for: %s", exp_id, question_text[:50])
        return exp_id

    def freeze_experiment(self, experiment_id: str) -> bool:
        """Mark experiment as frozen (output is immutable from this point)."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT status FROM experiments WHERE experiment_id = ?",
                (experiment_id,)
            )
            row = cursor.fetchone()
            if not row or row[0] != "registered":
                return False

            conn.execute(
                "UPDATE experiments SET status = 'frozen' WHERE experiment_id = ?",
                (experiment_id,)
            )
            conn.commit()

        self.log.append(experiment_id, "freeze", {"status": "frozen"})
        return True

    def annotate_outcome(
        self,
        experiment_id: str,
        outcome: str,
        outcome_details: dict = None,
    ) -> bool:
        """Annotate experiment with its actual outcome AFTER the time horizon."""
        valid_outcomes = ("success", "failure", "partial", "unknown")
        if outcome not in valid_outcomes:
            logger.warning("Invalid outcome '%s', must be one of %s", outcome, valid_outcomes)
            return False

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT status FROM experiments WHERE experiment_id = ?",
                (experiment_id,)
            )
            row = cursor.fetchone()
            if not row:
                return False

            conn.execute("""
                UPDATE experiments
                SET outcome = ?, outcome_details = ?, outcome_timestamp = ?,
                    status = 'evaluated'
                WHERE experiment_id = ?
            """, (outcome, json.dumps(outcome_details or {}), time.time(), experiment_id))
            conn.commit()

        self.log.append(experiment_id, "outcome", {
            "outcome": outcome,
            "details": outcome_details or {},
        })

        logger.info("Annotated outcome '%s' for experiment %s", outcome, experiment_id)
        return True

    def get_experiment(self, experiment_id: str) -> Optional[dict]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """SELECT experiment_id, question_text, entropy_signature,
                   oracle_id, oracle_version, oracle_graph_hash, prediction_payload,
                   prediction_hash, timestamp_created, time_horizon, domain,
                   status, outcome, outcome_details, outcome_timestamp, content_hash
                   FROM experiments WHERE experiment_id = ?""",
                (experiment_id,)
            )
            row = cursor.fetchone()
            if row:
                return {
                    "experiment_id": row[0], "question_text": row[1],
                    "entropy_signature": row[2], "oracle_id": row[3],
                    "oracle_version": row[4], "oracle_graph_hash": row[5],
                    "prediction_payload": json.loads(row[6]) if row[6] else {},
                    "prediction_hash": row[7], "timestamp_created": row[8],
                    "time_horizon": row[9], "domain": row[10],
                    "status": row[11], "outcome": row[12],
                    "outcome_details": json.loads(row[13]) if row[13] else {},
                    "outcome_timestamp": row[14], "content_hash": row[15],
                }
            return None

    def list_experiments(
        self, status: str = None, outcome: str = None, domain: str = None
    ) -> list[dict]:
        with sqlite3.connect(self.db_path) as conn:
            query = (
                "SELECT experiment_id, question_text, oracle_id, "
                "status, outcome, timestamp_created, time_horizon, domain "
                "FROM experiments"
            )
            params = []
            conditions = []
            if status:
                conditions.append("status = ?")
                params.append(status)
            if outcome:
                conditions.append("outcome = ?")
                params.append(outcome)
            if domain:
                conditions.append("domain = ?")
                params.append(domain)
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
            query += " ORDER BY timestamp_created DESC"

            cursor = conn.execute(query, params)
            return [
                {
                    "experiment_id": row[0], "question_text": row[1],
                    "oracle_id": row[2], "status": row[3], "outcome": row[4],
                    "timestamp_created": row[5], "time_horizon": row[6],
                    "domain": row[7],
                }
                for row in cursor.fetchall()
            ]

    def get_pending_experiments(self) -> list[dict]:
        """Get experiments waiting for outcome annotation."""
        return self.list_experiments(status="frozen", outcome="pending")

    def compute_accuracy(self) -> dict:
        """Compute accuracy statistics across all evaluated experiments."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT outcome, COUNT(*) FROM experiments "
                "WHERE status = 'evaluated' GROUP BY outcome"
            )
            counts = {row[0]: row[1] for row in cursor.fetchall()}
            total = sum(counts.values())
            successes = counts.get("success", 0)
            failures = counts.get("failure", 0)
            partial = counts.get("partial", 0)

            return {
                "total_evaluated": total,
                "successes": successes,
                "failures": failures,
                "partial": partial,
                "accuracy": successes / max(total, 1),
                "success_rate": successes / max(total, 1),
                "by_status": counts,
            }

    def verify_experiment_integrity(self, experiment_id: str) -> dict:
        """Full integrity check: experiment content + log chain."""
        exp = self.get_experiment(experiment_id)
        if not exp:
            return {"valid": False, "error": "Experiment not found"}

        chain_result = self.log.verify_chain(experiment_id)

        content = json.dumps({
            "question": exp["question_text"],
            "prediction": exp["prediction_payload"],
            "oracle_id": exp["oracle_id"],
            "oracle_version": exp["oracle_version"],
            "time_horizon": exp["time_horizon"],
            "domain": exp["domain"],
        }, sort_keys=True)
        content_hash = hashlib.sha256(content.encode()).hexdigest()
        content_valid = content_hash == exp["content_hash"]

        return {
            "experiment_id": experiment_id,
            "content_valid": content_valid,
            "chain_valid": chain_result["valid"],
            "chain_length": chain_result.get("chain_length", 0),
            "overall_valid": content_valid and chain_result["valid"],
        }
