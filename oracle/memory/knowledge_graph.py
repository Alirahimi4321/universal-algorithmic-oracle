"""Knowledge Graph using rdflib for storing oracle knowledge with SPARQL queries."""
from __future__ import annotations
import logging
from typing import Any

logger = logging.getLogger(__name__)

try:
    from rdflib import Graph, Literal, Namespace, URIRef, BNode
    from rdflib.namespace import RDF, RDFS, FOAF
    HAS_RDFLIB = True
except Exception:
    HAS_RDFLIB = False

ORACLE_NS = Namespace("http://oracle.ai/ontology/")
SYSTEM_NS = Namespace("http://oracle.ai/system/")
PREDICTION_NS = Namespace("http://oracle.ai/prediction/")


class KnowledgeGraph:
    """Graph-based knowledge storage for oracle entities and relationships."""

    def __init__(self) -> None:
        self.available = HAS_RDFLIB
        self._graph: Graph | None = None
        if HAS_RDFLIB:
            self._graph = Graph()
            self._graph.bind("oracle", ORACLE_NS)
            self._graph.bind("system", SYSTEM_NS)
            self._graph.bind("prediction", PREDICTION_NS)

    def add_knowledge(self, subject: str, predicate: str, obj: str, subject_type: str = "Entity") -> bool:
        if not self.available or self._graph is None:
            return False
        s = URIRef(subject) if subject.startswith("http") else ORACLE_NS[subject.replace(" ", "_")]
        p = URIRef(predicate) if predicate.startswith("http") else ORACLE_NS[predicate.replace(" ", "_")]
        o = URIRef(obj) if obj.startswith("http") else ORACLE_NS[obj.replace(" ", "_")]
        self._graph.add((s, p, o))
        return True

    def add_literal(self, subject: str, predicate: str, value: Any, datatype: str = "string") -> bool:
        if not self.available or self._graph is None:
            return False
        s = URIRef(subject) if subject.startswith("http") else ORACLE_NS[subject.replace(" ", "_")]
        p = URIRef(predicate) if predicate.startswith("http") else ORACLE_NS[predicate.replace(" ", "_")]
        self._graph.add((s, p, Literal(value)))
        return True

    def add_system(self, system_id: str, properties: dict[str, Any]) -> bool:
        if not self.available or self._graph is None:
            return False
        s = SYSTEM_NS[system_id]
        self._graph.add((s, RDF.type, ORACLE_NS.SymbolicSystem))
        for k, v in properties.items():
            self._graph.add((s, ORACLE_NS[k], Literal(str(v))))
        return True

    def add_prediction(self, prediction_id: str, system_id: str, confidence: float, question: str) -> bool:
        if not self.available or self._graph is None:
            return False
        p = PREDICTION_NS[prediction_id]
        self._graph.add((p, RDF.type, ORACLE_NS.Prediction))
        self._graph.add((p, ORACLENS_usedSystem, SYSTEM_NS[system_id]))
        self._graph.add((p, ORACLE_NS.confidence, Literal(confidence)))
        self._graph.add((p, ORACLE_NS.question, Literal(question)))
        return True

    def query(self, sparql: str) -> list[dict[str, Any]]:
        if not self.available or self._graph is None:
            return []
        try:
            results = self._graph.query(sparql)
            return [dict(row) for row in results.bindings]
        except Exception as e:
            logger.warning(f"SPARQL query failed: {e}")
            return []

    def get_system_relationships(self, system_id: str) -> dict[str, list[str]]:
        if not self.available or self._graph is None:
            return {}
        s = SYSTEM_NS[system_id]
        relationships = {}
        for p, o in self._graph.predicate_objects(s):
            pred_name = str(p).split("/")[-1]
            if pred_name not in relationships:
                relationships[pred_name] = []
            relationships[pred_name].append(str(o))
        return relationships

    def get_all_systems(self) -> list[str]:
        if not self.available or self._graph is None:
            return []
        systems = []
        for s, _, _ in self._graph.triples((None, RDF.type, ORACLE_NS.SymbolicSystem)):
            systems.append(str(s).split("/")[-1])
        return systems

    def get_statistics(self) -> dict[str, int]:
        if not self.available or self._graph is None:
            return {"triples": 0}
        return {"triples": len(self._graph), "subjects": len(set(s for s, _, _ in self._graph)),
                "predicates": len(set(p for _, p, _ in self._graph)),
                "objects": len(set(o for _, _, o in self._graph))}

    def export_turtle(self) -> str:
        if not self.available or self._graph is None:
            return ""
        return self._graph.serialize(format="turtle")

    def export_jsonld(self) -> str:
        if not self.available or self._graph is None:
            return ""
        return self._graph.serialize(format="json-ld")
