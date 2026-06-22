"""Graph fusion of multiple oracle graph structures."""
from collections import Counter

def merge_graphs(graphs: list[dict]) -> dict:
    merged_nodes = {}
    merged_edges = []
    for g in graphs:
        for node in g.get("nodes", []):
            nid = node.get("id", "")
            if nid not in merged_nodes:
                merged_nodes[nid] = node
        for edge in g.get("edges", []):
            merged_edges.append(edge)
    return {"nodes": list(merged_nodes.values()), "edges": merged_edges}

def find_common_patterns(graphs: list[dict]) -> list[dict]:
    if not graphs:
        return []
    node_types = Counter()
    for g in graphs:
        for node in g.get("nodes", []):
            node_types[node.get("type", "unknown")] += 1
    threshold = len(graphs) * 0.5
    return [{"type": t, "count": c} for t, c in node_types.items() if c >= threshold]

def compute_graph_resonance(g1: dict, g2: dict) -> float:
    nodes1 = {n.get("id") for n in g1.get("nodes", [])}
    nodes2 = {n.get("id") for n in g2.get("nodes", [])}
    if not nodes1 or not nodes2:
        return 0.0
    intersection = len(nodes1 & nodes2)
    union = len(nodes1 | nodes2)
    return intersection / max(union, 1)
