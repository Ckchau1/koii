"""Secret Service integration for Koii Settings.

Only API keys should pass through this module. Non-secret configuration belongs
in GSettings and the shared Koii settings JSON file.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional
from uuid import uuid4


SCHEMA_NAME = "org.koii.Settings"


@dataclass
class SecretResult:
    ok: bool
    secret_id: str = ""
    reason: str = ""


class KoiiSecretStore:
    def __init__(self) -> None:
        self._secret = None
        self._schema = None
        try:
            import gi

            gi.require_version("Secret", "1")
            from gi.repository import Secret

            self._secret = Secret
            self._schema = Secret.Schema.new(
                SCHEMA_NAME,
                Secret.SchemaFlags.NONE,
                {
                    "provider": Secret.SchemaAttributeType.STRING,
                    "base-url": Secret.SchemaAttributeType.STRING,
                    "model": Secret.SchemaAttributeType.STRING,
                    "secret-id": Secret.SchemaAttributeType.STRING,
                },
            )
        except Exception as exc:
            self._unavailable_reason = str(exc)

    @property
    def available(self) -> bool:
        return self._secret is not None and self._schema is not None

    def store_api_key(self, provider: str, base_url: str, model: str, api_key: str) -> SecretResult:
        if not self.available:
            return SecretResult(ok=False, reason=getattr(self, "_unavailable_reason", "Secret Service unavailable"))
        if not api_key:
            return SecretResult(ok=False, reason="API key is empty")

        secret_id = str(uuid4())
        label = f"Koii {provider} API key"
        attrs = {
            "provider": provider or "unknown",
            "base-url": base_url or "",
            "model": model or "",
            "secret-id": secret_id,
        }
        try:
            self._secret.password_store_sync(
                self._schema,
                attrs,
                self._secret.COLLECTION_DEFAULT,
                label,
                api_key,
                None,
            )
        except Exception as exc:
            return SecretResult(ok=False, reason=str(exc))
        return SecretResult(ok=True, secret_id=secret_id)

    def lookup_api_key(self, secret_id: str) -> Optional[str]:
        if not self.available or not secret_id:
            return None
        try:
            return self._secret.password_lookup_sync(self._schema, {"secret-id": secret_id}, None)
        except Exception:
            return None

    def clear_api_key(self, secret_id: str) -> bool:
        if not self.available or not secret_id:
            return False
        try:
            return bool(self._secret.password_clear_sync(self._schema, {"secret-id": secret_id}, None))
        except Exception:
            return False
