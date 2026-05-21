"""Base class for settings pages."""

import gi

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Adw


class BasePage(Gtk.Box):
    """Base class for all settings pages."""
    
    def __init__(self, config, title="Settings Page"):
        """Initialize the page.
        
        Args:
            config: Configuration object
            title: Page title
        """
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.config = config
        self._title = title
        
        # Add margins
        self.set_margin_start(12)
        self.set_margin_end(12)
        self.set_margin_top(12)
        self.set_margin_bottom(12)
    
    def get_title(self):
        """Get the page title.
        
        Returns:
            str: Page title
        """
        return self._title
    
    def refresh(self):
        """Refresh the page content.
        
        Override this method in subclasses to update dynamic content.
        """
        pass
    
    def create_preference_group(self, title, description=None):
        """Create a preference group.
        
        Args:
            title: Group title
            description: Optional group description
            
        Returns:
            Adw.PreferencesGroup: Preference group
        """
        group = Adw.PreferencesGroup()
        group.set_title(title)
        if description:
            group.set_description(description)
        return group
    
    def create_action_row(self, title, subtitle=None):
        """Create an action row.
        
        Args:
            title: Row title
            subtitle: Optional subtitle
            
        Returns:
            Adw.ActionRow: Action row
        """
        row = Adw.ActionRow()
        row.set_title(title)
        if subtitle:
            row.set_subtitle(subtitle)
        return row
    
    def create_switch_row(self, title, subtitle=None, active=False):
        """Create a switch row.
        
        Args:
            title: Row title
            subtitle: Optional subtitle
            active: Initial switch state
            
        Returns:
            tuple: (Adw.ActionRow, Gtk.Switch)
        """
        row = self.create_action_row(title, subtitle)
        switch = Gtk.Switch()
        switch.set_active(active)
        switch.set_valign(Gtk.Align.CENTER)
        row.add_suffix(switch)
        row.set_activatable_widget(switch)
        return row, switch
    
    def create_combo_row(self, title, subtitle=None, options=None):
        """Create a combo row.
        
        Args:
            title: Row title
            subtitle: Optional subtitle
            options: List of (value, label) tuples
            
        Returns:
            tuple: (Adw.ComboRow, Gtk.StringList)
        """
        row = Adw.ComboRow()
        row.set_title(title)
        if subtitle:
            row.set_subtitle(subtitle)
        
        if options:
            string_list = Gtk.StringList()
            for _, label in options:
                string_list.append(label)
            row.set_model(string_list)
        
        return row
    
    def create_spin_row(self, title, subtitle=None, value=0, min_val=0, max_val=100, step=1):
        """Create a spin button row.
        
        Args:
            title: Row title
            subtitle: Optional subtitle
            value: Initial value
            min_val: Minimum value
            max_val: Maximum value
            step: Step increment
            
        Returns:
            tuple: (Adw.ActionRow, Gtk.SpinButton)
        """
        row = self.create_action_row(title, subtitle)
        
        adjustment = Gtk.Adjustment(
            value=value,
            lower=min_val,
            upper=max_val,
            step_increment=step,
            page_increment=step * 10,
            page_size=0
        )
        
        spin = Gtk.SpinButton()
        spin.set_adjustment(adjustment)
        spin.set_valign(Gtk.Align.CENTER)
        row.add_suffix(spin)
        
        return row, spin
    
    def create_entry_row(self, title, subtitle=None, text=""):
        """Create an entry row.
        
        Args:
            title: Row title
            subtitle: Optional subtitle
            text: Initial text
            
        Returns:
            Adw.EntryRow: Entry row
        """
        row = Adw.EntryRow()
        row.set_title(title)
        if subtitle:
            row.set_subtitle(subtitle)
        row.set_text(text)
        return row
    
    def create_status_page(self, title, description, icon_name="dialog-information-symbolic"):
        """Create a status page for empty states.
        
        Args:
            title: Status title
            description: Status description
            icon_name: Icon name
            
        Returns:
            Adw.StatusPage: Status page
        """
        status = Adw.StatusPage()
        status.set_title(title)
        status.set_description(description)
        status.set_icon_name(icon_name)
        return status

# Made with Bob
