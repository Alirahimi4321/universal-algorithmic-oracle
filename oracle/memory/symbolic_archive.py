"""Symbolic State Archive - stores recurring patterns and symbolic signatures."""
import json
import hashlib
import time
import os


class SymbolicArchive:
    def __init__(self, archive_path: str = "data/symbolic_archive.json"):
        self.archive_path = archive_path
        self.states = {}
        self.signatures = {}
        self.resonance_patterns = {}
        os.makedirs(os.path.dirname(archive_path) or ".", exist_ok=True)
        self._load()

    def _load(self):
        if os.path.exists(self.archive_path):
            try:
                with open(self.archive_path, "r") as f:
                    data = json.load(f)
                    self.states = data.get("states", {})
                    self.signatures = data.get("signatures", {})
                    self.resonance_patterns = data.get("resonance_patterns", {})
            except (json.JSONDecodeError, IOError):
                pass

    def _save(self):
        with open(self.archive_path, "w") as f:
            json.dump({
                "states": self.states,
                "signatures": self.signatures,
                "resonance_patterns": self.resonance_patterns,
            }, f, indent=2)

    def archive_state(self, symbolic_state: dict, fitness: float) -> str:
        state_hash = hashlib.sha256(json.dumps(symbolic_state, sort_keys=True).encode()).hexdigest()[:16]
        if state_hash in self.states:
            self.states[state_hash]["count"] += 1
            self.states[state_hash]["avg_fitness"] = (
                self.states[state_hash]["avg_fitness"] + fitness
            ) / 2
        else:
            self.states[state_hash] = {
                "state": symbolic_state,
                "fitness": fitness,
                "avg_fitness": fitness,
                "count": 1,
                "first_seen": time.time(),
                "last_seen": time.time(),
            }
        self._save()
        return state_hash

    def archive_signature(self, signature: dict) -> str:
        sig_hash = hashlib.sha256(json.dumps(signature, sort_keys=True).encode()).hexdigest()[:16]
        if sig_hash in self.signatures:
            self.signatures[sig_hash]["count"] += 1
        else:
            self.signatures[sig_hash] = {
                "signature": signature,
                "count": 1,
                "first_seen": time.time(),
            }
        self._save()
        return sig_hash

    def find_recurring(self, min_count: int = 3) -> list[dict]:
        return [
            {"hash": h, **s}
            for h, s in self.states.items()
            if s.get("count", 0) >= min_count
        ]

    def get_frequent_signatures(self, min_count: int = 5) -> list[dict]:
        return [
            {"hash": h, **s}
            for h, s in self.signatures.items()
            if s.get("count", 0) >= min_count
        ]
