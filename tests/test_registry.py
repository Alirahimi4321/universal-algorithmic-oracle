"""Tests for the symbolic system registry."""
import sys
import os
import types
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


VALID_PACKET = {
    "bit_stream": [1, 0, 1] * 10,
    "seed": 42,
    "numeric_vector": [1, 2, 3, 4, 5],
    "normalized_text": "hello world",
    "calendar_context": {"year": 2024, "month": 6, "day": 15, "hour": 12},
    "timestamp": 0,
}


class TestRegistry:
    def test_imports_successfully(self):
        mod = _load_mod("oracle.symbolic.registry")
        assert hasattr(mod, "register_all")
        assert hasattr(mod, "list_systems")
        assert hasattr(mod, "get_system")
        assert hasattr(mod, "compute_system")

    def test_register_all(self):
        mod = _load_mod("oracle.symbolic.registry")
        mod.register_all()
        systems = mod.list_systems()
        assert isinstance(systems, list)
        assert len(systems) >= 25, f"Expected >= 25 systems, got {len(systems)}"

    def test_list_systems_contains_known(self):
        mod = _load_mod("oracle.symbolic.registry")
        mod.register_all()
        systems = mod.list_systems()
        for expected in ["astral", "ephem", "hafez", "sixline", "romanize", "mayacal"]:
            assert expected in systems, f"Expected '{expected}' not in {systems}"

    def test_get_system_returns_none_for_unknown(self):
        mod = _load_mod("oracle.symbolic.registry")
        assert mod.get_system("nonexistent_system_xyz_99999") is None

    def test_get_system_returns_wrapper(self):
        mod = _load_mod("oracle.symbolic.registry")
        mod.register_all()
        systems = mod.list_systems()
        for sid in ["astral", "ephem", "hafez", "sixline"]:
            if sid in systems:
                w = mod.get_system(sid)
                assert w is not None
                return

    def test_compute_system_raises_for_unknown(self):
        mod = _load_mod("oracle.symbolic.registry")
        try:
            mod.compute_system("nonexistent_system_xyz_99999", VALID_PACKET)
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "Unknown symbolic system" in str(e)

    def test_compute_system_with_known(self):
        mod = _load_mod("oracle.symbolic.registry")
        mod.register_all()
        for sid in ["astral", "ephem", "hafez", "sixline"]:
            if sid in mod.list_systems():
                r = mod.compute_system(sid, VALID_PACKET)
                assert r is not None
                if hasattr(r, "system_id"):
                    assert r.system_id == sid
                elif isinstance(r, dict):
                    assert "error" in r or r.get("system_id") == sid
                return

    def test_registry_classes_populated(self):
        mod = _load_mod("oracle.symbolic.registry")
        mod.register_all()
        assert len(mod._classes) >= 25
        assert all(isinstance(cls, type) for cls in mod._classes.values())

    def test_no_duplicate_registration(self):
        mod = _load_mod("oracle.symbolic.registry")
        c1 = len(mod.list_systems())
        assert c1 >= 25
        mod.register_all()
        c2 = len(mod.list_systems())
        assert c1 == c2
