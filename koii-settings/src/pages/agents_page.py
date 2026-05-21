"""Agent Overview page - Monitor and manage AI agents."""

import gi

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Adw, GLib
from .base_page import BasePage
from ..backend import KoiiBackend


class AgentsPage(BasePage):
    """Page for monitoring and managing AI agents."""
    
    def __init__(self, config):
        """Initialize the agents page.
        
        Args:
            config: Configuration object
        """
        super().__init__(config, "Agent Overview")
        self.backend = KoiiBackend()
        
        # Agent data (will be populated from backend)
        self.agents = []
        
        self.build_ui()
        self.refresh()
    
    def build_ui(self):
        """Build the user interface."""
        # Header with refresh button
        header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        header_box.set_margin_bottom(12)
        
        title = Gtk.Label(label="AI Agents")
        title.add_css_class('title-1')
        title.set_halign(Gtk.Align.START)
        title.set_hexpand(True)
        header_box.append(title)
        
        refresh_button = Gtk.Button(label="Refresh")
        refresh_button.set_icon_name("view-refresh-symbolic")
        refresh_button.connect('clicked', lambda _: self.refresh())
        header_box.append(refresh_button)
        
        self.append(header_box)
        
        # Agent statistics cards
        stats_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        stats_box.set_margin_bottom(24)
        stats_box.set_homogeneous(True)
        
        self.active_agents_card = self.create_stat_card("Active Agents", "0", "system-run-symbolic")
        self.total_tasks_card = self.create_stat_card("Total Tasks", "0", "view-list-symbolic")
        self.cpu_usage_card = self.create_stat_card("CPU Usage", "0%", "utilities-system-monitor-symbolic")
        
        stats_box.append(self.active_agents_card)
        stats_box.append(self.total_tasks_card)
        stats_box.append(self.cpu_usage_card)
        
        self.append(stats_box)
        
        # Agent list
        agents_group = self.create_preference_group(
            "Running Agents",
            "Monitor status and performance of active AI agents"
        )
        
        # Create list box for agents
        self.agents_listbox = Gtk.ListBox()
        self.agents_listbox.set_selection_mode(Gtk.SelectionMode.NONE)
        self.agents_listbox.add_css_class('boxed-list')
        agents_group.add(self.agents_listbox)
        
        self.append(agents_group)
        
        # Agent controls
        controls_group = self.create_preference_group(
            "Agent Controls",
            "Manage agent lifecycle and behavior"
        )
        
        # Start new agent button
        start_row = self.create_action_row(
            "Start New Agent",
            "Launch a new AI agent instance"
        )
        start_button = Gtk.Button(label="Start")
        start_button.set_valign(Gtk.Align.CENTER)
        start_button.add_css_class('suggested-action')
        start_button.connect('clicked', self.on_start_agent)
        start_row.add_suffix(start_button)
        controls_group.add(start_row)
        
        # Stop all agents button
        stop_row = self.create_action_row(
            "Stop All Agents",
            "Gracefully shutdown all running agents"
        )
        stop_button = Gtk.Button(label="Stop All")
        stop_button.set_valign(Gtk.Align.CENTER)
        stop_button.add_css_class('destructive-action')
        stop_button.connect('clicked', self.on_stop_all_agents)
        stop_row.add_suffix(stop_button)
        controls_group.add(stop_row)
        
        self.append(controls_group)
    
    def create_stat_card(self, title, value, icon_name):
        """Create a statistics card.
        
        Args:
            title: Card title
            value: Card value
            icon_name: Icon name
            
        Returns:
            Gtk.Box: Statistics card
        """
        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        card.add_css_class('card')
        card.set_margin_start(0)
        card.set_margin_end(0)
        card.set_margin_top(0)
        card.set_margin_bottom(0)
        
        # Inner box with padding
        inner = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        inner.set_margin_start(16)
        inner.set_margin_end(16)
        inner.set_margin_top(16)
        inner.set_margin_bottom(16)
        
        # Icon and title row
        header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        
        icon = Gtk.Image.new_from_icon_name(icon_name)
        icon.set_icon_size(Gtk.IconSize.NORMAL)
        icon.add_css_class('dim-label')
        header.append(icon)
        
        title_label = Gtk.Label(label=title)
        title_label.set_halign(Gtk.Align.START)
        title_label.add_css_class('caption')
        title_label.add_css_class('dim-label')
        header.append(title_label)
        
        inner.append(header)
        
        # Value label
        value_label = Gtk.Label(label=value)
        value_label.set_halign(Gtk.Align.START)
        value_label.add_css_class('title-1')
        inner.append(value_label)
        
        # Store value label for updates
        card.value_label = value_label
        
        card.append(inner)
        return card
    
    def create_agent_row(self, agent_data):
        """Create a row for an agent.
        
        Args:
            agent_data: Agent information dict
            
        Returns:
            Adw.ActionRow: Agent row
        """
        row = Adw.ActionRow()
        row.set_title(agent_data.get('name', 'Unknown Agent'))
        
        # Status and info
        status = agent_data.get('status', 'unknown')
        task_count = agent_data.get('task_count', 0)
        cpu_usage = agent_data.get('cpu_usage', 0)
        
        subtitle = f"Status: {status} • Tasks: {task_count} • CPU: {cpu_usage}%"
        row.set_subtitle(subtitle)
        
        # Status indicator
        status_icon = Gtk.Image()
        if status == 'running':
            status_icon.set_from_icon_name('emblem-ok-symbolic')
            status_icon.add_css_class('success')
        elif status == 'idle':
            status_icon.set_from_icon_name('media-playback-pause-symbolic')
            status_icon.add_css_class('warning')
        else:
            status_icon.set_from_icon_name('dialog-error-symbolic')
            status_icon.add_css_class('error')
        
        row.add_prefix(status_icon)
        
        # Action buttons
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        
        # Details button
        details_button = Gtk.Button(label="Details")
        details_button.set_valign(Gtk.Align.CENTER)
        details_button.connect('clicked', lambda _: self.on_agent_details(agent_data))
        button_box.append(details_button)
        
        # Stop button
        stop_button = Gtk.Button(label="Stop")
        stop_button.set_valign(Gtk.Align.CENTER)
        stop_button.add_css_class('destructive-action')
        stop_button.connect('clicked', lambda _: self.on_stop_agent(agent_data))
        button_box.append(stop_button)
        
        row.add_suffix(button_box)
        
        return row
    
    def refresh(self):
        """Refresh agent data from backend."""
        # Clear existing agents
        child = self.agents_listbox.get_first_child()
        while child:
            next_child = child.get_next_sibling()
            self.agents_listbox.remove(child)
            child = next_child
        
        # Load agent data from backend
        self.agents = self.load_agents_from_backend()
        
        # Update statistics
        active_count = sum(1 for a in self.agents if a.get('status') == 'running')
        total_tasks = sum(a.get('task_count', 0) for a in self.agents)
        avg_cpu = sum(a.get('cpu_usage', 0) for a in self.agents) / len(self.agents) if self.agents else 0
        
        self.active_agents_card.value_label.set_text(str(active_count))
        self.total_tasks_card.value_label.set_text(str(total_tasks))
        self.cpu_usage_card.value_label.set_text(f"{avg_cpu:.1f}%")
        
        # Populate agent list
        if self.agents:
            for agent in self.agents:
                row = self.create_agent_row(agent)
                self.agents_listbox.append(row)
        else:
            # Show empty state
            status = self.create_status_page(
                "No Active Agents",
                "Start a new agent to begin processing tasks",
                "system-run-symbolic"
            )
            self.agents_listbox.append(status)
    
    def load_agents_from_backend(self):
        """Load agent data from Koii OS backend.
        
        Returns:
            list: List of agent data dicts
        """
        try:
            return self.backend.get_agents()
        except Exception as e:
            print(f"Error loading agents: {e}")
            return []
    
    def on_start_agent(self, button):
        """Handle start agent button click."""
        # TODO: Show dialog to configure new agent
        print("Start new agent")
    
    def on_stop_all_agents(self, button):
        """Handle stop all agents button click."""
        # TODO: Show confirmation dialog
        print("Stop all agents")
        self.refresh()
    
    def on_agent_details(self, agent_data):
        """Show agent details dialog."""
        # TODO: Create detailed agent info dialog
        print(f"Show details for agent: {agent_data.get('name')}")
    
    def on_stop_agent(self, agent_data):
        """Stop a specific agent."""
        # TODO: Stop the agent via backend
        print(f"Stop agent: {agent_data.get('name')}")
        self.refresh()

# Made with Bob
