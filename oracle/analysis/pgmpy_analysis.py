"""Bayesian Network analysis using pgmpy."""
import logging

logger = logging.getLogger(__name__)

HAS_PGMPY = False
try:
    from pgmpy.models import BayesianNetwork
    from pgmpy.estimators import HillClimbSearch, BicScore, MaximumLikelihoodEstimator
    from pgmpy.inference import VariableElimination
    HAS_PGMPY = True
except ImportError:
    pass


class BayesianAnalyzer:
    """Bayesian network structure learning and inference."""

    def __init__(self):
        self.available = HAS_PGMPY
        self.model = None

    def learn_structure(self, data: list[dict], variables: list[str] = None) -> dict:
        if not self.available:
            return {"error": "pgmpy not available"}
        try:
            import pandas as pd
            df = pd.DataFrame(data)
            hc = HillClimbSearch(df)
            best_model = hc.estimate(scoring_method=BicScore(df), max_indegree=4, max_iter=100)
            edges = list(best_model.edges())
            self.model = BayesianNetwork(edges)
            self.model.fit(df, estimator=MaximumLikelihoodEstimator)

            return {
                "edges": edges,
                "num_nodes": len(best_model.nodes()),
                "num_edges": len(edges),
                "nodes": list(best_model.nodes()),
            }
        except Exception as e:
            logger.warning("pgmpy learn failed: %e", e)
            return {"error": str(e)}

    def infer(self, variable: str, evidence: dict = None) -> dict:
        if not self.available or self.model is None:
            return {"error": "model not available"}
        try:
            inference = VariableElimination(self.model)
            result = inference.query([variable], evidence=evidence or {})
            return {
                "variable": variable,
                "evidence": evidence or {},
                "values": {str(state): float(prob) for state, prob in zip(result.state_names[variable], result.values)},
            }
        except Exception as e:
            return {"error": str(e)}

    def analyze(self, data: dict) -> dict:
        evidence = data.get("evidence", {})
        variables = data.get("variables", [])
        edges = data.get("edges", [])

        if edges:
            try:
                self.model = BayesianNetwork(edges)
                import pandas as pd
                df = pd.DataFrame(data.get("data", []))
                self.model.fit(df, estimator=MaximumLikelihoodEstimator)
                return {"edges": edges, "fitted": True}
            except Exception:
                pass

        if data.get("data"):
            return self.learn_structure(data["data"], variables)

        return {"error": "no data or edges provided"}
