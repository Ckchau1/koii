from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


DEFAULT_SYSTEM_MODE = "development"
DEFAULT_LLM_PROVIDER = "mock"
DEFAULT_LLM_MODEL = "mock-llm-v1"


def _settings_path() -> Path:
    explicit = os.getenv("KOII_SETTINGS_FILE")
    if explicit:
        return Path(explicit)

    system_path = Path("/opt/aios/config/koii-settings.json")
    if system_path.parent.exists() and os.access(system_path.parent, os.W_OK):
        return system_path

    xdg_config = Path(os.getenv("XDG_CONFIG_HOME", Path.home() / ".config"))
    return xdg_config / "koii" / "settings.json"


def default_settings() -> dict[str, Any]:
    return {
        "llm": {
            "provider": DEFAULT_LLM_PROVIDER,
            "base_url": "",
            "model": DEFAULT_LLM_MODEL,
            "api_key_secret_id": "",
            "temperature": 0.7,
            "max_tokens": 2048,
        },
        "mode": {
            "system_mode": DEFAULT_SYSTEM_MODE,
            "initiative_level": "balanced",
        },
        "agents": {
            "plugin_agent_enabled": True,
            "core_settings_agent_enabled": True,
            "mode_settings_agent_enabled": True,
        },
    }


def load_settings() -> dict[str, Any]:
    data = default_settings()
    path = _settings_path()
    if not path.exists():
        return data

    try:
        loaded = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return data

    if not isinstance(loaded, dict):
        return data

    _deep_update(data, loaded)
    return data


def save_settings(settings: dict[str, Any]) -> Path:
    path = _settings_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = default_settings()
    _deep_update(payload, settings)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    try:
        path.chmod(0o600)
    except OSError:
        pass
    return path


def update_settings(section: str, values: dict[str, Any]) -> dict[str, Any]:
    settings = load_settings()
    current = settings.setdefault(section, {})
    if isinstance(current, dict):
        current.update(values)
    else:
        settings[section] = values
    save_settings(settings)
    return settings


def lookup_secret(secret_id: str) -> str | None:
    if not secret_id:
        return None
    try:
        import gi

        gi.require_version("Secret", "1")
        from gi.repository import Secret

        schema = Secret.Schema.new(
            "org.koii.Settings",
            Secret.SchemaFlags.NONE,
            {
                "provider": Secret.SchemaAttributeType.STRING,
                "base-url": Secret.SchemaAttributeType.STRING,
                "model": Secret.SchemaAttributeType.STRING,
                "secret-id": Secret.SchemaAttributeType.STRING,
            },
        )
        return Secret.password_lookup_sync(schema, {"secret-id": secret_id}, None)
    except Exception:
        return None


def mode_to_initiative(system_mode: str) -> str:
    mapping = {
        "development": "balanced",
        "production": "balanced",
        "privacy": "passive",
        "learning": "balanced",
        "highly-initiative": "highly-initiative",
    }
    return mapping.get(system_mode, "balanced")


def _deep_update(target: dict[str, Any], source: dict[str, Any]) -> None:
    for key, value in source.items():
        if isinstance(value, dict) and isinstance(target.get(key), dict):
            _deep_update(target[key], value)
        else:
            target[key] = value
