"""Chromosome Archive - saves the best evolved chromosomes across generations."""
import sqlite3
import json
import time
import hashlib
from typing import Any


class ChromosomeArchive:
    """Persists the best evolved chromosomes for future use."""

    def __init__(self, db_path: str = "data/chromosome_archive.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS best_chromosomes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chromosome_id TEXT UNIQUE,
                    generation INTEGER,
                    fitness_score REAL,
                    prediction_accuracy REAL,
                    chromosome_data TEXT,
                    system_configs TEXT,
                    custom_formulas TEXT,
                    fusion_rules TEXT,
                    invented_methods TEXT,
                    difficulty_level INTEGER,
                    timestamp REAL,
                    metadata TEXT
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS generation_snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    generation INTEGER,
                    best_fitness REAL,
                    avg_fitness REAL,
                    best_prediction_accuracy REAL,
                    difficulty_level INTEGER,
                    benchmark_accuracy REAL,
                    population_size INTEGER,
                    best_chromosome_id TEXT,
                    snapshot_data TEXT,
                    timestamp REAL
                )
            """)
            conn.commit()

    def save_best(self, chromosome, generation: int, difficulty_level: int = 1,
                  benchmark_accuracy: float = 0.0) -> str:
        """Save a chromosome if it's better than existing ones."""
        score = chromosome.fitness.get("total_fitness", 0) if isinstance(chromosome.fitness, dict) else 0
        pred_acc = chromosome.fitness.get("prediction_accuracy", 0) if isinstance(chromosome.fitness, dict) else 0
        chrom_id = getattr(chromosome, 'chromosome_id', None) or hashlib.md5(f"{time.time()}".encode()).hexdigest()[:8]

        existing = self.get_best(n=1)
        if existing and score <= existing[0].get("fitness_score", 0):
            return ""

        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO best_chromosomes 
                (chromosome_id, generation, fitness_score, prediction_accuracy,
                 chromosome_data, system_configs, custom_formulas, fusion_rules,
                 invented_methods, difficulty_level, timestamp, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                chrom_id, generation, score, pred_acc,
                json.dumps(chromosome.to_dict()),
                json.dumps({k: v.to_dict() for k, v in chromosome.system_configs.items()}),
                json.dumps(chromosome.custom_formulas),
                json.dumps(chromosome.fusion_rules),
                json.dumps(chromosome.invented_methods),
                difficulty_level,
                time.time(),
                json.dumps({"lineage_id": chromosome.lineage_id}),
            ))
            conn.commit()

        self._cleanup_old(limit=50)
        return chrom_id

    def get_best(self, n: int = 10) -> list[dict]:
        """Get the best chromosomes ever saved."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT chromosome_id, generation, fitness_score, prediction_accuracy,
                       chromosome_data, system_configs, custom_formulas, fusion_rules,
                       invented_methods, difficulty_level, timestamp, metadata
                FROM best_chromosomes ORDER BY fitness_score DESC LIMIT ?
            """, (n,))
            results = []
            for row in cursor.fetchall():
                results.append({
                    "chromosome_id": row[0],
                    "generation": row[1],
                    "fitness_score": row[2],
                    "prediction_accuracy": row[3],
                    "chromosome_data": json.loads(row[4]) if row[4] else {},
                    "system_configs": json.loads(row[5]) if row[5] else {},
                    "custom_formulas": json.loads(row[6]) if row[6] else {},
                    "fusion_rules": json.loads(row[7]) if row[7] else [],
                    "invented_methods": json.loads(row[8]) if row[8] else [],
                    "difficulty_level": row[9],
                    "timestamp": row[10],
                    "metadata": json.loads(row[11]) if row[11] else {},
                })
            return results

    def save_generation_snapshot(self, generation: int, best_fitness: float,
                                  avg_fitness: float, best_prediction_accuracy: float,
                                  difficulty_level: int, benchmark_accuracy: float,
                                  population_size: int, best_chromosome_id: str,
                                  snapshot_data: dict = None):
        """Save a snapshot of a generation for history."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO generation_snapshots 
                (generation, best_fitness, avg_fitness, best_prediction_accuracy,
                 difficulty_level, benchmark_accuracy, population_size,
                 best_chromosome_id, snapshot_data, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                generation, best_fitness, avg_fitness, best_prediction_accuracy,
                difficulty_level, benchmark_accuracy, population_size,
                best_chromosome_id, json.dumps(snapshot_data or {}),
                time.time(),
            ))
            conn.commit()

    def get_generation_history(self, n: int = 50) -> list[dict]:
        """Get the generation history."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT generation, best_fitness, avg_fitness, best_prediction_accuracy,
                       difficulty_level, benchmark_accuracy, population_size,
                       best_chromosome_id, snapshot_data, timestamp
                FROM generation_snapshots ORDER BY generation DESC LIMIT ?
            """, (n,))
            results = []
            for row in cursor.fetchall():
                results.append({
                    "generation": row[0],
                    "best_fitness": row[1],
                    "avg_fitness": row[2],
                    "best_prediction_accuracy": row[3],
                    "difficulty_level": row[4],
                    "benchmark_accuracy": row[5],
                    "population_size": row[6],
                    "best_chromosome_id": row[7],
                    "snapshot_data": json.loads(row[8]) if row[8] else {},
                    "timestamp": row[9],
                })
            return results

    def load_chromosome_data(self, chromosome_id: str) -> dict | None:
        """Load full chromosome data by ID."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT chromosome_data FROM best_chromosomes WHERE chromosome_id = ?
            """, (chromosome_id,))
            row = cursor.fetchone()
            if row:
                return json.loads(row[0])
            return None

    def get_stats(self) -> dict:
        """Get archive statistics."""
        with sqlite3.connect(self.db_path) as conn:
            chrom_count = conn.execute("SELECT COUNT(*) FROM best_chromosomes").fetchone()[0]
            gen_count = conn.execute("SELECT COUNT(*) FROM generation_snapshots").fetchone()[0]
            best = conn.execute("SELECT MAX(fitness_score) FROM best_chromosomes").fetchone()[0]
            best_pred = conn.execute("SELECT MAX(prediction_accuracy) FROM best_chromosomes").fetchone()[0]
            return {
                "total_chromosomes": chrom_count,
                "total_generations": gen_count,
                "best_fitness_ever": best or 0.0,
                "best_prediction_accuracy_ever": best_pred or 0.0,
            }

    def _cleanup_old(self, limit: int = 100):
        """Keep only the best N chromosomes."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                DELETE FROM best_chromosomes WHERE id NOT IN (
                    SELECT id FROM best_chromosomes ORDER BY fitness_score DESC LIMIT ?
                )
            """, (limit,))
            conn.commit()

    def to_dict(self) -> dict:
        return self.get_stats()
