"""Oracle version tracking for evolutionary lineage management.

Tracks versions, snapshots, and ancestry of oracle structures.
"""
import hashlib
import json
import time
import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class OracleVersionTracker:
    """Tracks oracle versions and their evolutionary history."""

    def __init__(self, storage_dir: str = None, db_path: str = None):
        self.storage_dir = storage_dir
        self.versions = {}
        self.lineages = {}
        self._storage = None
        if storage_dir:
            os.makedirs(storage_dir, exist_ok=True)
        if db_path:
            try:
                from oracle.storage.sqlalchemy_backend import StorageBackend
                url = f"sqlite:///{db_path}"
                self._storage = StorageBackend(url)
                logger.info("OracleVersionTracker using SQLAlchemy backend")
            except Exception as e:
                logger.warning("SQLAlchemy unavailable: %s", e)

    def register_version(
        self,
        oracle_id: str,
        chromosome,
        generation: int,
        parent_ids: list[str] = None,
        mutation_type: str = "initial",
    ) -> dict:
        """Register a new version of an oracle structure."""
        chrom_hash = self._hash_chromosome(chromosome)
        systems = [g.system_id for g in chromosome.gene_list] if hasattr(chromosome, 'gene_list') else []
        fitness = getattr(chromosome, 'fitness', {})

        version_id = f"v{generation}_{chrom_hash[:8]}"
        parent_id = parent_ids[0] if parent_ids else None

        version_info = {
            "version_id": version_id,
            "oracle_id": oracle_id,
            "chromosome_id": getattr(chromosome, 'chromosome_id', 'unknown'),
            "chromosome_hash": chrom_hash,
            "generation": generation,
            "parent_id": parent_id,
            "mutation_type": mutation_type,
            "systems": systems,
            "fitness": fitness,
            "gene_count": len(chromosome.genes) if hasattr(chromosome, 'genes') else 0,
            "edge_count": len(chromosome.edges) if hasattr(chromosome, 'edges') else 0,
            "timestamp": time.time(),
        }

        self.versions[version_id] = version_info

        if oracle_id not in self.lineages:
            self.lineages[oracle_id] = {"versions": [], "root": version_id}
        self.lineages[oracle_id]["versions"].append(version_id)
        self.lineages[oracle_id]["latest"] = version_id

        if self._storage:
            try:
                self._storage.store_version({
                    "version_id": version_id,
                    "oracle_id": oracle_id,
                    "chromosome_id": version_info["chromosome_id"],
                    "chromosome_hash": chrom_hash,
                    "generation": generation,
                    "parent_id": parent_id,
                    "mutation_type": mutation_type,
                    "systems": json.dumps(systems),
                    "fitness": json.dumps(fitness, default=str),
                    "gene_count": version_info["gene_count"],
                    "edge_count": version_info["edge_count"],
                    "timestamp": time.time(),
                })
            except Exception as e:
                logger.warning("Failed to store version to SQLAlchemy: %s", e)

        if self.storage_dir:
            self._save_snapshot(version_id, version_info, chromosome)

        logger.info("Registered version %s for oracle %s", version_id, oracle_id)
        return version_info

    def get_version(self, version_id: str) -> Optional[dict]:
        return self.versions.get(version_id)

    def get_lineage(self, oracle_id: str) -> Optional[dict]:
        return self.lineages.get(oracle_id)

    def get_lineage_history(self, oracle_id: str) -> list[dict]:
        """Get the full version history of an oracle."""
        lineage = self.lineages.get(oracle_id)
        if not lineage:
            return []
        return [
            self.versions[vid]
            for vid in lineage["versions"]
            if vid in self.versions
        ]

    def get_ancestry(self, version_id: str, max_depth: int = 20) -> list[dict]:
        """Get the ancestry chain of a version."""
        ancestry = []
        current = version_id
        for _ in range(max_depth):
            version = self.versions.get(current)
            if not version:
                break
            ancestry.append(version)
            parent = version.get("parent_id")
            if not parent:
                break
            current = parent
        return ancestry

    def get_stats(self) -> dict:
        total_versions = len(self.versions)
        total_lineages = len(self.lineages)
        all_systems = set()
        for v in self.versions.values():
            all_systems.update(v.get("systems", []))

        return {
            "total_versions": total_versions,
            "total_lineages": total_lineages,
            "unique_systems": len(all_systems),
            "system_list": sorted(all_systems),
        }

    def _hash_chromosome(self, chromosome) -> str:
        """Compute a hash of the chromosome structure."""
        gene_ids = sorted(g.system_id for g in chromosome.gene_list) if hasattr(chromosome, 'gene_list') else []
        edge_str = json.dumps(sorted(chromosome.edges)) if hasattr(chromosome, 'edges') else ""
        content = json.dumps({"genes": gene_ids, "edges": edge_str})
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def _save_snapshot(self, version_id: str, info: dict, chromosome):
        """Save a snapshot of the chromosome to disk."""
        if not self.storage_dir:
            return
        filepath = os.path.join(self.storage_dir, f"{version_id}.json")
        snapshot = {
            "version_info": info,
            "chromosome": chromosome.to_dict() if hasattr(chromosome, 'to_dict') else {},
        }
        try:
            with open(filepath, "w") as f:
                json.dump(snapshot, f, indent=2, default=str)
        except Exception as e:
            logger.warning("Failed to save snapshot %s: %s", version_id, e)

    def export_lineage(self, oracle_id: str) -> str:
        """Export lineage as JSON."""
        history = self.get_lineage_history(oracle_id)
        return json.dumps(history, indent=2, default=str)
