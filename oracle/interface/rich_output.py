"""Rich terminal output formatter for the Oracle.

Provides beautiful formatted output for oracle results, evolution progress,
and system listings using the Rich library.
"""
import logging
import time
from typing import Optional

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.text import Text
from rich.columns import Columns
from rich import box

logger = logging.getLogger(__name__)

console = Console()


def print_oracle_result(result: dict) -> None:
    """Display an oracle result with beautiful formatting."""
    answer = result.get("answer", "No answer")
    confidence = result.get("oracle_confidence", 0.0)
    systems = result.get("dominant_systems", [])
    fitness = result.get("fitness", {})
    explanation = result.get("explanation_trace", [])
    lineage_id = result.get("lineage_id", "unknown")
    generation = result.get("generation", 0)
    disclaimer = result.get("disclaimer", {})
    confidence_model = result.get("confidence_model", {})
    numeric_sig = result.get("numeric_signature", [])

    confidence_level = confidence_model.get("level", "unknown")
    confidence_color = {
        "high": "green",
        "medium": "yellow",
        "low": "red",
    }.get(confidence_level, "dim")

    header = Text()
    header.append("ORACLE READING", style="bold cyan")
    header.append(f"  [Lineage: {lineage_id[:12]}... | Gen {generation}]", style="dim")

    answer_panel = Panel(
        Text(answer, style="bold white"),
        title="[bold blue]Answer[/bold blue]",
        border_style="blue",
        box=box.ROUNDED,
    )

    confidence_bar = Text()
    confidence_bar.append(f"Confidence: ", style="bold")
    confidence_bar.append(f"{confidence:.2%}", style=f"bold {confidence_color}")
    confidence_bar.append(f" ({confidence_level})", style=f"{confidence_color}")

    systems_table = Table(
        title="Dominant Systems",
        box=box.SIMPLE_HEAVY,
        show_header=True,
        header_style="bold magenta",
    )
    systems_table.add_column("System", style="cyan")
    systems_table.add_column("Type", style="green")
    for sys_id in systems:
        sys_type = _classify_system(sys_id)
        systems_table.add_row(sys_id, sys_type)

    fitness_table = Table(
        title="Fitness Metrics",
        box=box.SIMPLE_HEAVY,
        show_header=True,
        header_style="bold magenta",
    )
    fitness_table.add_column("Metric", style="cyan")
    fitness_table.add_column("Value", style="yellow", justify="right")
    for key, val in fitness.items():
        if isinstance(val, float):
            fitness_table.add_row(key, f"{val:.4f}")
        else:
            fitness_table.add_row(key, str(val))

    numeric_text = Text()
    if numeric_sig:
        sig_preview = [f"{v:.3f}" for v in numeric_sig[:8]]
        numeric_text.append("Numeric Signature: ", style="bold")
        numeric_text.append("[" + ", ".join(sig_preview) + "...]", style="cyan")
    else:
        numeric_text.append("No numeric signature available", style="dim")

    console.print()
    console.print(header)
    console.print(answer_panel)
    console.print(confidence_bar)
    console.print()
    console.print(Columns([systems_table, fitness_table], equal=False, expand=True))
    console.print(numeric_text)

    if explanation:
        console.print()
        console.print("[bold]Explanation Trace:[/bold]", style="white")
        for line in explanation:
            console.print(f"  {line}", style="dim")

    if disclaimer and disclaimer.get("text"):
        console.print()
        console.print(
            Panel(
                Text(disclaimer["text"], style="dim italic"),
                title="[yellow]Disclaimer[/yellow]",
                border_style="yellow",
                box=box.ROUNDED,
            )
        )

    console.print()


def print_evolution_progress(generation: int, fitness: float, total: Optional[int] = None) -> None:
    """Display evolution progress."""
    progress_text = Text()
    progress_text.append("Evolution: ", style="bold cyan")
    progress_text.append(f"Gen {generation}", style="white")
    if total:
        progress_text.append(f"/{total}", style="dim")
    progress_text.append("  Fitness: ", style="bold cyan")
    progress_text.append(f"{fitness:.4f}", style="green")

    if fitness > 0.7:
        progress_text.append(" [EXCELLENT]", style="bold green")
    elif fitness > 0.5:
        progress_text.append(" [GOOD]", style="yellow")
    elif fitness > 0.3:
        progress_text.append(" [MODERATE]", style="dark_orange")
    else:
        progress_text.append(" [LOW]", style="red")

    console.print(progress_text)


