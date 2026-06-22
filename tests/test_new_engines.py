"""Tests for ALL new evolutionary engine classes."""
import sys
import os
import types
import random
import importlib

sys.path.insert(0, '/data/data/com.termux/files/home/universal_algorithmic_oracle')

PROJ = '/data/data/com.termux/files/home/universal_algorithmic_oracle'

_initialized = False


def _setup():
    global _initialized
    if _initialized:
        return
    _initialized = True

    def stub(name, rel):
        s = types.ModuleType(name)
        s.__path__ = [os.path.join(PROJ, rel)]
        s.__package__ = name
        sys.modules[name] = s

    stub('oracle', 'oracle')
    stub('oracle.symbolic', 'oracle/symbolic')
    stub('oracle.symbolic.astrology', 'oracle/symbolic/astrology')
    stub('oracle.symbolic.eastern', 'oracle/symbolic/eastern')
    stub('oracle.symbolic.mayan', 'oracle/symbolic/mayan')
    stub('oracle.symbolic.binary', 'oracle/symbolic/binary')
    stub('oracle.symbolic.cards', 'oracle/symbolic/cards')
    stub('oracle.symbolic.divination', 'oracle/symbolic/divination')
    stub('oracle.symbolic.dreams', 'oracle/symbolic/dreams')
    stub('oracle.symbolic.fortune_telling', 'oracle/symbolic/fortune_telling')
    stub('oracle.symbolic.gematria', 'oracle/symbolic/gematria')
    stub('oracle.symbolic.numerical', 'oracle/symbolic/numerical')
    stub('oracle.evolution', 'oracle/evolution')
    stub('oracle.evolution.engines', 'oracle/evolution/engines')
    stub('oracle.evolution.islands', 'oracle/evolution/islands')
    stub('oracle.genome', 'oracle/genome')
    stub('oracle.evaluation', 'oracle/evaluation')
    stub('oracle.memory', 'oracle/memory')
    stub('oracle.output', 'oracle/output')
    stub('oracle.entropy', 'oracle/entropy')
    stub('oracle.fusion', 'oracle/fusion')
    stub('oracle.interface', 'oracle/interface')
    stub('oracle.runtime', 'oracle/runtime')

    importlib.import_module('oracle.symbolic.base')
    reg = importlib.import_module('oracle.symbolic.registry')
    reg.register_all()


def _load_mod(dotted_name):
    _setup()
    if dotted_name in sys.modules:
        return sys.modules[dotted_name]
    return importlib.import_module(dotted_name)


def _ep(seed=42):
    return {
        "bit_stream": [random.randint(0, 1) for _ in range(30)],
        "seed": seed,
        "numeric_vector": [random.random() for _ in range(10)],
        "normalized_text": "test",
        "calendar_context": {"year": 2024, "month": 1, "day": 1, "hour": 12},
        "timestamp": 0,
    }


class TestStochopyEngine:
    def test_create_defaults(self):
        e = _load_mod("oracle.evolution.engines.stochopy_engine").StochopyEngine()
        assert e.population_size == 30
        assert e.method == "cmaes"

    def test_create_custom(self):
        e = _load_mod("oracle.evolution.engines.stochopy_engine").StochopyEngine({"population_size": 15, "method": "pso"})
        assert e.population_size == 15

    def test_initialize_population(self):
        e = _load_mod("oracle.evolution.engines.stochopy_engine").StochopyEngine({"population_size": 10})
        assert len(e.initialize_population()) == 10

    def test_evolve(self):
        e = _load_mod("oracle.evolution.engines.stochopy_engine").StochopyEngine({"population_size": 10})
        r = e.evolve(_ep(), generations=2)
        assert isinstance(r, list) and len(r) > 0
        assert all(hasattr(c, "fitness") for c in r)

    def test_auto_init(self):
        e = _load_mod("oracle.evolution.engines.stochopy_engine").StochopyEngine({"population_size": 8})
        r = e.evolve(_ep(), generations=1)
        assert len(r) > 0

    def test_best_history(self):
        e = _load_mod("oracle.evolution.engines.stochopy_engine").StochopyEngine({"population_size": 8})
        e.evolve(_ep(), generations=3)
        assert len(e.best_history) > 0
        assert "best_fitness" in e.best_history[0]


