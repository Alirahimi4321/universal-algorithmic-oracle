"""Raml (Arabic sand divination) wrapper."""
import hashlib
from ..base import SymbolicSystemWrapper, SymbolicOutput
from ..registry import register_system

FIGURES = {
    (1, 1, 1, 1): {"name": "First Mother", "element": "Fire", "nature": "hot_wet"},
    (2, 2, 2, 2): {"name": "Second Mother", "element": "Air", "nature": "hot_dry"},
    (3, 3, 3, 3): {"name": "Third Mother", "element": "Water", "nature": "cold_wet"},
    (4, 4, 4, 4): {"name": "Fourth Mother", "element": "Earth", "nature": "cold_dry"},
    (1, 2, 1, 2): {"name": "First Daughter", "element": "Air", "nature": "hot_dry"},
    (2, 1, 2, 1): {"name": "Second Daughter", "element": "Water", "nature": "cold_wet"},
    (3, 4, 3, 4): {"name": "Third Daughter", "element": "Earth", "nature": "cold_dry"},
    (4, 3, 4, 3): {"name": "Fourth Daughter", "element": "Fire", "nature": "hot_wet"},
    (1, 1, 2, 2): {"name": "First Son", "element": "Fire", "nature": "hot_wet"},
    (2, 2, 1, 1): {"name": "Second Son", "element": "Air", "nature": "hot_dry"},
    (3, 3, 4, 4): {"name": "Third Son", "element": "Water", "nature": "cold_wet"},
    (4, 4, 3, 3): {"name": "Fourth Son", "element": "Earth", "nature": "cold_dry"},
    (1, 3, 1, 3): {"name": "First Granddaughter", "element": "Water", "nature": "cold_wet"},
    (2, 4, 2, 4): {"name": "Second Granddaughter", "element": "Earth", "nature": "cold_dry"},
    (3, 1, 3, 1): {"name": "Third Granddaughter", "element": "Fire", "nature": "hot_wet"},
    (4, 2, 4, 2): {"name": "Fourth Granddaughter", "element": "Air", "nature": "hot_dry"},
}

RAML_HOUSES = [
    "Life", "Wealth", "Siblings", "Parents",
    "Children", "Health", "Spouse", "Enemies",
    "Journey", "Friends", "Work", "Property",
]


@register_system
class RamlWrapper(SymbolicSystemWrapper):
    SYSTEM_ID = "raml"
    LIBRARY_BACKEND = "internal"

    def compute(self, entropy_packet: dict, params: dict | None = None) -> SymbolicOutput:
        params = params or {}
        seed = entropy_packet.get("seed", 0)

        figures = []
        for i in range(16):
            h = hashlib.sha256(f"{seed}_raml_{i}".encode()).digest()
            lines = tuple((h[j] % 4) + 1 for j in range(4))
            fig_data = FIGURES.get(lines, {"name": "Unknown", "element": "Unknown", "nature": "unknown"})
            figures.append({"lines": lines, **fig_data})

        mother_figures = figures[:4]
        daughter_figures = figures[4:8]
        witness_figures = figures[8:10]
        judge_figure = figures[10] if len(figures) > 10 else figures[0]
        reconciler_figure = figures[11] if len(figures) > 11 else figures[1]

        element_counts = {"Fire": 0, "Air": 0, "Water": 0, "Earth": 0}
        for f in figures:
            elem = f.get("element", "Unknown")
            if elem in element_counts:
                element_counts[elem] += 1

        judge_element = judge_figure.get("element", "Unknown")
        judge_name = judge_figure.get("name", "Unknown")

        all_elements = [f.get("element", "Unknown") for f in figures]
        element_diversity = len(set(all_elements)) / 4

        symbolic_state = {
            "figures": [{"lines": f["lines"], "name": f["name"], "element": f["element"], "nature": f["nature"]} for f in figures],
            "mother_figures": [{"lines": f["lines"], "name": f["name"]} for f in mother_figures],
            "daughter_figures": [{"lines": f["lines"], "name": f["name"]} for f in daughter_figures],
            "witness_figures": [{"lines": f["lines"], "name": f["name"]} for f in witness_figures],
            "judge": {"lines": judge_figure["lines"], "name": judge_name, "element": judge_element},
            "reconciler": {"lines": reconciler_figure["lines"], "name": reconciler_figure.get("name", "Unknown")},
            "element_counts": element_counts,
            "dominant_element": max(element_counts, key=element_counts.get),
            "houses": {h: figures[i % len(figures)]["name"] for i, h in enumerate(RAML_HOUSES)},
        }

        fig_indices = [list(FIGURES.keys()).index(f["lines"]) % 16 if f["lines"] in FIGURES else 0 for f in figures[:8]]
        element_map = {"Fire": 0, "Air": 1, "Water": 2, "Earth": 3}
        element_indices = [element_map.get(f["element"], 0) for f in figures[:8]]

        numeric_projection = [
            fig_indices[0], fig_indices[1], fig_indices[2], fig_indices[3],
            element_indices[0], element_indices[1], element_indices[2], element_indices[3],
            sum(fig_indices) % 16,
            sum(element_indices) % 4,
            element_diversity * 4,
            seed % 1000,
        ]

        structural_features = {
            "element_balance": max(element_counts.values()) / max(sum(element_counts.values()), 1),
            "element_diversity": element_diversity,
            "figure_count": len(figures),
            "unique_figures": len(set(f["name"] for f in figures)),
            "judge_element": element_map.get(judge_element, 0) / 3,
        }

        return self._build_output(
            symbolic_state=symbolic_state,
            numeric_projection=numeric_projection,
            structural_features=structural_features,
            params=params,
        )
