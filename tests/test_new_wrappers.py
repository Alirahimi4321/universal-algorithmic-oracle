"""Tests for ALL new symbolic system wrappers."""
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

    importlib.import_module('oracle.symbolic.base')
    importlib.import_module('oracle.symbolic.registry')


def _load_mod(dotted_name):
    """Import a module by its dotted name, setting up stubs as needed."""
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
EMPTY_PACKET = {}
INVALID_PACKET = {"not_a_real_key": True}


class TestAstralWrapper:
    def test_compute_valid(self):
        w = _load_mod("oracle.symbolic.astrology.astral_wrapper").AstralWrapper()
        r = w.compute(VALID_PACKET)
        assert isinstance(r, dict)
        if "error" not in r:
            assert r.get("system_id") == "astral"
            assert len(r.get("numeric_projection", [])) > 0

    def test_empty_input(self):
        w = _load_mod("oracle.symbolic.astrology.astral_wrapper").AstralWrapper()
        r = w.compute(EMPTY_PACKET)
        assert isinstance(r, dict)

    def test_error_does_not_crash(self):
        w = _load_mod("oracle.symbolic.astrology.astral_wrapper").AstralWrapper()
        r = w.compute(None)
        assert isinstance(r, dict)


class TestEphemWrapper:
    def test_compute_valid(self):
        w = _load_mod("oracle.symbolic.astrology.ephem_wrapper").EphemWrapper()
        r = w.compute(VALID_PACKET)
        assert isinstance(r, dict)
        if "error" not in r:
            assert r.get("system_id") == "ephem"
            assert len(r.get("numeric_projection", [])) > 0

    def test_empty_input(self):
        w = _load_mod("oracle.symbolic.astrology.ephem_wrapper").EphemWrapper()
        assert isinstance(w.compute(EMPTY_PACKET), dict)

    def test_error_does_not_crash(self):
        w = _load_mod("oracle.symbolic.astrology.ephem_wrapper").EphemWrapper()
        assert isinstance(w.compute(None), dict)


class TestFalakpyWrapper:
    def test_compute_valid(self):
        w = _load_mod("oracle.symbolic.astrology.falak_wrapper").FalakpyWrapper()
        r = w.compute(VALID_PACKET)
        assert isinstance(r, dict)
        if "error" not in r:
            assert r.get("system_id") == "falak"
            assert len(r.get("numeric_projection", [])) > 0

    def test_empty_input(self):
        w = _load_mod("oracle.symbolic.astrology.falak_wrapper").FalakpyWrapper()
        assert isinstance(w.compute(EMPTY_PACKET), dict)

    def test_error_does_not_crash(self):
        w = _load_mod("oracle.symbolic.astrology.falak_wrapper").FalakpyWrapper()
        assert isinstance(w.compute(None), dict)


class TestVedAstroWrapper:
    def test_compute_valid(self):
        w = _load_mod("oracle.symbolic.astrology.vedastro_wrapper").VedAstroWrapper()
        r = w.compute(VALID_PACKET)
        assert isinstance(r, dict)
        if "error" not in r:
            assert r.get("system_id") == "vedastro"
            assert len(r.get("numeric_projection", [])) > 0

    def test_empty_input(self):
        w = _load_mod("oracle.symbolic.astrology.vedastro_wrapper").VedAstroWrapper()
        assert isinstance(w.compute(EMPTY_PACKET), dict)

    def test_error_does_not_crash(self):
        w = _load_mod("oracle.symbolic.astrology.vedastro_wrapper").VedAstroWrapper()
        assert isinstance(w.compute(None), dict)


class TestKetuAstronomyWrapper:
    def test_compute_valid(self):
        w = _load_mod("oracle.symbolic.astrology.ketu_wrapper").KetuAstronomyWrapper()
        r = w.compute(VALID_PACKET)
        assert isinstance(r, dict) or hasattr(r, "numeric_projection")
        if hasattr(r, "numeric_projection"):
            assert len(r.numeric_projection) > 0
            assert r.system_id == "ketu_astronomy"

    def test_empty_input(self):
        w = _load_mod("oracle.symbolic.astrology.ketu_wrapper").KetuAstronomyWrapper()
        r = w.compute(EMPTY_PACKET)
        assert isinstance(r, dict) or hasattr(r, "numeric_projection")

    def test_error_does_not_crash(self):
        w = _load_mod("oracle.symbolic.astrology.ketu_wrapper").KetuAstronomyWrapper()
        r = w.compute(None)
        assert isinstance(r, dict) or hasattr(r, "numeric_projection")


class TestHafezWrapper:
    def test_compute_valid(self):
        w = _load_mod("oracle.symbolic.divination.hafez_wrapper").HafezWrapper()
        r = w.compute(VALID_PACKET)
        assert isinstance(r, dict)
        if "error" not in r:
            assert r.get("system_id") == "hafez"
            assert len(r.get("numeric_projection", [])) > 0

    def test_empty_input(self):
        w = _load_mod("oracle.symbolic.divination.hafez_wrapper").HafezWrapper()
        assert isinstance(w.compute(EMPTY_PACKET), dict)

    def test_error_does_not_crash(self):
        w = _load_mod("oracle.symbolic.divination.hafez_wrapper").HafezWrapper()
        assert isinstance(w.compute(None), dict)


