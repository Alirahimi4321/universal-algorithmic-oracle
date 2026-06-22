"""Sigillin library wrapper - sigil/symbol processing."""
from __future__ import annotations

import hashlib
import json
import logging
import math
import os
import random
import tempfile
from typing import Optional

from ..base import SymbolicOutput, SymbolicSystemWrapper
from ..registry import register_system

logger = logging.getLogger(__name__)

try:
    from sigillin import Sigil
    HAS_SIGILLIN = True
except ImportError:
    HAS_SIGILLIN = False
    logger.info("sigillin not available")


@register_system
class SigillinWrapper(SymbolicSystemWrapper):
    """Wrapper for sigil/symbol processing using sigillin library."""
    SYSTEM_ID = "sigillin_sigil"
    LIBRARY_BACKEND = "sigillin"

    def __init__(self) -> None:
        self.available: bool = HAS_SIGILLIN

    def compute(self, entropy_packet: dict, params: dict | None = None) -> SymbolicOutput:
        if not self.available:
            return SymbolicOutput(
                system_id=self.SYSTEM_ID,
                library_backend=self.LIBRARY_BACKEND,
                raw_output={"error": "sigillin not available"},
            )

        seed = entropy_packet.get("seed", 42)
        rng = random.Random(seed)

        try:
            sigil_data = {
                "seed": seed,
                "entropy_hash": entropy_packet.get("sha_stream", str(seed))[:64],
                "timestamp": entropy_packet.get("timestamp", 0),
                "question_hash": hashlib.md5(str(entropy_packet.get("question", "")).encode()).hexdigest(),
            }

            tmp_dir = tempfile.mkdtemp()
            sigil_path = os.path.join(tmp_dir, "temp_sigil.yaml")

            yaml_content = f"""
name: oracle_sigil_{seed}
seed: {seed}
components:
  - type: entropy
    value: {sigil_data['entropy_hash'][:16]}
  - type: temporal
    value: {sigil_data['timestamp']}
  - type: semantic
    value: {sigil_data['question_hash'][:16]}
"""
            with open(sigil_path, "w") as f:
                f.write(yaml_content)

            sigil = Sigil(sigil_path)

            mandala = None
            if hasattr(sigil, 'render_mandala'):
                try:
                    mandala = sigil.render_mandala()
                except Exception:
                    mandala = None

            hash_val = int(hashlib.sha256(json.dumps(sigil_data).encode()).hexdigest()[:8], 16)

            numeric_projection = [
                (hash_val % 1000) / 1000.0,
                rng.random(),
                (seed % 1000) / 1000.0,
                rng.random(),
                rng.random(),
            ]

            has_mandala = mandala is not None

            symbolic_state = {
                "sigil_created": True,
                "seed": seed,
                "has_mandala": has_mandala,
                "components_count": 3,
            }

            structural_features = {
                "complexity": 3 / 5.0,
                "symmetry": 0.5,
            }

            try:
                os.unlink(sigil_path)
                os.rmdir(tmp_dir)
            except Exception:
                pass

            mandala_str = None
            if mandala is not None:
                try:
                    mandala_str = str(mandala)[:500]
                except Exception:
                    mandala_str = "numpy_array"

            return self._build_output(
                symbolic_state=symbolic_state,
                numeric_projection=numeric_projection,
                structural_features=structural_features,
                raw_output={"mandala": mandala_str},
                params=params,
            )
        except Exception as e:
            logger.warning(f"sigillin computation failed: {e}")
            return SymbolicOutput(
                system_id=self.SYSTEM_ID,
                library_backend=self.LIBRARY_BACKEND,
                raw_output={"error": str(e)},
            )
