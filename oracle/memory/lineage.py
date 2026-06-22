"""Lineage tracker for evolutionary histories."""
import sqlite3
import json
import time

class LineageTracker:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS lineage (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chromosome_id TEXT,
                    parent_ids TEXT,
                    generation INTEGER,
                    birth_time REAL,
                    death_time REAL,
                    metadata TEXT
                )
            """)
            conn.commit()

    def record_birth(self, chromosome_id: str, generation: int, parent_ids: list[str] = None, 
                     metadata: dict = None):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO lineage (chromosome_id, parent_ids, generation, birth_time, metadata) VALUES (?, ?, ?, ?, ?)",
                (chromosome_id, json.dumps(parent_ids or []), generation, time.time(), 
                 json.dumps(metadata or {}))
            )
            conn.commit()

    def record_death(self, chromosome_id: str):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "UPDATE lineage SET death_time = ? WHERE chromosome_id = ? AND death_time IS NULL",
                (time.time(), chromosome_id)
            )
            conn.commit()

    def get_parents(self, chromosome_id: str) -> list[str]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT parent_ids FROM lineage WHERE chromosome_id = ?",
                (chromosome_id,)
            )
            row = cursor.fetchone()
            if row:
                return json.loads(row[0])
            return []

    def get_children(self, chromosome_id: str) -> list[str]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT chromosome_id, parent_ids FROM lineage")
            children = []
            for row in cursor.fetchall():
                parents = json.loads(row[1])
                if chromosome_id in parents:
                    children.append(row[0])
            return children

    def get_generation(self, generation: int) -> list[str]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT chromosome_id FROM lineage WHERE generation = ?",
                (generation,)
            )
            return [row[0] for row in cursor.fetchall()]

    def count(self) -> int:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM lineage")
            return cursor.fetchone()[0]
