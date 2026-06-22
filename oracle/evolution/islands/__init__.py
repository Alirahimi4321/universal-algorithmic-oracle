"""Island model for parallel evolution."""
from .migration import MigrationManager
from .scheduler import IslandScheduler

__all__ = ["MigrationManager", "IslandScheduler"]
