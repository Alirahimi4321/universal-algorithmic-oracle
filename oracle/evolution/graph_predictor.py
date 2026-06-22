"""Graph Neural Network Predictor using PyTorch Geometric for graph-based predictions."""
from __future__ import annotations
import logging
import numpy as np
from typing import Any

logger = logging.getLogger(__name__)

try:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
    from torch_geometric.data import Data
    from torch_geometric.nn import GCNConv, global_mean_pool
    HAS_PYTORCH_GEOMETRIC = True
except Exception:
    HAS_PYTORCH_GEOMETRIC = False


class SimpleGCN(nn.Module if HAS_PYTORCH_GEOMETRIC else object):
    """Simple Graph Convolutional Network for oracle graph predictions."""
    def __init__(self, in_channels: int = 8, hidden_channels: int = 16, out_channels: int = 1) -> None:
        if not HAS_PYTORCH_GEOMETRIC:
            return
        super().__init__()
        self.conv1 = GCNConv(in_channels, hidden_channels)
        self.conv2 = GCNConv(hidden_channels, hidden_channels)
        self.fc = nn.Linear(hidden_channels, out_channels)

    def forward(self, x, edge_index, batch=None) -> torch.Tensor:
        x = F.relu(self.conv1(x, edge_index))
        x = F.relu(self.conv2(x, edge_index))
        if batch is not None:
            x = global_mean_pool(x, batch)
        else:
            x = x.mean(dim=0, keepdim=True)
        return self.fc(x)


class GraphPredictor:
    """Predict using graph neural networks on oracle chromosome graphs."""

    def __init__(self) -> None:
        self.available = HAS_PYTORCH_GEOMETRIC
        self._model = None
        if HAS_PYTORCH_GEOMETRIC:
            try:
                self._model = SimpleGCN()
            except Exception:
                self.available = False

    def chromosome_to_graph(self, chromosome: dict) -> dict[str, Any]:
        genes = chromosome.get("genes", {})
        edges = chromosome.get("edges", [])
        if not genes:
            return {"node_features": [], "edge_index": [[], []]}
        node_features = []
        node_map = {}
        for i, (gid, gene) in enumerate(genes.items()):
            node_map[gid] = i
            params = gene.get("params", {})
            weight = gene.get("weight", 1.0)
            features = [
                hash(gene.get("system_id", "")) % 100 / 100.0,
                weight,
                len(params),
                sum(float(v) for v in params.values() if isinstance(v, (int, float))) / max(len(params), 1),
                1.0 if gene.get("gene_type") == "symbolic_system" else 0.0,
                len(gene.get("input_slots", [])),
                len(gene.get("output_slots", [])),
                hash(gene.get("backend", "")) % 100 / 100.0,
            ]
            node_features.append(features)
        edge_index = [[], []]
        for src, dst in edges:
            if src in node_map and dst in node_map:
                edge_index[0].append(node_map[src])
                edge_index[1].append(node_map[dst])
        return {"node_features": node_features, "edge_index": edge_index, "num_nodes": len(node_features)}

    def predict(self, chromosome: dict, entropy_features: list[float] | None = None) -> dict[str, Any]:
        if not self.available or self._model is None:
            return {"prediction": 0.5, "method": "unavailable", "node_embeddings": []}
        graph_data = self.chromosome_to_graph(chromosome)
        if not graph_data["node_features"]:
            return {"prediction": 0.5, "method": "empty_graph", "node_embeddings": []}
        try:
            x = torch.tensor(graph_data["node_features"], dtype=torch.float)
            edge_index = torch.tensor(graph_data["edge_index"], dtype=torch.long)
            if edge_index.numel() == 0:
                edge_index = torch.zeros((2, 0), dtype=torch.long)
            data = Data(x=x, edge_index=edge_index)
            self._model.eval()
            with torch.no_grad():
                pred = self._model(data.x, data.edge_index)
                prediction = float(torch.sigmoid(pred).mean())
                node_emb = data.x.mean(dim=0).tolist()
            return {"prediction": round(prediction, 4), "method": "gcn",
                    "node_embeddings": [round(v, 4) for v in node_emb], "num_nodes": len(graph_data["node_features"])}
        except Exception as e:
            return {"prediction": 0.5, "method": "failed", "error": str(e)}

    def encode_graph_features(self, chromosome: dict) -> list[float]:
        graph_data = self.chromosome_to_graph(chromosome)
        features = [
            graph_data["num_nodes"],
            len(graph_data["edge_index"][0]),
            len(graph_data["edge_index"][0]) / max(graph_data["num_nodes"], 1),
        ]
        if graph_data["node_features"]:
            node_arr = np.array(graph_data["node_features"])
            features.extend(node_arr.mean(axis=0).tolist())
            features.extend(node_arr.std(axis=0).tolist())
        else:
            features.extend([0.0] * 16)
        return features[:32]
