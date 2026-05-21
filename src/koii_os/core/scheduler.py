from __future__ import annotations

import asyncio
import heapq
import itertools
import uuid
from dataclasses import dataclass, field
from typing import Any

from ..agents.base import BaseAgent
from ..state.store import EventStore


@dataclass(order=True)
class ScheduledTask:
    # Negative priority gives max-priority behavior using min-heap.
    sort_index: tuple[int, int] = field(init=False)
    priority: int
    seq: int
    agent_id: str
    task: dict[str, Any]

    def __post_init__(self) -> None:
        self.sort_index = (-self.priority, self.seq)


class AgentScheduler:
    def __init__(self, max_agents: int, state_store: EventStore | None = None) -> None:
        self.max_agents = max_agents
        self.state_store = state_store
        self.agents: dict[str, BaseAgent] = {}
        self._queue: list[ScheduledTask] = []
        self._counter = itertools.count()
        self._lock = asyncio.Lock()

    def register_agent(self, agent: BaseAgent) -> None:
        if len(self.agents) >= self.max_agents:
            raise RuntimeError("agent limit reached")
        self.agents[agent.agent_id] = agent

    def unregister_agent(self, agent_id: str) -> None:
        self.agents.pop(agent_id, None)

    def get_agent(self, agent_id: str) -> BaseAgent | None:
        return self.agents.get(agent_id)

    def discover_agents(self, role: str | None = None, agent_type: str | None = None) -> list[BaseAgent]:
        candidates = list(self.agents.values())
        if role is not None:
            candidates = [agent for agent in candidates if role in agent.roles]
        if agent_type is not None:
            candidates = [agent for agent in candidates if agent.agent_type == agent_type]
        return sorted(candidates, key=lambda agent: (-agent.priority, agent.agent_id))

    def queue_length(self) -> int:
        return len(self._queue)

    def get_agent_load(self, agent_id: str) -> int:
        return sum(1 for item in self._queue if item.agent_id == agent_id)

    async def submit(self, agent_id: str, task: dict[str, Any]) -> None:
        async with self._lock:
            task = dict(task)
            task_id = str(task.get("task_id") or uuid.uuid4())
            task["task_id"] = task_id
            if agent_id not in self.agents:
                raise KeyError(f"agent not registered: {agent_id}")
            agent = self.agents[agent_id]
            item = ScheduledTask(
                priority=agent.priority,
                seq=next(self._counter),
                agent_id=agent_id,
                task=task,
            )
            heapq.heappush(self._queue, item)
            if self.state_store is not None:
                self.state_store.append(
                    "task.submitted",
                    {
                        "task_id": task_id,
                        "agent_id": agent_id,
                        "task": task,
                    },
                )

    async def route_task(self, task: dict[str, Any], role: str | None = None, agent_type: str | None = None) -> str:
        candidates = self.discover_agents(role=role, agent_type=agent_type)
        if not candidates:
            raise RuntimeError("no available agent matches the requested role/type")
        selected = candidates[0]
        await self.submit(selected.agent_id, task)
        return selected.agent_id

    async def pop_next(self) -> ScheduledTask | None:
        async with self._lock:
            while self._queue:
                item = heapq.heappop(self._queue)
                if item.agent_id in self.agents:
                    return item
            return None

    async def execute_next(self) -> dict[str, Any] | None:
        item = await self.pop_next()
        if item is None:
            return None
        agent = self.agents[item.agent_id]
        if not agent.is_healthy():
            agent.self_heal()
        result = await agent.run(item.task)
        if self.state_store is not None:
            self.state_store.append(
                "task.completed",
                {
                    "task_id": item.task.get("task_id"),
                    "agent_id": item.agent_id,
                    "result": result,
                },
            )
        return result
