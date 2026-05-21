"""Configuration management for Koii Settings."""

import gi  # type: ignore[import-untyped]

gi.require_version('Gio', '2.0')

from gi.repository import Gio  # type: ignore[import-untyped,import-not-found]

try:
    from koii_os.settings import load_settings, mode_to_initiative, update_settings  # type: ignore[import-not-found]
except Exception:  # pragma: no cover - standalone development without koii_os path
    load_settings = None
    mode_to_initiative = None
    update_settings = None


class Config:
    """Manages application configuration using GSettings."""
    
    SCHEMA_ID = "org.koii.Settings"
    
    def __init__(self):
        """Initialize configuration."""
        self.settings = Gio.Settings.new(self.SCHEMA_ID)
    
    # Window state
    @property
    def window_width(self):
        return self.settings.get_int("window-width")
    
    @window_width.setter
    def window_width(self, value):
        self.settings.set_int("window-width", value)
    
    @property
    def window_height(self):
        return self.settings.get_int("window-height")
    
    @window_height.setter
    def window_height(self, value):
        self.settings.set_int("window-height", value)
    
    @property
    def window_maximized(self):
        return self.settings.get_boolean("window-maximized")
    
    @window_maximized.setter
    def window_maximized(self, value):
        self.settings.set_boolean("window-maximized", value)
    
    # Agent system settings
    @property
    def initiative_level(self):
        return self.settings.get_string("initiative-level")
    
    @initiative_level.setter
    def initiative_level(self, value):
        self.settings.set_string("initiative-level", value)
    
    @property
    def initiative_score_threshold(self):
        return self.settings.get_double("initiative-score-threshold")
    
    @initiative_score_threshold.setter
    def initiative_score_threshold(self, value):
        self.settings.set_double("initiative-score-threshold", value)
    
    @property
    def enable_reflexion(self):
        return self.settings.get_boolean("enable-reflexion")
    
    @enable_reflexion.setter
    def enable_reflexion(self, value):
        self.settings.set_boolean("enable-reflexion", value)
    
    @property
    def max_agent_memory_mb(self):
        return self.settings.get_int("max-agent-memory-mb")
    
    @max_agent_memory_mb.setter
    def max_agent_memory_mb(self, value):
        self.settings.set_int("max-agent-memory-mb", value)
    
    @property
    def agent_cpu_quota(self):
        return self.settings.get_int("agent-cpu-quota")
    
    @agent_cpu_quota.setter
    def agent_cpu_quota(self, value):
        self.settings.set_int("agent-cpu-quota", value)
    
    # AI Browser settings
    @property
    def browser_semantic_mode(self):
        return self.settings.get_boolean("browser-semantic-mode")
    
    @browser_semantic_mode.setter
    def browser_semantic_mode(self, value):
        self.settings.set_boolean("browser-semantic-mode", value)
    
    @property
    def browser_privacy_level(self):
        return self.settings.get_string("browser-privacy-level")
    
    @browser_privacy_level.setter
    def browser_privacy_level(self, value):
        self.settings.set_string("browser-privacy-level", value)
    
    @property
    def browser_auto_summarize(self):
        return self.settings.get_boolean("browser-auto-summarize")
    
    @browser_auto_summarize.setter
    def browser_auto_summarize(self, value):
        self.settings.set_boolean("browser-auto-summarize", value)
    
    # Task system settings
    @property
    def task_auto_planning(self):
        return self.settings.get_boolean("task-auto-planning")
    
    @task_auto_planning.setter
    def task_auto_planning(self, value):
        self.settings.set_boolean("task-auto-planning", value)
    
    @property
    def task_max_concurrent(self):
        return self.settings.get_int("task-max-concurrent")
    
    @task_max_concurrent.setter
    def task_max_concurrent(self, value):
        self.settings.set_int("task-max-concurrent", value)
    
    @property
    def task_history_days(self):
        return self.settings.get_int("task-history-days")
    
    @task_history_days.setter
    def task_history_days(self, value):
        self.settings.set_int("task-history-days", value)
    
    # Security settings
    @property
    def enable_audit_log(self):
        return self.settings.get_boolean("enable-audit-log")
    
    @enable_audit_log.setter
    def enable_audit_log(self, value):
        self.settings.set_boolean("enable-audit-log", value)
    
    @property
    def require_confirmation(self):
        return self.settings.get_boolean("require-confirmation")
    
    @require_confirmation.setter
    def require_confirmation(self, value):
        self.settings.set_boolean("require-confirmation", value)
    
    @property
    def log_retention_days(self):
        return self.settings.get_int("log-retention-days")
    
    @log_retention_days.setter
    def log_retention_days(self, value):
        self.settings.set_int("log-retention-days", value)
    
    # LLM provider settings
    @property
    def llm_provider(self):
        return self.settings.get_string("llm-provider")
    
    @llm_provider.setter
    def llm_provider(self, value):
        self.settings.set_string("llm-provider", value)
        self._mirror_llm(provider=value)
    
    @property
    def llm_model(self):
        return self.settings.get_string("llm-model")
    
    @llm_model.setter
    def llm_model(self, value):
        self.settings.set_string("llm-model", value)
        self._mirror_llm(model=value)

    @property
    def llm_base_url(self):
        return self.settings.get_string("llm-base-url")

    @llm_base_url.setter
    def llm_base_url(self, value):
        self.settings.set_string("llm-base-url", value)
        self._mirror_llm(base_url=value)

    @property
    def llm_api_key_secret_id(self):
        return self.settings.get_string("llm-api-key-secret-id")

    @llm_api_key_secret_id.setter
    def llm_api_key_secret_id(self, value):
        self.settings.set_string("llm-api-key-secret-id", value)
        self._mirror_llm(api_key_secret_id=value)
    
    @property
    def llm_temperature(self):
        return self.settings.get_double("llm-temperature")
    
    @llm_temperature.setter
    def llm_temperature(self, value):
        self.settings.set_double("llm-temperature", value)
        self._mirror_llm(temperature=value)
    
    @property
    def llm_max_tokens(self):
        return self.settings.get_int("llm-max-tokens")
    
    @llm_max_tokens.setter
    def llm_max_tokens(self, value):
        self.settings.set_int("llm-max-tokens", value)
        self._mirror_llm(max_tokens=value)

    @property
    def system_mode(self):
        return self.settings.get_string("system-mode")

    @system_mode.setter
    def system_mode(self, value):
        self.settings.set_string("system-mode", value)
        if mode_to_initiative:
            self.initiative_level = mode_to_initiative(value)
        self._mirror_mode(system_mode=value, initiative_level=self.initiative_level)

    @property
    def plugin_agent_enabled(self):
        return self.settings.get_boolean("plugin-agent-enabled")

    @plugin_agent_enabled.setter
    def plugin_agent_enabled(self, value):
        self.settings.set_boolean("plugin-agent-enabled", value)
        self._mirror_agents(plugin_agent_enabled=value)

    @property
    def core_settings_agent_enabled(self):
        return self.settings.get_boolean("core-settings-agent-enabled")

    @core_settings_agent_enabled.setter
    def core_settings_agent_enabled(self, value):
        self.settings.set_boolean("core-settings-agent-enabled", value)
        self._mirror_agents(core_settings_agent_enabled=value)

    @property
    def mode_settings_agent_enabled(self):
        return self.settings.get_boolean("mode-settings-agent-enabled")

    @mode_settings_agent_enabled.setter
    def mode_settings_agent_enabled(self, value):
        self.settings.set_boolean("mode-settings-agent-enabled", value)
        self._mirror_agents(mode_settings_agent_enabled=value)
    
    def bind(self, key, obj, prop, flags=Gio.SettingsBindFlags.DEFAULT):
        """Bind a setting to an object property."""
        self.settings.bind(key, obj, prop, flags)

    def sync_from_shared_settings(self):
        """Import non-secret settings from the shared Koii runtime settings file."""
        if not load_settings:
            return
        shared = load_settings()
        llm = shared.get("llm", {})
        mode = shared.get("mode", {})
        agents = shared.get("agents", {})
        for key, attr in (
            ("provider", "llm_provider"),
            ("base_url", "llm_base_url"),
            ("model", "llm_model"),
            ("api_key_secret_id", "llm_api_key_secret_id"),
            ("temperature", "llm_temperature"),
            ("max_tokens", "llm_max_tokens"),
        ):
            if key in llm:
                setattr(self, attr, llm[key])
        if "system_mode" in mode:
            self.system_mode = mode["system_mode"]
        if "plugin_agent_enabled" in agents:
            self.plugin_agent_enabled = bool(agents["plugin_agent_enabled"])
        if "core_settings_agent_enabled" in agents:
            self.core_settings_agent_enabled = bool(agents["core_settings_agent_enabled"])
        if "mode_settings_agent_enabled" in agents:
            self.mode_settings_agent_enabled = bool(agents["mode_settings_agent_enabled"])

    def _mirror_llm(self, **values):
        if update_settings:
            update_settings("llm", values)

    def _mirror_mode(self, **values):
        if update_settings:
            update_settings("mode", values)

    def _mirror_agents(self, **values):
        if update_settings:
            update_settings("agents", values)

# Made with Bob
