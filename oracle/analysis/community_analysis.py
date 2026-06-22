"""Community detection using python-louvain."""
import logging

logger = logging.getLogger(__name__)

HAS_LOUVAIN = False
try:
    import community as community_louvain
    import networkx as nx
    HAS_LOUVAIN = True
except ImportError:
    pass


class CommunityAnalyzer:
    """Detect communities in graphs using Louvain method."""

    def __init__(self):
        self.available = HAS_LOUVAIN

    def detect_communities(self, edges: list[tuple], n_nodes: int = None) -> dict:
        if not self.available:
            return {"error": "python-louvain not available"}
        try:
            G = nx.Graph()
            G.add_edges_from(edges)
            if n_nodes:
                G.add_nodes_from(range(n_nodes))

            partition = community_louvain.best_partition(G)
            modularity = community_louvain.modularity(partition, G)

            communities = {}
            for node, comm_id in partition.items():
                communities.setdefault(comm_id, []).append(node)

            return {
                "num_communities": len(communities),
                "modularity": float(modularity),
                "partition": {str(k): v for k, v in communities.items()},
                "num_nodes": G.number_of_nodes(),
                "num_edges": G.number_of_edges(),
            }
        except Exception as e:
            logger.warning("louvain failed: %s", e)
            return {"error": str(e)}

    def analyze(self, data: dict) -> dict:
        edges = [tuple(e) for e in data.get("edges", [])]
        n_nodes = data.get("n_nodes")
        return self.detect_communities(edges, n_nodes)
