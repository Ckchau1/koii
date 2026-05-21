"""Main window for Koii Settings."""

import gi

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Adw, GLib

from .config import Config
from .pages.agents_page import AgentsPage
from .pages.browser_page import BrowserPage
from .pages.tasks_page import TasksPage
from .pages.system_page import SystemPage
from .pages.security_page import SecurityPage


class KoiiSettingsWindow(Adw.ApplicationWindow):
    """Main application window with navigation sidebar."""
    
    def __init__(self, **kwargs):
        """Initialize the window."""
        super().__init__(**kwargs)
        
        self.config = Config()
        self.config.sync_from_shared_settings()
        
        # Setup window properties
        self.set_title("Koii Settings")
        self.set_default_size(
            self.config.window_width,
            self.config.window_height
        )
        if self.config.window_maximized:
            self.maximize()
        
        # Build UI
        self.build_ui()
        
        # Connect signals
        self.connect('close-request', self.on_close_request)
    
    def build_ui(self):
        """Build the user interface."""
        # Create main box
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        
        # Create header bar
        header = Adw.HeaderBar()
        main_box.append(header)
        
        # Create navigation split view (sidebar + content)
        self.split_view = Adw.NavigationSplitView()
        
        # Create sidebar
        sidebar = self.create_sidebar()
        self.split_view.set_sidebar(sidebar)
        
        # Create content area with stack
        self.stack = Gtk.Stack()
        self.stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
        self.stack.set_transition_duration(200)
        
        # Add pages to stack
        self.pages = {
            'agents': AgentsPage(self.config),
            'browser': BrowserPage(self.config),
            'tasks': TasksPage(self.config),
            'system': SystemPage(self.config),
            'security': SecurityPage(self.config),
        }
        
        for page_id, page in self.pages.items():
            self.stack.add_titled(page, page_id, page.get_title())
        
        # Wrap stack in scrolled window
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_child(self.stack)
        
        # Create content page
        content_page = Adw.NavigationPage()
        content_page.set_child(scrolled)
        content_page.set_title("Koii Settings")
        
        self.split_view.set_content(content_page)
        
        main_box.append(self.split_view)
        self.set_content(main_box)
    
    def create_sidebar(self):
        """Create the navigation sidebar.
        
        Returns:
            Adw.NavigationPage: Sidebar navigation page
        """
        # Create sidebar list box
        listbox = Gtk.ListBox()
        listbox.set_selection_mode(Gtk.SelectionMode.SINGLE)
        listbox.add_css_class('navigation-sidebar')
        listbox.connect('row-activated', self.on_sidebar_row_activated)
        
        # Define navigation items
        nav_items = [
            {
                'id': 'agents',
                'title': 'Agent Overview',
                'subtitle': 'Monitor and manage AI agents',
                'icon': 'system-run-symbolic'
            },
            {
                'id': 'browser',
                'title': 'AI Browser',
                'subtitle': 'Semantic browsing settings',
                'icon': 'web-browser-symbolic'
            },
            {
                'id': 'tasks',
                'title': 'Task System',
                'subtitle': 'Manage AI-powered tasks',
                'icon': 'view-list-symbolic'
            },
            {
                'id': 'system',
                'title': 'System Settings',
                'subtitle': 'Core parameters and resources',
                'icon': 'preferences-system-symbolic'
            },
            {
                'id': 'security',
                'title': 'Security & Logs',
                'subtitle': 'Audit trails and security',
                'icon': 'security-high-symbolic'
            },
        ]
        
        # Create rows
        self.nav_rows = {}
        for item in nav_items:
            row = self.create_nav_row(
                item['title'],
                item['subtitle'],
                item['icon']
            )
            row.page_id = item['id']
            self.nav_rows[item['id']] = row
            listbox.append(row)
        
        # Select first row by default
        listbox.select_row(listbox.get_row_at_index(0))
        
        # Wrap in scrolled window
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_child(listbox)
        
        # Create sidebar page
        sidebar_page = Adw.NavigationPage()
        sidebar_page.set_child(scrolled)
        sidebar_page.set_title("Navigation")
        
        return sidebar_page
    
    def create_nav_row(self, title, subtitle, icon_name):
        """Create a navigation row.
        
        Args:
            title: Row title
            subtitle: Row subtitle
            icon_name: Icon name
            
        Returns:
            Gtk.ListBoxRow: Navigation row
        """
        row = Gtk.ListBoxRow()
        
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        box.set_margin_start(12)
        box.set_margin_end(12)
        box.set_margin_top(8)
        box.set_margin_bottom(8)
        
        # Icon
        icon = Gtk.Image.new_from_icon_name(icon_name)
        icon.set_icon_size(Gtk.IconSize.LARGE)
        box.append(icon)
        
        # Labels
        label_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        
        title_label = Gtk.Label(label=title)
        title_label.set_halign(Gtk.Align.START)
        title_label.add_css_class('heading')
        label_box.append(title_label)
        
        subtitle_label = Gtk.Label(label=subtitle)
        subtitle_label.set_halign(Gtk.Align.START)
        subtitle_label.add_css_class('dim-label')
        subtitle_label.add_css_class('caption')
        label_box.append(subtitle_label)
        
        box.append(label_box)
        row.set_child(box)
        
        return row
    
    def on_sidebar_row_activated(self, listbox, row):
        """Handle sidebar row activation.
        
        Args:
            listbox: The list box
            row: Activated row
        """
        if hasattr(row, 'page_id'):
            self.stack.set_visible_child_name(row.page_id)
            # Refresh the page when it becomes visible
            if row.page_id in self.pages:
                self.pages[row.page_id].refresh()
    
    def on_close_request(self, window):
        """Handle window close request.
        
        Args:
            window: The window
            
        Returns:
            bool: False to allow closing
        """
        # Save window state
        if self.is_maximized():
            self.config.window_maximized = True
        else:
            self.config.window_maximized = False
            size = self.get_default_size()
            self.config.window_width = size.width
            self.config.window_height = size.height
        
        return False

# Made with Bob
