"""Pythagorean numerology wrapper using the numerology library."""
import hashlib
from ..base import SymbolicSystemWrapper, SymbolicOutput
from ..registry import register_system

try:
    from numerology import Pythagorean as PythagoreanNumerology
    NUMEROLOGY_AVAILABLE = True
except ImportError:
    NUMEROLOGY_AVAILABLE = False


@register_system
class PythagoreanNumerologyWrapper(SymbolicSystemWrapper):
    """Wrapper for numerology library - Pythagorean numerology analysis."""
    SYSTEM_ID = "pythagorean_numerology"
    LIBRARY_BACKEND = "numerology" if NUMEROLOGY_AVAILABLE else "internal"

    def compute(self, entropy_packet: dict, params: dict | None = None) -> SymbolicOutput:
        params = params or {}
        seed = entropy_packet.get("seed", 0)
        text = entropy_packet.get("normalized_text", "unknown")

        h = hashlib.sha256(f"pythag_{seed}".encode()).hexdigest()[:12]
        first_name = params.get("first_name", text.split()[0] if text.split() else "Oracle")
        last_name = params.get("last_name", text.split()[-1] if len(text.split()) > 1 else "System")

        if NUMEROLOGY_AVAILABLE:
            try:
                return self._compute_numerology(first_name, last_name, seed, params)
            except Exception as e:
                pass
        return self._compute_internal(first_name, last_name, seed, params)

    def _compute_numerology(self, first_name, last_name, seed, params):
        try:
            num = PythagoreanNumerology(first_name=first_name, last_name=last_name)

            life_path = getattr(num, 'life_path_number', 0) or 0
            destiny = getattr(num, 'destiny_number', 0) or 0
            personality = getattr(num, 'personality_number', 0) or 0
            hearth_desire = getattr(num, 'hearth_desire_number', 0) or 0
            active = getattr(num, 'active_number', 0) or 0
            legacy = getattr(num, 'legacy_number', 0) or 0
            power = getattr(num, 'power_number', 0) or 0

            symbolic_state = {
                "first_name": first_name,
                "last_name": last_name,
                "life_path": life_path,
                "destiny": destiny,
                "personality": personality,
                "hearth_desire": hearth_desire,
                "active": active,
                "legacy": legacy,
                "power": power,
            }

            numeric_projection = [
                life_path / 9.0,
                destiny / 9.0,
                personality / 9.0,
                hearth_desire / 9.0,
                active / 9.0,
                legacy / 9.0,
                power / 9.0 if power else 0,
                seed % 1000 / 1000.0,
            ]

            structural_features = {
                "master_number": 1 if life_path in [11, 22, 33] else 0,
                "all_numbers_present": all([life_path, destiny, personality]),
                "name_length": len(first_name) + len(last_name),
            }

            return self._build_output(
                symbolic_state=symbolic_state,
                numeric_projection=numeric_projection,
                structural_features=structural_features,
                params=params,
            )
        except Exception as e:
            return self._compute_internal(first_name, last_name, seed, params)

    def _compute_internal(self, first_name, last_name, seed, params):
        h = hashlib.sha256(f"pythag_{first_name}_{last_name}_{seed}".encode()).digest()
        life_path = (h[0] % 9) + 1
        destiny = (h[1] % 9) + 1
        personality = (h[2] % 9) + 1
        hearth_desire = (h[3] % 9) + 1
        active = (h[4] % 9) + 1
        legacy = (h[5] % 9) + 1
        power = (h[6] % 9) + 1

        symbolic_state = {"first_name": first_name, "last_name": last_name, "life_path": life_path, "destiny": destiny, "personality": personality, "hearth_desire": hearth_desire, "active": active, "legacy": legacy, "power": power}
        numeric_projection = [life_path / 9.0, destiny / 9.0, personality / 9.0, hearth_desire / 9.0, active / 9.0, legacy / 9.0, power / 9.0, seed % 1000 / 1000.0]
        structural_features = {"master_number": 1 if life_path in [11, 22, 33] else 0, "all_numbers_present": True, "name_length": len(first_name) + len(last_name)}
        return self._build_output(symbolic_state=symbolic_state, numeric_projection=numeric_projection, structural_features=structural_features, params=params)
