"""Symbolic fusion of multiple system outputs."""
from collections import Counter

def symbolic_state_fusion(states: list[dict]) -> dict:
    if not states:
        return {}
    fused = {"source_states": len(states)}
    all_keys = set()
    for s in states:
        all_keys.update(s.keys())
    for key in all_keys:
        values = [s[key] for s in states if key in s]
        if all(isinstance(v, (int, float)) for v in values):
            fused[key] = sum(values) / len(values)
        elif all(isinstance(v, str) for v in values):
            counter = Counter(values)
            fused[key] = counter.most_common(1)[0][0]
        elif all(isinstance(v, list) for v in values):
            fused[key] = [item for sublist in values for item in sublist]
        else:
            fused[key] = values[-1] if values else None
    return fused

def find_dominant_element(states: list[dict]) -> str:
    element_counts = Counter()
    for state in states:
        for key in ["element", "dominant_element", "element_balance"]:
            if key in state:
                val = state[key]
                if isinstance(val, str):
                    element_counts[val] += 1
                elif isinstance(val, dict):
                    for k, v in val.items():
                        if isinstance(v, (int, float)):
                            element_counts[k] += v
    if not element_counts:
        return "unknown"
    return element_counts.most_common(1)[0][0]

def symbolic_phase_detection(states: list[dict]) -> str:
    phases = []
    for state in states:
        for key in ["phase", "transition", "state"]:
            if key in state:
                phases.append(state[key])
    if not phases:
        return "stable"
    phase_counts = Counter(phases)
    return phase_counts.most_common(1)[0][0]

def compute_symbolic_coherence(states: list[dict]) -> float:
    if len(states) < 2:
        return 1.0
    agreement = 0
    total = 0
    for i in range(len(states)):
        for j in range(i + 1, len(states)):
            common_keys = set(states[i].keys()) & set(states[j].keys())
            for key in common_keys:
                if states[i][key] == states[j][key]:
                    agreement += 1
                total += 1
    return agreement / max(total, 1)


class SymbolicFusion:
    def __init__(self, method: str = "weighted_average"):
        self.method = method

    def fuse(self, states: list[dict]) -> dict:
        if self.method == "weighted_average":
            return symbolic_state_fusion(states)
        return symbolic_state_fusion(states)
