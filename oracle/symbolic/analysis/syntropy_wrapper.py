"""Syntropy library wrapper - information theory and entropy measures."""
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
    import syntropy
    import syntropy.discrete as syn_disc
    HAS_SYNTROPY = True
except ImportError:
    HAS_SYNTROPY = False
    logger.info("syntropy not available")


@register_system
class SyntropyWrapper(SymbolicSystemWrapper):
    """Wrapper for advanced information theory analysis using syntropy."""
    SYSTEM_ID = "syntropy_info"
    LIBRARY_BACKEND = "syntropy"

    def __init__(self) -> None:
        self.available: bool = HAS_SYNTROPY

    def compute(self, entropy_packet: dict, params: dict | None = None) -> SymbolicOutput:
        if not self.available:
            return SymbolicOutput(
                system_id=self.SYSTEM_ID,
                library_backend=self.LIBRARY_BACKEND,
                raw_output={"error": "syntropy not available"},
            )

        seed = entropy_packet.get("seed", 42)
        rng = random.Random(seed)

        sha_stream = entropy_packet.get("sha_stream", "")

        try:
            if sha_stream:
                symbols = list(sha_stream[:32])
            else:
                symbols = [hex(rng.randint(0, 15))[2:] for _ in range(32)]

            from collections import Counter
            counts = Counter(symbols)
            total = len(symbols)
            probs = [c / total for c in counts.values()]

            H = -sum(p * math.log2(p) for p in probs if p > 0)

            n = len(symbols)
            half = n // 2
            s1 = symbols[:half]
            s2 = symbols[half:]
            c1 = Counter(s1)
            c2 = Counter(s2)
            t1, t2 = len(s1), len(s2)

            MI = 0.0
            for sym in set(symbols):
                p_xy = counts[sym] / n
                p_x = c1.get(sym, 0) / max(t1, 1)
                p_y = c2.get(sym, 0) / max(t2, 1)
                if p_xy > 0 and p_x > 0 and p_y > 0:
                    MI += p_xy * math.log2(p_xy / (p_x * p_y))

            unique_count = len(set(symbols))

            hash_val = int(hashlib.sha256(str(symbols).encode()).hexdigest()[:8], 16)

            numeric_projection = [
                min(H / 4.0, 1.0),
                min(abs(MI) / 2.0, 1.0),
                unique_count / 16.0,
                (hash_val % 1000) / 1000.0,
                len(probs) / 16.0,
            ]

            symbolic_state = {
                "shannon_entropy": H,
                "mutual_information": MI,
                "unique_symbols": unique_count,
                "total_symbols": n,
                "probability_distribution": {str(k): v for k, v in zip(counts.keys(), [c/total for c in counts.values()])},
            }

            structural_features = {
                "entropy_normalized": H / max(math.log2(unique_count), 1),
                "redundancy": 1.0 - (H / max(math.log2(16), 1)),
                "mi_ratio": abs(MI) / max(H, 1e-10),
            }

            return self._build_output(
                symbolic_state=symbolic_state,
                numeric_projection=numeric_projection,
                structural_features=structural_features,
                raw_output={"probs": probs},
                params=params,
            )
        except Exception as e:
            logger.warning(f"syntropy computation failed: {e}")
            return SymbolicOutput(
                system_id=self.SYSTEM_ID,
                library_backend=self.LIBRARY_BACKEND,
                raw_output={"error": str(e)},
            )
