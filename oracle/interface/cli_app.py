"""Typer CLI application for the Universal Algorithmic Oracle.

Provides command-line interface for querying the oracle, listing systems,
running benchmarks, and starting the web API server.
"""
import sys
import time
import logging
import typing

import typer

from ..runtime.executor import OraclePipeline

app = typer.Typer(
    name="oracle",
    help="Universal Algorithmic Oracle - Evolved Symbolic Computation",
    add_completion=False,
)

logger = logging.getLogger(__name__)


def _get_pipeline() -> OraclePipeline:
    return OraclePipeline()


@app.command()
def ask(
    question: str = typer.Argument(..., help="Question to ask the oracle"),
    engine: str = typer.Option("ga", "--engine", "-e", help="Evolution engine (ga, gp, nsga)"),
    generations: int = typer.Option(50, "--generations", "-g", help="Number of evolutionary generations"),
    timestamp: typing.Optional[float] = typer.Option(None, "--timestamp", "-t", help="Timestamp override"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output raw JSON"),
):
    """Ask the oracle a question and receive a reading."""
    from .rich_output import print_oracle_result, print_error, print_info

    print_info(f"Question: {question}\nEngine: {engine} | Generations: {generations}")

    pipeline = _get_pipeline()
    try:
        start = time.time()
        result = pipeline.ask(
            question=question,
            timestamp=timestamp,
            generations=generations,
            engine=engine,
        )
        elapsed = time.time() - start
    except Exception as e:
        logger.exception("Oracle ask failed")
        print_error(f"Oracle failed: {e}")
        raise typer.Exit(code=1)

    if json_output:
        import json
        output = result.to_dict()
        output["elapsed_seconds"] = round(elapsed, 3)
        typer.echo(json.dumps(output, indent=2, default=str))
    else:
        print_oracle_result(result.to_dict())
        typer.echo(f"[dim]Completed in {elapsed:.2f}s[/dim]")


@app.command("list-systems")
def list_systems():
    """List all available symbolic systems."""
    from .rich_output import print_system_list, print_error

    pipeline = _get_pipeline()
    try:
        systems = pipeline.get_available_systems()
    except Exception as e:
        logger.exception("Failed to list systems")
        print_error(f"Failed to list systems: {e}")
        raise typer.Exit(code=1)

    print_system_list(systems)


@app.command("list-engines")
def list_engines():
    """List all available evolution engines."""
    from .rich_output import print_engine_list, print_error

    pipeline = _get_pipeline()
    try:
        engines = pipeline.get_available_engines()
    except Exception as e:
        logger.exception("Failed to list engines")
        print_error(f"Failed to list engines: {e}")
        raise typer.Exit(code=1)

    print_engine_list(engines)


@app.command()
def serve(
    host: str = typer.Option("127.0.0.1", "--host", help="Host to bind"),
    port: int = typer.Option(8000, "--port", "-p", help="Port to listen on"),
):
    """Start the Oracle REST API server."""
    from .rich_output import print_info

    print_info(f"Starting Oracle API on {host}:{port}")
    try:
        from .web_api import run_server
        run_server(host=host, port=port)
    except ImportError:
        typer.echo("Error: FastAPI and uvicorn are required. Install with: pip install fastapi uvicorn", err=True)
        raise typer.Exit(code=1)
    except Exception as e:
        logger.exception("Server failed")
        typer.echo(f"Server error: {e}", err=True)
        raise typer.Exit(code=1)


@app.command()
def benchmark(
    trials: int = typer.Option(10, "--trials", "-n", help="Number of benchmark trials"),
    generations: int = typer.Option(30, "--generations", "-g", help="Generations per trial"),
    engine: str = typer.Option("ga", "--engine", "-e", help="Evolution engine"),
):
    """Run prediction benchmarks against cryptographically random targets."""
    from .rich_output import print_benchmark_result, print_info, print_error
    from ..evaluation.benchmark import PredictionBenchmark

    pipeline = _get_pipeline()
    bench = PredictionBenchmark()

    print_info(f"Running {trials} benchmark trials (engine={engine}, gens={generations})")

    accuracies = []
    for i in range(trials):
        target = bench.generate_target_numbers()
        entropy_packet = {"seed": i * 137 + 42, "numeric_vector": target}

        try:
            result = pipeline.ask(
                question=f"benchmark trial {i}",
                generations=generations,
                engine=engine,
            )
            predicted = result.numeric_signature[:len(target)] if hasattr(result, 'numeric_signature') else []
        except Exception as e:
            logger.warning("Benchmark trial %d failed: %s", i, e)
            predicted = [0.0] * len(target)

        validation = bench.validate_prediction(predicted, target)
        accuracies.append(validation.accuracy)

        if (i + 1) % max(1, trials // 10) == 0 or i == trials - 1:
            avg = sum(accuracies) / len(accuracies)
            typer.echo(f"  Trial {i+1}/{trials} - Running avg: {avg:.2%}")

    stats = bench.get_stats()
    avg_accuracy = stats["avg_accuracy"]
    max_acc = max(accuracies) if accuracies else 0.0
    min_acc = min(accuracies) if accuracies else 0.0

    typer.echo()
    typer.echo(f"=== Benchmark Summary ===")
    typer.echo(f"  Trials: {trials}")
    typer.echo(f"  Avg Accuracy: {avg_accuracy:.2%}")
    typer.echo(f"  Best: {max_acc:.2%}  |  Worst: {min_acc:.2%}")
    typer.echo(f"  Difficulty Level: {stats['difficulty_level']}")
    typer.echo()


@app.command()
def health():
    """Check oracle system health."""
    from .rich_output import print_info, print_error

    pipeline = _get_pipeline()
    try:
        systems = pipeline.get_available_systems()
        engines = pipeline.get_available_engines()
        print_info(
            f"Status: OK\n"
            f"Systems loaded: {len(systems)}\n"
            f"Engines available: {len(engines)}\n"
            f"Engine list: {', '.join(engines)}"
        )
    except Exception as e:
        logger.exception("Health check failed")
        print_error(f"Health check failed: {e}")
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
