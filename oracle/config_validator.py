"""Configuration schema validation for the oracle package."""
import yaml
import logging
from pathlib import Path

logger = logging.getLogger("oracle.config")

REQUIRED_FIELDS = {
    "systems": dict,
}

VALID_ENGINE_TYPES = ["ga", "gp", "nsga", "stochopy", "psopy", "evogine", "cma", "bayesian"]

def validate_systems_config(path: str | Path) -> dict:
    """Validate systems.yaml and return parsed config."""
    path = Path(path)
    if not path.exists():
        logger.warning("Config file not found: %s", path)
        return {}
    
    with open(path) as f:
        data = yaml.safe_load(f)
    
    if not isinstance(data, dict):
        logger.error("Config must be a YAML dict, got %s", type(data).__name__)
        return {}
    
    if "systems" not in data:
        logger.error("Config missing required 'systems' key")
        return {}
    
    for name, cfg in data["systems"].items():
        if not isinstance(cfg, dict):
            logger.warning("System '%s' config is not a dict, skipping", name)
            continue
        if "features" not in cfg:
            logger.warning("System '%s' missing 'features' key", name)
    
    return data

def validate_evolution_config(config: dict) -> dict:
    """Validate evolution configuration with defaults."""
    defaults = {
        "population_size": 30,
        "max_generations": 100,
        "mutation_rate": 0.15,
        "method": "cmaes",
    }
    validated = {**defaults, **config}
    
    if validated["population_size"] < 5:
        logger.warning("population_size too small, setting to 5")
        validated["population_size"] = 5
    
    if not (0.0 <= validated["mutation_rate"] <= 1.0):
        logger.warning("mutation_rate out of range [0,1], setting to 0.15")
        validated["mutation_rate"] = 0.15
    
    return validated
