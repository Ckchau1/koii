from __future__ import annotations

from typing import Any

from ..automation.task_center import TaskCenter
from ..state.store import EventStore
from .resource_federation import GlobalResourceManager


class WorkflowRuntime:
    def __init__(
        self,
        task_center: TaskCenter,
        resource_manager: GlobalResourceManager,
        state_store: EventStore | None = None,
    ) -> None:
        self.task_center = task_center
        self.resource_manager = resource_manager
        self.state_store = state_store

    async def run_workflows(self, cfg: dict[str, Any], autonomy_cfg: dict[str, Any]) -> list[dict[str, Any]]:
        workflows = list(cfg.get("workflows", []))
        results: list[dict[str, Any]] = []

        for workflow in workflows:
            result = await self.run_single_workflow(workflow, autonomy_cfg)
            results.append(result)
        return results

    async def run_single_workflow(self, workflow: dict[str, Any], autonomy_cfg: dict[str, Any]) -> dict[str, Any]:
        name = str(workflow.get("name", "workflow"))
        resource_requirements = workflow.get("resources", {})
        reserve = self.resource_manager.reserve(
            cpu=int(resource_requirements.get("cpu", 1)),
            memory_mb=int(resource_requirements.get("memory_mb", 512)),
            gpu=int(resource_requirements.get("gpu", 0)),
            preferred_region=workflow.get("region"),
        )
        if reserve.get("status") != "ok":
            result = {"status": "error", "workflow": name, "phase": "reserve", "detail": reserve}
            self._append_event("workflow.failed", result)
            return result

        local_autonomy_cfg = dict(autonomy_cfg)
        local_autonomy_cfg["goal_tasks"] = list(workflow.get("goals", []))
        local_autonomy_cfg["enabled"] = True
        if "max_iterations" in workflow:
            local_autonomy_cfg["max_iterations"] = int(workflow["max_iterations"])

        goal_results = await self.task_center.run_goal_tasks(local_autonomy_cfg)

        release = self.resource_manager.release(
            node_id=str(reserve["node_id"]),
            cpu=int(resource_requirements.get("cpu", 1)),
            memory_mb=int(resource_requirements.get("memory_mb", 512)),
            gpu=int(resource_requirements.get("gpu", 0)),
        )

        status = "ok" if all(r.get("status") == "ok" for r in goal_results) else "error"
        result = {
            "status": status,
            "workflow": name,
            "reservation": reserve,
            "goals": goal_results,
            "release": release,
        }
        self._append_event("workflow.completed" if status == "ok" else "workflow.failed", result)
        return result

    def _append_event(self, topic: str, payload: dict[str, Any]) -> None:
        if self.state_store is not None:
            self.state_store.append(topic, payload)
