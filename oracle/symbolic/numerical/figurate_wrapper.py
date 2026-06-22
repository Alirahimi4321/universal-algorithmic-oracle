"""Figurate number sequences wrapper using figuratenum library (235+ sequences)."""
import hashlib
from ..base import SymbolicSystemWrapper, SymbolicOutput
from ..registry import register_system

try:
    from figuratenum import PlaneFigurateNum
    PLANE_AVAILABLE = True
except ImportError:
    PLANE_AVAILABLE = False

try:
    from figuratenum import SpaceFigurateNum
    SPACE_AVAILABLE = True
except ImportError:
    SPACE_AVAILABLE = False

# Common plane sequence methods (parameterless)
_PLANE_SEQUENCES = [
    "centered_square", "centered_dodecagonal", "pronic", "polite", "impolite",
    "cross", "aztec_diamond", "pentagram", "gnomonic", "truncated_triangular",
    "truncated_square", "truncated_pronic", "truncated_centered_hexagonal",
    "triangular", "square", "pentagonal", "hexagonal", "heptagonal", "octagonal",
    "nonagonal", "decagonal", "hendecagonal", "dodecagonal", "tridecagonal",
    "tetradecagonal", "pentadecagonal", "hexadecagonal", "heptadecagonal",
    "octadecagonal", "nonadecagonal", "icosagonal", "icosihenagonal",
    "icosiheptagonal", "icosidigonal", "icositrigonal", "icositetragonal",
    "icosipentagonal", "icosihexagonal", "icosioctagonal", "icosinonagonal",
    "triacontagonal", "centered_triangular", "centered_pentagonal",
    "centered_hexagonal", "centered_heptagonal", "centered_octagonal",
    "centered_nonagonal", "centered_decagonal", "centered_hendecagonal",
    "centered_tridecagonal", "centered_tetradecagonal", "centered_pentadecagonal",
    "centered_hexadecagonal", "centered_heptadecagonal", "centered_octadecagonal",
    "centered_nonadecagonal", "centered_icosagonal", "centered_icosihenagonal",
    "centered_icosidigonal", "centered_icositrigonal", "centered_icositetragonal",
    "centered_icosipentagonal", "centered_icosihexagonal", "centered_icosiheptagonal",
    "centered_icosioctagonal", "centered_icosinonagonal", "centered_triacontagonal",
    "truncated_centered_triangular", "truncated_centered_square",
    "truncated_centered_pentagonal", "generalized_pentagonal",
    "generalized_hexagonal",
]

# Common space sequence methods (parameterless)
_SPACE_SEQUENCES = [
    "cubic", "tetrahedral", "octahedral", "dodecahedral", "icosahedral",
    "truncated_tetrahedral", "truncated_cubic", "truncated_octahedral",
    "stella_octangula", "centered_cube", "rhombic_dodecahedral",
    "hauy_rhombic_dodecahedral", "centered_tetrahedron",
    "centered_square_pyramid", "centered_octahedron", "centered_icosahedron",
    "centered_dodecahedron", "centered_truncated_tetrahedron",
    "centered_truncated_cube", "centered_truncated_octahedron",
    "centered_hexagonal_pyramidal", "hexagonal_prism",
    "triangular_pyramidal", "square_pyramidal", "pentagonal_pyramidal",
    "hexagonal_pyramidal", "heptagonal_pyramidal", "octagonal_pyramidal",
    "nonagonal_pyramidal", "decagonal_pyramidal", "hendecagonal_pyramidal",
    "dodecagonal_pyramidal", "tridecagonal_pyramidal", "tetradecagonal_pyramidal",
    "pentadecagonal_pyramidal", "hexadecagonal_pyramidal", "heptadecagonal_pyramidal",
    "octadecagonal_pyramidal", "nonadecagonal_pyramidal", "icosagonal_pyramidal",
    "icosihenagonal_pyramidal", "icosidigonal_pyramidal", "icositrigonal_pyramidal",
    "icositetragonal_pyramidal", "icosipentagonal_pyramidal", "icosihexagonal_pyramidal",
    "icosiheptagonal_pyramidal", "icosioctagonal_pyramidal", "icosinonagonal_pyramidal",
    "triacontagonal_pyramidal", "triangular_tetrahedral",
    "triangular_square_pyramidal", "square_tetrahedral",
    "square_square_pyramidal", "tetrahedral_square_pyramidal",
    "centered_pentagonal_pyramid", "centered_hexagonal_pyramid",
    "centered_heptagonal_pyramid", "centered_octagonal_pyramid",
    "centered_triangular_pyramidal", "centered_square_pyramidal",
    "centered_pentagonal_pyramidal", "centered_heptagonal_pyramidal",
    "centered_octagonal_pyramidal", "centered_nonagonal_pyramidal",
    "centered_decagonal_pyramidal", "centered_hendecagonal_pyramidal",
    "centered_dodecagonal_pyramidal", "generalized_pentagonal_pyramidal",
    "generalized_hexagonal_pyramidal",
]


def _seed_from_entropy(entropy_packet: dict) -> int:
    """Derive a deterministic seed from an entropy packet."""
    bit_stream = entropy_packet.get("bit_stream", [])
    seed = entropy_packet.get("seed", 0)
    h = hashlib.sha256(str(seed).encode()).digest()
    val = 0
    for i, b in enumerate(bit_stream[:32]):
        val = (val << 1) | (b & 1)
        val ^= h[i % len(h)]
    return val if val else seed


def _extract_generator_values(generator, count: int) -> list[int]:
    """Extract values from a figuratenum generator."""
    values = []
    for _ in range(count):
        try:
            values.append(next(generator))
        except StopIteration:
            break
    return values


