from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen


class TelegramNotifier:
    def __init__(self, bot_token: str, chat_id: str) -> None:
        self.bot_token = bot_token
        self.chat_id = chat_id

    def send_message(self, text: str) -> dict[str, Any]:
        if not self.bot_token or not self.chat_id:
            return {"status": "error", "reason": "missing telegram bot token or chat id"}

        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        payload = {"chat_id": self.chat_id, "text": text}
        data = urlencode(payload).encode("utf-8")
        request = Request(url, data=data, method="POST")
        try:
            with urlopen(request, timeout=15) as response:
                body = response.read().decode("utf-8", errors="replace")
                return {"status": "ok", "response": json.loads(body)}
        except Exception as exc:
            return {"status": "error", "reason": str(exc)}


class WhatsAppNotifier:
    def __init__(self, access_token: str, phone_number_id: str, recipient: str) -> None:
        self.access_token = access_token
        self.phone_number_id = phone_number_id
        self.recipient = recipient

    def send_message(self, text: str) -> dict[str, Any]:
        if not self.access_token or not self.phone_number_id or not self.recipient:
            return {"status": "error", "reason": "missing WhatsApp credentials or recipient number"}

        url = f"https://graph.facebook.com/v17.0/{self.phone_number_id}/messages"
        body = json.dumps({
            "messaging_product": "whatsapp",
            "to": self.recipient,
            "type": "text",
            "text": {"body": text},
        }).encode("utf-8")
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.access_token}",
        }
        request = Request(url, data=body, headers=headers, method="POST")
        try:
            with urlopen(request, timeout=15) as response:
                body = response.read().decode("utf-8", errors="replace")
                return {"status": "ok", "response": json.loads(body)}
        except Exception as exc:
            return {"status": "error", "reason": str(exc)}


class CodingWorkspaceIntegration:
    def __init__(self, workspace_path: str | None = None) -> None:
        self.workspace_path = Path(workspace_path or ".").expanduser().resolve()

    def workspace_status(self) -> dict[str, Any]:
        git_root = self._find_git_root()
        branch = self._git_branch(git_root) if git_root else None
        changes = self._git_status(git_root) if git_root else []
        return {
            "workspace_path": str(self.workspace_path),
            "git_root": str(git_root) if git_root else None,
            "git_branch": branch,
            "git_changes": changes,
            "files": self._list_files(),
        }

    def _find_git_root(self) -> Path | None:
        current = self.workspace_path
        for _ in range(10):
            if (current / ".git").exists():
                return current
            if current.parent == current:
                break
            current = current.parent
        return None

    def _git_branch(self, git_root: Path) -> str | None:
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                cwd=git_root,
                capture_output=True,
                text=True,
                check=True,
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError:
            return None

    def _git_status(self, git_root: Path) -> list[str]:
        try:
            result = subprocess.run(
                ["git", "status", "--short"],
                cwd=git_root,
                capture_output=True,
                text=True,
                check=True,
            )
            return [line.strip() for line in result.stdout.splitlines() if line.strip()]
        except subprocess.CalledProcessError:
            return []

    def _list_files(self) -> list[str]:
        entries = []
        for path in sorted(self.workspace_path.rglob("*")):
            if path.is_file():
                entries.append(str(path.relative_to(self.workspace_path)))
                if len(entries) >= 100:
                    break
        return entries
