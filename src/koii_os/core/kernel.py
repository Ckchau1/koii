from __future__ import annotations

import asyncio
import time
from typing import Any

from .scheduler import AgentScheduler
from ..llm.registry import LLMRegistry
from ..security.policy import SecurityPolicyEngine


class KernelRuntime:
    def __init__(
        self,
        scheduler: AgentScheduler,
        security: SecurityPolicyEngine,
        llm_registry: LLMRegistry,
        tick_ms: int = 1,
    ) -> None:
        self.scheduler = scheduler
        self.security = security
        self.llm_registry = llm_registry
        self.tick_ms = tick_ms
        self._running = False
        self._results: list[dict[str, Any]] = []

    async def syscall_model_infer(
        self,
        agent_id: str,
        model_name: str,
        prompt: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        if not self.security.authorize_model_call(agent_id, model_name):
            return {"status": "error", "reason": "unauthorized"}
        return await self.llm_registry.infer(model_name=model_name, prompt=prompt, **kwargs)

    async def run_for(self, duration_s: float) -> list[dict[str, Any]]:
        self._running = True
        deadline = time.time() + duration_s
        tick_s = self.tick_ms / 1000.0
        results: list[dict[str, Any]] = []

        while self._running and time.time() < deadline:
            result = await self.scheduler.execute_next()
            if result is not None:
                results.append(result)
            await asyncio.sleep(tick_s)

        self._running = False
        return results

    def stop(self) -> None:
        self._running = False