class TestPsopyEngine:
    def test_create_defaults(self):
        e = _load_mod("oracle.evolution.engines.psopy_engine").PsopyEngine()
        assert e.population_size == 30

    def test_create_custom(self):
        e = _load_mod("oracle.evolution.engines.psopy_engine").PsopyEngine({"population_size": 12})
        assert e.population_size == 12

    def test_initialize_population(self):
        e = _load_mod("oracle.evolution.engines.psopy_engine").PsopyEngine({"population_size": 10})
        assert len(e.initialize_population()) == 10

    def test_evolve(self):
        e = _load_mod("oracle.evolution.engines.psopy_engine").PsopyEngine({"population_size": 10})
        r = e.evolve(_ep(), generations=2)
        assert isinstance(r, list) and len(r) > 0

    def test_auto_init(self):
        e = _load_mod("oracle.evolution.engines.psopy_engine").PsopyEngine({"population_size": 8})
        r = e.evolve(_ep(), generations=1)
        assert len(r) > 0

    def test_best_history(self):
        e = _load_mod("oracle.evolution.engines.psopy_engine").PsopyEngine({"population_size": 8})
        e.evolve(_ep(), generations=3)
        assert len(e.best_history) == 3


class TestEvogineEngine:
    def test_create_defaults(self):
        e = _load_mod("oracle.evolution.engines.evogine_engine").EvogineEngine()
        assert e.population_size == 30
        assert e.method == "ga"

    def test_create_custom(self):
        e = _load_mod("oracle.evolution.engines.evogine_engine").EvogineEngine({"population_size": 15})
        assert e.population_size == 15

    def test_initialize_population(self):
        e = _load_mod("oracle.evolution.engines.evogine_engine").EvogineEngine({"population_size": 10})
        assert len(e.initialize_population()) == 10

    def test_evolve(self):
        e = _load_mod("oracle.evolution.engines.evogine_engine").EvogineEngine({"population_size": 10})
        r = e.evolve(_ep(), generations=2)
        assert isinstance(r, list) and len(r) > 0

    def test_fallback(self):
        e = _load_mod("oracle.evolution.engines.evogine_engine").EvogineEngine({"population_size": 8})
        e.initialize_population()
        r = e._fallback_evolve(_ep(), 2)
        assert isinstance(r, list) and len(r) > 0

    def test_best_history(self):
        e = _load_mod("oracle.evolution.engines.evogine_engine").EvogineEngine({"population_size": 8})
        e.evolve(_ep(), generations=3)
        assert len(e.best_history) == 3


class TestCMAEngine:
    def test_create_defaults(self):
        e = _load_mod("oracle.evolution.engines.cma_engine").CMAEngine()
        assert e.population_size == 30
        assert e.sigma == 0.5

    def test_create_custom(self):
        e = _load_mod("oracle.evolution.engines.cma_engine").CMAEngine({"population_size": 20, "sigma": 0.3})
        assert e.sigma == 0.3

    def test_initialize_population(self):
        e = _load_mod("oracle.evolution.engines.cma_engine").CMAEngine({"population_size": 10})
        assert len(e.initialize_population()) == 10

    def test_evolve(self):
        e = _load_mod("oracle.evolution.engines.cma_engine").CMAEngine({"population_size": 10})
        r = e.evolve(_ep(), generations=2)
        assert isinstance(r, list) and len(r) > 0

    def test_auto_init(self):
        e = _load_mod("oracle.evolution.engines.cma_engine").CMAEngine({"population_size": 8})
        r = e.evolve(_ep(), generations=1)
        assert len(r) > 0

    def test_best_history(self):
        e = _load_mod("oracle.evolution.engines.cma_engine").CMAEngine({"population_size": 8})
        e.evolve(_ep(), generations=3)
        assert len(e.best_history) == 3


class TestBayesianOptEngine:
    def test_create_defaults(self):
        e = _load_mod("oracle.evolution.engines.bayesian_engine").BayesianOptEngine()
        assert e.population_size == 30

    def test_create_custom(self):
        e = _load_mod("oracle.evolution.engines.bayesian_engine").BayesianOptEngine({"population_size": 15})
        assert e.population_size == 15

    def test_initialize_population(self):
        e = _load_mod("oracle.evolution.engines.bayesian_engine").BayesianOptEngine({"population_size": 10})
        assert len(e.initialize_population()) == 10

    def test_evolve(self):
        e = _load_mod("oracle.evolution.engines.bayesian_engine").BayesianOptEngine({"population_size": 10})
        r = e.evolve(_ep(), generations=2)
        assert isinstance(r, list) and len(r) > 0

    def test_auto_init(self):
        e = _load_mod("oracle.evolution.engines.bayesian_engine").BayesianOptEngine({"population_size": 8})
        r = e.evolve(_ep(), generations=1)
        assert len(r) > 0

    def test_best_history(self):
        e = _load_mod("oracle.evolution.engines.bayesian_engine").BayesianOptEngine({"population_size": 8})
        e.evolve(_ep(), generations=3)
        assert len(e.best_history) == 3

    def test_sorted_by_fitness(self):
        e = _load_mod("oracle.evolution.engines.bayesian_engine").BayesianOptEngine({"population_size": 10})
        r = e.evolve(_ep(), generations=2)
        for i in range(len(r) - 1):
            f1 = r[i].fitness.get("total_fitness", 0)
            f2 = r[i + 1].fitness.get("total_fitness", 0)
            assert f1 >= f2
