"""Visualization utilities for oracle results."""
import json
import logging
import os
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.ticker as ticker
    HAS_MATPLOTLIB = True
except ImportError:
    plt = None
    HAS_MATPLOTLIB = False
    logger.info("matplotlib not available, plotting disabled")

try:
    from jinja2 import Template
    HAS_JINJA2 = True
except ImportError:
    Template = None
    HAS_JINJA2 = False
    logger.info("jinja2 not available, HTML reports disabled")


def format_ascii_bar_chart(data: dict, width: int = 40) -> str:
    """Create ASCII bar chart from dictionary of values."""
    if not data:
        return ""

    max_val = max(abs(v) for v in data.values() if isinstance(v, (int, float)))
    if max_val == 0:
        max_val = 1

    lines = []
    for key, value in data.items():
        if not isinstance(value, (int, float)):
            continue
        bar_len = int(abs(value) / max_val * width)
        bar = "\u2588" * bar_len
        lines.append(f"{key:>25s} | {bar} {value:.3f}")

    return "\n".join(lines)


def format_population_stats(population: list, generation: int) -> str:
    """Format population statistics as ASCII text."""
    if not population:
        return "Empty population"

    fitnesses = []
    for ind in population:
        if hasattr(ind, 'fitness'):
            f = ind.fitness
            if isinstance(f, dict):
                fitnesses.append(f.get("structural_coherence", 0))
            elif isinstance(f, (int, float)):
                fitnesses.append(f)

    if not fitnesses:
        return f"Generation {generation}: {len(population)} individuals, no fitness data"

    avg_fit = sum(fitnesses) / len(fitnesses)
    max_fit = max(fitnesses)
    min_fit = min(fitnesses)

    lines = [
        f"Generation {generation} Stats:",
        f"  Population: {len(population)}",
        f"  Avg Fitness: {avg_fit:.4f}",
        f"  Max Fitness: {max_fit:.4f}",
        f"  Min Fitness: {min_fit:.4f}",
        f"  Fitness Spread: {max_fit - min_fit:.4f}",
    ]

    return "\n".join(lines)


def format_system_distribution(population: list) -> str:
    """Show distribution of symbolic systems across population."""
    system_counts = {}
    total_genes = 0
    for ind in population:
        genes = list(ind.genes.values()) if isinstance(ind.genes, dict) else list(ind.genes)
        for gene in genes:
            system_counts[gene.system_id] = system_counts.get(gene.system_id, 0) + 1
            total_genes += 1

    if total_genes == 0:
        return "No gene data available"

    lines = ["System Distribution:"]
    for sys_id, count in sorted(system_counts.items(), key=lambda x: -x[1]):
        pct = count / total_genes * 100
        bar = "\u2588" * int(pct / 2)
        lines.append(f"  {sys_id:>25s} {bar} {count} ({pct:.1f}%)")

    return "\n".join(lines)


def plot_evolution_chart(history: List[Dict[str, Any]], save_path: str = "data/evolution_chart.png") -> Optional[str]:
    """Plot evolution history chart showing fitness over generations.

    Parameters
    ----------
    history : list of dict
        List of dicts with keys: 'generation', 'best_fitness', 'avg_fitness',
        'min_fitness' (optional).
    save_path : str
        Path to save the chart image.

    Returns
    -------
    str or None
        Path to saved image, or None if matplotlib is unavailable.
    """
    if not HAS_MATPLOTLIB:
        logger.warning("matplotlib not available, cannot plot evolution chart")
        return None

    if not history:
        logger.warning("Empty history, nothing to plot")
        return None

    generations = [h.get("generation", i) for i, h in enumerate(history)]
    best = [h.get("best_fitness", 0.0) for h in history]
    avg = [h.get("avg_fitness", 0.0) for h in history]
    min_f = [h.get("min_fitness", 0.0) for h in history]

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(generations, best, label="Best Fitness", color="#2ecc71", linewidth=2)
    ax.plot(generations, avg, label="Avg Fitness", color="#3498db", linewidth=1.5, linestyle="--")
    if any(v != 0 for v in min_f):
        ax.plot(generations, min_f, label="Min Fitness", color="#e74c3c", linewidth=1, linestyle=":")

    ax.set_xlabel("Generation", fontsize=12)
    ax.set_ylabel("Fitness", fontsize=12)
    ax.set_title("Oracle Evolution Fitness Over Generations", fontsize=14)
    ax.legend(loc="best")
    ax.grid(True, alpha=0.3)
    ax.xaxis.set_major_locator(ticker.MaxNLocator(integer=True))

    plt.tight_layout()
    try:
        os.makedirs(os.path.dirname(save_path) or ".", exist_ok=True)
        fig.savefig(save_path, dpi=150, bbox_inches="tight")
        plt.close(fig)
        logger.info("Evolution chart saved to %s", save_path)
        return save_path
    except Exception as e:
        logger.error("Failed to save evolution chart: %s", e)
        plt.close(fig)
        return None


