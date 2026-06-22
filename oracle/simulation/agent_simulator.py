"""Agent-Based Simulator using Mesa for multi-agent oracle simulation."""
from __future__ import annotations
import logging
import numpy as np
from typing import Any

logger = logging.getLogger(__name__)

try:
    import mesa
    HAS_MESA = True
except Exception:
    HAS_MESA = False


class OracleAgent:
    """A single oracle agent that applies a subset of symbolic systems."""
    def __init__(self, unique_id, model, systems: list[str], weights: list[float] | None = None) -> None:
        self.unique_id = unique_id
        self.model = model
        self.systems = systems
        self.weights = weights or [1.0 / max(len(systems), 1)] * len(systems)
        self.prediction_history: list[float] = []
        self.fitness = 0.5

    def step(self) -> None:
        raw = sum(w * (hash(s + str(self.model.schedule.time)) % 1000) / 1000.0
                  for s, w in zip(self.systems, self.weights))
        noise = np.random.normal(0, 0.05)
        prediction = max(0.0, min(1.0, raw / max(len(self.systems), 1) + noise))
        self.prediction_history.append(prediction)
        if len(self.prediction_history) > 10:
            self.prediction_history.pop(0)
        self.fitness = np.mean(self.prediction_history[-5:]) if self.prediction_history else 0.5

    def get_prediction(self) -> float:
        return self.prediction_history[-1] if self.prediction_history else 0.5


class OracleModel:
    """Mesa model for multi-agent oracle simulation."""
    def __init__(self, num_agents: int = 10, systems_per_agent: int = 3, all_systems: list[str] | None = None) -> None:
        if not HAS_MESA:
            return
        self.schedule = _SimpleScheduler()
        all_systems = all_systems or [f"system_{i}" for i in range(20)]
        for i in range(num_agents):
            selected = list(np.random.choice(all_systems, size=min(systems_per_agent, len(all_systems)), replace=False))
            agent = OracleAgent(i, self, selected)
            self.schedule.add(agent)

    def step(self) -> None:
        self.schedule.step()

    def get_consensus(self) -> dict[str, Any]:
        agents = self.schedule.agents
        if not agents:
            return {"consensus": 0.5, "diversity": 0.0, "num_agents": 0}
        predictions = [a.get_prediction() for a in agents]
        consensus = float(np.mean(predictions))
        diversity = float(np.std(predictions))
        return {"consensus": round(consensus, 4), "diversity": round(diversity, 4),
                "num_agents": len(agents), "min_prediction": round(min(predictions), 4),
                "max_prediction": round(max(predictions), 4),
                "agent_predictions": [round(p, 4) for p in predictions]}


class _SimpleScheduler:
    """Simple scheduler for Mesa-like agent stepping."""
    def __init__(self) -> None:
        self.agents: list = []
        self.time = 0

    def add(self, agent) -> None:
        self.agents.append(agent)

    def step(self) -> None:
        for agent in self.agents:
            agent.step()
        self.time += 1


class AgentSimulator:
    """Run multi-agent oracle simulations."""

    def __init__(self) -> None:
        self.available = HAS_MESA

    def simulate(self, num_agents: int = 10, steps: int = 20, systems_per_agent: int = 3,
                 all_systems: list[str] | None = None) -> dict[str, Any]:
        if not self.available:
            return {"consensus": 0.5, "diversity": 0.0, "method": "unavailable"}
        model = OracleModel(num_agents=num_agents, systems_per_agent=systems_per_agent, all_systems=all_systems)
        trajectory = []
        for _ in range(steps):
            model.step()
            state = model.get_consensus()
            trajectory.append(state["consensus"])
        final = model.get_consensus()
        trend = "stable"
        if len(trajectory) >= 3:
            slope = (trajectory[-1] - trajectory[-3]) / 2
            trend = "converging" if abs(slope) < 0.01 else ("diverging" if abs(slope) > 0.05 else "shifting")
        return {"consensus": final["consensus"], "diversity": final["diversity"],
                "trajectory": [round(t, 4) for t in trajectory], "trend": trend,
                "num_agents": num_agents, "steps": steps,
                "agent_predictions": final.get("agent_predictions", [])}

    def simulate_with_different_configs(self, configs: list[dict]) -> list[dict[str, Any]]:
        results = []
        for cfg in configs:
            result = self.simulate(
                num_agents=cfg.get("num_agents", 10),
                steps=cfg.get("steps", 20),
                systems_per_agent=cfg.get("systems_per_agent", 3),
                all_systems=cfg.get("all_systems"),
            )
            results.append({"config": cfg, "result": result})
        return results
