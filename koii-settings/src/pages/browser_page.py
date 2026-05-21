"""AI Browser settings page - Configure semantic browsing features."""

import gi

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Adw, Gio
from .base_page import BasePage


class BrowserPage(BasePage):
    """Page for configuring AI browser settings."""
    
    def __init__(self, config):
        """Initialize the browser page.
        
        Args:
            config: Configuration object
        """
        super().__init__(config, "AI Browser")
        self.build_ui()
    
    def build_ui(self):
        """Build the user interface."""
        # Page title
        title = Gtk.Label(label="AI Browser Settings")
        title.add_css_class('title-1')
        title.set_halign(Gtk.Align.START)
        title.set_margin_bottom(12)
        self.append(title)
        
        # Semantic browsing group
        semantic_group = self.create_preference_group(
            "Semantic-Driven Browsing",
            "Enable AI-powered understanding and interaction with web content"
        )
        
        # Semantic mode switch
        semantic_row, semantic_switch = self.create_switch_row(
            "Enable Semantic Mode",
            "Use AI to understand page content and context",
            self.config.browser_semantic_mode
        )
        self.config.bind('browser-semantic-mode', semantic_switch, 'active')
        semantic_group.add(semantic_row)
        
        # Auto-summarize switch
        summarize_row, summarize_switch = self.create_switch_row(
            "Auto-Summarize Pages",
            "Automatically generate summaries of web pages",
            self.config.browser_auto_summarize
        )
        self.config.bind('browser-auto-summarize', summarize_switch, 'active')
        semantic_group.add(summarize_row)
        
        self.append(semantic_group)
        
        # Privacy settings group
        privacy_group = self.create_preference_group(
            "Privacy & Security",
            "Control how AI browser handles your data"
        )
        
        # Privacy level combo
        privacy_row = self.create_combo_row(
            "Privacy Level",
            "Balance between functionality and privacy",
            [
                ('strict', 'Strict - Maximum privacy, limited AI features'),
                ('balanced', 'Balanced - Recommended for most users'),
                ('permissive', 'Permissive - Full AI features, less privacy'),
            ]
        )
        
        # Set current value
        current_privacy = self.config.browser_privacy_level
        privacy_levels = ['strict', 'balanced', 'permissive']
        if current_privacy in privacy_levels:
            privacy_row.set_selected(privacy_levels.index(current_privacy))
        
        # Connect signal
        privacy_row.connect('notify::selected', self.on_privacy_level_changed)
        
        privacy_group.add(privacy_row)
        
        # Privacy info
        privacy_info = Adw.ActionRow()
        privacy_info.set_title("Data Processing")
        
        info_label = Gtk.Label()
        info_label.set_markup(
            "<small>• Strict: All processing on-device\n"
            "• Balanced: Anonymized cloud processing\n"
            "• Permissive: Full cloud AI capabilities</small>"
        )
        info_label.set_halign(Gtk.Align.START)
        info_label.add_css_class('dim-label')
        privacy_info.set_child(info_label)
        
        privacy_group.add(privacy_info)
        
        self.append(privacy_group)
        
        # Features group
        features_group = self.create_preference_group(
            "AI Features",
            "Configure intelligent browsing capabilities"
        )
        
        # Feature list
        features = [
            {
                'title': 'Smart Navigation',
                'subtitle': 'AI suggests relevant links and actions',
                'key': 'browser-smart-navigation',
                'default': True
            },
            {
                'title': 'Content Extraction',
                'subtitle': 'Extract structured data from pages',
                'key': 'browser-content-extraction',
                'default': True
            },
            {
                'title': 'Form Auto-Fill',
                'subtitle': 'Intelligently fill forms based on context',
                'key': 'browser-form-autofill',
                'default': False
            },
            {
                'title': 'Translation',
                'subtitle': 'Real-time page translation',
                'key': 'browser-translation',
                'default': True
            },
        ]
        
        for feature in features:
            # Note: These settings would need to be added to the schema
            row = Adw.ActionRow()
            row.set_title(feature['title'])
            row.set_subtitle(feature['subtitle'])
            
            switch = Gtk.Switch()
            switch.set_active(feature['default'])
            switch.set_valign(Gtk.Align.CENTER)
            row.add_suffix(switch)
            row.set_activatable_widget(switch)
            
            features_group.add(row)
        
        self.append(features_group)
        
        # Performance group
        performance_group = self.create_preference_group(
            "Performance",
            "Optimize AI browser performance"
        )
        
        # Cache size
        cache_row, cache_spin = self.create_spin_row(
            "AI Cache Size (MB)",
            "Memory allocated for AI processing cache",
            value=512,
            min_val=128,
            max_val=2048,
            step=128
        )
        performance_group.add(cache_row)
        
        # Prefetch
        prefetch_row, prefetch_switch = self.create_switch_row(
            "Prefetch Content",
            "Preload likely next pages for faster browsing",
            True
        )
        performance_group.add(prefetch_row)
        
        self.append(performance_group)
        
        # Advanced group
        advanced_group = self.create_preference_group(
            "Advanced",
            "Expert settings for power users"
        )
        
        # User agent
        ua_row = self.create_entry_row(
            "Custom User Agent",
            "Override default browser identification",
            ""
        )
        advanced_group.add(ua_row)
        
        # Debug mode
        debug_row, debug_switch = self.create_switch_row(
            "Debug Mode",
            "Enable detailed logging for troubleshooting",
            False
        )
        advanced_group.add(debug_row)
        
        # Reset button
        reset_row = self.create_action_row(
            "Reset to Defaults",
            "Restore all browser settings to default values"
        )
        reset_button = Gtk.Button(label="Reset")
        reset_button.set_valign(Gtk.Align.CENTER)
        reset_button.add_css_class('destructive-action')
        reset_button.connect('clicked', self.on_reset_settings)
        reset_row.add_suffix(reset_button)
        advanced_group.add(reset_row)
        
        self.append(advanced_group)
    
    def on_privacy_level_changed(self, combo_row, param):
        """Handle privacy level change.
        
        Args:
            combo_row: The combo row
            param: Parameter spec
        """
        selected = combo_row.get_selected()
        privacy_levels = ['strict', 'balanced', 'permissive']
        if selected < len(privacy_levels):
            self.config.browser_privacy_level = privacy_levels[selected]
    
    def on_reset_settings(self, button):
        """Reset all browser settings to defaults."""
        # TODO: Show confirmation dialog
        self.config.browser_semantic_mode = True
        self.config.browser_privacy_level = 'balanced'
        self.config.browser_auto_summarize = True
        
        # Refresh UI
        self.refresh()
    
    def refresh(self):
        """Refresh the page content."""
        # Rebuild UI to reflect current settings
        # In a real implementation, we'd update widgets directly
        pass

# Made with Bob
