"""igraph-based advanced graph metrics for oracle analysis."""
from __future__ import annotations
import logging
import numpy as np
from typing import Any

logger = logging.getLogger(__name__)

try:
    import igraph as ig
    HAS_IGRAPH = True
except Exception:
    HAS_IGRAPH = False

try:
    import networkx as nx
    HAS_NETWORKX = True
except Exception:
    HAS_NETWORKX = False


class IgraphMetrics:
    """Compute advanced graph metrics using igraph."""

    def __init__(self) -> None:
        self.igraph_available = HAS_IGRAPH
        self.networkx_available = HAS_NETWORKX

    def compute(self, nodes: list[str], edges: list[tuple[str, str]], weighted: bool = False) -> dict[str, Any]:
        if not self.igraph_available:
            return self._compute_networkx(nodes, edges) if self.networkx_available else {"method": "unavailable"}
        try:
            g = ig.Graph(directed=True)
            g.add_vertices(len(nodes))
            g.add_vertices(nodes)
            node_map = {n: i for i, n in enumerate(nodes)}
            edge_list = [(node_map[s], node_map[t]) for s, t in edges if s in node_map and t in node_map]
            g.add_edges(edge_list)
            result: dict[str, Any] = {"num_nodes": g.vcount(), "num_edges": g.ecount(),
                                       "density": round(g.density(), 4),
                                       "is_dag": g.is_dag()}
            try:
                clust = g.transitivity_avglocal_undirected()
                result["clustering_coefficient"] = round(float(clust), 4)
            except Exception:
                result["clustering_coefficient"] = 0.0
            try:
                if g.is_connected(mode="weak") or g.is_connected():
                    result["diameter"] = g.diameter()
                else:
                    components = g.connected_components(mode="weak")
                    result["diameter"] = max(c.diameter() for c in components) if components else 0
            except Exception:
                result["diameter"] = 0
            try:
                pr = g.pagerank()
                pr_dict = {nodes[i]: round(pr[i], 4) for i in range(min(len(nodes), len(pr)))}
                result["pagerank"] = dict(sorted(pr_dict.items(), key=lambda x: x[1], reverse=True)[:10])
            except Exception:
                result["pagerank"] = {}
            try:
                betweenness = g.betweenness()
                bt_dict = {nodes[i]: round(betweenness[i], 4) for i in range(min(len(nodes), len(betweenness)))}
                result["betweenness_centrality"] = dict(sorted(bt_dict.items(), key=lambda x: x[1], reverse=True)[:10])
            except Exception:
                result["betweenness_centrality"] = {}
            try:
                in_degree = g.degree(mode="in")
                out_degree = g.degree(mode="out")
                result["in_degree"] = {nodes[i]: in_degree[i] for i in range(min(len(nodes), len(in_degree)))}
                result["out_degree"] = {nodes[i]: out_degree[i] for i in range(min(len(nodes), len(out_degree)))}
            except Exception:
                result["in_degree"] = {}
                result["out_degree"] = {}
            return result
        except Exception as e:
            return {"method": "failed", "error": str(e)}

    def find_communities(self, nodes: list[str], edges: list[tuple[str, str]]) -> dict[str, Any]:
        if not self.igraph_available:
            return {"communities": [], "modularity": 0.0, "method": "unavailable"}
        try:
            g = ig.Graph(directed=False)
            g.add_vertices(nodes)
            g.add_edges(edges)
            try:
                comp = g.community_leading_eigenvector()
                communities = [sorted([nodes[i] for i in cluster]) for cluster in comp]
                return {"communities": communities, "num_communities": len(communities),
                        "modularity": round(float(comp.q), 4), "method": "leading_eigenvector"}
            except Exception:
                try:
                    comp = g.community_multilevel()
                    communities = [sorted([nodes[i] for i in cluster]) for cluster in comp]
                    return {"communities": communities, "num_communities": len(communities),
                            "modularity": round(float(comp.q), 4), "method": "multilevel"}
                except Exception:
                    return {"communities": [], "modularity": 0.0, "method": "failed"}
        except Exception as e:
            return {"communities": [], "modularity": 0.0, "method": "failed", "error": str(e)}

    def find_shortest_paths(self, nodes: list[str], edges: list[tuple[str, str]],
                            source: str, target: str) -> dict[str, Any]:
        if not self.igraph_available:
            return {"path": [], "distance": -1, "method": "unavailable"}
        try:
            g = ig.Graph(directed=True)
            g.add_vertices(nodes)
            g.add_edges(edges)
            source_idx = nodes.index(source) if source in nodes else -1
            target_idx = nodes.index(target) if target in nodes else -1
            if source_idx == -1 or target_idx == -1:
                return {"path": [], "distance": -1, "method": "node_not_found"}
            shortest = g.get_shortest_paths(source_idx, to=target_idx, output="vpath")
            if shortest and shortest[0]:
                path = [nodes[i] for i in shortest[0]]
                return {"path": path, "distance": len(path) - 1, "method": "dijkstra"}
            return {"path": [], "distance": -1, "method": "no_path"}
        except Exception as e:
            return {"path": [], "distance": -1, "method": "failed", "error": str(e)}

    def analyze_system_family(self, family_name: str, system_ids: list[str],
                              correlations: dict[tuple[str, str], float] | None = None) -> dict[str, Any]:
        edges = []
        if correlations:
            for (s1, s2), weight in correlations.items():
                if s1 in system_ids and s2 in system_ids and abs(weight) > 0.3:
                    edges.append((s1, s2))
        else:
            for i, s1 in enumerate(system_ids):
                for s2 in system_ids[i+1:]:
                    if np.random.random() > 0.5:
                        edges.append((s1, s2))
        metrics = self.compute(system_ids, edges)
        communities = self.find_communities(system_ids, edges)
        return {"family": family_name, "num_systems": len(system_ids),
                "num_edges": len(edges), "metrics": metrics, "communities": communities}

    def _compute_networkx(self, nodes: list[str], edges: list[tuple[str, str]]) -> dict[str, Any]:
        if not HAS_NETWORKX:
            return {"method": "unavailable"}
        try:
            G = nx.DiGraph()
            G.add_nodes_from(nodes)
            G.add_edges_from(edges)
            result = {"num_nodes": G.number_of_nodes(), "num_edges": G.number_of_edges(),
                      "density": round(nx.density(G), 4)}
            try:
                result["pagerank"] = {k: round(v, 4) for k, v in sorted(nx.pagerank(G).items(), key=lambda x: x[1], reverse=True)[:10]}
            except Exception:
                result["pagerank"] = {}
            return result
        except Exception:
            return {"method": "networkx_failed"}
