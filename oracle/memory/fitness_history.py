"""Fitness history tracking."""
import sqlite3
import json
import time

class FitnessHistory:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS fitness_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chromosome_id TEXT,
                    generation INTEGER,
                    fitness_data TEXT,
                    timestamp REAL
                )
            """)
            conn.commit()

    def record(self, chromosome_id: str, generation: int, fitness_data: dict):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO fitness_history (chromosome_id, generation, fitness_data, timestamp) VALUES (?, ?, ?, ?)",
                (chromosome_id, generation, json.dumps(fitness_data), time.time())
            )
            conn.commit()

    def get_history(self, chromosome_id: str) -> list[dict]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT generation, fitness_data, timestamp FROM fitness_history WHERE chromosome_id = ? ORDER BY generation",
                (chromosome_id,)
            )
            return [{"generation": row[0], "fitness_data": json.loads(row[1]), "timestamp": row[2]} 
                    for row in cursor.fetchall()]

    def get_best_fitness(self, chromosome_id: str) -> float:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT fitness_data FROM fitness_history WHERE chromosome_id = ? ORDER BY generation",
                (chromosome_id,)
            )
            best = 0.0
            for row in cursor.fetchall():
                data = json.loads(row[0])
                if "total_fitness" in data:
                    best = max(best, data["total_fitness"])
            return best

    def count(self) -> int:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM fitness_history")
            return cursor.fetchone()[0]