def plot_fitness_landscape(population: list, save_path: str = "data/fitness_landscape.png") -> Optional[str]:
    """Plot fitness landscape as a scatter/heatmap of individual fitnesses.

    Parameters
    ----------
    population : list
        List of chromosome objects with fitness attributes.
    save_path : str
        Path to save the chart image.

    Returns
    -------
    str or None
        Path to saved image, or None if matplotlib is unavailable.
    """
    if not HAS_MATPLOTLIB:
        logger.warning("matplotlib not available, cannot plot fitness landscape")
        return None

    if not population:
        logger.warning("Empty population, nothing to plot")
        return None

    fitness_values = []
    gene_counts = []
    for ind in population:
        f = ind.fitness
        if isinstance(f, dict):
            fitness_values.append(f.get("total_fitness", 0.0))
        elif isinstance(f, (int, float)):
            fitness_values.append(f)
        else:
            fitness_values.append(0.0)
        gene_counts.append(len(ind.genes) if hasattr(ind, "genes") else 0)

    fig, ax = plt.subplots(figsize=(10, 6))
    scatter = ax.scatter(
        range(len(fitness_values)),
        fitness_values,
        c=gene_counts,
        cmap="viridis",
        alpha=0.7,
        edgecolors="white",
        linewidth=0.5,
        s=50,
    )

    cbar = plt.colorbar(scatter, ax=ax)
    cbar.set_label("Gene Count", fontsize=11)

    avg_fitness = sum(fitness_values) / len(fitness_values) if fitness_values else 0
    ax.axhline(y=avg_fitness, color="#e74c3c", linestyle="--", alpha=0.7, label=f"Avg: {avg_fitness:.4f}")
    ax.axhline(y=max(fitness_values) if fitness_values else 0, color="#2ecc71", linestyle=":", alpha=0.5, label="Max")

    ax.set_xlabel("Individual Index", fontsize=12)
    ax.set_ylabel("Fitness Score", fontsize=12)
    ax.set_title("Fitness Landscape", fontsize=14)
    ax.legend(loc="best")
    ax.grid(True, alpha=0.2)

    plt.tight_layout()
    try:
        os.makedirs(os.path.dirname(save_path) or ".", exist_ok=True)
        fig.savefig(save_path, dpi=150, bbox_inches="tight")
        plt.close(fig)
        logger.info("Fitness landscape saved to %s", save_path)
        return save_path
    except Exception as e:
        logger.error("Failed to save fitness landscape: %s", e)
        plt.close(fig)
        return None


