"""Tests for analysis modules: correlation, chaos, graph, community, sympy, moocore."""
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
    importlib.import_module('oracle.symbolic.registry')


def _load_mod(dotted_name):
    _setup()
    if dotted_name in sys.modules:
        return sys.modules[dotted_name]
    return importlib.import_module(dotted_name)


class TestSystemCorrelationAnalyzer:
    def test_instantiate(self):
        a = _load_mod("oracle.evaluation.correlation").SystemCorrelationAnalyzer()
        assert hasattr(a, "correlation_cache")

    def test_analyze_system_pair(self):
        a = _load_mod("oracle.evaluation.correlation").SystemCorrelationAnalyzer()
        x = [float(i) for i in range(1, 11)]
        y = [float(i * 2) for i in range(1, 11)]
        r = a.analyze_system_pair(x, y)
        assert isinstance(r, dict)
        assert "mi" in r and "jsd" in r and "te_a_to_b" in r

    def test_short_vectors(self):
        a = _load_mod("oracle.evaluation.correlation").SystemCorrelationAnalyzer()
        r = a.analyze_system_pair([1.0], [2.0])
        assert r["mi"] == 0.0

    def test_find_independent_systems(self):
        a = _load_mod("oracle.evaluation.correlation").SystemCorrelationAnalyzer()
        out = {
            "a": [float(i) for i in range(1, 11)],
            "b": [float(10 - i) for i in range(10)],
            "c": [1.0] * 10,
        }
        r = a.find_independent_systems(out, threshold=0.5)
        assert isinstance(r, list) and len(r) > 0

    def test_caching(self):
        a = _load_mod("oracle.evaluation.correlation").SystemCorrelationAnalyzer()
        x = [float(i) for i in range(1, 11)]
        y = [float(i * 2) for i in range(1, 11)]
        r1 = a.analyze_system_pair(x, y)
        r2 = a.analyze_system_pair(x, y)
        assert r1 is r2


class TestChaosAnalyzer:
    def test_instantiate(self):
        a = _load_mod("oracle.evaluation.chaos_analysis").ChaosAnalyzer()
        assert hasattr(a, "cache")

    def test_full_analysis(self):
        a = _load_mod("oracle.evaluation.chaos_analysis").ChaosAnalyzer()
        random.seed(42)
        ts = [random.random() for _ in range(100)]
        r = a.full_analysis(ts)
        assert isinstance(r, dict)
        if "error" not in r:
            assert "lyapunov" in r and "hurst" in r and "is_chaotic" in r

    def test_short_timeseries(self):
        a = _load_mod("oracle.evaluation.chaos_analysis").ChaosAnalyzer()
        assert isinstance(a.full_analysis([1.0, 2.0, 3.0]), dict)

    def test_analyze_system_dynamics(self):
        a = _load_mod("oracle.evaluation.chaos_analysis").ChaosAnalyzer()
        random.seed(42)
        out = {"a": [random.random() for _ in range(50)],
               "b": [random.random() for _ in range(50)]}
        assert isinstance(a.analyze_system_dynamics(out), dict)

    def test_individual_metrics(self):
        a = _load_mod("oracle.evaluation.chaos_analysis").ChaosAnalyzer()
        random.seed(42)
        ts = [random.random() for _ in range(100)]
        assert isinstance(a.lyapunov_exponent(ts), float)
        assert isinstance(a.hurst_exponent(ts), float)
        assert isinstance(a.sample_entropy(ts), float)
        assert isinstance(a.correlation_dimension(ts), float)
        assert isinstance(a.dfa_exponent(ts), float)


class TestSystemGraphAnalyzer:
    def test_instantiate(self):
        a = _load_mod("oracle.evolution.graph_analysis").SystemGraphAnalyzer()
        assert a.graph is None

    def test_build_graph(self):
        a = _load_mod("oracle.evolution.graph_analysis").SystemGraphAnalyzer()
        corr = {"a": {"b": 0.5}, "b": {"a": 0.5}}
        g = a.build_graph(corr)
        if g is not None:
            assert g.number_of_nodes() == 2

    def test_find_communities(self):
        a = _load_mod("oracle.evolution.graph_analysis").SystemGraphAnalyzer()
        corr = {"a": {"b": 0.9}, "b": {"a": 0.9}, "c": {"d": 0.8}, "d": {"c": 0.8}}
        a.build_graph(corr, threshold=0.05)
        assert isinstance(a.find_communities(), list)

    def test_find_central_systems(self):
        a = _load_mod("oracle.evolution.graph_analysis").SystemGraphAnalyzer()
        a.build_graph({"a": {"b": 0.5}, "b": {"a": 0.5}})
        assert isinstance(a.find_central_systems(), list)

    def test_get_stats(self):
        a = _load_mod("oracle.evolution.graph_analysis").SystemGraphAnalyzer()
        a.build_graph({"a": {"b": 0.5}, "b": {"a": 0.5}})
        assert isinstance(a.get_stats(), dict)

    def test_no_graph_returns_empty(self):
        a = _load_mod("oracle.evolution.graph_analysis").SystemGraphAnalyzer()
        assert a.find_communities() == []
        assert a.find_central_systems() == []
        assert a.get_stats() == {}