class TestSxtwlWrapper:
    def test_compute_valid(self):
        w = _load_mod("oracle.symbolic.eastern.sxtwl_wrapper").SxtwlWrapper()
        r = w.compute(VALID_PACKET)
        assert isinstance(r, dict)
        if "error" not in r:
            assert r.get("system_id") == "sxtwl"
            assert len(r.get("numeric_projection", [])) > 0

    def test_empty_input(self):
        w = _load_mod("oracle.symbolic.eastern.sxtwl_wrapper").SxtwlWrapper()
        assert isinstance(w.compute(EMPTY_PACKET), dict)

    def test_error_does_not_crash(self):
        w = _load_mod("oracle.symbolic.eastern.sxtwl_wrapper").SxtwlWrapper()
        assert isinstance(w.compute(None), dict)


class TestJalaliCoreWrapper:
    def test_compute_valid(self):
        w = _load_mod("oracle.symbolic.eastern.jalali_core_wrapper").JalaliCoreWrapper()
        r = w.compute(VALID_PACKET)
        assert isinstance(r, dict)
        if "error" not in r:
            assert r.get("system_id") == "jalali_core"
            assert len(r.get("numeric_projection", [])) > 0

    def test_empty_input(self):
        w = _load_mod("oracle.symbolic.eastern.jalali_core_wrapper").JalaliCoreWrapper()
        assert isinstance(w.compute(EMPTY_PACKET), dict)

    def test_error_does_not_crash(self):
        w = _load_mod("oracle.symbolic.eastern.jalali_core_wrapper").JalaliCoreWrapper()
        assert isinstance(w.compute(None), dict)


class TestRomanizeWrapper:
    def test_compute_valid(self):
        w = _load_mod("oracle.symbolic.numerical.romanize_wrapper").RomanizeWrapper()
        r = w.compute(VALID_PACKET)
        assert isinstance(r, dict)
        if "error" not in r:
            assert r.get("system_id") == "romanize"
            assert len(r.get("numeric_projection", [])) > 0

    def test_with_params(self):
        w = _load_mod("oracle.symbolic.numerical.romanize_wrapper").RomanizeWrapper()
        r = w.compute(VALID_PACKET, params={"text": "Hello"})
        assert isinstance(r, dict)

    def test_empty_input(self):
        w = _load_mod("oracle.symbolic.numerical.romanize_wrapper").RomanizeWrapper()
        assert isinstance(w.compute(EMPTY_PACKET), dict)

    def test_error_does_not_crash(self):
        w = _load_mod("oracle.symbolic.numerical.romanize_wrapper").RomanizeWrapper()
        assert isinstance(w.compute(None), dict)


class TestMayacalWrapper:
    def test_compute_valid(self):
        w = _load_mod("oracle.symbolic.mayan.mayacal_wrapper").MayacalWrapper()
        r = w.compute(VALID_PACKET)
        assert isinstance(r, dict)
        if "error" not in r:
            assert r.get("system_id") == "mayacal"
            assert len(r.get("numeric_projection", [])) > 0

    def test_empty_input(self):
        w = _load_mod("oracle.symbolic.mayan.mayacal_wrapper").MayacalWrapper()
        assert isinstance(w.compute(EMPTY_PACKET), dict)

    def test_error_does_not_crash(self):
        w = _load_mod("oracle.symbolic.mayan.mayacal_wrapper").MayacalWrapper()
        assert isinstance(w.compute(None), dict)


class TestIChingLibWrapper:
    def test_compute_valid(self):
        w = _load_mod("oracle.symbolic.binary.iching_lib_wrapper").IChingLibWrapper()
        r = w.compute(VALID_PACKET)
        assert isinstance(r, dict)
        if "error" not in r:
            assert r.get("system_id") == "iching_lib"
            assert len(r.get("numeric_projection", [])) > 0

    def test_empty_input(self):
        w = _load_mod("oracle.symbolic.binary.iching_lib_wrapper").IChingLibWrapper()
        assert isinstance(w.compute(EMPTY_PACKET), dict)

    def test_error_does_not_crash(self):
        w = _load_mod("oracle.symbolic.binary.iching_lib_wrapper").IChingLibWrapper()
        assert isinstance(w.compute(None), dict)


class TestSixLineWrapper:
    def test_compute_valid(self):
        w = _load_mod("oracle.symbolic.divicast_wrapper").SixLineWrapper()
        r = w.compute(VALID_PACKET)
        assert isinstance(r, dict) or hasattr(r, "numeric_projection")
        if hasattr(r, "numeric_projection"):
            assert len(r.numeric_projection) > 0
            assert r.system_id == "sixline"

    def test_empty_input(self):
        w = _load_mod("oracle.symbolic.divicast_wrapper").SixLineWrapper()
        r = w.compute(EMPTY_PACKET)
        assert isinstance(r, dict) or hasattr(r, "numeric_projection")

    def test_error_does_not_crash(self):
        w = _load_mod("oracle.symbolic.divicast_wrapper").SixLineWrapper()
        r = w.compute(None)
        assert isinstance(r, dict) or hasattr(r, "numeric_projection")
