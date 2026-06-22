"""Evolutionary memory archive."""
import sqlite3
import json
import time

class EvolutionaryMemory:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS memories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chromosome_id TEXT,
                    generation INTEGER,
                    fitness_score REAL,
                    chromosome_data TEXT,
                    timestamp REAL,
                    metadata TEXT
                )
            """)
            conn.commit()

    def store(self, chromosome_id: str, generation: int, fitness_score: float, 
              chromosome_data: dict = None, metadata: dict = None):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO memories (chromosome_id, generation, fitness_score, chromosome_data, timestamp, metadata) VALUES (?, ?, ?, ?, ?, ?)",
                (chromosome_id, generation, fitness_score, json.dumps(chromosome_data or {}), 
                 time.time(), json.dumps(metadata or {}))
            )
            conn.commit()

    def retrieve_best(self, n: int = 10) -> list[dict]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT chromosome_id, generation, fitness_score, chromosome_data, timestamp, metadata FROM memories ORDER BY fitness_score DESC LIMIT ?",
                (n,)
            )
            return [{"chromosome_id": row[0], "generation": row[1], "fitness_score": row[2],
                     "chromosome_data": json.loads(row[3]), "timestamp": row[4], 
                     "metadata": json.loads(row[5])} for row in cursor.fetchall()]

    def save_chromosome(self, chromosome):
        data = chromosome.to_dict()
        score = chromosome.fitness.get("total_fitness", 0) if isinstance(chromosome.fitness, dict) else 0
        chrom_id = getattr(chromosome, 'chromosome_id', None) or getattr(chromosome, 'genome_id', 'unknown')
        gen = getattr(chromosome, 'generation', 0)
        self.store(chrom_id, gen, score, data)

    def count(self) -> int:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM memories")
            return cursor.fetchone()[0]
