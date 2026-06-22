"""I Ching wrapper using ichingshifa (authentic yarrow stalks + Najia hexagram layout)."""
import hashlib
from ..base import SymbolicSystemWrapper, SymbolicOutput
from ..registry import register_system

try:
    from ichingshifa.ichingshifa import Iching
    ICHINGSHIFA_AVAILABLE = True
except ImportError:
    ICHINGSHIFA_AVAILABLE = False


@register_system
class IChingShifaWrapper(SymbolicSystemWrapper):
    SYSTEM_ID = "iching_shifa"
    LIBRARY_BACKEND = "ichingshifa" if ICHINGSHIFA_AVAILABLE else "internal"

    def compute(self, entropy_packet: dict, params: dict | None = None) -> SymbolicOutput:
        params = params or {}

        if not ICHINGSHIFA_AVAILABLE:
            return self._compute_internal(entropy_packet, params)

        manual_lines = params.get("lines")
        if manual_lines:
            return self._compute_manual(manual_lines, entropy_packet, params)
        return self._compute_random(entropy_packet, params)

    def _compute_random(self, entropy_packet: dict, params: dict) -> SymbolicOutput:
        try:
            iching = Iching()
            result = iching.bookgua_details()
            return self._parse_result(result, entropy_packet, params)
        except Exception:
            return self._compute_internal(entropy_packet, params)

    def _compute_manual(self, lines: list[int], entropy_packet: dict, params: dict) -> SymbolicOutput:
        try:
            iching = Iching()
            result = iching.mget_bookgua_details(lines)
            return self._parse_result(result, entropy_packet, params)
        except Exception:
            return self._compute_internal(entropy_packet, params)

    def _parse_result(self, result, entropy_packet: dict, params: dict) -> SymbolicOutput:
        seed = entropy_packet.get("seed", 0)

        if isinstance(result, list) and len(result) >= 3:
            hex_code = result[0] if len(result) > 0 else ""
            hexagram_name = result[1] if len(result) > 1 else ""
            changed_name = result[2] if len(result) > 2 else ""
            description = result[3] if len(result) > 3 and isinstance(result[3], dict) else {}

            lines = []
            if isinstance(hex_code, str):
                lines = [int(c) for c in hex_code if c.isdigit()]
            elif isinstance(hex_code, (list, tuple)):
                lines = list(hex_code)

            changing = [i + 1 for i, l in enumerate(lines) if l in (6, 9)]
            yin_count = sum(1 for l in lines if l in (6, 8))
            yang_count = sum(1 for l in lines if l in (7, 9))

            symbolic_state = {
                "hexagram_name": hexagram_name,
                "changed_name": changed_name,
                "hex_code": str(hex_code),
                "lines": lines,
                "changing_lines": changing,
                "description": {str(k): str(v)[:200] for k, v in description.items()} if description else {},
                "library": "ichingshifa",
            }

            numeric_projection = [
                len(changing),
                yin_count,
                yang_count,
                len(lines),
                sum(lines) % 100,
                seed % 1000,
                hash(str(hex_code)) % 100 if hex_code else 0,
            ]

            structural_features = {
                "yin_yang_balance": yang_count / max(len(lines), 1),
                "changing_line_count": len(changing),
                "line_entropy": len(changing) / max(len(lines), 1),
                "has_description": bool(description),
            }

            return self._build_output(
                symbolic_state=symbolic_state,
                numeric_projection=numeric_projection,
                structural_features=structural_features,
                params=params,
            )

        return self._compute_internal(entropy_packet, params)

    def _compute_internal(self, entropy_packet: dict, params: dict) -> SymbolicOutput:
        seed = entropy_packet.get("seed", 0)
        h = hashlib.sha256(f"iching_{seed}".encode()).digest()

        lines = []
        for i in range(6):
            val = h[i % len(h)] % 4
            lines.append([6, 7, 8, 9][val])

        changing = [i + 1 for i, l in enumerate(lines) if l in (6, 9)]
        yin_count = sum(1 for l in lines if l in (6, 8))
        yang_count = sum(1 for l in lines if l in (7, 9))

        hex_code = "".join(str(l) for l in lines)

        symbolic_state = {
            "hex_code": hex_code,
            "lines": lines,
            "changing_lines": changing,
            "library": "internal",
        }

        numeric_projection = [
            len(changing),
            yin_count,
            yang_count,
            len(lines),
            sum(lines) % 100,
            seed % 1000,
        ]

        structural_features = {
            "yin_yang_balance": yang_count / max(len(lines), 1),
            "changing_line_count": len(changing),
            "line_entropy": len(changing) / max(len(lines), 1),
        }

        return self._build_output(
            symbolic_state=symbolic_state,
            numeric_projection=numeric_projection,
            structural_features=structural_features,
            params=params,
        )
