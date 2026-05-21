"""System Settings page - Configure Koii OS core parameters."""

import gi

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Adw
from .base_page import BasePage
from ..keyring import KoiiSecretStore


class SystemPage(BasePage):
    """Page for configuring Koii OS system settings."""
    
    def __init__(self, config):
        """Initialize the system page.
        
        Args:
            config: Configuration object
        """
        super().__init__(config, "System Settings")
        self.secret_store = KoiiSecretStore()
        self.build_ui()
    
    def build_ui(self):
        """Build the user interface."""
        # Page title
        title = Gtk.Label(label="Koii OS System Settings")
        title.add_css_class('title-1')
        title.set_halign(Gtk.Align.START)
        title.set_margin_bottom(12)
        self.append(title)
        
        # Agent behavior group
        behavior_group = self.create_preference_group(
            "Agent Behavior",
            "Control how AI agents interact and make decisions"
        )
        
        # Initiative level
        initiative_row = self.create_combo_row(
            "Initiative Level",
            "How proactive agents should be in taking actions",
            [
                ('passive', 'Passive - Wait for explicit instructions'),
                ('balanced', 'Balanced - Moderate proactivity (Recommended)'),
                ('highly-initiative', 'Highly Initiative - Maximum autonomy'),
            ]
        )
        
        # Set current value
        current_level = self.config.initiative_level
        levels = ['passive', 'balanced', 'highly-initiative']
        if current_level in levels:
            initiative_row.set_selected(levels.index(current_level))
        
        initiative_row.connect('notify::selected', self.on_initiative_changed)
        behavior_group.add(initiative_row)
        
        # Initiative score threshold
        threshold_row, threshold_spin = self.create_spin_row(
            "Initiative Score Threshold",
            "Minimum score (0.0-1.0) for agent to take initiative",
            value=self.config.initiative_score_threshold,
            min_val=0.0,
            max_val=1.0,
            step=0.1
        )
        threshold_spin.set_digits(1)
        threshold_spin.connect('value-changed', self.on_threshold_changed)
        behavior_group.add(threshold_row)
        
        # Reflexion mechanism
        reflexion_row, reflexion_switch = self.create_switch_row(
            "Enable Reflexion",
            "Allow agents to reflect on and improve their responses",
            self.config.enable_reflexion
        )
        self.config.bind('enable-reflexion', reflexion_switch, 'active')
        behavior_group.add(reflexion_row)
        
        self.append(behavior_group)

        # Operating mode group
        mode_group = self.create_preference_group(
            "Koii OS Mode",
            "Switch the system profile used by agents, task automation, and privacy controls"
        )

        mode_row = self.create_combo_row(
            "System Mode",
            "Mode changes also update the semantic initiative level",
            [
                ('development', 'Development - Debug-friendly automation'),
                ('production', 'Production - Stable guarded automation'),
                ('privacy', 'Privacy - Minimize proactive and browser actions'),
                ('learning', 'Learning - Explain and guide while acting'),
                ('highly-initiative', 'Highly Initiative - Maximum autonomy'),
            ]
        )
        modes = ['development', 'production', 'privacy', 'learning', 'highly-initiative']
        if self.config.system_mode in modes:
            mode_row.set_selected(modes.index(self.config.system_mode))
        mode_row.connect('notify::selected', self.on_mode_changed)
        mode_group.add(mode_row)

        builtin_agents = [
            (
                "Plugin Development Agent",
                "Generate, test, debug, version, and deploy third-party API plugins",
                "plugin-agent-enabled",
            ),
            (
                "Core Settings Agent",
                "Manage kernel settings, resources, and zero-trust security policy",
                "core-settings-agent-enabled",
            ),
            (
                "Mode Settings Agent",
                "Switch operating modes and semantic initiative levels",
                "mode-settings-agent-enabled",
            ),
        ]
        for title_text, subtitle, key in builtin_agents:
            current = self.config.settings.get_boolean(key)
            row, switch = self.create_switch_row(title_text, subtitle, current)
            self.config.bind(key, switch, 'active')
            mode_group.add(row)

        self.append(mode_group)
        
        # Resource allocation group
        resources_group = self.create_preference_group(
            "Resource Allocation",
            "Manage system resources for AI agents"
        )
        
        # Memory limit
        memory_row, memory_spin = self.create_spin_row(
            "Max Agent Memory (MB)",
            "Maximum memory allocation per agent",
            value=self.config.max_agent_memory_mb,
            min_val=256,
            max_val=8192,
            step=256
        )
        memory_spin.connect('value-changed', self.on_memory_changed)
        resources_group.add(memory_row)
        
        # CPU quota
        cpu_row, cpu_spin = self.create_spin_row(
            "Agent CPU Quota (%)",
            "CPU usage limit for agents",
            value=self.config.agent_cpu_quota,
            min_val=10,
            max_val=100,
            step=5
        )
        cpu_spin.connect('value-changed', self.on_cpu_changed)
        resources_group.add(cpu_row)
        
        # Resource info
        info_row = Adw.ActionRow()
        info_row.set_title("Current Resource Usage")
        
        info_label = Gtk.Label()
        info_label.set_markup(
            "<small>Memory: 2.1 GB / 8 GB\n"
            "CPU: 35% / 100%\n"
            "Active Agents: 2</small>"
        )
        info_label.set_halign(Gtk.Align.START)
        info_label.add_css_class('dim-label')
        info_row.set_child(info_label)
        
        resources_group.add(info_row)
        
        self.append(resources_group)
        
        # LLM provider group
        llm_group = self.create_preference_group(
            "LLM Provider",
            "Configure language model backend"
        )
        
        # Provider selection
        provider_row = self.create_combo_row(
            "Default Provider",
            "Language model provider for AI agents",
            [
                ('mock', 'Mock - Testing only (no API calls)'),
                ('openai', 'OpenAI - GPT models'),
                ('anthropic', 'Anthropic - Claude models'),
                ('vllm', 'vLLM - Local inference server'),
            ]
        )
        
        current_provider = self.config.llm_provider
        providers = ['mock', 'openai', 'anthropic', 'vllm']
        if current_provider in providers:
            provider_row.set_selected(providers.index(current_provider))
        
        provider_row.connect('notify::selected', self.on_provider_changed)
        llm_group.add(provider_row)
        
        # Model name
        model_row = self.create_entry_row(
            "Model Name",
            "Specific model to use (e.g., gpt-4, claude-3-opus)",
            self.config.llm_model
        )
        model_row.connect('changed', self.on_model_changed)
        llm_group.add(model_row)

        # Base API URL
        base_url_row = self.create_entry_row(
            "Base API URL",
            "Optional OpenAI-compatible endpoint (e.g., https://api.openai.com/v1)",
            self.config.llm_base_url
        )
        base_url_row.connect('changed', self.on_base_url_changed)
        llm_group.add(base_url_row)

        # API key in Secret Service
        key_row = Adw.PasswordEntryRow()
        key_row.set_title("API Key")
        key_row.set_text("")
        key_row.set_show_apply_button(True)
        key_row.connect('apply', self.on_api_key_apply)
        if self.config.llm_api_key_secret_id:
            key_row.set_text("configured")
        llm_group.add(key_row)

        secret_status = "Secret Service available" if self.secret_store.available else "Secret Service unavailable"
        secret_row = self.create_action_row(
            "API Key Storage",
            f"{secret_status}; keys are never stored in GSettings"
        )
        clear_key_button = Gtk.Button(label="Clear Key")
        clear_key_button.set_valign(Gtk.Align.CENTER)
        clear_key_button.connect('clicked', self.on_clear_api_key)
        secret_row.add_suffix(clear_key_button)
        llm_group.add(secret_row)
        
        # Temperature
        temp_row, temp_spin = self.create_spin_row(
            "Temperature",
            "Randomness in model outputs (0.0-2.0)",
            value=self.config.llm_temperature,
            min_val=0.0,
            max_val=2.0,
            step=0.1
        )
        temp_spin.set_digits(1)
        temp_spin.connect('value-changed', self.on_temperature_changed)
        llm_group.add(temp_row)
        
        # Max tokens
        tokens_row, tokens_spin = self.create_spin_row(
            "Max Tokens",
            "Maximum length of model responses",
            value=self.config.llm_max_tokens,
            min_val=256,
            max_val=8192,
            step=256
        )
        tokens_spin.connect('value-changed', self.on_tokens_changed)
        llm_group.add(tokens_row)
        
        self.append(llm_group)
        
        # Multi-agent collaboration group
        collab_group = self.create_preference_group(
            "Multi-Agent Collaboration",
            "Configure how agents work together"
        )
        
        collab_features = [
            {
                'title': 'Enable Agent Communication',
                'subtitle': 'Allow agents to share information',
                'default': True
            },
            {
                'title': 'Shared Memory Pool',
                'subtitle': 'Agents can access shared context',
                'default': True
            },
            {
                'title': 'Task Delegation',
                'subtitle': 'Agents can delegate subtasks to others',
                'default': False
            },
            {
                'title': 'Consensus Decision Making',
                'subtitle': 'Multiple agents vote on important decisions',
                'default': False
            },
        ]
        
        for feature in collab_features:
            row, switch = self.create_switch_row(
                feature['title'],
                feature['subtitle'],
                feature['default']
            )
            collab_group.add(row)
        
        self.append(collab_group)
        
        # Advanced group
        advanced_group = self.create_preference_group(
            "Advanced",
            "Expert settings and system maintenance"
        )
        
        # Debug logging
        debug_row, debug_switch = self.create_switch_row(
            "Debug Logging",
            "Enable detailed system logs",
            False
        )
        advanced_group.add(debug_row)
        
        # Telemetry
        telemetry_row, telemetry_switch = self.create_switch_row(
            "Anonymous Telemetry",
            "Help improve Koii OS by sharing usage data",
            False
        )
        advanced_group.add(telemetry_row)
        
        # System info
        info_button_row = self.create_action_row(
            "System Information",
            "View detailed system and version info"
        )
        info_button = Gtk.Button(label="View")
        info_button.set_valign(Gtk.Align.CENTER)
        info_button.connect('clicked', self.on_view_system_info)
        info_button_row.add_suffix(info_button)
        advanced_group.add(info_button_row)
        
        # Reset all settings
        reset_row = self.create_action_row(
            "Reset All Settings",
            "Restore all Koii OS settings to defaults"
        )
        reset_button = Gtk.Button(label="Reset")
        reset_button.set_valign(Gtk.Align.CENTER)
        reset_button.add_css_class('destructive-action')
        reset_button.connect('clicked', self.on_reset_all)
        reset_row.add_suffix(reset_button)
        advanced_group.add(reset_row)
        
        self.append(advanced_group)
    
    def on_initiative_changed(self, combo_row, param):
        """Handle initiative level change."""
        selected = combo_row.get_selected()
        levels = ['passive', 'balanced', 'highly-initiative']
        if selected < len(levels):
            self.config.initiative_level = levels[selected]
            self.config._mirror_mode(initiative_level=levels[selected])

    def on_mode_changed(self, combo_row, param):
        """Handle Koii OS mode change."""
        selected = combo_row.get_selected()
        modes = ['development', 'production', 'privacy', 'learning', 'highly-initiative']
        if selected < len(modes):
            self.config.system_mode = modes[selected]
    
    def on_threshold_changed(self, spin_button):
        """Handle threshold change."""
        self.config.initiative_score_threshold = spin_button.get_value()
    
    def on_memory_changed(self, spin_button):
        """Handle memory limit change."""
        self.config.max_agent_memory_mb = int(spin_button.get_value())
    
    def on_cpu_changed(self, spin_button):
        """Handle CPU quota change."""
        self.config.agent_cpu_quota = int(spin_button.get_value())
    
    def on_provider_changed(self, combo_row, param):
        """Handle provider change."""
        selected = combo_row.get_selected()
        providers = ['mock', 'openai', 'anthropic', 'vllm']
        if selected < len(providers):
            self.config.llm_provider = providers[selected]
    
    def on_model_changed(self, entry_row):
        """Handle model name change."""
        self.config.llm_model = entry_row.get_text()

    def on_base_url_changed(self, entry_row):
        """Handle LLM base URL change."""
        self.config.llm_base_url = entry_row.get_text()

    def on_api_key_apply(self, entry_row):
        """Store API key in Secret Service and keep only the secret ID in settings."""
        text = entry_row.get_text()
        if not text or text == "configured":
            return
        result = self.secret_store.store_api_key(
            provider=self.config.llm_provider,
            base_url=self.config.llm_base_url,
            model=self.config.llm_model,
            api_key=text,
        )
        if result.ok:
            self.config.llm_api_key_secret_id = result.secret_id
            entry_row.set_text("configured")
        else:
            print(f"Failed to store API key: {result.reason}")

    def on_clear_api_key(self, button):
        """Clear the configured API key reference and remove the key if available."""
        secret_id = self.config.llm_api_key_secret_id
        if secret_id:
            self.secret_store.clear_api_key(secret_id)
        self.config.llm_api_key_secret_id = ""
    
    def on_temperature_changed(self, spin_button):
        """Handle temperature change."""
        self.config.llm_temperature = spin_button.get_value()
    
    def on_tokens_changed(self, spin_button):
        """Handle max tokens change."""
        self.config.llm_max_tokens = int(spin_button.get_value())
    
    def on_view_system_info(self, button):
        """Show system information dialog."""
        # TODO: Create system info dialog
        print("Show system info")
    
    def on_reset_all(self, button):
        """Reset all settings to defaults."""
        # TODO: Show confirmation dialog
        print("Reset all settings")

# Made with Bob
