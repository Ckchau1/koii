#!/usr/bin/env python3
from __future__ import annotations

import os
from pathlib import Path
from typing import Dict

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gio

ENV_PATH = Path("/opt/aios/.env")
DEFAULTS = {
    "KOII_LLM_PROFILE": "offline",
    "KOII_VLLM_ENDPOINT": "http://localhost:8000",
    "OPENAI_API_KEY": "",
    "ANTHROPIC_API_KEY": "",
    "KOII_LLM_MODEL": "",
    "KOII_2FA_ENABLED": "",
    "KOII_2FA_SECRET": "",
    "TELEGRAM_BOT_TOKEN": "",
    "TELEGRAM_CHAT_ID": "",
    "WHATSAPP_ACCESS_TOKEN": "",
    "WHATSAPP_PHONE_NUMBER_ID": "",
    "WHATSAPP_RECIPIENT_NUMBER": "",
    "CODING_WORKSPACE_PATH": "",
}

PROFILES = ["offline", "fast", "quality", "local"]


def parse_env(path: Path) -> Dict[str, str]:
    result: Dict[str, str] = {}
    if not path.exists():
        return result
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        result[key.strip()] = value.strip()
    return result


def write_env(path: Path, values: Dict[str, str]) -> None:
    existing = parse_env(path)
    existing.update(values)
    lines = [f"{k}={v}" for k, v in existing.items()]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


