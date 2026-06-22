"""Bayesian Network Predictor using bnlearn for probabilistic modeling."""
from __future__ import annotations
import logging
import numpy as np
from typing import Any

logger = logging.getLogger(__name__)

try:
    import bnlearn as bn
    import pandas as pd
    HAS_BNLEARN = True
except Exception:
    HAS_BNLEARN = False


class BayesianNetworkPredictor:
    """Build and query Bayesian networks from symbolic system outputs."""

    def __init__(self) -> None:
        self.available = HAS_BNLEARN
        self._model = None

    def build_network(self, system_outputs: dict[str, list[float]], bins: int = 5) -> dict[str, Any]:
        if not self.available:
            return {"structure": {}, "method": "unavailable"}
        systems = list(system_outputs.keys())
        min_len = min(len(v) for v in system_outputs.values())
        if min_len < 10:
            return {"structure": {}, "method": "insufficient_data"}
        data_dict = {}
        for s in systems:
            vals = np.array(system_outputs[s][:min_len], dtype=float)
            data_dict[s] = pd.cut(vals, bins=bins, labels=[f"{s}_{i}" for i in range(bins)]).astype(str)
        df = pd.DataFrame(data_dict)
        try:
            model = bn.structure_learning.fit(df, methodtype="hc", scoretype="bic")
            self._model = model
            return {"edges": model.get("model_edges", []), "score": model.get("score", 0),
                    "method": "hill_climbing", "num_variables": len(systems),
                    "num_edges": len(model.get("model_edges", []))}
        except Exception as e:
            return {"structure": {}, "method": "failed", "error": str(e)}

    def query(self, evidence: dict[str, str], target: str) -> dict[str, Any]:
        if not self.available or self._model is None:
            return {"probability": {}, "method": "unavailable"}
        try:
            result = bn.inference.fit(self._model, variables=[target], evidence=evidence, verbose=0)
            probs = result.values if hasattr(result, "values") else []
            return {"target": target, "evidence": evidence, "probabilities": probs.tolist() if hasattr(probs, "tolist") else list(probs), "method": "variable_elimination"}
        except Exception as e:
            return {"target": target, "method": "failed", "error": str(e)}
