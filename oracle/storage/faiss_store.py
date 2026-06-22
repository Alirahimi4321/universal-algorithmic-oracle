"""FAISS vector search for similarity-based oracle lookup.

Per design doc section 21.2: vector search with FAISS.
"""
import json
import time
import logging
import os
import numpy as np
from typing import Optional

logger = logging.getLogger(__name__)

try:
    import faiss
    HAS_FAISS = True
except ImportError:
    HAS_FAISS = False
    logger.info("faiss not available")


class FAISSVectorStore:
    """Vector store using FAISS for similarity search of oracle structures."""

    def __init__(self, dimension: int = 128, storage_dir: str = None):
        self.dimension = dimension
        self.storage_dir = storage_dir
        self.index = None
        self.metadata = []
        self.available = False

        if not HAS_FAISS:
            logger.warning("FAISS not installed")
            return

        self.index = faiss.IndexFlatL2(dimension)
        self.available = True

        if storage_dir:
            os.makedirs(storage_dir, exist_ok=True)
            self._load()

    def _load(self):
        """Load index from disk."""
        if not self.storage_dir:
            return
        index_path = os.path.join(self.storage_dir, "faiss.index")
        meta_path = os.path.join(self.storage_dir, "faiss_meta.json")

        if os.path.exists(index_path):
            try:
                self.index = faiss.read_index(index_path)
                if os.path.exists(meta_path):
                    with open(meta_path) as f:
                        self.metadata = json.load(f)
                logger.info("Loaded FAISS index with %d vectors", self.index.ntotal)
            except Exception as e:
                logger.warning("Failed to load FAISS index: %s", e)

    def _save(self):
        """Save index to disk."""
        if not self.storage_dir or not self.index:
            return
        index_path = os.path.join(self.storage_dir, "faiss.index")
        meta_path = os.path.join(self.storage_dir, "faiss_meta.json")

        try:
            faiss.write_index(self.index, index_path)
            with open(meta_path, "w") as f:
                json.dump(self.metadata, f)
        except Exception as e:
            logger.warning("Failed to save FAISS index: %s", e)

    def add_vector(
        self,
        vector: list[float],
        metadata: dict,
    ) -> int:
        """Add a vector with metadata to the store."""
        if not self.available:
            return -1

        vec = np.array([vector], dtype=np.float32)
        if vec.shape[1] != self.dimension:
            if vec.shape[1] < self.dimension:
                vec = np.pad(vec, ((0, 0), (0, self.dimension - vec.shape[1])))
            else:
                vec = vec[:, :self.dimension]

        idx = self.index.ntotal
        self.index.add(vec)
        self.metadata.append({
            "index": idx,
            "metadata": metadata,
            "timestamp": time.time(),
        })

        self._save()
        return idx

    def search(
        self,
        query_vector: list[float],
        k: int = 5,
    ) -> list[dict]:
        """Search for k nearest neighbors."""
        if not self.available or self.index.ntotal == 0:
            return []

        vec = np.array([query_vector], dtype=np.float32)
        if vec.shape[1] != self.dimension:
            if vec.shape[1] < self.dimension:
                vec = np.pad(vec, ((0, 0), (0, self.dimension - vec.shape[1])))
            else:
                vec = vec[:, :self.dimension]

        k = min(k, self.index.ntotal)
        distances, indices = self.index.search(vec, k)

        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx < len(self.metadata):
                results.append({
                    "distance": float(dist),
                    "metadata": self.metadata[idx]["metadata"],
                    "index": int(idx),
                })

        return results

    def add_chromosome(
        self,
        chromosome_id: str,
        chromosome_vector: list[float],
        fitness: float,
        systems: list[str],
        generation: int,
    ) -> int:
        """Add a chromosome's vector representation."""
        return self.add_vector(
            vector=chromosome_vector,
            metadata={
                "chromosome_id": chromosome_id,
                "fitness": fitness,
                "systems": systems,
                "generation": generation,
                "type": "chromosome",
            },
        )

    def find_similar_chromosomes(
        self,
        query_vector: list[float],
        k: int = 5,
    ) -> list[dict]:
        """Find similar chromosomes."""
        results = self.search(query_vector, k)
        return [r for r in results if r["metadata"].get("type") == "chromosome"]

    def get_stats(self) -> dict:
        return {
            "total_vectors": self.index.ntotal if self.index else 0,
            "dimension": self.dimension,
            "available": self.available,
        }
