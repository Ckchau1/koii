from __future__ import annotations

from typing import Any

from ..state.store import EventStore
from .planner import AutonomousTaskLoop


class TaskCenter:
    def __init__(
        self,
        autonomous_loop: AutonomousTaskLoop,
        state_store: EventStore | None = None,
    ) -> None:
        self.autonomous_loop = autonomous_loop
        self.state_store = state_store

    async def run_goal_tasks(self, cfg: dict[str, Any]) -> list[dict[str, Any]]:
        if not cfg.get("enabled", False):
            return []

        agent_id = str(cfg.get("default_agent_id", "orchestrator-1"))
        max_iterations = int(cfg.get("max_iterations", 2))
        tasks = list(cfg.get("goal_tasks", []))
        results: list[dict[str, Any]] = []

        for task in tasks:
            retry_limit = int(task.get("retry_limit", 1))
            result = await self._run_with_retries(
                agent_id=agent_id,
                goal_task=task,
                max_iterations=max_iterations,
                retry_limit=retry_limit,
            )
            results.append(result)
        return results

    async def _run_with_retries(
        self,
        agent_id: str,
        goal_task: dict[str, Any],
        max_iterations: int,
        retry_limit: int,
    ) -> dict[str, Any]:
        goal_id = str(goal_task.get("id", "goal"))

        for attempt in range(1, retry_limit + 1):
            self._append_event("task_center.attempt.started", {"goal_id": goal_id, "attempt": attempt})
            result = await self.autonomous_loop.run_goal(
                agent_id=agent_id,
                goal_task=goal_task,
                max_iterations=max_iterations,
            )
            if result.get("status") == "ok":
                final = {**result, "attempt": attempt}
                self._append_event("task_center.attempt.completed", final)
                return final
            self._append_event("task_center.attempt.failed", {"goal_id": goal_id, "attempt": attempt, "result": result})

        return {
            "status": "error",
            "goal_id": goal_id,
            "reason": "retry limit reached",
            "retry_limit": retry_limit,
        }

    def _append_event(self, topic: str, payload: dict[str, Any]) -> None:
        if self.state_store is not None:
            self.state_store.append(topic, payload)
