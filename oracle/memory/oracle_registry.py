"""Oracle Registry - tracks all evolved oracles."""
import json
import hashlib
import time
import os


class OracleRegistry:
    def __init__(self, registry_path: str = "data/oracle_registry.json"):
        self.registry_path = registry_path
        self.oracles = {}
        os.makedirs(os.path.dirname(registry_path) or ".", exist_ok=True)
        self._load()

    def _load(self):
        if os.path.exists(self.registry_path):
            try:
                with open(self.registry_path, "r") as f:
                    self.oracles = json.load(f)
            except (json.JSONDecodeError, IOError):
                self.oracles = {}

    def _save(self):
        with open(self.registry_path, "w") as f:
            json.dump(self.oracles, f, indent=2)

    def register(self, oracle_id: str, chromosome_dict: dict, fitness: dict,
                 generation: int, lineage_id: str = "") -> str:
        oracle_hash = hashlib.sha256(json.dumps(chromosome_dict, sort_keys=True).encode()).hexdigest()[:16]
        entry = {
            "oracle_id": oracle_id,
            "oracle_hash": oracle_hash,
            "chromosome": chromosome_dict,
            "fitness": fitness,
            "generation": generation,
            "lineage_id": lineage_id,
            "registered_at": time.time(),
            "status": "active",
        }
        self.oracles[oracle_id] = entry
        self._save()
        return oracle_hash

    def get(self, oracle_id: str) -> dict | None:
        return self.oracles.get(oracle_id)

    def list_oracles(self, status: str = None) -> list[dict]:
        oracles = list(self.oracles.values())
        if status:
            oracles = [o for o in oracles if o.get("status") == status]
        return sorted(oracles, key=lambda o: o.get("fitness", {}).get("total_fitness", 0), reverse=True)

    def update_status(self, oracle_id: str, status: str):
        if oracle_id in self.oracles:
            self.oracles[oracle_id]["status"] = status
            self._save()

    def get_best(self, n: int = 5) -> list[dict]:
        all_oracles = self.list_oracles(status="active")
        return all_oracles[:n]
