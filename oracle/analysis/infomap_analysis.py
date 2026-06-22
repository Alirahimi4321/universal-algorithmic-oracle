"""Community Detection on networks using infomap."""
import logging

logger = logging.getLogger(__name__)

HAS_INFOMAP = False
try:
    import infomap as infomap_lib
    HAS_INFOMAP = True
except ImportError:
    pass


class InfomapAnalyzer:
    """Community detection using the InfoMap algorithm."""

    def __init__(self):
        self.available = HAS_INFOMAP

    def find_communities(self, edges: list[tuple], num_trials: int = 10) -> dict:
        if not self.available:
            return {"error": "infomap not available"}
        try:
            im = infomap_lib.Infomap(silent=True, two_level=True, num_trials=num_trials)
            for src, dst in edges:
                im.add_link(int(src), int(dst))
            im.run()
            communities = {}
            for node in im.nodes:
                module = im.get_modules()[node] if hasattr(im, 'get_modules') else 0
                if module not in communities:
                    communities[module] = []
                communities[module].append(node)
            return {
                "num_communities": len(communities),
                "communities": {str(k): v for k, v in communities.items()},
                "codelength": im.codelength if hasattr(im, 'codelength') else 0,
                "num_nodes": len(im.nodes) if hasattr(im, 'nodes') else 0,
                "num_edges": len(edges),
            }
        except Exception as e:
            return {"error": str(e)}
