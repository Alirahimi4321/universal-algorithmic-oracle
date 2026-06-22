"""Universal Algorithmic Oracle."""
import logging

logger = logging.getLogger("oracle")

from .logging_config import setup_logging
setup_logging()


def __getattr__(name: str):
    if name == "OraclePipeline":
        from .runtime.executor import OraclePipeline
        return OraclePipeline
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = ["OraclePipeline", "list_systems", "compute_system"]


def list_systems():
    from .symbolic.registry import list_systems
    return list_systems()


def compute_system(*args, **kwargs):
    from .symbolic.registry import compute_system
    return compute_system(*args, **kwargs)
