"""Report generation for oracle results."""
import json
import time


def generate_report(oracle_output: dict, evolution_stats: dict = None) -> str:
    """Generate a human-readable report of the oracle output."""
    lines = []
    lines.append("=" * 60)
    lines.append("UNIVERSAL ALGORITHMIC ORACLE - REPORT")
    lines.append("=" * 60)
    lines.append("")

    lines.append(f"Answer: {oracle_output.get('answer', 'N/A')}")
    lines.append("")

    symbolic = oracle_output.get("symbolic_answer", {})
    if symbolic:
        lines.append("Symbolic Analysis:")
        for key, value in symbolic.items():
            lines.append(f"  {key}: {value}")
    lines.append("")

    lines.append(f"Confidence: {oracle_output.get('oracle_confidence', 0):.2f}")
    lines.append(f"Generation: {oracle_output.get('generation', 'N/A')}")
    lines.append(f"Lineage: {oracle_output.get('lineage_id', 'N/A')}")
    lines.append("")

    systems = oracle_output.get("dominant_systems", [])
    lines.append(f"Dominant Systems ({len(systems)}):")
    for s in systems:
        lines.append(f"  - {s}")
    lines.append("")

    fitness = oracle_output.get("fitness", {})
    if fitness:
        lines.append("Fitness Metrics:")
        for key, value in fitness.items():
            lines.append(f"  {key}: {value:.4f}" if isinstance(value, float) else f"  {key}: {value}")
    lines.append("")

    sig = oracle_output.get("numeric_signature", [])
    if sig:
        lines.append(f"Numeric Signature: {sig[:10]}{'...' if len(sig) > 10 else ''}")
    lines.append("")

    if evolution_stats:
        lines.append("Evolution Statistics:")
        for key, value in evolution_stats.items():
            lines.append(f"  {key}: {value}")
        lines.append("")

    disclaimer = oracle_output.get("disclaimer", "")
    if disclaimer:
        lines.append("-" * 60)
        lines.append(disclaimer)

    return "\n".join(lines)
