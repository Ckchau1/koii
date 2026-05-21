from __future__ import annotations

import asyncio
import os
from pathlib import Path
import shutil
from typing import Any


class OSToolExecutor:
    def __init__(self, allowed_shell_commands: list[str] | None = None) -> None:
        self.allowed_shell_commands = allowed_shell_commands or []

    def _is_allowed(self, command: str) -> bool:
        normalized = command.strip()
        return any(
            normalized == allowed or normalized.startswith(f"{allowed} ")
            for allowed in self.allowed_shell_commands
        )

    async def run_shell(self, command: str, cwd: str | None = None) -> dict[str, Any]:
        if not self._is_allowed(command):
            return {
                "status": "error",
                "reason": "command not allowed",
                "command": command,
            }

        if os.name == "nt":
            shell_path = shutil.which("pwsh") or shutil.which("powershell")
            if shell_path is None:
                return {
                    "status": "error",
                    "reason": "no PowerShell executable found",
                    "command": command,
                }
            process = await asyncio.create_subprocess_exec(
                shell_path,
                "-NoProfile",
                "-Command",
                command,
                cwd=cwd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
        else:
            process = await asyncio.create_subprocess_exec(
                "/bin/bash",
                "-lc",
                command,
                cwd=cwd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
        stdout, stderr = await process.communicate()
        return {
            "status": "ok" if process.returncode == 0 else "error",
            "command": command,
            "returncode": process.returncode,
            "stdout": stdout.decode("utf-8", errors="replace").strip(),
            "stderr": stderr.decode("utf-8", errors="replace").strip(),
        }

    async def read_text(self, path: str) -> dict[str, Any]:
        target = Path(path)
        if not target.exists() or not target.is_file():
            return {"status": "error", "reason": "file not found", "path": path}
        return {"status": "ok", "path": path, "content": target.read_text(encoding="utf-8")}

    async def list_dir(self, path: str) -> dict[str, Any]:
        target = Path(path)
        if not target.exists() or not target.is_dir():
            return {"status": "error", "reason": "directory not found", "path": path}
        return {
            "status": "ok",
            "path": path,
            "entries": sorted(child.name for child in target.iterdir()),
        }
