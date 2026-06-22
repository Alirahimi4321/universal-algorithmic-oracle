#!/usr/bin/env python3
"""CLI entry point for Universal Algorithmic Oracle - supports all engines."""
import argparse
import json
import logging
import time
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)


def cmd_ask(args):
    from oracle import OraclePipeline

    pipeline = OraclePipeline()
    print(f"[*] Encoding question: {args.question}")
    print(f"[*] Engine: {args.engine} | Generations: {args.generations}")

    start = time.time()
    if args.engine == "gp":
        output = pipeline.ask_tree(args.question, generations=args.generations)
    else:
        output = pipeline.ask(args.question, generations=args.generations, engine=args.engine)
    elapsed = time.time() - start

    result = output.to_dict()
    print(f"\n{'='*60}")
    print(f"ORACLE RESPONSE (engine={args.engine}, evolved in {elapsed:.2f}s)")
    print(f"{'='*60}")
    print(f"\nAnswer:\n{result['answer']}")
    print(f"\nSymbolic Answer: {json.dumps(result['symbolic_answer'], indent=2)}")
    print(f"\nConfidence: {result['oracle_confidence']:.2f}")
    print(f"Dominant Systems: {', '.join(result['dominant_systems'])}")
    print(f"Generation: {result['generation']}")
    print(f"Lineage: {result['lineage_id']}")
    print(f"\nNumeric Signature: {result['numeric_signature'][:10]}")
    print(f"\nExplanation Trace:")
    for line in result['explanation_trace']:
        print(f"  {line}")
    disclaimer = result.get('disclaimer', {})
    if isinstance(disclaimer, dict) and disclaimer.get('text'):
        print(f"\n{disclaimer['text']}")
    elif disclaimer:
        print(f"\n{disclaimer}")

    if args.output:
        try:
            with open(args.output, "w") as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            print(f"\n[*] Full output saved to: {args.output}")
        except OSError as e:
            print(f"\n[!] Failed to save output: {e}")


def cmd_list(args):
    from oracle import OraclePipeline
    pipeline = OraclePipeline()
    print("Available systems:")
    for s in pipeline.get_available_systems():
        print(f"  - {s}")
    print(f"\nAvailable engines:")
    for e in pipeline.get_available_engines():
        print(f"  - {e}")


def cmd_benchmark(args):
    from oracle import OraclePipeline

    pipeline = OraclePipeline()
    questions = [
        "آیا مسیر شغلی من تغییر می‌کند؟",
        "What does the future hold?",
        "آیا این پروژه موفق خواهد شد؟",
    ]

    for engine in ["ga", "gp", "nsga"]:
        print(f"\n{'='*60}")
        print(f"BENCHMARK: {engine.upper()} Engine")
        print(f"{'='*60}")
        for q in questions:
            print(f"\n--- Question: {q} ---")
            start = time.time()
            if engine == "gp":
                output = pipeline.ask_tree(q, generations=args.generations)
            else:
                output = pipeline.ask(q, generations=args.generations, engine=engine)
            elapsed = time.time() - start
            print(f"  Confidence: {output.oracle_confidence:.2f}")
            print(f"  Systems: {', '.join(output.dominant_systems)}")
            print(f"  Time: {elapsed:.2f}s")


def main():
    parser = argparse.ArgumentParser(description="Universal Algorithmic Oracle")
    subparsers = parser.add_subparsers(dest="command")

    ask_parser = subparsers.add_parser("ask", help="Ask the oracle a question")
    ask_parser.add_argument("question", help="The question to ask")
    ask_parser.add_argument("-g", "--generations", type=int, default=50, help="Evolution generations")
    ask_parser.add_argument("-e", "--engine", choices=["ga", "gp", "nsga", "stochopy", "psopy", "evogine"], default="ga", help="Evolution engine")
    ask_parser.add_argument("-o", "--output", help="Save output to JSON file")

    subparsers.add_parser("list", help="List available systems and engines")

    bench_parser = subparsers.add_parser("benchmark", help="Run benchmark across all engines")
    bench_parser.add_argument("-g", "--generations", type=int, default=20, help="Generations per question")

    args = parser.parse_args()

    if args.command == "ask":
        cmd_ask(args)
    elif args.command == "list":
        cmd_list(args)
    elif args.command == "benchmark":
        cmd_benchmark(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
