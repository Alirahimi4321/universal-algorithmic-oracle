"""Tests for the Oracle Pipeline - Phase 1."""
import sys
import os
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def test_entropy_encoder():
    from oracle.entropy.encoder import EntropyEncoder

    encoder = EntropyEncoder()
    packet = encoder.encode("test question", timestamp=1234567890.0)

    assert packet.raw_question == "test question"
    assert packet.seed > 0
    assert len(packet.bit_stream) > 0
    assert len(packet.numeric_vector) > 0
    assert len(packet.sha_stream) > 0
    assert packet.calendar_context["year"] > 0
    print("[PASS] test_entropy_encoder")


def test_gematria_wrapper():
    from oracle.symbolic.gematria.abjad import GematriaWrapper

    wrapper = GematriaWrapper()
    packet = {"normalized_text": "سلام", "seed": 42, "numeric_vector": [1, 2, 3]}
    result = wrapper.compute(packet)

    assert result.system_id == "gematria"
    assert "abjad" in result.symbolic_state["systems"]
    assert len(result.numeric_projection) > 0
    print("[PASS] test_gematria_wrapper")


def test_iching_wrapper():
    from oracle.symbolic.binary.iching import IChingWrapper

    wrapper = IChingWrapper()
    packet = {
        "bit_stream": [1, 0, 1, 1, 0, 0, 1, 1, 0, 1, 0, 0],
        "seed": 42,
        "numeric_vector": [1, 2, 3],
    }
    result = wrapper.compute(packet)

    assert result.system_id == "iching"
    assert "hexagram" in result.symbolic_state
    assert 0 <= result.symbolic_state["hexagram"] <= 63
    print("[PASS] test_iching_wrapper")


def test_geomancy_wrapper():
    from oracle.symbolic.binary.geomancy import GeomancyWrapper

    wrapper = GeomancyWrapper()
    packet = {
        "bit_stream": [1, 0, 1, 1, 0, 0, 1, 1] * 20,
        "seed": 42,
        "numeric_vector": [1, 2, 3],
    }
    result = wrapper.compute(packet)

    assert result.system_id == "geomancy"
    assert "mother" in result.symbolic_state or "mother_figures" in result.symbolic_state
    assert len(result.numeric_projection) > 0
    print("[PASS] test_geomancy_wrapper")


def test_calendar_wrapper():
    from oracle.symbolic.astrology.calendar import CalendarWrapper

    wrapper = CalendarWrapper()
    packet = {"timestamp": "1234567890.0", "calendar_context": {}}
    result = wrapper.compute(packet)

    assert result.system_id == "calendar"
    assert "jalali" in result.symbolic_state
    assert "hijri" in result.symbolic_state
    assert "gregorian" in result.symbolic_state
    print("[PASS] test_calendar_wrapper")


def test_chromosome():
    from oracle.genome.chromosome import Chromosome

    chrom = Chromosome.create_random([
        ("gematria", "internal"),
        ("iching", "internal"),
    ])

    assert len(chrom.genes) == 2
    assert len(chrom.edges) == 1
    assert chrom.chromosome_id

    d = chrom.to_dict()
    chrom2 = Chromosome.from_dict(d)
    assert chrom2.chromosome_id == chrom.chromosome_id
    print("[PASS] test_chromosome")


def test_fitness_evaluator():
    from oracle.genome.chromosome import Chromosome
    from oracle.evaluation.fitness import FitnessEvaluator

    chrom = Chromosome.create_random([
        ("gematria", "internal"),
        ("iching", "internal"),
    ])

    evaluator = FitnessEvaluator()
    entropy = {
        "normalized_text": "test",
        "seed": 42,
        "bit_stream": [1, 0, 1, 1, 0, 0] * 50,
        "numeric_vector": [1, 2, 3],
        "timestamp": "1234567890.0",
        "calendar_context": {},
    }

    scores = evaluator.evaluate(chrom, entropy)
    assert "total_fitness" in scores
    assert 0 <= scores["total_fitness"] <= 1
    print("[PASS] test_fitness_evaluator")


def test_evolutionary_engine():
    from oracle.evolution.deap_engine import EvolutionaryEngine
    from oracle.entropy.encoder import EntropyEncoder

    engine = EvolutionaryEngine({"population_size": 10, "max_generations": 3})
    engine.initialize_population()

    encoder = EntropyEncoder()
    packet = encoder.encode("test")
    ep_dict = {
        "normalized_text": packet.normalized_text,
        "seed": packet.seed,
        "bit_stream": packet.bit_stream,
        "numeric_vector": packet.numeric_vector,
        "timestamp": packet.timestamp,
        "calendar_context": packet.calendar_context,
    }

    evolved = engine.evolve(ep_dict, generations=3)
    assert len(evolved) > 0
    assert evolved[0].fitness.get("total_fitness", 0) >= 0
    print("[PASS] test_evolutionary_engine")


def test_full_pipeline():
    from oracle import OraclePipeline

    pipeline = OraclePipeline()
    output = pipeline.ask("آیا این پروژه موفق می‌شود؟", generations=5)

    assert output.answer
    assert output.oracle_confidence >= 0
    assert len(output.dominant_systems) > 0
    assert output.disclaimer
    print("[PASS] test_full_pipeline")


if __name__ == "__main__":
    test_entropy_encoder()
    test_gematria_wrapper()
    test_iching_wrapper()
    test_geomancy_wrapper()
    test_calendar_wrapper()
    test_chromosome()
    test_fitness_evaluator()
    test_evolutionary_engine()
    test_full_pipeline()
    print("\n=== ALL TESTS PASSED ===")
