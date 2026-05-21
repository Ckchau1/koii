"""Security & Logs page - Audit trails and security settings."""

import gi

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Adw, GLib
from .base_page import BasePage
import datetime


class SecurityPage(BasePage):
    """Page for security settings and audit logs."""
    
    def __init__(self, config):
        """Initialize the security page.
        
        Args:
            config: Configuration object
        """
        super().__init__(config, "Security & Logs")
        self.logs = []
        self.build_ui()
        self.refresh()
    
    def build_ui(self):
        """Build the user interface."""
        # Header
        header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        header_box.set_margin_bottom(12)
        
        title = Gtk.Label(label="Security & Audit Logs")
        title.add_css_class('title-1')
        title.set_halign(Gtk.Align.START)
        title.set_hexpand(True)
        header_box.append(title)
        
        # Refresh button
        refresh_button = Gtk.Button(label="Refresh")
        refresh_button.set_icon_name("view-refresh-symbolic")
        refresh_button.connect('clicked', lambda _: self.refresh())
        header_box.append(refresh_button)
        
        self.append(header_box)
        
        # Security settings group
        security_group = self.create_preference_group(
            "Security Settings",
            "Configure security and privacy features"
        )
        
        # Audit logging
        audit_row, audit_switch = self.create_switch_row(
            "Enable Audit Logging",
            "Record all agent actions for security review",
            self.config.enable_audit_log
        )
        self.config.bind('enable-audit-log', audit_switch, 'active')
        security_group.add(audit_row)
        
        # User confirmation
        confirm_row, confirm_switch = self.create_switch_row(
            "Require User Confirmation",
            "Ask before agents perform sensitive operations",
            self.config.require_confirmation
        )
        self.config.bind('require-confirmation', confirm_switch, 'active')
        security_group.add(confirm_row)
        
        # Log retention
        retention_row, retention_spin = self.create_spin_row(
            "Log Retention (days)",
            "How long to keep security logs",
            value=self.config.log_retention_days,
            min_val=1,
            max_val=365,
            step=1
        )
        retention_spin.connect('value-changed', self.on_retention_changed)
        security_group.add(retention_row)
        
        self.append(security_group)
        
        # Security status group
        status_group = self.create_preference_group(
            "Security Status",
            "Current security posture and alerts"
        )
        
        # Security score card
        score_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        score_box.add_css_class('card')
        score_box.set_margin_start(0)
        score_box.set_margin_end(0)
        score_box.set_margin_top(0)
        score_box.set_margin_bottom(12)
        
        inner = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        inner.set_margin_start(16)
        inner.set_margin_end(16)
        inner.set_margin_top(16)
        inner.set_margin_bottom(16)
        
        score_title = Gtk.Label(label="Security Score")
        score_title.set_halign(Gtk.Align.START)
        score_title.add_css_class('caption')
        score_title.add_css_class('dim-label')
        inner.append(score_title)
        
        score_value = Gtk.Label(label="85/100")
        score_value.set_halign(Gtk.Align.START)
        score_value.add_css_class('title-1')
        score_value.add_css_class('success')
        inner.append(score_value)
        
        score_desc = Gtk.Label(label="Good - No critical issues detected")
        score_desc.set_halign(Gtk.Align.START)
        score_desc.add_css_class('caption')
        score_desc.add_css_class('dim-label')
        inner.append(score_desc)
        
        score_box.append(inner)
        status_group.add(score_box)
        
        # Recent alerts
        alerts_row = self.create_action_row(
            "Security Alerts",
            "0 active alerts, 3 resolved in last 24h"
        )
        alerts_button = Gtk.Button(label="View")
        alerts_button.set_valign(Gtk.Align.CENTER)
        alerts_button.connect('clicked', self.on_view_alerts)
        alerts_row.add_suffix(alerts_button)
        status_group.add(alerts_row)
        
        self.append(status_group)
        
        # Audit log group
        log_group = self.create_preference_group(
            "Recent Audit Log",
            "Latest security-relevant events"
        )
        
        # Log filter buttons
        filter_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        filter_box.set_margin_bottom(12)
        
        filter_label = Gtk.Label(label="Filter:")
        filter_label.add_css_class('dim-label')
        filter_box.append(filter_label)
        
        filters = ['All', 'Info', 'Warning', 'Error', 'Critical']
        for filter_name in filters:
            button = Gtk.ToggleButton(label=filter_name)
            if filter_name == 'All':
                button.set_active(True)
            button.connect('toggled', lambda b, f=filter_name: self.on_filter_changed(f, b))
            filter_box.append(button)
        
        log_group.add(filter_box)
        
        # Log list
        self.log_listbox = Gtk.ListBox()
        self.log_listbox.set_selection_mode(Gtk.SelectionMode.NONE)
        self.log_listbox.add_css_class('boxed-list')
        log_group.add(self.log_listbox)
        
        self.append(log_group)
        
        # Log management group
        management_group = self.create_preference_group(
            "Log Management",
            "Export and manage audit logs"
        )
        
        # Export logs
        export_row = self.create_action_row(
            "Export Logs",
            "Save audit logs to file for external analysis"
        )
        export_button = Gtk.Button(label="Export")
        export_button.set_valign(Gtk.Align.CENTER)
        export_button.connect('clicked', self.on_export_logs)
        export_row.add_suffix(export_button)
        management_group.add(export_row)
        
        # Clear logs
        clear_row = self.create_action_row(
            "Clear Old Logs",
            f"Delete logs older than {self.config.log_retention_days} days"
        )
        clear_button = Gtk.Button(label="Clear")
        clear_button.set_valign(Gtk.Align.CENTER)
        clear_button.add_css_class('destructive-action')
        clear_button.connect('clicked', self.on_clear_logs)
        clear_row.add_suffix(clear_button)
        management_group.add(clear_row)
        
        self.append(management_group)
        
        # Permissions group
        permissions_group = self.create_preference_group(
            "Agent Permissions",
            "Control what agents can access"
        )
        
        permissions = [
            {
                'title': 'File System Access',
                'subtitle': 'Read and write files',
                'level': 'restricted'
            },
            {
                'title': 'Network Access',
                'subtitle': 'Make HTTP requests',
                'level': 'allowed'
            },
            {
                'title': 'System Commands',
                'subtitle': 'Execute shell commands',
                'level': 'denied'
            },
            {
                'title': 'User Data Access',
                'subtitle': 'Access personal information',
                'level': 'restricted'
            },
        ]
        
        for perm in permissions:
            row = Adw.ActionRow()
            row.set_title(perm['title'])
            row.set_subtitle(perm['subtitle'])
            
            # Permission level indicator
            level_label = Gtk.Label(label=perm['level'].capitalize())
            level_label.set_valign(Gtk.Align.CENTER)
            
            if perm['level'] == 'allowed':
                level_label.add_css_class('success')
            elif perm['level'] == 'restricted':
                level_label.add_css_class('warning')
            else:
                level_label.add_css_class('error')
            
            row.add_suffix(level_label)
            
            # Configure button
            config_button = Gtk.Button(label="Configure")
            config_button.set_valign(Gtk.Align.CENTER)
            config_button.connect('clicked', lambda _, p=perm: self.on_configure_permission(p))
            row.add_suffix(config_button)
            
            permissions_group.add(row)
        
        self.append(permissions_group)
    
    def create_log_row(self, log_entry):
        """Create a row for a log entry.
        
        Args:
            log_entry: Log entry dict
            
        Returns:
            Adw.ActionRow: Log row
        """
        row = Adw.ActionRow()
        
        timestamp = log_entry.get('timestamp', '')
        level = log_entry.get('level', 'info')
        message = log_entry.get('message', '')
        agent = log_entry.get('agent', 'system')
        
        row.set_title(message)
        row.set_subtitle(f"{timestamp} • {agent}")
        
        # Level icon
        level_icon = Gtk.Image()
        if level == 'critical' or level == 'error':
            level_icon.set_from_icon_name('dialog-error-symbolic')
            level_icon.add_css_class('error')
        elif level == 'warning':
            level_icon.set_from_icon_name('dialog-warning-symbolic')
            level_icon.add_css_class('warning')
        else:
            level_icon.set_from_icon_name('dialog-information-symbolic')
            level_icon.add_css_class('accent')
        
        row.add_prefix(level_icon)
        
        # Details button
        details_button = Gtk.Button(label="Details")
        details_button.set_valign(Gtk.Align.CENTER)
        details_button.connect('clicked', lambda _: self.on_log_details(log_entry))
        row.add_suffix(details_button)
        
        return row
    
    def refresh(self):
        """Refresh log list."""
        # Clear existing logs
        child = self.log_listbox.get_first_child()
        while child:
            next_child = child.get_next_sibling()
            self.log_listbox.remove(child)
            child = next_child
        
        # Load logs
        self.logs = self.load_logs_from_backend()
        
        if self.logs:
            for log in self.logs[:20]:  # Show last 20 entries
                row = self.create_log_row(log)
                self.log_listbox.append(row)
        else:
            status = self.create_status_page(
                "No Log Entries",
                "Audit logging is enabled but no events recorded yet",
                "security-high-symbolic"
            )
            self.log_listbox.append(status)
    
    def load_logs_from_backend(self):
        """Load audit logs from backend.
        
        Returns:
            list: List of log entry dicts
        """
        # TODO: Load from actual backend
        now = datetime.datetime.now()
        return [
            {
                'timestamp': (now - datetime.timedelta(minutes=5)).strftime('%H:%M:%S'),
                'level': 'info',
                'message': 'Agent started task execution',
                'agent': 'browser-agent',
            },
            {
                'timestamp': (now - datetime.timedelta(minutes=15)).strftime('%H:%M:%S'),
                'level': 'warning',
                'message': 'High memory usage detected',
                'agent': 'system',
            },
            {
                'timestamp': (now - datetime.timedelta(hours=1)).strftime('%H:%M:%S'),
                'level': 'info',
                'message': 'Configuration updated',
                'agent': 'system',
            },
        ]
    
    def on_retention_changed(self, spin_button):
        """Handle retention period change."""
        self.config.log_retention_days = int(spin_button.get_value())
    
    def on_filter_changed(self, filter_name, button):
        """Handle log filter change."""
        if button.get_active():
            print(f"Filter by: {filter_name}")
            self.refresh()
    
    def on_view_alerts(self, button):
        """View security alerts."""
        print("View security alerts")
    
    def on_export_logs(self, button):
        """Export audit logs."""
        # TODO: Show file chooser dialog
        print("Export logs")
    
    def on_clear_logs(self, button):
        """Clear old logs."""
        # TODO: Show confirmation dialog
        print("Clear old logs")
        self.refresh()
    
    def on_configure_permission(self, permission):
        """Configure agent permission."""
        print(f"Configure permission: {permission['title']}")
    
    def on_log_details(self, log_entry):
        """Show log entry details."""
        print(f"Show details for: {log_entry['message']}")

# Made with Bob
