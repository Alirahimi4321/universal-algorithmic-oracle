"""Qdrant vector search for similarity-based oracle lookup.

Per design doc section 21.2: vector search with Qdrant.
"""
import json
import time
import logging
from typing import Optional

logger = logging.getLogger(__name__)

try:
    from qdrant_client import QdrantClient
    from qdrant_client.models import VectorParams, Distance, PointStruct
    HAS_QDRANT = True
except ImportError:
    HAS_QDRANT = False
    logger.info("qdrant_client not available")


class QdrantVectorStore:
    """Vector store using Qdrant for similarity search."""

    def __init__(
        self,
        collection_name: str = "oracle_vectors",
        dimension: int = 128,
        host: str = "localhost",
        port: int = 6333,
        in_memory: bool = True,
    ):
        self.collection_name = collection_name
        self.dimension = dimension
        self.available = False
        self.client = None

        if not HAS_QDRANT:
            logger.warning("Qdrant client not installed")
            return

        try:
            if in_memory:
                self.client = QdrantClient(":memory:")
            else:
                self.client = QdrantClient(host=host, port=port)

            collections = self.client.get_collections().collections
            collection_names = [c.name for c in collections]

            if collection_name not in collection_names:
                self.client.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(
                        size=dimension,
                        distance=Distance.EUCLID,
                    ),
                )

            self.available = True
            logger.info("Qdrant store initialized: %s", collection_name)
        except Exception as e:
            logger.warning("Qdrant init failed: %s", e)

    def add_vector(
        self,
        vector: list[float],
        metadata: dict,
        vector_id: int = None,
    ) -> Optional[str]:
        """Add a vector with metadata."""
        if not self.available:
            return None

        if vector_id is None:
            vector_id = int(time.time() * 1000000) % (2**63)

        padded = vector[:self.dimension]
        if len(padded) < self.dimension:
            padded = padded + [0.0] * (self.dimension - len(padded))

        point = PointStruct(
            id=vector_id,
            vector=padded,
            payload=metadata,
        )

        self.client.upsert(
            collection_name=self.collection_name,
            points=[point],
        )

        return str(vector_id)

    def search(
        self,
        query_vector: list[float],
        k: int = 5,
        score_threshold: float = None,
    ) -> list[dict]:
        """Search for k nearest neighbors."""
        if not self.available:
            return []

        padded = query_vector[:self.dimension]
        if len(padded) < self.dimension:
            padded = padded + [0.0] * (self.dimension - len(padded))

        results = self.client.query_points(
            collection_name=self.collection_name,
            query=padded,
            limit=k,
            score_threshold=score_threshold,
        )

        return [
            {
                "id": str(hit.id),
                "score": hit.score,
                "metadata": hit.payload,
            }
            for hit in results.points
        ]

    def add_chromosome(
        self,
        chromosome_id: str,
        chromosome_vector: list[float],
        fitness: float,
        systems: list[str],
        generation: int,
    ) -> Optional[str]:
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
        if not self.available:
            return {"available": False}

        info = self.client.get_collection(self.collection_name)
        return {
            "available": True,
            "collection": self.collection_name,
            "total_vectors": info.points_count,
            "dimension": self.dimension,
        }

    def delete_vector(self, vector_id: str) -> bool:
        """Delete a vector by ID."""
        if not self.available:
            return False
        self.client.delete(
            collection_name=self.collection_name,
            points_selector=[int(vector_id)],
        )
        return True
