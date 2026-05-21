from __future__ import annotations

import json
from typing import Any

from ..core.kernel import KernelRuntime
from ..state.store import EventStore
from .runner import TaskAutomationEngine


class TaskPlanner:
    def __init__(
        self,
        kernel: KernelRuntime,
        planner_model: str,
        state_store: EventStore | None = None,
        browser: Any | None = None,
    ) -> None:
        self.kernel = kernel
        self.planner_model = planner_model
        self.state_store = state_store
        self.browser = browser

    async def plan(
        self,
        agent_id: str,
        goal: str,
        observations: list[dict[str, Any]],
        cwd: str | None = None,
    ) -> dict[str, Any]:
        prompt = self._build_prompt(goal=goal, observations=observations, cwd=cwd)
        model_result = await self.kernel.syscall_model_infer(
            agent_id=agent_id,
            model_name=self.planner_model,
            prompt=prompt,
        )
        self._append_event("autonomy.plan.generated", {"agent_id": agent_id, "goal": goal, "model_result": model_result})

        if model_result.get("status") == "ok":
            parsed = self._try_parse_plan(str(model_result.get("output", "")))
            if parsed is not None:
                return parsed

        return self._fallback_plan(goal=goal, cwd=cwd)

    def observe(self, execution_result: dict[str, Any]) -> dict[str, Any]:
        if execution_result.get("status") == "ok":
            return {
                "status": "ok",
                "complete": True,
                "summary": "goal executed successfully",
            }

        failed_output = next(
            (output for output in execution_result.get("outputs", []) if output.get("result", {}).get("status") != "ok"),
            None,
        )
        return {
            "status": "error",
            "complete": False,
            "summary": failed_output.get("result", {}).get("reason", "task execution failed") if failed_output else "task execution failed",
        }

    def _build_prompt(self, goal: str, observations: list[dict[str, Any]], cwd: str | None) -> str:
        payload = {
            "goal": goal,
            "cwd": cwd or ".",
            "observations": observations[-3:],
            "schema": {
                "steps": [
                    {"type": "shell", "command": "whoami"},
                    {"type": "list_dir", "path": "."},
                    {"type": "browser", "action": {"action": "navigate", "url": "https://example.com"}},
                    {"type": "browser", "action": {"action": "screenshot", "label": "page"}},
                    {"type": "model", "model": self.planner_model, "prompt": "Summarize findings"},
                ]
            },
            "instruction": "Return JSON only with a top-level 'steps' array. Supported step types: shell, read_file, list_dir, model, browser. For browser steps, use action dict with: navigate, click, type, press, screenshot, get_text, get_links, get_elements, dom_snapshot, execute_js.",
        }
        return json.dumps(payload)

    def _try_parse_plan(self, output: str) -> dict[str, Any] | None:
        output = output.strip()
        if not output:
            return None
        try:
            data = json.loads(output)
        except json.JSONDecodeError:
            return None
        if not isinstance(data, dict):
            return None
        steps = data.get("steps")
        if not isinstance(steps, list):
            return None
        return {"steps": steps}

    def _fallback_plan(self, goal: str, cwd: str | None) -> dict[str, Any]:
        summary_prompt = f"Summarize results for goal: {goal}"
        return {
            "steps": [
                {"type": "shell", "command": "whoami"},
                {"type": "shell", "command": "pwd"},
                {"type": "list_dir", "path": cwd or "."},
                {"type": "model", "model": self.planner_model, "prompt": summary_prompt},
            ]
        }

    def _append_event(self, topic: str, payload: dict[str, Any]) -> None:
        if self.state_store is not None:
            self.state_store.append(topic, payload)


class AutonomousTaskLoop:
    def __init__(
        self,
        planner: TaskPlanner,
        runner: TaskAutomationEngine,
        state_store: EventStore | None = None,
    ) -> None:
        self.planner = planner
        self.runner = runner
        self.state_store = state_store

    async def run_goal(
        self,
        agent_id: str,
        goal_task: dict[str, Any],
        max_iterations: int,
    ) -> dict[str, Any]:
        goal_id = str(goal_task.get("id", "goal"))
        goal = str(goal_task.get("goal", goal_id))
        cwd = goal_task.get("cwd")
        observations: list[dict[str, Any]] = []

        self._append_event("autonomy.goal.started", {"goal_id": goal_id, "agent_id": agent_id, "goal": goal})

        for iteration in range(1, max_iterations + 1):
            plan = await self.planner.plan(agent_id=agent_id, goal=goal, observations=observations, cwd=cwd)
            execution = await self.runner.run_task(
                agent_id=agent_id,
                task={
                    "id": f"{goal_id}-iter-{iteration}",
                    "description": f"{goal} [iteration {iteration}]",
                    "steps": list(plan.get("steps", [])),
                },
            )
            observation = self.planner.observe(execution)
            observations.append({
                "iteration": iteration,
                "plan": plan,
                "execution": execution,
                "observation": observation,
            })
            self._append_event(
                "autonomy.goal.iteration",
                {"goal_id": goal_id, "iteration": iteration, "plan": plan, "observation": observation},
            )
            if observation.get("complete"):
                result = {
                    "status": "ok",
                    "goal_id": goal_id,
                    "goal": goal,
                    "iterations": iteration,
                    "observations": observations,
                }
                self._append_event("autonomy.goal.completed", result)
                return result

        result = {
            "status": "error",
            "goal_id": goal_id,
            "goal": goal,
            "iterations": max_iterations,
            "observations": observations,
            "reason": "max iterations reached",
        }
        self._append_event("autonomy.goal.failed", result)
        return result

    def _append_event(self, topic: str, payload: dict[str, Any]) -> None:
        if self.state_store is not None:
            self.state_store.append(topic, payload)
