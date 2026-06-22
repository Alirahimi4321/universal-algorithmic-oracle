"""PyTarot library wrapper - tarot divination."""
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
    import pytarot
    HAS_PYTAROT = True
except ImportError:
    HAS_PYTAROT = False
    logger.info("pytarot not available")


@register_system
class PyTarotWrapper(SymbolicSystemWrapper):
    """Wrapper for PyTarot divination system."""
    SYSTEM_ID = "pytarot"
    LIBRARY_BACKEND = "pytarot"

    def __init__(self) -> None:
        self.available: bool = HAS_PYTAROT

    def compute(self, entropy_packet: dict, params: dict | None = None) -> SymbolicOutput:
        if not self.available:
            return SymbolicOutput(
                system_id=self.SYSTEM_ID,
                library_backend=self.LIBRARY_BACKEND,
                raw_output={"error": "pytarot not available"},
            )

        seed = entropy_packet.get("seed", 42)
        rng = random.Random(seed)

        try:
            results = {}

            try:
                wisdom = pytarot.get_answers_of_wisdom()
                results["answers_of_wisdom"] = wisdom
            except Exception:
                pass

            try:
                lucky = pytarot.get_lucky_day()
                results["lucky_day"] = lucky
            except Exception:
                pass

            try:
                action = pytarot.get_positive_action()
                results["positive_action"] = action
            except Exception:
                pass

            try:
                lover = pytarot.get_true_lover()
                results["true_lover"] = lover
            except Exception:
                pass

            all_values = []
            for key, val in results.items():
                if isinstance(val, (int, float)):
                    all_values.append(val)
                elif isinstance(val, str):
                    h = int(hashlib.md5(val.encode()).hexdigest()[:4], 16)
                    all_values.append(h)
                elif isinstance(val, dict):
                    for v in val.values():
                        if isinstance(v, (int, float)):
                            all_values.append(v)

            hash_val = int(hashlib.sha256(str(results).encode()).hexdigest()[:8], 16)

            numeric_projection = [
                (hash_val % 1000) / 1000.0,
                (sum(all_values) % 10000) / 10000.0 if all_values else rng.random(),
                len(results) / 4.0,
                rng.random(),
                rng.random(),
            ]

            symbolic_state = {
                "readings_count": len(results),
                "readings": {k: str(v)[:100] for k, v in results.items()},
                "has_wisdom": "answers_of_wisdom" in results,
                "has_lucky_day": "lucky_day" in results,
                "has_action": "positive_action" in results,
                "has_lover": "true_lover" in results,
            }

            structural_features = {
                "diversity": len(results) / 4.0,
                "complexity": len(str(results)) / 1000.0,
            }

            return self._build_output(
                symbolic_state=symbolic_state,
                numeric_projection=numeric_projection,
                structural_features=structural_features,
                raw_output=results,
                params=params,
            )
        except Exception as e:
            logger.warning(f"pytarot computation failed: {e}")
            return SymbolicOutput(
                system_id=self.SYSTEM_ID,
                library_backend=self.LIBRARY_BACKEND,
                raw_output={"error": str(e)},
            )
