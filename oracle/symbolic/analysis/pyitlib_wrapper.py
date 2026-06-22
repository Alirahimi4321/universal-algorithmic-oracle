"""Pyitlib wrapper - information theory calculations (entropy, mutual info, divergence)."""
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
    from pyitlib import discrete_random_variable as drv
    import numpy as np
    HAS_PYITLIB = True
except ImportError:
    HAS_PYITLIB = False
    logger.info("pyitlib not available")


@register_system
class PyitlibWrapper(SymbolicSystemWrapper):
    """Wrapper for information theory analysis using pyitlib."""
    SYSTEM_ID = "pyitlib_info"
    LIBRARY_BACKEND = "pyitlib"

    def __init__(self) -> None:
        self.available: bool = HAS_PYITLIB

    def compute(self, entropy_packet: dict, params: dict | None = None) -> SymbolicOutput:
        if not self.available:
            return SymbolicOutput(
                system_id=self.SYSTEM_ID,
                library_backend=self.LIBRARY_BACKEND,
                numeric_projection=[0.0] * 5,
                raw_output={"error": "pyitlib not available"},
            )

        seed = entropy_packet.get("seed", 42)
        rng = random.Random(seed)

        sha_stream = entropy_packet.get("sha_stream", "")
        bitstream = entropy_packet.get("bitstream", "")

        try:
            if sha_stream:
                data = np.array([int(c, 16) for c in sha_stream[:32]], dtype=int)
            elif bitstream:
                data = np.array([int(c) for c in bitstream[:64]], dtype=int)
            else:
                data = np.array([rng.randint(0, 15) for _ in range(32)], dtype=int)

            H = float(drv.entropy(data))

            data1 = data[:len(data)//2] if len(data) > 1 else data
            data2 = data[len(data)//2:] if len(data) > 1 else data
            if len(data1) != len(data2):
                min_len = min(len(data1), len(data2))
                data1 = data1[:min_len]
                data2 = data2[:min_len]

            MI = float(drv.information_mutual(data1, data2)) if len(data1) > 0 else 0.0

            unique_vals = np.unique(data)
            pmf = np.array([np.sum(data == v) / len(data) for v in unique_vals])

            hash_val = int(hashlib.sha256(data.tobytes()).hexdigest()[:8], 16)

            numeric_projection = [
                min(H / 4.0, 1.0),
                min(abs(MI) / 2.0, 1.0),
                len(unique_vals) / 16.0,
                (hash_val % 1000) / 1000.0,
                float(np.std(data)) / 8.0,
            ]

            symbolic_state = {
                "entropy": H,
                "mutual_information": MI,
                "unique_values": int(len(unique_vals)),
                "data_length": len(data),
                "mean": float(np.mean(data)),
                "std": float(np.std(data)),
                "min": int(np.min(data)),
                "max": int(np.max(data)),
            }

            structural_features = {
                "information_density": H / max(math.log2(len(unique_vals)), 1),
                "redundancy": 1.0 - (H / max(math.log2(16), 1)),
                "uniformity": float(1.0 - np.std(pmf)) if len(pmf) > 0 else 0,
            }

            return self._build_output(
                symbolic_state=symbolic_state,
                numeric_projection=numeric_projection,
                structural_features=structural_features,
                raw_output={"pmf": pmf.tolist()},
                params=params,
            )
        except Exception as e:
            logger.warning(f"pyitlib computation failed: {e}")
            return SymbolicOutput(
                system_id=self.SYSTEM_ID,
                library_backend=self.LIBRARY_BACKEND,
                numeric_projection=[0.0] * 5,
                raw_output={"error": str(e)},
            )
