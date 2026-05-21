from __future__ import annotations

import asyncio
from typing import Any

from ..core.scheduler import AgentScheduler
from .registry import AgentRegistry
from ..transport.bus import MessageBus


class CollaborationEngine:
    def __init__(self, scheduler: AgentScheduler, registry: AgentRegistry, bus: MessageBus) -> None:
        self.scheduler = scheduler
        self.registry = registry
        self.bus = bus

    def decompose(self, objective: str) -> list[dict[str, Any]]:
        return [
            {"name": "analyze", "payload": f"analyze:{objective}"},
            {"name": "compute", "payload": 2500},
            {"name": "summarize", "payload": f"summarize:{objective}"},
        ]

    async def delegate(self, tasks: list[dict[str, Any]]) -> None:
        workers = self.registry.discover(role="worker")
        if not workers:
            return
        for idx, task in enumerate(tasks):
            target = workers[idx % len(workers)].agent_id
            await self.scheduler.submit(target, task)
            await self.bus.publish(
                "task.delegated",
                {
                    "target_agent": target,
                    "task": task,
                },
            )

    async def execute_parallel(self, tasks: list[dict[str, Any]]) -> list[dict[str, Any]]:
        workers = self.registry.discover(role="worker")
        if not workers:
            return []

        coros = []
        for idx, task in enumerate(tasks):
            agent = self.scheduler.agents[workers[idx % len(workers)].agent_id]
            coros.append(agent.run(task))
        return await asyncio.gather(*coros)

    def synthesize(self, results: list[dict[str, Any]]) -> dict[str, Any]:
        valid = [r for r in results if r.get("status") == "ok"]
        summary = {
            "status": "ok" if valid else "error",
            "count": len(valid),
            "results": valid,
        }
        return summary
