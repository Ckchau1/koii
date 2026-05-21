from __future__ import annotations

import asyncio
import json
import os
from abc import ABC, abstractmethod
from typing import Any
from urllib import request


class LLMProvider(ABC):
    def __init__(self, name: str) -> None:
        self.name = name

    @abstractmethod
    async def infer(self, model: str, prompt: str, **kwargs: Any) -> dict[str, Any]:
        raise NotImplementedError


class MockLLMProvider(LLMProvider):
    async def infer(self, model: str, prompt: str, **kwargs: Any) -> dict[str, Any]:
        await asyncio.sleep(0)
        return {
            "status": "ok",
            "provider": self.name,
            "model": model,
            "output": f"[{model}] {prompt[:256]}",
        }


class OpenAIProvider(LLMProvider):
    def __init__(
        self,
        name: str,
        api_key_env: str = "OPENAI_API_KEY",
        base_url: str | None = None,
        api_key: str | None = None,
    ) -> None:
        super().__init__(name)
        self.api_key_env = api_key_env
        self.base_url = base_url
        self.api_key = api_key

    async def infer(self, model: str, prompt: str, **kwargs: Any) -> dict[str, Any]:
        api_key = self.api_key or os.getenv(self.api_key_env)
        if not api_key:
            return {"status": "error", "reason": f"missing env {self.api_key_env}"}
        try:
            from openai import AsyncOpenAI
            client_kwargs = {"api_key": api_key}
            if self.base_url:
                client_kwargs["base_url"] = self.base_url
            client = AsyncOpenAI(**client_kwargs)
            messages = kwargs.get("messages") or [{"role": "user", "content": prompt}]
            response = await client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=kwargs.get("temperature", 0.2),
                max_tokens=kwargs.get("max_tokens", 1024),
            )
            output = response.choices[0].message.content or ""
            return {
                "status": "ok",
                "provider": self.name,
                "model": model,
                "output": output,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                    "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                },
            }
        except Exception as exc:
            return {"status": "error", "provider": self.name, "model": model, "reason": str(exc)}


class AnthropicProvider(LLMProvider):
    def __init__(
        self,
        name: str,
        api_key_env: str = "ANTHROPIC_API_KEY",
        base_url: str | None = None,
        api_key: str | None = None,
    ) -> None:
        super().__init__(name)
        self.api_key_env = api_key_env
        self.base_url = base_url
        self.api_key = api_key

    async def infer(self, model: str, prompt: str, **kwargs: Any) -> dict[str, Any]:
        api_key = self.api_key or os.getenv(self.api_key_env)
        if not api_key:
            return {"status": "error", "reason": f"missing env {self.api_key_env}"}
        try:
            import anthropic
            client_kwargs = {"api_key": api_key}
            if self.base_url:
                client_kwargs["base_url"] = self.base_url
            client = anthropic.AsyncAnthropic(**client_kwargs)
            messages = kwargs.get("messages") or [{"role": "user", "content": prompt}]
            response = await client.messages.create(
                model=model,
                max_tokens=kwargs.get("max_tokens", 1024),
                messages=messages,
            )
            output = response.content[0].text if response.content else ""
            return {
                "status": "ok",
                "provider": self.name,
                "model": model,
                "output": output,
                "usage": {
                    "prompt_tokens": response.usage.input_tokens if response.usage else 0,
                    "completion_tokens": response.usage.output_tokens if response.usage else 0,
                },
            }
        except Exception as exc:
            return {"status": "error", "provider": self.name, "model": model, "reason": str(exc)}


class VLLMProvider(LLMProvider):
    def __init__(self, name: str, endpoint: str) -> None:
        super().__init__(name)
        self.endpoint = endpoint.rstrip("/")

    async def infer(self, model: str, prompt: str, **kwargs: Any) -> dict[str, Any]:
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": kwargs.get("max_tokens", 256),
            "temperature": kwargs.get("temperature", 0.2),
        }
        headers = {"Content-Type": "application/json"}
        return await _post_json(
            f"{self.endpoint}/v1/chat/completions",
            payload,
            headers,
            provider=self.name,
            model=model,
            extractor=lambda data: (data.get("choices", [{}])[0].get("message", {}) or {}).get("content", ""),
        )


async def _post_json(
    url: str,
    payload: dict[str, Any],
    headers: dict[str, str],
    provider: str,
    model: str,
    extractor: Any,
) -> dict[str, Any]:
    body = json.dumps(payload).encode("utf-8")

    def _request() -> dict[str, Any]:
        req = request.Request(url=url, method="POST", data=body, headers=headers)
        try:
            with request.urlopen(req, timeout=20) as res:
                raw = res.read().decode("utf-8")
                data = json.loads(raw)
                return {
                    "status": "ok",
                    "provider": provider,
                    "model": model,
                    "output": extractor(data),
                    "raw": data,
                }
        except Exception as exc:  # pragma: no cover - network and remote errors
            return {
                "status": "error",
                "provider": provider,
                "model": model,
                "reason": str(exc),
            }

    return await asyncio.to_thread(_request)