class TestAdvancedCommunityDetector:
    def test_instantiate(self):
        d = _load_mod("oracle.evolution.community_detection").AdvancedCommunityDetector()
        assert hasattr(d, "results_cache")

    def test_compare_algorithms(self):
        mod = _load_mod("oracle.evolution.community_detection")
        d = mod.AdvancedCommunityDetector()
        if not mod.HAS_NETWORKX:
            return
        import networkx as nx
        g = nx.DiGraph()
        g.add_edge("a", "b", weight=0.9)
        g.add_edge("b", "a", weight=0.9)
        r = d.compare_algorithms(g)
        assert isinstance(r, dict)
        assert "louvain" in r or "girvan_newman" in r

    def test_find_optimal_partition(self):
        mod = _load_mod("oracle.evolution.community_detection")
        d = mod.AdvancedCommunityDetector()
        if not mod.HAS_NETWORKX:
            return
        import networkx as nx
        g = nx.DiGraph()
        g.add_edge("a", "b", weight=0.9)
        g.add_edge("b", "a", weight=0.9)
        assert isinstance(d.find_optimal_partition(g), list)

    def test_detect_infomap_no_lib(self):
        d = _load_mod("oracle.evolution.community_detection").AdvancedCommunityDetector()
        assert d.detect_infomap(None) == []

    def test_detect_leiden_no_lib(self):
        d = _load_mod("oracle.evolution.community_detection").AdvancedCommunityDetector()
        assert d.detect_leiden(None) == []


class TestSymPyWrapper:
    def test_instantiate(self):
        w = _load_mod("oracle.evaluation.sympy_wrapper").SymPyWrapper()
        assert w is not None

    def test_symbolic_analysis(self):
        w = _load_mod("oracle.evaluation.sympy_wrapper").SymPyWrapper()
        r = w.symbolic_analysis([1.0, 1.618, 2.618, 4.236])
        assert isinstance(r, dict)
        if "error" not in r:
            assert "golden_ratio" in r and "pi" in r

    def test_prime_analysis(self):
        w = _load_mod("oracle.evaluation.sympy_wrapper").SymPyWrapper()
        r = w.prime_analysis(17)
        assert isinstance(r, dict)
        if "error" not in r:
            assert r["is_prime"] is True

    def test_prime_composite(self):
        w = _load_mod("oracle.evaluation.sympy_wrapper").SymPyWrapper()
        r = w.prime_analysis(12)
        if "error" not in r:
            assert r["is_prime"] is False

    def test_empty_input(self):
        w = _load_mod("oracle.evaluation.sympy_wrapper").SymPyWrapper()
        assert isinstance(w.symbolic_analysis([]), dict)

    def test_prime_zero(self):
        w = _load_mod("oracle.evaluation.sympy_wrapper").SymPyWrapper()
        assert isinstance(w.prime_analysis(0), dict)


class TestMoocoreWrapper:
    def test_instantiate(self):
        w = _load_mod("oracle.evaluation.moocore_wrapper").MoocoreWrapper()
        assert w is not None

    def test_compute(self):
        w = _load_mod("oracle.evaluation.moocore_wrapper").MoocoreWrapper()
        r = w.compute({"seed": 42})
        assert isinstance(r, dict)
        if "error" not in r:
            assert r.get("system_id") == "moocore"
            assert len(r.get("numeric_projection", [])) > 0

    def test_compute_empty(self):
        w = _load_mod("oracle.evaluation.moocore_wrapper").MoocoreWrapper()
        assert isinstance(w.compute({}), dict)

    def test_compute_none(self):
        w = _load_mod("oracle.evaluation.moocore_wrapper").MoocoreWrapper()
        assert isinstance(w.compute(None), dict)
