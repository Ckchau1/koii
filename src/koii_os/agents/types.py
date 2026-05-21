from __future__ import annotations

import asyncio
from typing import Any

from .base import BaseAgent


class TaskAgent(BaseAgent):
    async def run(self, task: dict[str, Any]) -> dict[str, Any]:
        await asyncio.sleep(0.002)
        self.heartbeat()
        return {
            "agent_id": self.agent_id,
            "status": "ok",
            "kind": "task",
            "output": f"task processed: {task.get('payload')}",
        }


class ComputeAgent(BaseAgent):
    async def run(self, task: dict[str, Any]) -> dict[str, Any]:
        n = int(task.get("payload", 1000))
        result = sum(i * i for i in range(n))
        await asyncio.sleep(0)
        self.heartbeat()
        return {
            "agent_id": self.agent_id,
            "status": "ok",
            "kind": "compute",
            "output": result,
        }


class OrchestrationAgent(BaseAgent):
    async def run(self, task: dict[str, Any]) -> dict[str, Any]:
        await asyncio.sleep(0)
        self.heartbeat()
        return {
            "agent_id": self.agent_id,
            "status": "ok",
            "kind": "orchestration",
            "output": f"workflow staged for {task.get('name', 'unnamed')}",
        }


class SystemAgent(BaseAgent):
    async def run(self, task: dict[str, Any]) -> dict[str, Any]:
        await asyncio.sleep(0)
        self.heartbeat()
        return {
            "agent_id": self.agent_id,
            "status": "ok",
            "kind": "system",
            "output": "system health verified",
        }


def create_agent(agent_cfg: dict[str, Any]) -> BaseAgent:
    common = dict(
        agent_id=agent_cfg["id"],
        agent_type=agent_cfg["type"],
        priority=int(agent_cfg.get("priority", 50)),
        cpu_quota=int(agent_cfg.get("cpu_quota", 1)),
        memory_mb=int(agent_cfg.get("memory_mb", 128)),
        roles=list(agent_cfg.get("roles", [])),
        attributes=dict(agent_cfg.get("attributes", {})),
    )

    mapping = {
        "task": TaskAgent,
        "compute": ComputeAgent,
        "orchestration": OrchestrationAgent,
        "system": SystemAgent,
    }
    cls = mapping.get(agent_cfg["type"], TaskAgent)
    return cls(**common)
