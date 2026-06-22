"""Bayesian Network analysis using bnlearn."""
import logging

logger = logging.getLogger(__name__)

HAS_BNLEARN = False
try:
    import bnlearn as bn
    HAS_BNLEARN = True
except ImportError:
    pass


class BNLearnAnalyzer:
    """Bayesian network structure learning, parameter learning, and inference."""

    def __init__(self):
        self.available = HAS_BNLEARN
        self.model = None

    def learn_structure(self, data: list[dict]) -> dict:
        if not self.available:
            return {"error": "bnlearn not available"}
        try:
            import pandas as pd
            df = pd.DataFrame(data)
            model = bn.structure_learning.fit(df, methodtype="hc", scoretype="bic")
            self.model = model
            return {
                "edges": model.get("edges", []),
                "nodes": model.get("nodes", []),
                "score": model.get("score", 0),
                "learning_method": "hill_climbing",
            }
        except Exception as e:
            return {"error": str(e)}

    def parameter_learning(self, data: list[dict], structure: dict = None) -> dict:
        if not self.available:
            return {"error": "bnlearn not available"}
        try:
            import pandas as pd
            df = pd.DataFrame(data)
            if structure and self.model is None:
                self.model = bn.make_DAG(structure.get("edges", []))
            if self.model is None:
                return {"error": "no model available"}
            self.model = bn.parameter_learning.fit(self.model, df, methodtype="bayes")
            return {"status": "success", "model_updated": True}
        except Exception as e:
            return {"error": str(e)}

    def inference(self, query: dict, evidence: dict = None) -> dict:
        if not self.available or self.model is None:
            return {"error": "no model available"}
        try:
            from pgmpy.inference import VariableElimination
            inference = VariableElimination(self.model.get("model", self.model))
            result = inference.query(query.get("variables", []), evidence=evidence or {})
            return {"result": str(result), "query": query, "evidence": evidence}
        except Exception as e:
            return {"error": str(e)}
