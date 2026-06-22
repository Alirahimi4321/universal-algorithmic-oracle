"""Registry for all symbolic system wrappers.

Uses lazy registration - systems are registered when first accessed
or when register_all() is called.
"""
import functools
import importlib
import logging
from typing import Type
from .base import SymbolicSystemWrapper
from ..config_validator import validate_systems_config


_registry: dict[str, SymbolicSystemWrapper] = {}
_classes: dict[str, Type[SymbolicSystemWrapper]] = {}
_registered_all = False
logger = logging.getLogger("oracle.symbolic.registry")


def register_system(cls: Type[SymbolicSystemWrapper]) -> Type[SymbolicSystemWrapper]:
    _classes[cls.SYSTEM_ID] = cls
    return cls


@functools.lru_cache(maxsize=1)
def register_all():
    """Import all wrapper modules to trigger @register_system decorators."""
    global _registered_all
    
    modules = [
        ".gematria",
        ".gematria.hebrew_advanced",
        ".binary",
        ".binary.ichingshifa_wrapper",
        ".binary.iching_lib_wrapper",
        ".astrology",
        ".astrology.kerykeion_wrapper",
        ".astrology.yaegi_wrapper",
        ".astrology.skyfield_wrapper",
        ".astrology.astral_wrapper",
        ".astrology.ephem_wrapper",
        ".astrology.falak_wrapper",
        ".astrology.ketu_wrapper",
        ".astrology.vedastro_wrapper",
        ".astrology.flatlib_wrapper",
        ".astrology.ndastro_wrapper",
        ".astrology.libephemeris_wrapper",
        ".astrology.stellium_wrapper",
        ".astrology.jyotishganit_wrapper",
        ".cards",
        ".cards.ai_divination_wrapper",
        ".cards.ai_divination_wrapper_new",
        ".cards.tarot_oracle_wrapper",
        ".cards.arcanite_wrapper",
        ".cards.tarot_meanings_wrapper",
        ".gematria.gematria_engine_wrapper",
        ".gematria.hebrew_numbers_wrapper",
        ".eastern",
        ".eastern.tianji_wrapper",
        ".eastern.korean_saju_wrapper",
        ".eastern.hijri",
        ".eastern.jalali",
        ".eastern.jalali_core_wrapper",
        ".eastern.sxtwl_wrapper",
        ".eastern.lunar_mcp_wrapper",
        ".eastern.holidays_wrapper",
        ".eastern.lunardate_wrapper",
        ".mayan",
        ".mayan.pohualli_wrapper",
        ".mayan.mayacal_wrapper",
        ".dreams",
        ".fortune_telling",
        ".divination.hafez_wrapper",
        ".divination.opendivination_wrapper",
        ".divicast_wrapper",
        ".numerical",
        ".numerical.romanize_wrapper",
        ".numerical.roman_wrapper",
        ".numerical.pythagorean_wrapper",
        ".binary.ogham_wrapper",
        ".persian.proces_wrapper",
        ".eastern.purplestar_wrapper",
        ".eastern.rokh_wrapper",
        ".numerical.numero_fun_wrapper",
        ".sigil.sigillin_wrapper",
        ".analysis.pyitlib_wrapper",
        ".analysis.syntropy_wrapper",
        ".text.grapheme_wrapper",
        ".cards.pytarot_wrapper",
        ".mayan.mayacalendar_wrapper",
        ".nlp.spacy_wrapper",
        ".nlp.sentence_transformer_wrapper",
        ".nlp.langdetect_wrapper",
        ".eastern.kintaiyi_wrapper",
        ".eastern.kinliuren_wrapper",
        ".eastern.lunar_python_wrapper",
        ".astrology.nataly_wrapper",
        ".astrology.pyjhora_wrapper",
        ".astrology.pyvo_wrapper",
        ".eastern.khayyam_wrapper",
        ".eastern.lunarcalendar_wrapper",
        ".cards.tarot_oracle_ai_wrapper",
        ".cards.tarot_meanings_db_wrapper",
        ".eastern.cn2an_wrapper",
        ".eastern.cnlunar_wrapper",
        ".eastern.zhdate_wrapper",
        ".eastern.chinese_calendar_wrapper",
        ".eastern.iztro_wrapper",
        ".binary.riimut_wrapper",
        ".persian.persiantools_wrapper",
        ".eastern.meihua_wrapper",
        ".eastern.sajupy_wrapper",
        ".gematria.gematriapy_wrapper",
        ".cards.tarotteller_wrapper",
        ".cards.cli_tarot_wrapper",
        ".eastern.ziwei_stars_wrapper",
        ".gematria.hebrew_gematria_wrapper",
        ".gematria.pygematria_wrapper",
    ]
    
    for mod_path in modules:
        try:
            importlib.import_module(mod_path, package='oracle.symbolic')
        except Exception:
            pass  # Skip modules that fail to import
    
    _registered_all = True


def get_system(system_id: str) -> SymbolicSystemWrapper | None:
    if system_id not in _registry:
        if system_id in _classes:
            _registry[system_id] = _classes[system_id]()
        else:
            # Try registering all systems if this one isn't found
            register_all()
            if system_id in _classes:
                _registry[system_id] = _classes[system_id]()
            else:
                return None
    return _registry[system_id]


def list_systems() -> list[str]:
    register_all()
    return list(_classes.keys())


def compute_system(system_id: str, entropy_packet: dict, params: dict | None = None):
    system = get_system(system_id)
    if system is None:
        raise ValueError(f"Unknown symbolic system: {system_id}")
    return system.compute(entropy_packet, params)