def _detect_golden_ratio(values: list[int]) -> bool:
    """Detect if consecutive ratio approaches golden ratio (phi ~ 1.618)."""
    if len(values) < 3:
        return False
    for i in range(2, min(len(values), 10)):
        if values[i - 1] > 0:
            ratio = values[i] / values[i - 1]
            if abs(ratio - 1.6180339887) < 0.1:
                return True
    return False


def _detect_fibonacci_pattern(values: list[int]) -> bool:
    """Check if values follow Fibonacci-like additive pattern."""
    if len(values) < 5:
        return False
    matches = 0
    for i in range(2, min(len(values), 12)):
        if values[i - 1] + values[i - 2] == values[i]:
            matches += 1
    return matches >= 2


def _select_sequences(seed: int, pool: list[str], count: int) -> list[str]:
    """Select a deterministic subset of sequences based on seed."""
    indices = set()
    rng = seed
    while len(indices) < min(count, len(pool)):
        rng = (rng * 6364136223846793005 + 1442695040888963407) & ((1 << 64) - 1)
        idx = rng % len(pool)
        indices.add(idx)
    return [pool[i] for i in sorted(indices)]


@register_system
class FiguratePlaneWrapper(SymbolicSystemWrapper):
    """Plane figurate number sequences (triangular, square, pentagonal, etc.)."""
    SYSTEM_ID = "figurate_plane"
    LIBRARY_BACKEND = "figuratenum"

    def compute(self, entropy_packet: dict, params: dict | None = None) -> SymbolicOutput:
        params = params or {}
        seed = _seed_from_entropy(entropy_packet)

        if not PLANE_AVAILABLE:
            return self._build_output(
                symbolic_state={"error": "figuratenum.PlaneFigurateNum not installed"},
                numeric_projection=[],
                structural_features={},
                raw_output={},
                params=params,
            )

        n_terms = params.get("n_terms", 10)
        selected = params.get("sequences", None)

        if not selected:
            n_select = min(params.get("n_select", 5), len(_PLANE_SEQUENCES))
            selected = _select_sequences(seed, _PLANE_SEQUENCES, n_select)

        seq = PlaneFigurateNum()
        all_sequences = {}
        combined_values = []

        for name in selected:
            method = getattr(seq, name, None)
            if method is None or not callable(method):
                continue
            try:
                generator = method()
                values = _extract_generator_values(generator, n_terms)
                all_sequences[name] = values
                combined_values.extend(values)
            except Exception:
                continue

        symbolic_state = {
            "sequences_generated": list(all_sequences.keys()),
            "sequence_data": all_sequences,
            "seed_used": seed,
        }

        numeric_projection = [float(v) for v in combined_values[:50]]

        structural_features = {
            "golden_ratio_detected": _detect_golden_ratio(combined_values),
            "fibonacci_pattern_detected": _detect_fibonacci_pattern(combined_values),
            "sequence_count": len(all_sequences),
            "total_terms": len(combined_values),
            "seed_mod_7": seed % 7,
            "seed_mod_11": seed % 11,
            "sum_mod_13": sum(combined_values) % 13 if combined_values else 0,
        }

        return self._build_output(
            symbolic_state=symbolic_state,
            numeric_projection=numeric_projection,
            structural_features=structural_features,
            raw_output={"all_sequences": all_sequences, "selected_names": selected},
            params=params,
        )


@register_system
class FigurateSpaceWrapper(SymbolicSystemWrapper):
    """Space figurate number sequences (tetrahedral, octahedral, etc.)."""
    SYSTEM_ID = "figurate_space"
    LIBRARY_BACKEND = "figuratenum"

    def compute(self, entropy_packet: dict, params: dict | None = None) -> SymbolicOutput:
        params = params or {}
        seed = _seed_from_entropy(entropy_packet)

        if not SPACE_AVAILABLE:
            return self._build_output(
                symbolic_state={"error": "figuratenum.SpaceFigurateNum not installed"},
                numeric_projection=[],
                structural_features={},
                raw_output={},
                params=params,
            )

        n_terms = params.get("n_terms", 10)
        selected = params.get("sequences", None)

        if not selected:
            n_select = min(params.get("n_select", 5), len(_SPACE_SEQUENCES))
            selected = _select_sequences(seed, _SPACE_SEQUENCES, n_select)

        seq = SpaceFigurateNum()
        all_sequences = {}
        combined_values = []

        for name in selected:
            method = getattr(seq, name, None)
            if method is None or not callable(method):
                continue
            try:
                generator = method()
                values = _extract_generator_values(generator, n_terms)
                all_sequences[name] = values
                combined_values.extend(values)
            except Exception:
                continue

        symbolic_state = {
            "sequences_generated": list(all_sequences.keys()),
            "sequence_data": all_sequences,
            "seed_used": seed,
        }

        numeric_projection = [float(v) for v in combined_values[:50]]

        structural_features = {
            "golden_ratio_detected": _detect_golden_ratio(combined_values),
            "fibonacci_pattern_detected": _detect_fibonacci_pattern(combined_values),
            "sequence_count": len(all_sequences),
            "total_terms": len(combined_values),
            "seed_mod_7": seed % 7,
            "seed_mod_13": seed % 13,
            "sum_mod_17": sum(combined_values) % 17 if combined_values else 0,
        }

        return self._build_output(
            symbolic_state=symbolic_state,
            numeric_projection=numeric_projection,
            structural_features=structural_features,
            raw_output={"all_sequences": all_sequences, "selected_names": selected},
            params=params,
        )
