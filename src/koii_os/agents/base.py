from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass
class AgentContext:
    agent_id: str
    model_name: str | None = None
    memory: Dict[str, Any] = field(default_factory=dict)


class BaseAgent:
    def __init__(
        self,
        agent_id: str,
        agent_type: str,
        priority: int,
        cpu_quota: int,
        memory_mb: int,
        roles: list[str],
        attributes: dict[str, Any],
    ) -> None:
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.priority = priority
        self.cpu_quota = cpu_quota
        self.memory_mb = memory_mb
        self.roles = roles
        self.attributes = attributes
        self.context = AgentContext(agent_id=agent_id)
        self._alive = True
        self._last_heartbeat = time.time()

    async def run(self, task: dict[str, Any]) -> dict[str, Any]:
        await asyncio.sleep(0)
        self.heartbeat()
        return {
            "agent_id": self.agent_id,
            "status": "ok",
            "task": task,
            "result": f"{self.agent_type} handled task",
        }

    def heartbeat(self) -> None:
        self._last_heartbeat = time.time()

    def is_healthy(self, timeout_s: float = 5.0) -> bool:
        return self._alive and (time.time() - self._last_heartbeat) < timeout_s

    def self_heal(self) -> None:
        self._alive = True
        self.heartbeat()

    def terminate(self) -> None:
        self._alive = False

    def can_access(self, resource: str) -> bool:
        allowed = self.attributes.get("allowed_resources", ["model", "memory", "task_queue"])
        return resource in allowed
