"""Main application entry point for Koii Settings."""

import sys
import gettext
import gi

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Adw, Gio

from .window import KoiiSettingsWindow

# Setup gettext
_ = gettext.gettext


class KoiiSettingsApplication(Adw.Application):
    """Main application class for Koii Settings."""
    
    def __init__(self, version):
        """Initialize the application.
        
        Args:
            version: Application version string
        """
        super().__init__(
            application_id='org.koii.Settings',
            flags=Gio.ApplicationFlags.DEFAULT_FLAGS
        )
        self.version = version
        self.window = None
    
    def do_activate(self):
        """Activate the application."""
        if not self.window:
            self.window = KoiiSettingsWindow(application=self)
        self.window.present()
    
    def do_startup(self):
        """Startup the application."""
        Adw.Application.do_startup(self)
        self.setup_actions()
    
    def setup_actions(self):
        """Setup application actions."""
        # About action
        about_action = Gio.SimpleAction.new("about", None)
        about_action.connect("activate", self.on_about)
        self.add_action(about_action)
        
        # Quit action
        quit_action = Gio.SimpleAction.new("quit", None)
        quit_action.connect("activate", lambda *_: self.quit())
        self.add_action(quit_action)
        self.set_accels_for_action("app.quit", ["<Control>q"])
        
        # Preferences action (opens main window)
        prefs_action = Gio.SimpleAction.new("preferences", None)
        prefs_action.connect("activate", lambda *_: self.do_activate())
        self.add_action(prefs_action)
    
    def on_about(self, action, param):
        """Show about dialog."""
        about = Adw.AboutWindow(
            transient_for=self.window,
            application_name="Koii Settings",
            application_icon="org.koii.Settings",
            developer_name="Koiiai",
            version=self.version,
            website="https://koiiai.com",
            issue_url="https://github.com/koii-network/koii-os/issues",
            copyright="© 2026 Koii Network",
            license_type=Gtk.License.GPL_3_0,
            developers=[
                "Koii Network Team",
            ],
            # Translators: Replace this with your name for credits
            translator_credits=_("translator-credits"),
        )
        about.present()


def main(version):
    """Run the application.
    
    Args:
        version: Application version string
        
    Returns:
        Exit code
    """
    app = KoiiSettingsApplication(version)
    return app.run(sys.argv)

# Made with Bob