HTML_REPORT_TEMPLATE = """\
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Oracle Evolution Report</title>
<style>
body { font-family: 'Segoe UI', Tahoma, sans-serif; margin: 2em; background: #f8f9fa; color: #333; }
h1 { color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 0.5em; }
h2 { color: #2980b9; margin-top: 1.5em; }
.card { background: white; border-radius: 8px; padding: 1.5em; margin: 1em 0; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }
table { border-collapse: collapse; width: 100%%; }
th, td { text-align: left; padding: 8px 12px; border-bottom: 1px solid #eee; }
th { background: #3498db; color: white; }
tr:hover { background: #f1f8ff; }
.metric { font-size: 1.3em; font-weight: bold; color: #27ae60; }
.muted { color: #95a5a6; }
.tag { display: inline-block; background: #3498db; color: white; padding: 2px 8px; border-radius: 4px; font-size: 0.85em; margin: 2px; }
pre { background: #ecf0f1; padding: 1em; border-radius: 4px; overflow-x: auto; font-size: 0.9em; }
</style>
</head>
<body>
<h1>Oracle Evolution Report</h1>

<div class="card">
<h2>Summary</h2>
<p><strong>Total Generations:</strong> <span class="metric">{{ total_generations }}</span></p>
<p><strong>Best Fitness:</strong> <span class="metric">{{ "%.4f"|format(best_fitness) }}</span></p>
<p><strong>Population Size:</strong> <span class="metric">{{ population_size }}</span></p>
<p class="muted">Generated: {{ timestamp }}</p>
</div>

{% if generations %}
<div class="card">
<h2>Generation History</h2>
<table>
<tr><th>Gen</th><th>Best Fitness</th><th>Avg Fitness</th><th>Min Fitness</th><th>Diversity</th></tr>
{% for gen in generations %}
<tr>
<td>{{ gen.generation }}</td>
<td>{{ "%.4f"|format(gen.best_fitness) }}</td>
<td>{{ "%.4f"|format(gen.avg_fitness) }}</td>
<td>{{ "%.4f"|format(gen.min_fitness) }}</td>
<td>{{ "%.4f"|format(gen.diversity) if gen.diversity is defined else "N/A" }}</td>
</tr>
{% endfor %}
</table>
</div>
{% endif %}

{% if top_oracles %}
<div class="card">
<h2>Top Oracles</h2>
<table>
<tr><th>Rank</th><th>ID</th><th>Fitness</th><th>Systems</th></tr>
{% for oracle in top_oracles %}
<tr>
<td>{{ loop.index }}</td>
<td>{{ oracle.id }}</td>
<td>{{ "%.4f"|format(oracle.fitness) }}</td>
<td>{% for sys in oracle.systems %}<span class="tag">{{ sys }}</span>{% endfor %}</td>
</tr>
{% endfor %}
</table>
</div>
{% endif %}

{% if config %}
<div class="card">
<h2>Configuration</h2>
<pre>{{ config }}</pre>
</div>
{% endif %}

{% if custom_sections %}
{% for section in custom_sections %}
<div class="card">
<h2>{{ section.title }}</h2>
{{ section.content }}
</div>
{% endfor %}
{% endif %}

</body>
</html>
"""


def generate_html_report(results: Dict[str, Any], save_path: str = "data/oracle_report.html") -> Optional[str]:
    """Generate an HTML report from oracle evolution results.

    Parameters
    ----------
    results : dict
        Report data with keys:
        - generations: list of dicts with generation stats
        - top_oracles: list of dicts with top oracle info
        - config: dict or string of configuration
        - custom_sections: list of dicts with title/content
        - best_fitness: float
        - population_size: int
    save_path : str
        Path to save the HTML file.

    Returns
    -------
    str or None
        Path to saved HTML file, or None if jinja2 is unavailable.
    """
    if not HAS_JINJA2:
        logger.warning("jinja2 not available, cannot generate HTML report")
        return None

    import time as _time

    generations = results.get("generations", [])
    total_generations = results.get("total_generations", len(generations))
    best_fitness = results.get("best_fitness", 0.0)
    if not best_fitness and generations:
        best_fitness = max(g.get("best_fitness", 0) for g in generations)
    population_size = results.get("population_size", 0)
    if not population_size and generations:
        population_size = generations[-1].get("population_size", 0)

    template_data = {
        "total_generations": total_generations,
        "best_fitness": best_fitness,
        "population_size": population_size,
        "timestamp": _time.strftime("%Y-%m-%d %H:%M:%S"),
        "generations": generations,
        "top_oracles": results.get("top_oracles", []),
        "config": json.dumps(results.get("config", {}), indent=2) if results.get("config") else None,
        "custom_sections": results.get("custom_sections", []),
    }

    try:
        template = Template(HTML_REPORT_TEMPLATE)
        html = template.render(**template_data)
        os.makedirs(os.path.dirname(save_path) or ".", exist_ok=True)
        with open(save_path, "w", encoding="utf-8") as f:
            f.write(html)
        logger.info("HTML report saved to %s", save_path)
        return save_path
    except Exception as e:
        logger.error("Failed to generate HTML report: %s", e)
        return None
