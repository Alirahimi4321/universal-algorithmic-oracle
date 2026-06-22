"""Geomancy wrapper - real internal geomancy computation (16 figures, 4 elements, binary operations)."""
import hashlib
import logging
from ..base import SymbolicSystemWrapper, SymbolicOutput
from ..registry import register_system

logger = logging.getLogger(__name__)

GEOMANCY_AVAILABLE = True

FIGURES = [
    "Via", "Cauda Draconis", "Puer", "Fortuna Minor",
    "Conjunctio", "Amissio", "Acquisitio", "Carcer",
    "Laetitia", "Tristitia", "Fortuna Major", "Albedo",
    "Populus", "Rubeus", "Via", "Cauda Draconis",
]

FIGURES_BINARY = {
    "Via": (0, 0, 0, 0), "Cauda Draconis": (0, 0, 0, 1),
    "Puer": (0, 0, 1, 0), "Fortuna Minor": (0, 0, 1, 1),
    "Conjunctio": (0, 1, 0, 0), "Amissio": (0, 1, 0, 1),
    "Acquisitio": (0, 1, 1, 0), "Carcer": (0, 1, 1, 1),
    "Laetitia": (1, 0, 0, 0), "Tristitia": (1, 0, 0, 1),
    "Fortuna Major": (1, 0, 1, 0), "Albedo": (1, 0, 1, 1),
    "Populus": (1, 1, 0, 0), "Rubeus": (1, 1, 0, 1),
}

ELEMENTS = {
    "fire": [0, 3, 6, 9, 12],
    "earth": [1, 4, 7, 10, 13],
    "air": [2, 5, 8, 11, 14],
    "water": [0, 3, 6, 9, 12],
}

GEOMANCY_HOUSES = [
    "Self", "Wealth", "Communication", "Home",
    "Children", "Health", "Partnership", "Death",
    "Journey", "Friends", "Work", "Enemies",
]


def _seed_to_figures(seed: int, count: int = 16) -> list[tuple[int, int, int, int]]:
    """Generate figures from a seed deterministically."""
    figures = []
    for i in range(count):
        h = hashlib.sha256(f"geomancy_{seed}_{i}".encode()).digest()
        lines = tuple((h[j] % 2) + 1 for j in range(4))
        figures.append(lines)
    return figures


def _figure_name(lines: tuple) -> str:
    """Get figure name from lines (1-2 pattern)."""
    binary = tuple(1 if x % 2 == 0 else 0 for x in lines)
    idx = sum(b << i for i, b in enumerate(binary))
    return FIGURES[idx % len(FIGURES)]


def _figure_element(name: str) -> str:
    """Get element for a figure."""
    idx = FIGURES.index(name) if name in FIGURES else 0
    for elem, indices in ELEMENTS.items():
        if idx in indices:
            return elem
    return "fire"


def _judge_from_figures(figures: list[tuple]) -> tuple:
    """Compute judge figure from mother/daughter figures."""
    judge_lines = []
    for pos in range(4):
        col_sum = sum(fig[pos] for fig in figures[:4]) % 2
        judge_lines.append(1 if col_sum == 0 else 2)
    return tuple(judge_lines)


def _witnesses_from_figures(figures: list[tuple]) -> tuple:
    """Compute witness figures from mother/daughter figures."""
    left_witness = []
    right_witness = []
    for pos in range(4):
        left_sum = sum(figures[i][pos] for i in [0, 2]) % 2
        right_sum = sum(figures[i][pos] for i in [1, 3]) % 2
        left_witness.append(1 if left_sum == 0 else 2)
        right_witness.append(1 if right_sum == 0 else 2)
    return tuple(left_witness), tuple(right_witness)


@register_system
class GeomancyWrapper(SymbolicSystemWrapper):
    """Real geomancy computation using 16 figures, mother/daughter/witness/judge/reconciler."""
    SYSTEM_ID = "geomancy"
    LIBRARY_BACKEND = "internal"

    def compute(self, entropy_packet: dict, params: dict | None = None) -> SymbolicOutput:
        params = params or {}
        seed = entropy_packet.get("seed", 0)
        bit_stream = entropy_packet.get("bit_stream", [])

        figures = _seed_to_figures(seed, 16)
        mother_figures = figures[:4]
        daughter_figures = figures[4:8]

        judge_lines = _judge_from_figures(mother_figures)
        judge_name = _figure_name(judge_lines)

        left_witness, right_witness = _witnesses_from_figures(mother_figures)

        reconciler_lines = []
        for pos in range(4):
            r_sum = (left_witness[pos] + right_witness[pos]) % 2
            reconciler_lines.append(1 if r_sum == 0 else 2)
        reconciler_name = _figure_name(tuple(reconciler_lines))

        figure_names = [_figure_name(f) for f in figures]
        elements = [_figure_element(name) for name in figure_names]

        element_counts = {e: elements.count(e) for e in ["fire", "earth", "air", "water"]}
        dominant_element = max(element_counts, key=element_counts.get)

        house_assignments = []
        for i, name in enumerate(figure_names):
            house_idx = i % len(GEOMANCY_HOUSES)
            house_assignments.append({
                "house": GEOMANCY_HOUSES[house_idx],
                "figure": name,
                "element": _figure_element(name),
            })

        parity_balance = sum(sum(f) % 2 for f in figures) / len(figures)
        symmetry = sum(1 for f in figures if f[:2] == f[2:]) / len(figures)
        unique_figures = len(set(figure_names))
        figure_entropy = unique_figures / len(FIGURES)

        element_balance = max(element_counts.values()) / max(1, min(element_counts.values()))

        judge_binary = tuple(1 if x % 2 == 0 else 0 for x in judge_lines)

        symbolic_state = {
            "figures": figure_names,
            "elements": elements,
            "mother": [list(f) for f in mother_figures],
            "daughter": [list(f) for f in daughter_figures],
            "left_witness": list(left_witness),
            "right_witness": list(right_witness),
            "judge": list(judge_lines),
            "judge_name": judge_name,
            "judge_binary": list(judge_binary),
            "reconciler": list(reconciler_lines),
            "reconciler_name": reconciler_name,
            "element_counts": element_counts,
            "dominant_element": dominant_element,
            "house_assignments": house_assignments,
            "library": "geomancy",
        }

        numeric_projection = []
        for f in figures:
            numeric_projection.append(sum(f))
        numeric_projection.append(FIGURES.index(judge_name) % 16)
        numeric_projection.append(FIGURES.index(reconciler_name) % 16)
        for elem in ["fire", "earth", "air", "water"]:
            numeric_projection.append(element_counts[elem])

        structural_features = {
            "parity_balance": parity_balance,
            "symmetry": symmetry,
            "figure_entropy": figure_entropy,
            "unique_figures": unique_figures,
            "total_figures": len(figures),
            "element_balance": element_balance,
            "dominant_element": dominant_element,
        }

        return self._build_output(
            symbolic_state=symbolic_state,
            numeric_projection=numeric_projection,
            structural_features=structural_features,
            params=params,
        )
