from __future__ import annotations

import asyncio
from typing import Any

from ..state.store import EventStore
from .task_center import TaskCenter


class TaskCenterDaemon:
    def __init__(
        self,
        task_center: TaskCenter,
        state_store: EventStore | None = None,
    ) -> None:
        self.task_center = task_center
        self.state_store = state_store
        self._running = False

    async def run(self, cfg: dict[str, Any]) -> list[dict[str, Any]]:
        if not cfg.get("enabled", False):
            return []

        self._running = True
        mode = str(cfg.get("mode", "bounded"))
        poll_interval_s = float(cfg.get("poll_interval_s", 5.0))
        max_cycles = int(cfg.get("max_cycles", 1))
        cycle_results: list[dict[str, Any]] = []
        cycle = 0

        self._append_event("daemon.started", {"mode": mode, "poll_interval_s": poll_interval_s, "max_cycles": max_cycles})

        try:
            while self._running:
                cycle += 1
                result = await self.task_center.run_goal_tasks(cfg)
                cycle_payload = {"cycle": cycle, "results": result}
                cycle_results.append(cycle_payload)
                self._append_event("daemon.cycle.completed", cycle_payload)

                if mode != "forever" and cycle >= max_cycles:
                    break

                await asyncio.sleep(poll_interval_s)
        finally:
            self._running = False
            self._append_event("daemon.stopped", {"cycles": cycle})

        return cycle_results

    def stop(self) -> None:
        self._running = False

    def _append_event(self, topic: str, payload: dict[str, Any]) -> None:
        if self.state_store is not None:
            self.state_store.append(topic, payload)
