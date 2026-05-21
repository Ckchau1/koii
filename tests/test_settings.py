from __future__ import annotations

from pathlib import Path

from src.koii_os import settings as koii_settings
from src.koii_os.llm.registry import build_llm_registry_from_settings


def test_settings_round_trip(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("KOII_SETTINGS_FILE", str(tmp_path / "settings.json"))

    koii_settings.update_settings("llm", {"provider": "mock", "model": "mock-llm-v1"})
    koii_settings.update_settings("mode", {"system_mode": "privacy"})

    data = koii_settings.load_settings()

    assert data["llm"]["provider"] == "mock"
    assert data["llm"]["model"] == "mock-llm-v1"
    assert data["mode"]["system_mode"] == "privacy"
    assert koii_settings.mode_to_initiative("privacy") == "passive"


def test_llm_registry_from_mock_settings(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("KOII_SETTINGS_FILE", str(tmp_path / "settings.json"))
    koii_settings.update_settings("llm", {"provider": "mock", "model": "mock-llm-v1"})

    registry = build_llm_registry_from_settings(
        {
            "providers": [{"name": "mock-local", "type": "mock"}],
            "model_routes": {"mock-llm-v1": "mock-local"},
        }
    )

    assert "mock-local" in registry.providers
    assert registry.model_to_provider["mock-llm-v1"] == "mock-local"
