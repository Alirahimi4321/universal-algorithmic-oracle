"""Mutation bank for storing successful mutations."""
import sqlite3
import json
import time

class MutationBank:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS mutations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    mutation_type TEXT,
                    source_chromosome TEXT,
                    target_chromosome TEXT,
                    success_rate REAL,
                    fitness_delta REAL,
                    timestamp REAL,
                    parameters TEXT
                )
            """)
            conn.commit()

    def store(self, mutation_type: str, source_chromosome: str, target_chromosome: str,
              success_rate: float, fitness_delta: float, parameters: dict = None):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO mutations (mutation_type, source_chromosome, target_chromosome, success_rate, fitness_delta, timestamp, parameters) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (mutation_type, source_chromosome, target_chromosome, success_rate, 
                 fitness_delta, time.time(), json.dumps(parameters or {}))
            )
            conn.commit()

    def get_successful_mutations(self, min_success_rate: float = 0.5) -> list[dict]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT mutation_type, source_chromosome, target_chromosome, success_rate, fitness_delta, parameters FROM mutations WHERE success_rate >= ? ORDER BY fitness_delta DESC",
                (min_success_rate,)
            )
            return [{"mutation_type": row[0], "source_chromosome": row[1], 
                     "target_chromosome": row[2], "success_rate": row[3],
                     "fitness_delta": row[4], "parameters": json.loads(row[5])} 
                    for row in cursor.fetchall()]

    def count(self) -> int:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM mutations")
            return cursor.fetchone()[0]
