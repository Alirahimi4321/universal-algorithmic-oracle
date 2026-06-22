"""Graph analysis of system relations using networkx, infomap, leidenalg."""
from __future__ import annotations

import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)

try:
    import networkx as nx
    HAS_NETWORKX = True
except ImportError:
    HAS_NETWORKX = False
    logger.info("networkx not available")

try:
    from .community_detection import AdvancedCommunityDetector
    HAS_ADVANCED_COMMUNITY = True
except ImportError:
    HAS_ADVANCED_COMMUNITY = False


SYSTEM_FAMILIES = {
    "astrology": ["astrology_western", "astrology_vedic", "astrology_kerykeion",
                   "skyfield_astro", "yaegi_kundali", "yaegi_panchang"],
    "calendrical": ["calendar", "lunar_calendar", "hijri_calendar", "jalali_calendar"],
    "gematria": ["gematria", "hebrew_gematria", "hebrew_gematria_advanced",
                  "english_gematria", "numerology"],
    "binary": ["iching", "iching_shifa", "geomancy", "raml"],
    "cards": ["tarot", "tarot_oracle", "runes", "lenormand"],
    "eastern": ["bazi", "ziwei", "qimen", "tianji_bazi", "tianji_ziwei",
                 "tianji_qimen", "tianji_liuren", "korean_saju"],
    "mayan": ["tzolkin", "long_count", "pohualli_calendar"],
    "other": ["dream_symbols", "fortune_telling_core"],
}


class SystemGraphAnalyzer:
    """Analyzes relationships between symbolic systems using graph theory."""

    def __init__(self) -> None:
        self.graph: Optional[nx.DiGraph] = None

    def build_graph(self, system_correlations: dict[str, dict[str, float]], threshold: float = 0.1) -> 'Optional[nx.DiGraph]':
        """Build a directed graph from system correlation data."""
        if not HAS_NETWORKX:
            logger.warning("networkx not available")
            return None

        G = nx.DiGraph()

        all_systems = set()
        for sys_a, correlations in system_correlations.items():
            all_systems.add(sys_a)
            for sys_b, mi_value in correlations.items():
                all_systems.add(sys_b)

        for sys_name in all_systems:
            family = self._get_family(sys_name)
            G.add_node(sys_name, family=family)

        for sys_a, correlations in system_correlations.items():
            for sys_b, mi_value in correlations.items():
                if sys_a != sys_b and abs(mi_value) > threshold:
                    G.add_edge(sys_a, sys_b, weight=abs(mi_value), mi=mi_value)

        self.graph = G
        return G

    def find_communities(self) -> list[set]:
        """Detect communities (groups of related systems) using multiple algorithms."""
        if not HAS_NETWORKX or self.graph is None:
            return []

        # Try advanced community detection first
        if HAS_ADVANCED_COMMUNITY:
            try:
                detector = AdvancedCommunityDetector()
                result = detector.find_optimal_partition(self.graph)
                if result:
                    return result
            except Exception as e:
                logger.warning(f"Advanced community detection failed: {e}")

        # Fallback to Louvain
        try:
            undirected = self.graph.to_undirected()
            communities = nx.community.louvain_communities(undirected, seed=42)
            return [set(c) for c in communities]
        except Exception as e:
            logger.warning(f"Louvain community detection failed: {e}")
            return []

    def find_central_systems(self, top_n: int = 5) -> list[tuple[str, float]]:
        """Find the most central (important) systems using betweenness centrality."""
        if not HAS_NETWORKX or self.graph is None:
            return []

        try:
            centrality = nx.betweenness_centrality(self.graph)
            sorted_central = sorted(centrality.items(), key=lambda x: x[1], reverse=True)
            return sorted_central[:top_n]
        except Exception as e:
            logger.warning(f"Centrality computation failed: {e}")
            return []

    def find_redundant_systems(self, threshold: float = 0.8) -> list[tuple[str, str, float]]:
        """Find pairs of systems with very high correlation (potentially redundant)."""
        if not HAS_NETWORKX or self.graph is None:
            return []

        redundant = []
        for u, v, data in self.graph.edges(data=True):
            mi = abs(data.get("mi", 0))
            if mi > threshold:
                redundant.append((u, v, mi))

        return sorted(redundant, key=lambda x: x[2], reverse=True)

    def suggest_optimal_subset(self, max_systems: int = 10) -> list[str]:
        """Suggest an optimal subset of systems that maximizes diversity and minimizes redundancy."""
        if not HAS_NETWORKX or self.graph is None:
            return []

        try:
            centrality = nx.betweenness_centrality(self.graph)
            communities = self.find_communities()

            selected = []
            if communities:
                for community in communities:
                    best_in_community = max(community, key=lambda s: centrality.get(s, 0))
                    selected.append(best_in_community)
                    if len(selected) >= max_systems:
                        break

            remaining = sorted(
                [s for s in centrality if s not in selected],
                key=lambda s: centrality.get(s, 0),
                reverse=True,
            )
            for s in remaining:
                if len(selected) >= max_systems:
                    break
                selected.append(s)

            return selected
        except Exception as e:
            logger.warning(f"Optimal subset suggestion failed: {e}")
            return []

    def get_stats(self) -> dict[str, Any]:
        """Get graph statistics."""
        if not HAS_NETWORKX or self.graph is None:
            return {}

        G = self.graph
        return {
            "num_nodes": G.number_of_nodes(),
            "num_edges": G.number_of_edges(),
            "density": nx.density(G),
            "num_communities": len(self.find_communities()),
            "avg_clustering": nx.average_clustering(G.to_undirected()) if G.number_of_nodes() > 0 else 0,
        }

    def _get_family(self, system_name: str) -> str:
        for family, systems in SYSTEM_FAMILIES.items():
            if system_name in systems:
                return family
        return "unknown"