def print_system_list(systems: list) -> None:
    """Display a table of available symbolic systems."""
    table = Table(
        title="Available Symbolic Systems",
        box=box.DOUBLE_EDGE,
        show_header=True,
        header_style="bold cyan",
        border_style="blue",
    )
    table.add_column("#", style="dim", justify="right")
    table.add_column("System ID", style="bold white")
    table.add_column("Category", style="green")
    table.add_column("Type", style="yellow")

    categories = {
        "gematria": "Hebrew Numerology",
        "binary": "Binary/I Ching",
        "astrology": "Astrology",
        "cards": "Divination Cards",
        "eastern": "Eastern Systems",
        "mayan": "Mayan Calendar",
        "dreams": "Dream Analysis",
        "numerical": "Numerical",
        "persian": "Persian Systems",
        "divination": "Divination",
        "text": "Text Analysis",
        "analysis": "Analysis",
        "sigil": "Sigil Systems",
    }

    for i, sys_id in enumerate(systems, 1):
        category = "Unknown"
        sys_type = "Symbolic"
        for prefix, cat_name in categories.items():
            if sys_id.startswith(prefix):
                category = cat_name
                break
        sys_type = _classify_system(sys_id)
        table.add_row(str(i), sys_id, category, sys_type)

    console.print()
    console.print(table)
    console.print(f"\n[dim]Total: {len(systems)} systems available[/dim]")


def print_engine_list(engines: list) -> None:
    """Display a table of available evolution engines."""
    table = Table(
        title="Available Evolution Engines",
        box=box.DOUBLE_EDGE,
        show_header=True,
        header_style="bold cyan",
        border_style="blue",
    )
    table.add_column("Engine", style="bold white")
    table.add_column("Description", style="green")
    table.add_column("Type", style="yellow")

    descriptions = {
        "ga": ("Genetic Algorithm", "Population-based"),
        "gp": ("Genetic Programming", "Tree-based"),
        "nsga": ("NSGA-II", "Multi-objective"),
        "stochopy": ("Stochastic Optimization", "Optimizer-based"),
        "psopy": ("PSO Optimization", "Swarm-based"),
        "evogine": ("Evogene", "Gene-based"),
        "cma": ("CMA-ES", "Evolution Strategy"),
        "bayesian": ("Bayesian Optimization", "Surrogate-based"),
    }

    for engine in engines:
        desc, eng_type = descriptions.get(engine, ("Unknown", "Unknown"))
        table.add_row(engine, desc, eng_type)

    console.print()
    console.print(table)


def print_benchmark_result(result: dict) -> None:
    """Display benchmark results."""
    accuracy = result.get("accuracy", 0.0)
    target = result.get("target_numbers", [])
    predicted = result.get("predicted_numbers", [])
    difficulty = result.get("difficulty_level", 1)

    header = Text()
    header.append("BENCHMARK RESULT", style="bold cyan")

    accuracy_color = "green" if accuracy > 0.7 else "yellow" if accuracy > 0.4 else "red"
    accuracy_text = Text()
    accuracy_text.append(f"Accuracy: ", style="bold")
    accuracy_text.append(f"{accuracy:.2%}", style=f"bold {accuracy_color}")
    accuracy_text.append(f"  |  Difficulty: Level {difficulty}", style="dim")

    comparison_table = Table(
        title="Prediction vs Target",
        box=box.SIMPLE_HEAVY,
        show_header=True,
        header_style="bold magenta",
    )
    comparison_table.add_column("#", style="dim", justify="right")
    comparison_table.add_column("Target", style="green")
    comparison_table.add_column("Predicted", style="cyan")
    comparison_table.add_column("Error", style="red")

    for i, (t, p) in enumerate(zip(target[:10], predicted[:10]), 1):
        err = abs(t - p)
        comparison_table.add_row(str(i), f"{t:.2f}", f"{p:.2f}", f"{err:.2f}")

    console.print()
    console.print(header)
    console.print(accuracy_text)
    console.print(comparison_table)
    console.print()


def print_error(message: str) -> None:
    """Display an error message."""
    console.print(Panel(
        Text(message, style="bold red"),
        title="[red]Error[/red]",
        border_style="red",
        box=box.ROUNDED,
    ))


def print_info(message: str) -> None:
    """Display an info message."""
    console.print(Panel(
        Text(message, style="white"),
        title="[blue]Info[/blue]",
        border_style="blue",
        box=box.ROUNDED,
    ))


def _classify_system(sys_id: str) -> str:
    """Classify a system ID into a human-readable type."""
    if "astrology" in sys_id or "kerykeion" in sys_id or "yaegi" in sys_id or "skyfield" in sys_id:
        return "Celestial"
    elif "gematria" in sys_id or "hebrew" in sys_id:
        return "Numerological"
    elif "binary" in sys_id or "iching" in sys_id or "ogham" in sys_id:
        return "Binary Pattern"
    elif "tarot" in sys_id or "cards" in sys_id or "divination" in sys_id:
        return "Divination"
    elif "mayan" in sys_id or "pohualli" in sys_id:
        return "Calendar"
    elif "eastern" in sys_id or "tianji" in sys_id or "saju" in sys_id or "jalali" in sys_id:
        return "Eastern"
    elif "numerical" in sys_id or "pythagorean" in sys_id or "roman" in sys_id:
        return "Numerical"
    elif "dream" in sys_id:
        return "Symbolic"
    elif "sigil" in sys_id:
        return "Sigil"
    elif "text" in sys_id or "grapheme" in sys_id:
        return "Textual"
    elif "syntropy" in sys_id or "pyitlib" in sys_id:
        return "Analytical"
    else:
        return "Symbolic"