class AIOSSettingsWindow(Gtk.Window):
    def __init__(self) -> None:
        super().__init__(title="AIOS Settings")
        self.set_border_width(16)
        self.set_default_size(580, 360)

        self.env_values = DEFAULTS.copy()
        self.env_values.update(parse_env(ENV_PATH))

        grid = Gtk.Grid(column_spacing=16, row_spacing=12, margin=12)
        self.add(grid)

        heading = Gtk.Label(label="Configure AIOS LLM settings")
        heading.set_xalign(0)
        heading.get_style_context().add_class("title")
        grid.attach(heading, 0, 0, 2, 1)

        self.profile_combo = Gtk.ComboBoxText()
        for profile in PROFILES:
            self.profile_combo.append_text(profile)
        try:
            active_index = PROFILES.index(self.env_values.get("KOII_LLM_PROFILE", "offline"))
        except ValueError:
            active_index = 0
        self.profile_combo.set_active(active_index)

        self.endpoint_entry = Gtk.Entry()
        self.endpoint_entry.set_text(self.env_values.get("KOII_VLLM_ENDPOINT", DEFAULTS["KOII_VLLM_ENDPOINT"]))

        self.openai_entry = Gtk.Entry()
        self.openai_entry.set_text(self.env_values.get("OPENAI_API_KEY", ""))
        self.openai_entry.set_visibility(False)

        self.anthropic_entry = Gtk.Entry()
        self.anthropic_entry.set_text(self.env_values.get("ANTHROPIC_API_KEY", ""))
        self.anthropic_entry.set_visibility(False)

        self.model_entry = Gtk.Entry()
        self.model_entry.set_text(self.env_values.get("KOII_LLM_MODEL", ""))

        self.telegram_token_entry = Gtk.Entry()
        self.telegram_token_entry.set_text(self.env_values.get("TELEGRAM_BOT_TOKEN", ""))
        self.telegram_token_entry.set_visibility(False)

        self.telegram_chat_entry = Gtk.Entry()
        self.telegram_chat_entry.set_text(self.env_values.get("TELEGRAM_CHAT_ID", ""))

        self.whatsapp_token_entry = Gtk.Entry()
        self.whatsapp_token_entry.set_text(self.env_values.get("WHATSAPP_ACCESS_TOKEN", ""))
        self.whatsapp_token_entry.set_visibility(False)

        self.whatsapp_phone_id_entry = Gtk.Entry()
        self.whatsapp_phone_id_entry.set_text(self.env_values.get("WHATSAPP_PHONE_NUMBER_ID", ""))

        self.whatsapp_recipient_entry = Gtk.Entry()
        self.whatsapp_recipient_entry.set_text(self.env_values.get("WHATSAPP_RECIPIENT_NUMBER", ""))

        self.workspace_path_entry = Gtk.Entry()
        self.workspace_path_entry.set_text(self.env_values.get("CODING_WORKSPACE_PATH", ""))

        # 2FA settings
        self.twofa_checkbox = Gtk.CheckButton(label="Enable 2FA (TOTP)")
        self.twofa_checkbox.set_active(self.env_values.get("KOII_2FA_ENABLED", "") == "1")

        self.twofa_secret_entry = Gtk.Entry()
        self.twofa_secret_entry.set_text(self.env_values.get("KOII_2FA_SECRET", ""))
        self.twofa_secret_entry.set_visibility(False)

        self.twofa_code_entry = Gtk.Entry()
        self.twofa_code_entry.set_placeholder_text("Enter current code to verify")

        verify_button = Gtk.Button(label="Verify Code")
        verify_button.connect("clicked", self.on_verify_2fa_clicked)

        grid.attach(Gtk.Label(label="LLM Profile:"), 0, 1, 1, 1)
        grid.attach(self.profile_combo, 1, 1, 1, 1)

        grid.attach(Gtk.Label(label="vLLM endpoint:"), 0, 2, 1, 1)
        grid.attach(self.endpoint_entry, 1, 2, 1, 1)

        grid.attach(Gtk.Label(label="OpenAI API key:"), 0, 3, 1, 1)
        grid.attach(self.openai_entry, 1, 3, 1, 1)

        grid.attach(Gtk.Label(label="Anthropic API key:"), 0, 4, 1, 1)
        grid.attach(self.anthropic_entry, 1, 4, 1, 1)

        grid.attach(Gtk.Label(label="Explicit LLM model:"), 0, 5, 1, 1)
        grid.attach(self.model_entry, 1, 5, 1, 1)

        grid.attach(Gtk.Label(label="Telegram bot token:"), 0, 6, 1, 1)
        grid.attach(self.telegram_token_entry, 1, 6, 1, 1)

        grid.attach(Gtk.Label(label="Telegram chat id:"), 0, 7, 1, 1)
        grid.attach(self.telegram_chat_entry, 1, 7, 1, 1)

        grid.attach(Gtk.Label(label="WhatsApp access token:"), 0, 8, 1, 1)
        grid.attach(self.whatsapp_token_entry, 1, 8, 1, 1)

        grid.attach(Gtk.Label(label="WhatsApp phone number ID:"), 0, 9, 1, 1)
        grid.attach(self.whatsapp_phone_id_entry, 1, 9, 1, 1)

        grid.attach(Gtk.Label(label="WhatsApp recipient number:"), 0, 10, 1, 1)
        grid.attach(self.whatsapp_recipient_entry, 1, 10, 1, 1)

        grid.attach(Gtk.Label(label="Coding workspace path:"), 0, 11, 1, 1)
        grid.attach(self.workspace_path_entry, 1, 11, 1, 1)

        grid.attach(Gtk.Label(label="Enable 2FA:"), 0, 12, 1, 1)
        grid.attach(self.twofa_checkbox, 1, 12, 1, 1)

        grid.attach(Gtk.Label(label="2FA Secret:"), 0, 13, 1, 1)
        grid.attach(self.twofa_secret_entry, 1, 13, 1, 1)

        grid.attach(Gtk.Label(label="2FA Code (verify):"), 0, 14, 1, 1)
        grid.attach(self.twofa_code_entry, 1, 14, 1, 1)
        grid.attach(verify_button, 1, 15, 1, 1)

        button_box = Gtk.ButtonBox(spacing=8)
        button_box.set_layout(Gtk.ButtonBoxStyle.END)
        save_button = Gtk.Button(label="Save")
        save_button.connect("clicked", self.on_save_clicked)
        close_button = Gtk.Button(label="Close")
        close_button.connect("clicked", self.on_close_clicked)
        button_box.add(save_button)
        button_box.add(close_button)

        grid.attach(button_box, 0, 6, 2, 1)

        note = Gtk.Label(
            label="This tool edits /opt/aios/.env. Use a root-enabled launcher or run with sudo.",
            xalign=0,
        )
        note.set_line_wrap(True)
        grid.attach(note, 0, 7, 2, 1)

    def on_save_clicked(self, button: Gtk.Button) -> None:
        values = {
            "KOII_LLM_PROFILE": self.profile_combo.get_active_text() or "offline",
            "KOII_VLLM_ENDPOINT": self.endpoint_entry.get_text().strip() or DEFAULTS["KOII_VLLM_ENDPOINT"],
            "OPENAI_API_KEY": self.openai_entry.get_text().strip(),
            "ANTHROPIC_API_KEY": self.anthropic_entry.get_text().strip(),
            "KOII_LLM_MODEL": self.model_entry.get_text().strip(),
            "TELEGRAM_BOT_TOKEN": self.telegram_token_entry.get_text().strip(),
            "TELEGRAM_CHAT_ID": self.telegram_chat_entry.get_text().strip(),
            "WHATSAPP_ACCESS_TOKEN": self.whatsapp_token_entry.get_text().strip(),
            "WHATSAPP_PHONE_NUMBER_ID": self.whatsapp_phone_id_entry.get_text().strip(),
            "WHATSAPP_RECIPIENT_NUMBER": self.whatsapp_recipient_entry.get_text().strip(),
            "CODING_WORKSPACE_PATH": self.workspace_path_entry.get_text().strip(),
            "KOII_2FA_ENABLED": "1" if self.twofa_checkbox.get_active() else "",
            "KOII_2FA_SECRET": self.twofa_secret_entry.get_text().strip(),
        }
        try:
            if not ENV_PATH.exists():
                ENV_PATH.parent.mkdir(parents=True, exist_ok=True)
                ENV_PATH.write_text("", encoding="utf-8")
            write_env(ENV_PATH, values)
            self.show_message("Saved configuration to /opt/aios/.env")
        except Exception as exc:
            self.show_message(f"Unable to save settings: {exc}")

    def show_message(self, message: str) -> None:
        dialog = Gtk.MessageDialog(
            parent=self,
            flags=0,
            message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.OK,
            text=message,
        )
        dialog.run()
        dialog.destroy()

    def on_verify_2fa_clicked(self, button: Gtk.Button) -> None:
        secret = self.twofa_secret_entry.get_text().strip()
        code = self.twofa_code_entry.get_text().strip()
        if not secret or not code:
            self.show_message("Please enter both a 2FA secret and code before verifying.")
            return
        # Try to verify using local helper script
        try:
            import subprocess
            p = subprocess.run(["/usr/bin/env", "python3", "/opt/aios/aios-2fa.py", "verify", secret, code], capture_output=True, text=True)
            out = p.stdout.strip()
            if out == "ok":
                self.show_message("2FA code verified successfully.")
            else:
                self.show_message("2FA verification failed. Make sure your device time is correct.")
        except Exception as exc:
            self.show_message(f"Verification failed: {exc}")

    def on_close_clicked(self, button: Gtk.Button) -> None:
        self.close()


def main() -> None:
    app = Gtk.Application(application_id="org.aios.settings")

    def on_activate(application: Gtk.Application) -> None:
        window = AIOSSettingsWindow()
        window.set_application(application)
        window.show_all()

    app.connect("activate", on_activate)
    app.run(None)


if __name__ == "__main__":
    main()
