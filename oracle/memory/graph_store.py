"""Graph-based storage for oracle lineage and structure graphs."""
import json
import sqlite3
import time


class GraphStore:
    def __init__(self, db_path: str = "data/oracle_memory.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        conn.execute("""CREATE TABLE IF NOT EXISTS graph_nodes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            node_id TEXT,
            graph_id TEXT,
            node_type TEXT,
            properties TEXT,
            created_at REAL
        )""")
        conn.execute("""CREATE TABLE IF NOT EXISTS graph_edges (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            graph_id TEXT,
            source TEXT,
            target TEXT,
            edge_type TEXT,
            weight REAL DEFAULT 1.0,
            properties TEXT,
            created_at REAL
        )""")
        conn.commit()
        conn.close()

    def store_graph(self, graph_id: str, nodes: list[dict], edges: list[dict]):
        conn = sqlite3.connect(self.db_path)
        now = time.time()
        for node in nodes:
            conn.execute(
                "INSERT INTO graph_nodes (node_id, graph_id, node_type, properties, created_at) VALUES (?, ?, ?, ?, ?)",
                (node.get("id", ""), graph_id, node.get("type", "generic"), json.dumps(node.get("properties", {})), now)
            )
        for edge in edges:
            conn.execute(
                "INSERT INTO graph_edges (graph_id, source, target, edge_type, weight, properties, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (graph_id, edge.get("source", ""), edge.get("target", ""), edge.get("type", "connects"), edge.get("weight", 1.0), json.dumps(edge.get("properties", {})), now)
            )
        conn.commit()
        conn.close()

    def get_graph(self, graph_id: str) -> dict:
        conn = sqlite3.connect(self.db_path)
        nodes = conn.execute("SELECT node_id, node_type, properties FROM graph_nodes WHERE graph_id = ?", (graph_id,)).fetchall()
        edges = conn.execute("SELECT source, target, edge_type, weight, properties FROM graph_edges WHERE graph_id = ?", (graph_id,)).fetchall()
        conn.close()
        return {
            "nodes": [{"id": n[0], "type": n[1], "properties": json.loads(n[2])} for n in nodes],
            "edges": [{"source": e[0], "target": e[1], "type": e[2], "weight": e[3], "properties": json.loads(e[4])} for e in edges],
        }

    def find_paths(self, graph_id: str, source: str, target: str, max_depth: int = 5) -> list[list[str]]:
        graph = self.get_graph(graph_id)
        adj = {}
        for edge in graph["edges"]:
            if edge["source"] not in adj:
                adj[edge["source"]] = []
            adj[edge["source"]].append(edge["target"])

        paths = []

        def dfs(node, path):
            if len(path) > max_depth:
                return
            if node == target:
                paths.append(list(path))
                return
            for neighbor in adj.get(node, []):
                if neighbor not in path:
                    path.append(neighbor)
                    dfs(neighbor, path)
                    path.pop()

        dfs(source, [source])
        return paths
