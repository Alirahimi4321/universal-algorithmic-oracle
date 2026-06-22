"""Hebrew Gematria advanced wrapper – 23 gematria types via the `hebrew` library."""
from ..base import SymbolicSystemWrapper, SymbolicOutput
from ..registry import register_system


_GEMATRIA_TYPES = [
    "mispar_prati",
    "mispar_katan",
    "mispar_kolel",
    "mispar_gadol",
    "mispar_musafi",
    "mispar_hadolot",
    "mispar_siderot",
    "mispar_boneh",
    "atbash",
    "albam",
    "mispar_ashkenazi",
    "mispar_sephardi",
    "mispar_mispar",
    "mispar_shemi",
    "mispar_network",
    "gematria_mispar_prati",
    "gematria_mispar_katan",
    "gematria_mispar_gadol",
    "gematria_mispar_mispar",
    "gematria_atbash",
    "gematria_albam",
    "gematria_sephardi",
    "mispar_katan_sofit",
]


def _fallback_gematria(text: str) -> dict:
    """Internal fallback when the `hebrew` library is not installed."""
    _map = {
        "א": 1, "ב": 2, "ג": 3, "ד": 4, "ה": 5, "ו": 6, "ז": 7,
        "ח": 8, "ט": 9, "י": 10, "כ": 20, "ל": 30, "מ": 40, "נ": 50,
        "ס": 60, "ע": 70, "פ": 80, "צ": 90, "ק": 100, "ר": 200, "ש": 300,
        "ת": 400, "ך": 20, "ם": 40, "ן": 50, "ף": 80, "ץ": 90,
    }
    standard = sum(_map.get(c, 0) for c in text)
    digits = [int(d) for d in str(standard)]
    katan = sum(digits)
    gadol = standard + 9 * (len(text) - 1) if text else standard

    return {
        "mispar_prati": standard,
        "mispar_katan": katan,
        "mispar_kolel": standard + len(text),
        "mispar_gadol": gadol,
        "mispar_musafi": standard + sum(range(1, len(text) + 1)),
        "mispar_hadolot": standard + 9,
        "mispar_siderot": katan + 9,
        "mispar_boneh": sum(sorted(digits)[-1:]) if digits else 0,
        "atbash": sum(_map.get(c, 0) for c in text),
        "albam": sum(_map.get(c, 0) for c in text),
        "mispar_ashkenazi": standard + 16 * len(text),
        "mispar_sephardi": standard + 30 * len(text),
        "mispar_mispar": sum(int(d) for d in str(standard)),
        "mispar_shemi": sum(_map.get(c, 0) ** 2 for c in text),
        "mispar_network": len(set(text)),
        "gematria_mispar_prati": standard,
        "gematria_mispar_katan": katan,
        "gematria_mispar_gadol": gadol,
        "gematria_mispar_mispar": sum(int(d) for d in str(standard)),
        "gematria_atbash": standard,
        "gematria_albam": standard,
        "gematria_sephardi": standard + 30 * len(text),
        "mispar_katan_sofit": sum(int(d) for d in str(standard)) + 1,
    }


@register_system
class HebrewAdvancedGematriaWrapper(SymbolicSystemWrapper):
    """Compute 23 Hebrew gematria variants for a given question text."""

    SYSTEM_ID = "hebrew_gematria_advanced"
    LIBRARY_BACKEND = "hebrew"

    def compute(self, entropy_packet: dict, params: dict | None = None) -> SymbolicOutput:
        params = params or {}
        text = entropy_packet.get("raw_question", "")
        seed = entropy_packet.get("seed", 0)
        modulus = params.get("modulus", 22)

        try:
            from hebrew import Hebrew, GematriaTypes  # type: ignore

            h = Hebrew(text)
            values = {}
            for gt_name in _GEMATRIA_TYPES:
                gem_type = getattr(GematriaTypes, gt_name, None)
                if gem_type is not None:
                    try:
                        values[gt_name] = h.gematria(gem_type)
                    except Exception:
                        values[gt_name] = 0
                else:
                    values[gt_name] = 0
            library_used = True
        except ImportError:
            values = _fallback_gematria(text)
            library_used = False

        numeric_list = list(values.values())
        digit_sum = sum(int(d) for v in numeric_list for d in str(abs(v)))
        max_val = max(numeric_list) if numeric_list else 0
        min_val = min(n for n in numeric_list if n > 0) if any(n > 0 for n in numeric_list) else 0
        mean_val = sum(numeric_list) / len(numeric_list) if numeric_list else 0
        modular_residue = sum(numeric_list) % modulus if modulus > 0 else 0

        symbolic_state = {
            "text": text,
            **{k: v for k, v in values.items()},
            "digit_sum": digit_sum,
            "modulus": modulus,
            "modular_residue": modular_residue,
            "library_used": library_used,
        }
        numeric_projection = numeric_list
        structural_features = {
            "max_value": max_val,
            "min_value": min_val,
            "mean_value": mean_val,
            "value_spread": max_val - min_val,
            "digit_sum": digit_sum,
            "letter_count": len(text),
            "unique_letters": len(set(text)),
            "letter_diversity": len(set(text)) / max(len(text), 1),
            "modular_state": modular_residue % 7,
            "value_entropy": mean_val / max(len(text), 1),
        }

        return self._build_output(
            symbolic_state=symbolic_state,
            numeric_projection=numeric_projection,
            structural_features=structural_features,
            raw_output={"values": values, "library_used": library_used},
            params=params,
        )
