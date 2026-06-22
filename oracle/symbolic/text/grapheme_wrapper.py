"""Grapheme library wrapper - Unicode grapheme cluster processing."""
from __future__ import annotations

import hashlib
import logging
import math
import random
from typing import Optional

from ..base import SymbolicOutput, SymbolicSystemWrapper
from ..registry import register_system

logger = logging.getLogger(__name__)

try:
    import grapheme
    HAS_GRAPHEME = True
except ImportError:
    HAS_GRAPHEME = False
    logger.info("grapheme not available")


@register_system
class GraphemeWrapper(SymbolicSystemWrapper):
    """Wrapper for Unicode grapheme cluster analysis."""
    SYSTEM_ID = "grapheme_analysis"
    LIBRARY_BACKEND = "grapheme"

    def __init__(self) -> None:
        self.available: bool = HAS_GRAPHEME

    def compute(self, entropy_packet: dict, params: dict | None = None) -> SymbolicOutput:
        if not self.available:
            return SymbolicOutput(
                system_id=self.SYSTEM_ID,
                library_backend=self.LIBRARY_BACKEND,
                raw_output={"error": "grapheme not available"},
            )

        seed = entropy_packet.get("seed", 42)
        rng = random.Random(seed)
        text = entropy_packet.get("text", entropy_packet.get("question", ""))

        if not text:
            text = f"oracle_{seed}_query"

        try:
            clusters = list(grapheme.graphemes(text))
            g_len = grapheme.length(text)

            cluster_hashes = [int(hashlib.md5(c.encode()).hexdigest()[:4], 16) for c in clusters]

            hash_val = int(hashlib.sha256(text.encode()).hexdigest()[:8], 16)

            numeric_projection = [
                g_len / max(len(text), 1),
                len(clusters) / max(g_len, 1),
                (hash_val % 1000) / 1000.0,
                (sum(cluster_hashes) % 10000) / 10000.0,
                rng.random(),
            ]

            symbolic_state = {
                "input_text": text[:100],
                "grapheme_count": len(clusters),
                "char_count": g_len,
                "clusters": clusters[:20],
                "unique_clusters": len(set(clusters)),
                "ratio": len(clusters) / max(g_len, 1),
            }

            structural_features = {
                "grapheme_density": len(clusters) / max(g_len, 1),
                "cluster_variety": len(set(clusters)) / max(len(clusters), 1),
                "avg_cluster_hash": sum(cluster_hashes) / max(len(cluster_hashes), 1),
            }

            return self._build_output(
                symbolic_state=symbolic_state,
                numeric_projection=numeric_projection,
                structural_features=structural_features,
                raw_output={"clusters": clusters},
                params=params,
            )
        except Exception as e:
            logger.warning(f"grapheme computation failed: {e}")
            return SymbolicOutput(
                system_id=self.SYSTEM_ID,
                library_backend=self.LIBRARY_BACKEND,
                raw_output={"error": str(e)},
            )
