"""ChromaDB vector memory for semantic search over Q&A pairs."""
import hashlib
import json
import logging
import os
import time
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

try:
    import chromadb
    from chromadb.config import Settings
    HAS_CHROMA = True
except ImportError:
    chromadb = None
    HAS_CHROMA = False
    logger.info("chromadb not available, vector memory disabled")

try:
    from sentence_transformers import SentenceTransformer
    HAS_SENTENCE_TRANSFORMERS = True
except ImportError:
    SentenceTransformer = None
    HAS_SENTENCE_TRANSFORMERS = False
    logger.info("sentence-transformers not available, using hash-based embeddings")


class VectorMemory:
    """Persistent vector memory for semantic search over Q&A pairs.

    Uses ChromaDB for storage and retrieval. Embeddings are computed via
    sentence-transformers if available, otherwise a deterministic hash-based
    fallback is used.
    """

    DEFAULT_MODEL = "all-MiniLM-L6-v2"

    def __init__(self, persist_directory: str = "data/vector_memory"):
        """Initialize vector memory store.

        Parameters
        ----------
        persist_directory : str
            Directory for ChromaDB persistent storage.
        """
        self.persist_directory = persist_directory
        self._model = None
        self._collection = None
        self._client = None

        if not HAS_CHROMA:
            logger.warning("chromadb not installed; VectorMemory will use in-memory fallback")
            self._init_fallback()
            return

        os.makedirs(persist_directory, exist_ok=True)

        try:
            self._client = chromadb.PersistentClient(
                path=persist_directory,
                settings=Settings(anonymized_telemetry=False),
            )
            self._collection = self._client.get_or_create_collection(
                name="oracle_qa",
                metadata={"hnsw:space": "cosine"},
            )
            logger.info(
                "VectorMemory initialized at %s (%d existing entries)",
                persist_directory, self._collection.count(),
            )
        except Exception as e:
            logger.error("Failed to initialize ChromaDB: %s", e)
            self._init_fallback()

        self._load_model()

    def _init_fallback(self):
        """Initialize in-memory fallback storage."""
        self._fallback_store: List[Dict[str, Any]] = []

    def _load_model(self):
        """Load sentence-transformers model if available."""
        if not HAS_SENTENCE_TRANSFORMERS:
            return
        try:
            self._model = SentenceTransformer(self.DEFAULT_MODEL)
            logger.debug("Loaded sentence-transformers model: %s", self.DEFAULT_MODEL)
        except Exception as e:
            logger.warning("Failed to load sentence-transformers: %s", e)
            self._model = None

    def _embed(self, text: str) -> List[float]:
        """Compute embedding for text.

        Uses sentence-transformers if available, otherwise a hash-based fallback
        that produces a deterministic pseudo-embedding.
        """
        if self._model is not None:
            try:
                embedding = self._model.encode(text, normalize_embeddings=True)
                return embedding.tolist()
            except Exception as e:
                logger.warning("Embedding failed, using hash fallback: %s", e)

        return self._hash_embedding(text)

    @staticmethod
    def _hash_embedding(text: str, dim: int = 384) -> List[float]:
        """Deterministic hash-based pseudo-embedding."""
        import math
        h = hashlib.sha512(text.encode("utf-8")).digest()
        extended = h
        while len(extended) < dim * 4:
            extended += hashlib.sha512(extended).digest()

        values = []
        for i in range(dim):
            chunk = extended[i * 4 : (i + 1) * 4]
            val = int.from_bytes(chunk, byteorder="big", signed=False)
            values.append((val / 0xFFFFFFFF) * 2 - 1)

        norm = math.sqrt(sum(v * v for v in values))
        if norm > 0:
            values = [v / norm for v in values]
        return values

    def store(self, question: str, answer: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Store a Q&A pair with embeddings.

        Parameters
        ----------
        question : str
            The question text.
        answer : str
            The answer text.
        metadata : dict, optional
            Additional metadata to attach to the entry.

        Returns
        -------
        str
            The document ID.
        """
        metadata = metadata or {}
        doc_id = hashlib.sha256(f"{question}:{answer}:{time.time()}".encode()).hexdigest()[:16]

        embedding = self._embed(question)
        full_metadata = {
            "question": question,
            "answer": answer,
            "timestamp": time.time(),
            **metadata,
        }

        if self._collection is not None:
            try:
                self._collection.add(
                    ids=[doc_id],
                    embeddings=[embedding],
                    metadatas=[full_metadata],
                    documents=[question],
                )
                logger.debug("Stored Q&A pair: %s", doc_id)
                return doc_id
            except Exception as e:
                logger.error("Failed to store in ChromaDB: %s", e)

        self._fallback_store.append({
            "id": doc_id,
            "embedding": embedding,
            "metadata": full_metadata,
            "document": question,
        })
        logger.debug("Stored Q&A pair (fallback): %s", doc_id)
        return doc_id

    def search(self, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """Semantic search for similar past questions.

        Parameters
        ----------
        query : str
            The search query.
        n_results : int
            Number of results to return.

        Returns
        -------
        list of dict
            Matching documents with scores.
        """
        embedding = self._embed(query)

        if self._collection is not None:
            try:
                results = self._collection.query(
                    query_embeddings=[embedding],
                    n_results=min(n_results, self._collection.count() or 1),
                )
                output = []
                for i in range(len(results["ids"][0])):
                    output.append({
                        "id": results["ids"][0][i],
                        "question": results["metadatas"][0][i].get("question", ""),
                        "answer": results["metadatas"][0][i].get("answer", ""),
                        "distance": results["distances"][0][i] if results.get("distances") else 0.0,
                        "metadata": results["metadatas"][0][i],
                    })
                return output
            except Exception as e:
                logger.warning("ChromaDB search failed: %s", e)

        return self._fallback_search(query, embedding, n_results)

    def _fallback_search(self, query: str, embedding: List[float], n_results: int) -> List[Dict[str, Any]]:
        """Fallback cosine similarity search."""
        import math

        scored = []
        for entry in self._fallback_store:
            sim = self._cosine_similarity(embedding, entry["embedding"])
            scored.append((sim, entry))

        scored.sort(key=lambda x: x[0], reverse=True)

        results = []
        for sim, entry in scored[:n_results]:
            results.append({
                "id": entry["id"],
                "question": entry["metadata"].get("question", ""),
                "answer": entry["metadata"].get("answer", ""),
                "distance": 1.0 - sim,
                "metadata": entry["metadata"],
            })
        return results

    @staticmethod
    def _cosine_similarity(a: List[float], b: List[float]) -> float:
        """Compute cosine similarity between two vectors."""
        import math
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(x * x for x in b))
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)

    def get_stats(self) -> Dict[str, Any]:
        """Return collection statistics."""
        if self._collection is not None:
            try:
                count = self._collection.count()
                return {
                    "total_entries": count,
                    "backend": "chromadb",
                    "persist_directory": self.persist_directory,
                    "model": self.DEFAULT_MODEL if self._model else "hash_fallback",
                }
            except Exception as e:
                logger.warning("Failed to get ChromaDB stats: %s", e)

        return {
            "total_entries": len(self._fallback_store),
            "backend": "fallback_in_memory",
            "model": "hash_fallback",
        }
