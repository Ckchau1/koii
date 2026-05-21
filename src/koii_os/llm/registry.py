from __future__ import annotations

from typing import Any

from ..settings import load_settings, lookup_secret

from .providers import (
    AnthropicProvider,
    LLMProvider,
    MockLLMProvider,
    OpenAIProvider,
    VLLMProvider,
)


class LLMRegistry:
    def __init__(self) -> None:
        self.providers: dict[str, LLMProvider] = {}
        self.model_to_provider: dict[str, str] = {}

    def register_provider(self, provider: LLMProvider) -> None:
        self.providers[provider.name] = provider

    def route_model(self, model_name: str, provider_name: str) -> None:
        if provider_name not in self.providers:
            raise ValueError(f"provider not registered: {provider_name}")
        self.model_to_provider[model_name] = provider_name

    async def infer(self, model_name: str, prompt: str, **kwargs: Any) -> dict[str, Any]:
        provider_name = self.model_to_provider.get(model_name)
        if provider_name is None:
            return {"status": "error", "reason": f"no route for model {model_name}"}

        provider = self.providers[provider_name]
        return await provider.infer(model=model_name, prompt=prompt, **kwargs)


def resolve_selected_model(
    cfg: dict[str, Any],
    profile_name: str | None,
    capability_name: str | None,
    explicit_model: str | None,
) -> str:
    if explicit_model:
        return explicit_model

    selection_cfg = cfg.get("selection", {})
    profiles = selection_cfg.get("profiles", {})
    capabilities = selection_cfg.get("capability_routes", {})

    if profile_name:
        model = profiles.get(profile_name)
        if model:
            return model

    if capability_name:
        model = capabilities.get(capability_name)
        if model:
            return model

    return str(selection_cfg.get("default_model", "mock-llm-v1"))


def build_llm_registry(cfg: dict[str, Any]) -> LLMRegistry:
    registry = LLMRegistry()

    providers_cfg = cfg.get("providers", [])
    for item in providers_cfg:
        ptype = item.get("type", "mock")
        name = item["name"]

        if ptype == "openai":
            provider = OpenAIProvider(
                name=name,
                api_key_env=item.get("api_key_env", "OPENAI_API_KEY"),
                base_url=item.get("base_url") or None,
                api_key=item.get("api_key") or None,
            )
        elif ptype == "anthropic":
            provider = AnthropicProvider(
                name=name,
                api_key_env=item.get("api_key_env", "ANTHROPIC_API_KEY"),
                base_url=item.get("base_url") or None,
                api_key=item.get("api_key") or None,
            )
        elif ptype == "vllm":
            provider = VLLMProvider(name=name, endpoint=item.get("endpoint", "http://localhost:8000"))
        else:
            provider = MockLLMProvider(name=name)

        registry.register_provider(provider)

    for model_name, provider_name in cfg.get("model_routes", {}).items():
        registry.route_model(model_name=model_name, provider_name=provider_name)

    return registry


def build_llm_registry_from_settings(base_cfg: dict[str, Any] | None = None) -> LLMRegistry:
    cfg = dict(base_cfg or {})
    settings = load_settings()
    llm = settings.get("llm", {})
    provider_type = str(llm.get("provider") or "mock")
    model = str(llm.get("model") or "mock-llm-v1")
    base_url = str(llm.get("base_url") or "")
    secret_id = str(llm.get("api_key_secret_id") or "")
    api_key = lookup_secret(secret_id)

    if provider_type == "mock":
        return build_llm_registry(cfg or {
            "providers": [{"name": "mock-local", "type": "mock"}],
            "model_routes": {model: "mock-local"},
            "selection": {"default_model": model},
        })

    provider_name = f"{provider_type}-settings"
    provider_cfg: dict[str, Any] = {"name": provider_name, "type": provider_type}
    if base_url:
        if provider_type == "vllm":
            provider_cfg["endpoint"] = base_url
        else:
            provider_cfg["base_url"] = base_url
    if api_key:
        provider_cfg["api_key"] = api_key

    merged = {
        **cfg,
        "providers": [provider_cfg],
        "model_routes": {model: provider_name},
        "selection": {
            **cfg.get("selection", {}),
            "default_model": model,
        },
    }
    return build_llm_registry(merged)
