"""Advanced community detection using infomap, leidenalg, and igraph."""
from __future__ import annotations

import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)

try:
    import infomap
    HAS_INFOMAP = True
except ImportError:
    HAS_INFOMAP = False
    logger.info("infomap not available")

try:
    import leidenalg
    import igraph
    HAS_LEIDEN = True
except ImportError:
    HAS_LEIDEN = False
    logger.info("leidenalg/igraph not available")

try:
    import networkx as nx
    HAS_NETWORKX = True
except ImportError:
    HAS_NETWORKX = False


class AdvancedCommunityDetector:
    """Advanced community detection using multiple algorithms."""

    def __init__(self) -> None:
        self.results_cache: dict[str, Any] = {}

    def detect_infomap(self, graph) -> list[set]:
        """Detect communities using Infomap algorithm."""
        if not HAS_INFOMAP:
            logger.warning("infomap not available")
            return []

        try:
            im = infomap.Infomap(silent=True)

            # Build node ID mapping for non-integer nodes
            if HAS_NETWORKX and isinstance(graph, (nx.Graph, nx.DiGraph)):
                node_list = list(graph.nodes())
                id_map = {node: i for i, node in enumerate(node_list)}
                for u, v, data in graph.edges(data=True):
                    weight = data.get("weight", 1.0)
                    im.add_link(id_map[u], id_map[v], weight)
            elif hasattr(graph, 'edges'):
                for u, v, data in graph.edges(data=True):
                    weight = data.get("weight", 1.0)
                    im.add_link(int(u), int(v), weight)

            im.run()

            # Map back to original node IDs
            communities = {}
            for node in im.nodes:
                module_id = node.module_id
                node_id = node.node_id
                if module_id not in communities:
                    communities[module_id] = set()
                if HAS_NETWORKX and isinstance(graph, (nx.Graph, nx.DiGraph)):
                    reverse_map = {i: nd for nd, i in id_map.items()}
                    communities[module_id].add(reverse_map.get(node_id, node_id))
                else:
                    communities[module_id].add(node_id)

            return list(communities.values())
        except Exception as e:
            logger.warning(f"Infomap failed: {e}")
            return []

    def detect_leiden(self, graph, resolution: float = 1.0) -> list[set]:
        """Detect communities using Leiden algorithm."""
        if not HAS_LEIDEN:
            logger.warning("leidenalg not available")
            return []

        try:
            if HAS_NETWORKX and isinstance(graph, (nx.Graph, nx.DiGraph)):
                ig_graph = igraph.Graph.from_networkx(graph)
            elif hasattr(graph, 'edges'):
                ig_graph = graph
            else:
                return []

            partition = leidenalg.find_partition(
                ig_graph,
                leidenalg.RBConfigurationVertexPartition,
                resolution_parameter=resolution,
            )

            communities = []
            for community in partition:
                communities.append(set(community))

            return communities
        except Exception as e:
            logger.warning(f"Leiden failed: {e}")
            return []

    def compare_algorithms(self, graph: Any) -> dict[str, Any]:
        """Compare community detection results from multiple algorithms."""
        results = {}

        if HAS_NETWORKX and isinstance(graph, (nx.Graph, nx.DiGraph)):
            # Louvain
            try:
                louvain_communities = nx.community.louvain_communities(graph, seed=42)
                results["louvain"] = [set(c) for c in louvain_communities]
                results["louvain_modularity"] = nx.community.modularity(graph, results["louvain"])
            except Exception as e:
                logger.warning(f"Louvain failed: {e}")

            # Girvan-Newman (limited depth)
            try:
                gn_communities = nx.community.girvan_newman(graph)
                top_level = next(gn_communities)
                results["girvan_newman"] = [set(c) for c in top_level]
                results["girvan_newman_modularity"] = nx.community.modularity(graph, results["girvan_newman"])
            except Exception as e:
                logger.warning(f"Girvan-Newman failed: {e}")

        # Infomap
        infomap_result = self.detect_infomap(graph)
        if infomap_result:
            results["infomap"] = infomap_result

        # Leiden
        leiden_result = self.detect_leiden(graph)
        if leiden_result:
            results["leiden"] = leiden_result

        return results

    def find_optimal_partition(self, graph: Any) -> list[set[Any]]:
        """Find the best partition using modularity comparison."""
        results = self.compare_algorithms(graph)

        best_partition = None
        best_modularity = -1

        for algo_name, partition in results.items():
            if isinstance(partition, list) and len(partition) > 0:
                if isinstance(partition[0], set):
                    try:
                        if HAS_NETWORKX and isinstance(graph, (nx.Graph, nx.DiGraph)):
                            mod = nx.community.modularity(graph, partition)
                            if mod > best_modularity:
                                best_modularity = mod
                                best_partition = partition
                    except Exception:
                        pass

        return best_partition or []
