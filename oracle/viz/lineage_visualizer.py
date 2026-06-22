"""Graphical lineage visualization using matplotlib and networkx.

Per design doc section 21.1: Lineage Graph visualization.
"""
import json
import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)

try:
    import networkx as nx
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    HAS_VIZ = True
except ImportError:
    HAS_VIZ = False
    logger.info("visualization dependencies not available")


class GraphicalLineageVisualizer:
    """Generates graphical lineage visualizations."""

    def __init__(self, output_dir: str = None):
        self.output_dir = output_dir
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)

    def render_lineage(
        self,
        nodes: dict,
        edges: list[dict],
        output_file: str = "lineage.png",
        title: str = "Oracle Lineage Graph",
        figsize: tuple = (16, 10),
        show_fitness: bool = True,
        color_by_generation: bool = True,
    ) -> Optional[str]:
        """Render a graphical lineage visualization."""
        if not HAS_VIZ:
            logger.warning("Visualization dependencies not available")
            return None

        G = nx.DiGraph()

        for node_id, node_data in nodes.items():
            G.add_node(node_id, **node_data)

        for edge in edges:
            G.add_edge(edge["from"], edge["to"], edge_type=edge.get("type", "evolved"))

        fig, ax = plt.subplots(1, 1, figsize=figsize)

        if color_by_generation:
            generations = [nodes[n].get("generation", 0) for n in G.nodes()]
            max_gen = max(generations) if generations else 1
            colors = [plt.cm.viridis(g / max(max_gen, 1)) for g in generations]
        else:
            colors = ["#4ECDC4" for _ in G.nodes()]

        fitnesses = [nodes[n].get("fitness", 0) for n in G.nodes()]
        max_fitness = max(fitnesses) if fitnesses else 1
        sizes = [300 + 700 * (f / max(max_fitness, 0.01)) for f in fitnesses]

        pos = nx.spring_layout(G, k=2, iterations=50, seed=42)

        nx.draw_networkx_edges(
            G, pos, ax=ax,
            edge_color="#888888",
            arrows=True,
            arrowsize=15,
            width=1.5,
            alpha=0.6,
            connectionstyle="arc3,rad=0.1",
        )

        node_collection = nx.draw_networkx_nodes(
            G, pos, ax=ax,
            node_color=colors,
            node_size=sizes,
            edgecolors="#333333",
            linewidths=1.5,
            alpha=0.9,
        )

        labels = {}
        for n in G.nodes():
            gen = nodes[n].get("generation", 0)
            fitness = nodes[n].get("fitness", 0)
            if show_fitness:
                labels[n] = f"g{gen}\nf={fitness:.2f}"
            else:
                labels[n] = f"g{gen}"

        nx.draw_networkx_labels(
            G, pos, labels, ax=ax,
            font_size=7,
            font_weight="bold",
            font_color="white",
        )

        fitness_patches = [
            mpatches.Patch(color=plt.cm.viridis(i / max(max_gen, 1)), label=f"Gen {i}")
            for i in range(min(max_gen + 1, 10))
        ]
        ax.legend(handles=fitness_patches, loc="upper left", fontsize=8)

        ax.set_title(title, fontsize=14, fontweight="bold")
        ax.axis("off")

        plt.tight_layout()

        if self.output_dir:
            filepath = os.path.join(self.output_dir, output_file)
        else:
            filepath = output_file

        plt.savefig(filepath, dpi=150, bbox_inches="tight", facecolor="white")
        plt.close(fig)

        logger.info("Lineage visualization saved to %s", filepath)
        return filepath

    def render_fitness_history(
        self,
        history: list[dict],
        output_file: str = "fitness_history.png",
        title: str = "Fitness Evolution History",
    ) -> Optional[str]:
        """Render fitness history over generations."""
        if not HAS_VIZ or not history:
            return None

        generations = [h.get("generation", i) for i, h in enumerate(history)]
        fitnesses = [h.get("avg_best_fitness", h.get("fitness", 0)) for h in history]
        max_fitnesses = [h.get("max_fitness", h.get("best", 0)) for h in history]

        fig, ax = plt.subplots(1, 1, figsize=(12, 6))

        ax.plot(generations, fitnesses, "o-", color="#4ECDC4", linewidth=2, markersize=4, label="Avg Best")
        if any(f > 0 for f in max_fitnesses):
            ax.plot(generations, max_fitnesses, "s--", color="#FF6B6B", linewidth=1.5, markersize=3, label="Max")

        ax.set_xlabel("Generation", fontsize=11)
        ax.set_ylabel("Fitness", fontsize=11)
        ax.set_title(title, fontsize=13, fontweight="bold")
        ax.legend()
        ax.grid(True, alpha=0.3)

        plt.tight_layout()

        if self.output_dir:
            filepath = os.path.join(self.output_dir, output_file)
        else:
            filepath = output_file

        plt.savefig(filepath, dpi=150, bbox_inches="tight", facecolor="white")
        plt.close(fig)

        logger.info("Fitness history saved to %s", filepath)
        return filepath

    def render_system_distribution(
        self,
        systems_usage: dict,
        output_file: str = "system_distribution.png",
        title: str = "Symbolic System Usage Distribution",
    ) -> Optional[str]:
        """Render a bar chart of system usage."""
        if not HAS_VIZ or not systems_usage:
            return None

        systems = sorted(systems_usage.keys(), key=lambda x: systems_usage[x], reverse=True)[:20]
        counts = [systems_usage[s] for s in systems]

        fig, ax = plt.subplots(1, 1, figsize=(12, 6))

        colors = plt.cm.Set3(range(len(systems)))
        bars = ax.barh(range(len(systems)), counts, color=colors)
        ax.set_yticks(range(len(systems)))
        ax.set_yticklabels(systems, fontsize=9)
        ax.set_xlabel("Usage Count", fontsize=11)
        ax.set_title(title, fontsize=13, fontweight="bold")
        ax.invert_yaxis()

        for bar, count in zip(bars, counts):
            ax.text(bar.get_width() + 0.5, bar.get_y() + bar.get_height()/2,
                    str(count), va="center", fontsize=9)

        plt.tight_layout()

        if self.output_dir:
            filepath = os.path.join(self.output_dir, output_file)
        else:
            filepath = output_file

        plt.savefig(filepath, dpi=150, bbox_inches="tight", facecolor="white")
        plt.close(fig)

        logger.info("System distribution saved to %s", filepath)
        return filepath

    def render_pareto_front(
        self,
        chromosomes: list[dict],
        output_file: str = "pareto_front.png",
        objective_x: str = "structural_coherence",
        objective_y: str = "response_stability",
        title: str = "Pareto Front - Multi-Objective Optimization",
    ) -> Optional[str]:
        """Render a Pareto front visualization."""
        if not HAS_VIZ or not chromosomes:
            return None

        x_vals = [c.get("fitness", {}).get(objective_x, 0) for c in chromosomes]
        y_vals = [c.get("fitness", {}).get(objective_y, 0) for c in chromosomes]
        fitness = [c.get("fitness", {}).get("total_fitness", 0) for c in chromosomes]

        fig, ax = plt.subplots(1, 1, figsize=(10, 8))

        scatter = ax.scatter(x_vals, y_vals, c=fitness, cmap="viridis", s=50, alpha=0.7, edgecolors="#333")
        plt.colorbar(scatter, ax=ax, label="Total Fitness")

        ax.set_xlabel(objective_x.replace("_", " ").title(), fontsize=11)
        ax.set_ylabel(objective_y.replace("_", " ").title(), fontsize=11)
        ax.set_title(title, fontsize=13, fontweight="bold")
        ax.grid(True, alpha=0.3)

        plt.tight_layout()

        if self.output_dir:
            filepath = os.path.join(self.output_dir, output_file)
        else:
            filepath = output_file

        plt.savefig(filepath, dpi=150, bbox_inches="tight", facecolor="white")
        plt.close(fig)

        logger.info("Pareto front saved to %s", filepath)
        return filepath
