"""Base class for all symbolic system wrappers."""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
import logging
import time

logger = logging.getLogger(__name__)


@dataclass
class SymbolicOutput:
    system_id: str
    library_backend: str
    symbolic_state: dict = field(default_factory=dict)
    numeric_projection: list[float] = field(default_factory=list)
    structural_features: dict = field(default_factory=dict)
    raw_output: dict = field(default_factory=dict)
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "system_id": self.system_id,
            "library_backend": self.library_backend,
            "symbolic_state": self.symbolic_state,
            "numeric_projection": self.numeric_projection,
            "structural_features": self.structural_features,
            "raw_output": self.raw_output,
            "metadata": self.metadata,
        }


class SymbolicSystemWrapper(ABC):
    SYSTEM_ID: str = "base"
    LIBRARY_BACKEND: str = "internal"

    @abstractmethod
    def compute(self, entropy_packet: dict, params: dict | None = None) -> SymbolicOutput:
        pass

    def _safe_compute(self, fn, *args, **kwargs):
        """Safely call a compute function with error handling."""
        try:
            return fn(*args, **kwargs)
        except Exception as e:
            logger.warning("Compute failed for %s: %s", self.SYSTEM_ID, e)
            return {"error": str(e)}

    def _build_output(
        self,
        symbolic_state: dict,
        numeric_projection: list[float],
        structural_features: dict,
        raw_output: dict | None = None,
        params: dict | None = None,
        call_context: dict | None = None,
    ) -> SymbolicOutput:
        return SymbolicOutput(
            system_id=self.SYSTEM_ID,
            library_backend=self.LIBRARY_BACKEND,
            symbolic_state=symbolic_state,
            numeric_projection=numeric_projection,
            structural_features=structural_features,
            raw_output=raw_output or {},
            metadata={
                "version": "0.2.0",
                "mutation_enabled": True,
                "params_used": params or {},
                "call_context": call_context or {"timestamp": time.time()},
            },
        )
