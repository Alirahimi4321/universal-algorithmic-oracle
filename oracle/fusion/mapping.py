"""Output mapping - converts fused oracle output to final response with dynamic text generation."""
import math


def map_to_response(fused_numeric: list[float], fused_symbolic: dict,
                     dominant_systems: list[str] = None) -> dict:
    confidence = compute_confidence(fused_numeric)
    dominant_pattern = find_dominant_pattern(fused_symbolic)
    phase = fused_symbolic.get("phase", "unknown")
    polarity = fused_symbolic.get("polarity", "neutral")
    element = fused_symbolic.get("element", "")
    transition = fused_symbolic.get("transition_state", "")

    answer_text = generate_text_answer(
        confidence, dominant_pattern, phase, polarity, element, transition,
        fused_numeric, dominant_systems or []
    )

    return {
        "answer": answer_text,
        "symbolic_answer": {
            "phase": phase,
            "polarity": polarity,
            "dominant_pattern": dominant_pattern,
            "element": element,
            "transition_state": transition,
        },
        "numeric_signature": fused_numeric[:20],
        "oracle_confidence": confidence,
    }


def compute_confidence(numeric_vector: list[float]) -> float:
    if not numeric_vector:
        return 0.0
    nonzero = sum(1 for x in numeric_vector if abs(x) > 0.01)
    magnitude = sum(abs(x) for x in numeric_vector) / len(numeric_vector)
    diversity = len(set(round(x, 2) for x in numeric_vector)) / len(numeric_vector)
    variance = sum((x - sum(numeric_vector) / len(numeric_vector)) ** 2
                   for x in numeric_vector) / len(numeric_vector)
    stability = 1.0 - min(math.sqrt(variance), 1.0)
    return min(nonzero / len(numeric_vector) * 0.3 + min(magnitude, 1.0) * 0.25 +
               diversity * 0.25 + stability * 0.2, 1.0)


def find_dominant_pattern(symbolic_state: dict) -> str:
    if not symbolic_state:
        return "undefined"
    for key in ["dominant_element", "dominant_pattern", "element", "phase", "transition_state"]:
        if key in symbolic_state and symbolic_state[key]:
            return str(symbolic_state[key])
    keys = [k for k in symbolic_state.keys() if not k.startswith("_") and symbolic_state[k]]
    if keys:
        return keys[0]
    return "emerging"


def generate_text_answer(confidence: float, pattern: str, phase: str, polarity: str,
                          element: str, transition: str, numeric_signature: list,
                          dominant_systems: list[str]) -> str:
    if confidence > 0.8:
        strength = "very strong"
        certainty = "indicates a clear trajectory"
    elif confidence > 0.6:
        strength = "strong"
        certainty = "suggests a defined pattern"
    elif confidence > 0.4:
        strength = "moderate"
        certainty = "points toward a developing trend"
    elif confidence > 0.2:
        strength = "emerging"
        certainty = "hints at an initial formation"
    else:
        strength = "nascent"
        certainty = "is still crystallizing"

    phase_descriptions = {
        "transition": "a phase of transformation and shifting dynamics",
        "stable": "a period of established patterns and continuity",
        "growth": "an expanding phase with increasing momentum",
        "decline": "a contracting phase requiring careful navigation",
        "emergence": "the beginning of a new developmental arc",
        "convergence": "a point where multiple factors align",
        "divergence": "a branching point with multiple possible paths",
        "cyclical": "a recurring pattern that echoes previous cycles",
    }
    phase_text = phase_descriptions.get(phase, f"the current phase of {phase}")

    polarity_descriptions = {
        "positive": "favorable alignment of symbolic forces",
        "negative": "challenging tensions requiring resolution",
        "mixed-positive": "predominantly favorable with minor cautionary elements",
        "mixed-negative": "predominantly challenging with emerging opportunities",
        "neutral": "balanced interplay of opposing forces",
        "dynamic": "actively shifting polarity requiring adaptive response",
    }
    polarity_text = polarity_descriptions.get(polarity, f"the polarity signature of {polarity}")

    if element:
        element_clause = f" The dominant elemental influence is {element}, "
        element_effects = {
            "fire": "bringing energy, initiative, and transformative power.",
            "water": "bringing depth, intuition, and adaptive flow.",
            "earth": "bringing stability, practicality, and grounded manifestation.",
            "air": "bringing clarity, communication, and intellectual movement.",
            "metal": "bringing precision, structure, and refined focus.",
            "wood": "bringing growth, flexibility, and organic expansion.",
        }
        element_clause += element_effects.get(element, "contributing its characteristic qualities.")
    else:
        element_clause = ""

    systems_text = ""
    if dominant_systems:
        if len(dominant_systems) == 1:
            systems_text = f" The primary computational pathway operates through {dominant_systems[0]}."
        elif len(dominant_systems) == 2:
            systems_text = f" The dominant computational pathways are {dominant_systems[0]} and {dominant_systems[1]}, creating a dual-resonance structure."
        else:
            sys_list = ", ".join(dominant_systems[:3])
            systems_text = f" The evolved architecture integrates {sys_list}, forming a multi-system convergence."

    sig_magnitude = sum(abs(x) for x in numeric_signature) / max(len(numeric_signature), 1)
    if sig_magnitude > 0.7:
        sig_text = "The numeric signature carries high-energy resonance patterns."
    elif sig_magnitude > 0.4:
        sig_text = "The numeric signature shows balanced energy distribution."
    else:
        sig_text = "The numeric signature reveals subtle, distributed energy patterns."

    answer = (
        f"The evolved symbolic computational architecture ({strength} confidence, {confidence:.2f}) "
        f"{certainty}. "
        f"The dominant pattern reflects {pattern}, situated within {phase_text}. "
        f"The energy distribution aligns with {polarity_text}.{element_clause}{systems_text} "
        f"{sig_text}"
    )

    return answer
