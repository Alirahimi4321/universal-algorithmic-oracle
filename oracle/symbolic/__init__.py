"""Symbolic Substrate Layer - all ancient/divination system wrappers.

Uses lazy imports to avoid slow startup (30-57s → <1s).
Modules are imported on demand when first accessed.
"""
import importlib
import sys

_LAZY_IMPORTS = {
    # Gematria
    "GematriaWrapper": (".gematria", "GematriaWrapper"),
    "NumerologyWrapper": (".gematria", "NumerologyWrapper"),
    "HebrewGematriaWrapper": (".gematria", "HebrewGematriaWrapper"),
    "EnglishGematriaWrapper": (".gematria", "EnglishGematriaWrapper"),
    "HebrewAdvancedGematriaWrapper": (".gematria.hebrew_advanced", "HebrewAdvancedGematriaWrapper"),
    # Binary
    "IChingWrapper": (".binary", "IChingWrapper"),
    "GeomancyWrapper": (".binary", "GeomancyWrapper"),
    "RamlWrapper": (".binary", "RamlWrapper"),
    "IChingShifaWrapper": (".binary.ichingshifa_wrapper", "IChingShifaWrapper"),
    "IChingLibWrapper": (".binary.iching_lib_wrapper", "IChingLibWrapper"),
    # Astrology
    "CalendarWrapper": (".astrology", "CalendarWrapper"),
    "WesternAstrologyWrapper": (".astrology", "WesternAstrologyWrapper"),
    "VedicAstrologyWrapper": (".astrology", "VedicAstrologyWrapper"),
    "KerykeionAstrologyWrapper": (".astrology.kerykeion_wrapper", "KerykeionAstrologyWrapper"),
    "YaegiKundaliWrapper": (".astrology.yaegi_wrapper", "YaegiKundaliWrapper"),
    "YaegiPanchangWrapper": (".astrology.yaegi_wrapper", "YaegiPanchangWrapper"),
    "SkyfieldAstronomyWrapper": (".astrology.skyfield_wrapper", "SkyfieldAstronomyWrapper"),
    "AstralWrapper": (".astrology.astral_wrapper", "AstralWrapper"),
    "EphemWrapper": (".astrology.ephem_wrapper", "EphemWrapper"),
    "FalakpyWrapper": (".astrology.falak_wrapper", "FalakpyWrapper"),
    "KetuAstronomyWrapper": (".astrology.ketu_wrapper", "KetuAstronomyWrapper"),
    "VedAstroWrapper": (".astrology.vedastro_wrapper", "VedAstroWrapper"),
    "FlatlibWrapper": (".astrology.flatlib_wrapper", "FlatlibWrapper"),
    "NdastroWrapper": (".astrology.ndastro_wrapper", "NdastroWrapper"),
    "LibephemerisWrapper": (".astrology.libephemeris_wrapper", "LibephemerisWrapper"),
    # Cards
    "TarotWrapper": (".cards", "TarotWrapper"),
    "RunesWrapper": (".cards", "RunesWrapper"),
    "LenormandWrapper": (".cards", "LenormandWrapper"),
    "AIDivinationTarotWrapper": (".cards.ai_divination_wrapper", "AIDivinationTarotWrapper"),
    "AIDivinationIChingWrapper": (".cards.ai_divination_wrapper", "AIDivinationIChingWrapper"),
    "AIDivinationXiaoLiuRenWrapper": (".cards.ai_divination_wrapper", "AIDivinationXiaoLiuRenWrapper"),
    "AIDivinationCombinedWrapper": (".cards.ai_divination_wrapper_new", "AIDivinationCombinedWrapper"),
    "TarotOracleWrapper": (".cards.tarot_oracle_wrapper", "TarotOracleWrapper"),
    "ArcaniteWrapper": (".cards.arcanite_wrapper", "ArcaniteWrapper"),
    # Eastern
    "BaZiWrapper": (".eastern", "BaZiWrapper"),
    "ZiWeiWrapper": (".eastern", "ZiWeiWrapper"),
    "QiMenWrapper": (".eastern", "QiMenWrapper"),
    "LunarCalendarWrapper": (".eastern", "LunarCalendarWrapper"),
    "TianjiBaZiWrapper": (".eastern.tianji_wrapper", "TianjiBaZiWrapper"),
    "TianjiZiWeiWrapper": (".eastern.tianji_wrapper", "TianjiZiWeiWrapper"),
    "TianjiQiMenWrapper": (".eastern.tianji_wrapper", "TianjiQiMenWrapper"),
    "TianjiLiuRenWrapper": (".eastern.tianji_wrapper", "TianjiLiuRenWrapper"),
    "KoreanSajuWrapper": (".eastern.korean_saju_wrapper", "KoreanSajuWrapper"),
    "HijriCalendarWrapper": (".eastern.hijri", "HijriCalendarWrapper"),
    "JalaliCalendarWrapper": (".eastern.jalali", "JalaliCalendarWrapper"),
    "JalaliCoreWrapper": (".eastern.jalali_core_wrapper", "JalaliCoreWrapper"),
    "SxtwlWrapper": (".eastern.sxtwl_wrapper", "SxtwlWrapper"),
    "HolidaysWrapper": (".eastern.holidays_wrapper", "HolidaysWrapper"),
    "LunarDateWrapper": (".eastern.lunardate_wrapper", "LunarDateWrapper"),
    # Mayan
    "TzolkinWrapper": (".mayan", "TzolkinWrapper"),
    "LongCountWrapper": (".mayan", "LongCountWrapper"),
    "PohualliWrapper": (".mayan.pohualli_wrapper", "PohualliWrapper"),
    "MayacalWrapper": (".mayan.mayacal_wrapper", "MayacalWrapper"),
    # Dreams
    "DreamSymbolsWrapper": (".dreams", "DreamSymbolsWrapper"),
    # Fortune Telling
    "FortuneTellingCoreWrapper": (".fortune_telling", "FortuneTellingCoreWrapper"),
    # Divination
    "HafezWrapper": (".divination.hafez_wrapper", "HafezWrapper"),
    "OpenDivinationWrapper": (".divination.opendivination_wrapper", "OpenDivinationWrapper"),
    "SixLineWrapper": (".divicast_wrapper", "SixLineWrapper"),
    # Numerical
    "FiguratePlaneWrapper": (".numerical", "FiguratePlaneWrapper"),
    "FigurateSpaceWrapper": (".numerical", "FigurateSpaceWrapper"),
    "RomanizeWrapper": (".numerical.romanize_wrapper", "RomanizeWrapper"),
    "RomanNumeralWrapper": (".numerical.roman_wrapper", "RomanNumeralWrapper"),
    "PythagoreanNumerologyWrapper": (".numerical.pythagorean_wrapper", "PythagoreanNumerologyWrapper"),
    # Ogham
    "OghamWrapper": (".binary.ogham_wrapper", "OghamWrapper"),
    # Stellium/JyotishGanit
    "StelliumWrapper": (".astrology.stellium_wrapper", "StelliumWrapper"),
    "JyotishGanitWrapper": (".astrology.jyotishganit_wrapper", "JyotishGanitWrapper"),
    # Gematria Engine
    "GematriaEngineWrapper": (".gematria.gematria_engine_wrapper", "GematriaEngineWrapper"),
    # Hebrew Numbers
    "HebrewNumbersWrapper": (".gematria.hebrew_numbers_wrapper", "HebrewNumbersWrapper"),
    # Tarot Card Meanings
    "TarotCardMeaningsWrapper": (".cards.tarot_meanings_wrapper", "TarotCardMeaningsWrapper"),
    # Lunar MCP
    "LunarMCPWrapper": (".eastern.lunar_mcp_wrapper", "LunarMCPWrapper"),
}

__all__ = list(_LAZY_IMPORTS.keys())


def __getattr__(name):
    if name in _LAZY_IMPORTS:
        module_path, attr_name = _LAZY_IMPORTS[name]
        try:
            mod = importlib.import_module(module_path, package=__name__)
            return getattr(mod, attr_name)
        except Exception as e:
            raise ImportError(f"Could not import {name} from {module_path}: {e}") from e
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__():
    return list(__all__)
