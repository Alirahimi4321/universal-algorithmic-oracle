"""Tests for Phase 10 wrappers: stellium, jyotishganit, gematria_engine, hebrew_numbers, tarot_meanings, lunar_mcp."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pytest
from oracle.symbolic.base import SymbolicOutput
from oracle.symbolic.registry import get_system, list_systems, register_all


def get_result_data(result):
    """Extract data from either dict or SymbolicOutput."""
    if isinstance(result, SymbolicOutput):
        return result.to_dict()
    elif isinstance(result, dict):
        return result
    return {}


class TestStelliumWrapper:
    def test_import(self):
        from oracle.symbolic.astrology.stellium_wrapper import StelliumWrapper
        w = StelliumWrapper()
        assert w.SYSTEM_ID == "stellium_astrology"

    def test_compute_returns_output(self):
        from oracle.symbolic.astrology.stellium_wrapper import StelliumWrapper
        w = StelliumWrapper()
        result = w.compute({"seed": 42})
        data = get_result_data(result)
        assert "numeric_projection" in data or "symbolic_state" in data

    def test_with_params(self):
        from oracle.symbolic.astrology.stellium_wrapper import StelliumWrapper
        w = StelliumWrapper()
        result = w.compute({"seed": 55}, params={"extra": True})
        assert result is not None


class TestJyotishGanitWrapper:
    def test_import(self):
        from oracle.symbolic.astrology.jyotishganit_wrapper import JyotishGanitWrapper
        w = JyotishGanitWrapper()
        assert w.SYSTEM_ID == "jyotishganit_vedic"

    def test_compute_returns_output(self):
        from oracle.symbolic.astrology.jyotishganit_wrapper import JyotishGanitWrapper
        w = JyotishGanitWrapper()
        result = w.compute({"seed": 42})
        data = get_result_data(result)
        assert "numeric_projection" in data or "symbolic_state" in data

    def test_no_params(self):
        from oracle.symbolic.astrology.jyotishganit_wrapper import JyotishGanitWrapper
        w = JyotishGanitWrapper()
        result = w.compute({"seed": 100})
        assert result is not None


class TestGematriaEngineWrapper:
    def test_import(self):
        from oracle.symbolic.gematria.gematria_engine_wrapper import GematriaEngineWrapper
        w = GematriaEngineWrapper()
        assert w.SYSTEM_ID == "gematria_engine"

    def test_compute_returns_output(self):
        from oracle.symbolic.gematria.gematria_engine_wrapper import GematriaEngineWrapper
        w = GematriaEngineWrapper()
        result = w.compute({"seed": 42})
        data = get_result_data(result)
        assert "numeric_projection" in data or "symbolic_state" in data

    def test_with_text_input(self):
        from oracle.symbolic.gematria.gematria_engine_wrapper import GematriaEngineWrapper
        w = GematriaEngineWrapper()
        result = w.compute({"seed": 42}, params={"text": "hello"})
        assert result is not None


class TestHebrewNumbersWrapper:
    def test_import(self):
        from oracle.symbolic.gematria.hebrew_numbers_wrapper import HebrewNumbersWrapper
        w = HebrewNumbersWrapper()
        assert w.SYSTEM_ID == "hebrew_numbers"

    def test_compute_returns_output(self):
        from oracle.symbolic.gematria.hebrew_numbers_wrapper import HebrewNumbersWrapper
        w = HebrewNumbersWrapper()
        result = w.compute({"seed": 42})
        data = get_result_data(result)
        assert "numeric_projection" in data or "symbolic_state" in data

    def test_with_params(self):
        from oracle.symbolic.gematria.hebrew_numbers_wrapper import HebrewNumbersWrapper
        w = HebrewNumbersWrapper()
        result = w.compute({"seed": 77}, params={"extra": True})
        assert result is not None


class TestTarotCardMeaningsWrapper:
    def test_import(self):
        from oracle.symbolic.cards.tarot_meanings_wrapper import TarotCardMeaningsWrapper
        w = TarotCardMeaningsWrapper()
        assert w.SYSTEM_ID == "tarot_card_meanings"

    def test_compute_returns_output(self):
        from oracle.symbolic.cards.tarot_meanings_wrapper import TarotCardMeaningsWrapper
        w = TarotCardMeaningsWrapper()
        result = w.compute({"seed": 42})
        data = get_result_data(result)
        assert "numeric_projection" in data or "symbolic_state" in data

    def test_with_seed(self):
        from oracle.symbolic.cards.tarot_meanings_wrapper import TarotCardMeaningsWrapper
        w = TarotCardMeaningsWrapper()
        result = w.compute({"seed": 99})
        assert result is not None


class TestLunarMCPWrapper:
    def test_import(self):
        from oracle.symbolic.eastern.lunar_mcp_wrapper import LunarMCPWrapper
        w = LunarMCPWrapper()
        assert w.SYSTEM_ID == "lunar_mcp"

    def test_compute_returns_output(self):
        from oracle.symbolic.eastern.lunar_mcp_wrapper import LunarMCPWrapper
        w = LunarMCPWrapper()
        result = w.compute({"seed": 42})
        data = get_result_data(result)
        assert "numeric_projection" in data or "symbolic_state" in data

    def test_with_date_input(self):
        from oracle.symbolic.eastern.lunar_mcp_wrapper import LunarMCPWrapper
        w = LunarMCPWrapper()
        result = w.compute({"seed": 42}, params={"year": 2025, "month": 1, "day": 1})
        assert result is not None


class TestAllPhase10Registered:
    @pytest.fixture(autouse=True)
    def _setup(self):
        register_all()
        self.systems = list_systems()

    def test_stellium_registered(self):
        assert "stellium_astrology" in self.systems

    def test_jyotishganit_registered(self):
        assert "jyotishganit_vedic" in self.systems

    def test_gematria_engine_registered(self):
        assert "gematria_engine" in self.systems

    def test_hebrew_numbers_registered(self):
        assert "hebrew_numbers" in self.systems

    def test_tarot_card_meanings_registered(self):
        assert "tarot_card_meanings" in self.systems

    def test_lunar_mcp_registered(self):
        assert "lunar_mcp" in self.systems

    def test_total_systems_count(self):
        assert len(self.systems) >= 60
