from __future__ import annotations

from typing import Any

from ..core.kernel import KernelRuntime
from ..security.policy import SecurityPolicyEngine
from ..state.store import EventStore
from ..tools.os_control import OSToolExecutor


class TaskAutomationEngine:
    def __init__(
        self,
        kernel: KernelRuntime,
        security: SecurityPolicyEngine,
        tool_executor: OSToolExecutor,
        state_store: EventStore | None = None,
        browser: Any | None = None,
    ) -> None:
        self.kernel = kernel
        self.security = security
        self.tool_executor = tool_executor
        self.state_store = state_store
        self.browser = browser

    async def run_startup_tasks(self, cfg: dict[str, Any]) -> list[dict[str, Any]]:
        if not cfg.get("enabled", False):
            return []

        agent_id = str(cfg.get("default_agent_id", "orchestrator-1"))
        tasks = list(cfg.get("startup_tasks", []))
        results: list[dict[str, Any]] = []

        for task in tasks:
            result = await self.run_task(agent_id=agent_id, task=task)
            results.append(result)
        return results

    async def run_task(self, agent_id: str, task: dict[str, Any]) -> dict[str, Any]:
        task_id = str(task.get("id", "task"))
        task_name = str(task.get("description", task_id))
        steps = list(task.get("steps", []))
        outputs: list[dict[str, Any]] = []

        self._append_event("automation.task.started", {"task_id": task_id, "agent_id": agent_id, "task": task_name})

        for index, step in enumerate(steps, start=1):
            step_result = await self._run_step(agent_id=agent_id, step=step)
            outputs.append({"step": index, "type": step.get("type"), "result": step_result})
            if step_result.get("status") != "ok":
                result = {
                    "status": "error",
                    "task_id": task_id,
                    "task": task_name,
                    "outputs": outputs,
                }
                self._append_event("automation.task.failed", result)
                return result

        result = {
            "status": "ok",
            "task_id": task_id,
            "task": task_name,
            "outputs": outputs,
        }
        self._append_event("automation.task.completed", result)
        return result

    async def _run_step(self, agent_id: str, step: dict[str, Any]) -> dict[str, Any]:
        step_type = str(step.get("type", "shell"))
        if step_type == "shell":
            command = str(step.get("command", ""))
            if not self.security.authorize_os_action(agent_id, command):
                return {"status": "error", "reason": "unauthorized shell action", "command": command}
            return await self.tool_executor.run_shell(command=command, cwd=step.get("cwd"))

        if step_type == "model":
            return await self.kernel.syscall_model_infer(
                agent_id=agent_id,
                model_name=str(step.get("model", "mock-llm-v1")),
                prompt=str(step.get("prompt", "")),
            )

        if step_type == "read_file":
            return await self.tool_executor.read_text(str(step.get("path", "")))

        if step_type == "list_dir":
            return await self.tool_executor.list_dir(str(step.get("path", ".")))

        if step_type == "browser":
            if hasattr(self, "browser") and self.browser:
                action = step.get("action", {})
                return await self.browser.run_action(action)
            return {"status": "error", "reason": "browser not available"}

        return {"status": "error", "reason": f"unsupported step type: {step_type}"}

    def _append_event(self, topic: str, payload: dict[str, Any]) -> None:
        if self.state_store is not None:
            self.state_store.append(topic, payload)
