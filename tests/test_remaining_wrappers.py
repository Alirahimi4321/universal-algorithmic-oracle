"""Tests for the 6 remaining wrappers: flatlib, ndastro, libephemeris, ogham, opendivination, arcanite."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pytest
from oracle.symbolic.base import SymbolicOutput


def get_result_data(result):
    """Extract data from either dict or SymbolicOutput."""
    if isinstance(result, SymbolicOutput):
        return result.to_dict()
    elif isinstance(result, dict):
        return result
    return {}


class TestFlatlibWrapper:
    def test_import(self):
        from oracle.symbolic.astrology.flatlib_wrapper import FlatlibWrapper
        w = FlatlibWrapper()
        assert w.SYSTEM_ID == "flatlib_astrology"

    def test_compute_returns_output(self):
        from oracle.symbolic.astrology.flatlib_wrapper import FlatlibWrapper
        w = FlatlibWrapper()
        result = w.compute({"seed": 42})
        data = get_result_data(result)
        assert "numeric_projection" in data or "symbolic_state" in data

    def test_no_params(self):
        from oracle.symbolic.astrology.flatlib_wrapper import FlatlibWrapper
        w = FlatlibWrapper()
        result = w.compute({"seed": 100})
        assert result is not None


class TestNdastroWrapper:
    def test_import(self):
        from oracle.symbolic.astrology.ndastro_wrapper import NdastroWrapper
        w = NdastroWrapper()
        assert w.SYSTEM_ID == "ndastro_vedic"

    def test_compute_returns_output(self):
        from oracle.symbolic.astrology.ndastro_wrapper import NdastroWrapper
        w = NdastroWrapper()
        result = w.compute({"seed": 42})
        data = get_result_data(result)
        assert "numeric_projection" in data or "symbolic_state" in data

    def test_with_params(self):
        from oracle.symbolic.astrology.ndastro_wrapper import NdastroWrapper
        w = NdastroWrapper()
        result = w.compute({"seed": 55}, params={"extra": True})
        assert result is not None


class TestLibephemerisWrapper:
    def test_import(self):
        from oracle.symbolic.astrology.libephemeris_wrapper import LibephemerisWrapper
        w = LibephemerisWrapper()
        assert w.SYSTEM_ID == "libephemeris_astrology"

    def test_compute_returns_output(self):
        from oracle.symbolic.astrology.libephemeris_wrapper import LibephemerisWrapper
        w = LibephemerisWrapper()
        result = w.compute({"seed": 42})
        data = get_result_data(result)
        assert "numeric_projection" in data or "symbolic_state" in data

    def test_numeric_projection(self):
        from oracle.symbolic.astrology.libephemeris_wrapper import LibephemerisWrapper
        w = LibephemerisWrapper()
        result = w.compute({"seed": 77})
        data = get_result_data(result)
        if "numeric_projection" in data:
            assert len(data["numeric_projection"]) > 0


class TestOghamWrapper:
    def test_import(self):
        from oracle.symbolic.binary.ogham_wrapper import OghamWrapper
        w = OghamWrapper()
        assert w.SYSTEM_ID == "ogham"

    def test_compute_returns_output(self):
        from oracle.symbolic.binary.ogham_wrapper import OghamWrapper
        w = OghamWrapper()
        result = w.compute({"seed": 42})
        data = get_result_data(result)
        assert "numeric_projection" in data or "symbolic_state" in data

    def test_with_question(self):
        from oracle.symbolic.binary.ogham_wrapper import OghamWrapper
        w = OghamWrapper()
        result = w.compute({"seed": 1, "question": "hello world"})
        assert result is not None


class TestOpenDivinationWrapper:
    def test_import(self):
        from oracle.symbolic.divination.opendivination_wrapper import OpenDivinationWrapper
        w = OpenDivinationWrapper()
        assert w.SYSTEM_ID == "opendivination_iching"

    def test_compute_returns_output(self):
        from oracle.symbolic.divination.opendivination_wrapper import OpenDivinationWrapper
        w = OpenDivinationWrapper()
        result = w.compute({"seed": 42})
        data = get_result_data(result)
        assert "numeric_projection" in data or "symbolic_state" in data

    def test_with_method(self):
        from oracle.symbolic.divination.opendivination_wrapper import OpenDivinationWrapper
        w = OpenDivinationWrapper()
        result = w.compute({"seed": 10}, params={"method": "three_coin"})
        assert result is not None


class TestArcaniteWrapper:
    def test_import(self):
        from oracle.symbolic.cards.arcanite_wrapper import ArcaniteWrapper
        w = ArcaniteWrapper()
        assert w.SYSTEM_ID == "arcanite_tarot"

    def test_compute_returns_output(self):
        from oracle.symbolic.cards.arcanite_wrapper import ArcaniteWrapper
        w = ArcaniteWrapper()
        result = w.compute({"seed": 42})
        data = get_result_data(result)
        assert "numeric_projection" in data or "symbolic_state" in data

    def test_with_spread(self):
        from oracle.symbolic.cards.arcanite_wrapper import ArcaniteWrapper
        w = ArcaniteWrapper()
        result = w.compute({"seed": 20}, params={"spread": "past-present-future"})
        assert result is not None


class TestRegistry:
    def test_all_new_systems_registered(self):
        from oracle.symbolic.registry import register_all, _classes
        register_all()
        new_systems = [
            "flatlib_astrology", "ndastro_vedic", "libephemeris_astrology",
            "ogham", "opendivination_iching", "arcanite_tarot",
        ]
        for sys_id in new_systems:
            assert sys_id in _classes, f"{sys_id} not registered"

    def test_total_system_count(self):
        from oracle.symbolic.registry import register_all, _classes
        register_all()
        assert len(_classes) >= 59, f"Expected >= 59 systems, got {len(_classes)}"

    def test_get_system_works(self):
        from oracle.symbolic.registry import get_system
        for sys_id in ["flatlib_astrology", "ogham", "arcanite_tarot"]:
            s = get_system(sys_id)
            assert s is not None, f"get_system({sys_id}) returned None"
