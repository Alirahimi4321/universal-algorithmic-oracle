"""Output formatting and report generation for oracle results."""
from .explanation import generate_explanation
from .oracle_output import OracleOutput, OracleOutputBuilder
from .disclaimer import DisclaimerGenerator
from .lineage_graph import LineageGraph, LineageTracker
from .report import generate_report
from .visualization import (
    format_ascii_bar_chart,
    format_population_stats,
    format_system_distribution,
    plot_evolution_chart,
    plot_fitness_landscape,
    generate_html_report,
)

__all__ = [
    "generate_explanation",
    "OracleOutput",
    "OracleOutputBuilder",
    "DisclaimerGenerator",
    "LineageGraph",
    "LineageTracker",
    "generate_report",
    "format_ascii_bar_chart",
    "format_population_stats",
    "format_system_distribution",
    "plot_evolution_chart",
    "plot_fitness_landscape",
    "generate_html_report",
]
