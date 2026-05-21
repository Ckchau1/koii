"""Task System page - Manage AI-powered tasks."""

import gi

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Adw, GLib
from .base_page import BasePage


class TasksPage(BasePage):
    """Page for managing AI-powered tasks."""
    
    def __init__(self, config):
        """Initialize the tasks page.
        
        Args:
            config: Configuration object
        """
        super().__init__(config, "Task System")
        self.tasks = []
        self.build_ui()
        self.refresh()
    
    def build_ui(self):
        """Build the user interface."""
        # Header
        header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        header_box.set_margin_bottom(12)
        
        title = Gtk.Label(label="Task Management")
        title.add_css_class('title-1')
        title.set_halign(Gtk.Align.START)
        title.set_hexpand(True)
        header_box.append(title)
        
        # New task button
        new_task_button = Gtk.Button(label="New Task")
        new_task_button.set_icon_name("list-add-symbolic")
        new_task_button.add_css_class('suggested-action')
        new_task_button.connect('clicked', self.on_new_task)
        header_box.append(new_task_button)
        
        self.append(header_box)
        
        # Task settings group
        settings_group = self.create_preference_group(
            "Task System Settings",
            "Configure how AI agents handle tasks"
        )
        
        # Auto-planning switch
        planning_row, planning_switch = self.create_switch_row(
            "Automatic Task Planning",
            "Let AI automatically break down complex tasks",
            self.config.task_auto_planning
        )
        self.config.bind('task-auto-planning', planning_switch, 'active')
        settings_group.add(planning_row)
        
        # Max concurrent tasks
        concurrent_row, concurrent_spin = self.create_spin_row(
            "Maximum Concurrent Tasks",
            "Number of tasks that can run simultaneously",
            value=self.config.task_max_concurrent,
            min_val=1,
            max_val=20,
            step=1
        )
        concurrent_spin.connect('value-changed', self.on_concurrent_changed)
        settings_group.add(concurrent_row)
        
        # History retention
        history_row, history_spin = self.create_spin_row(
            "History Retention (days)",
            "How long to keep completed task records",
            value=self.config.task_history_days,
            min_val=1,
            max_val=365,
            step=1
        )
        history_spin.connect('value-changed', self.on_history_changed)
        settings_group.add(history_row)
        
        self.append(settings_group)
        
        # Active tasks group
        active_group = self.create_preference_group(
            "Active Tasks",
            "Currently running and queued tasks"
        )
        
        # Task list
        self.tasks_listbox = Gtk.ListBox()
        self.tasks_listbox.set_selection_mode(Gtk.SelectionMode.NONE)
        self.tasks_listbox.add_css_class('boxed-list')
        active_group.add(self.tasks_listbox)
        
        self.append(active_group)
        
        # Task templates group
        templates_group = self.create_preference_group(
            "Task Templates",
            "Quick-start templates for common tasks"
        )
        
        templates = [
            {
                'name': 'Web Research',
                'description': 'Research a topic using multiple sources',
                'icon': 'web-browser-symbolic'
            },
            {
                'name': 'Data Analysis',
                'description': 'Analyze and visualize data files',
                'icon': 'utilities-system-monitor-symbolic'
            },
            {
                'name': 'Content Generation',
                'description': 'Generate articles, reports, or documentation',
                'icon': 'document-edit-symbolic'
            },
            {
                'name': 'Code Review',
                'description': 'Review code for issues and improvements',
                'icon': 'text-x-generic-symbolic'
            },
        ]
        
        for template in templates:
            row = Adw.ActionRow()
            row.set_title(template['name'])
            row.set_subtitle(template['description'])
            
            icon = Gtk.Image.new_from_icon_name(template['icon'])
            row.add_prefix(icon)
            
            use_button = Gtk.Button(label="Use")
            use_button.set_valign(Gtk.Align.CENTER)
            use_button.connect('clicked', lambda _, t=template: self.on_use_template(t))
            row.add_suffix(use_button)
            
            templates_group.add(row)
        
        self.append(templates_group)
        
        # Task history group
        history_group = self.create_preference_group(
            "Recent History",
            "View and manage completed tasks"
        )
        
        # View history button
        history_row = self.create_action_row(
            "View Task History",
            f"Browse {self.config.task_history_days} days of task records"
        )
        history_button = Gtk.Button(label="View")
        history_button.set_valign(Gtk.Align.CENTER)
        history_button.connect('clicked', self.on_view_history)
        history_row.add_suffix(history_button)
        history_group.add(history_row)
        
        # Clear history button
        clear_row = self.create_action_row(
            "Clear History",
            "Delete all completed task records"
        )
        clear_button = Gtk.Button(label="Clear")
        clear_button.set_valign(Gtk.Align.CENTER)
        clear_button.add_css_class('destructive-action')
        clear_button.connect('clicked', self.on_clear_history)
        clear_row.add_suffix(clear_button)
        history_group.add(clear_row)
        
        self.append(history_group)
    
    def create_task_row(self, task_data):
        """Create a row for a task.
        
        Args:
            task_data: Task information dict
            
        Returns:
            Adw.ActionRow: Task row
        """
        row = Adw.ActionRow()
        row.set_title(task_data.get('name', 'Unnamed Task'))
        
        status = task_data.get('status', 'unknown')
        progress = task_data.get('progress', 0)
        
        subtitle = f"Status: {status} • Progress: {progress}%"
        row.set_subtitle(subtitle)
        
        # Status icon
        status_icon = Gtk.Image()
        if status == 'running':
            status_icon.set_from_icon_name('media-playback-start-symbolic')
            status_icon.add_css_class('accent')
        elif status == 'completed':
            status_icon.set_from_icon_name('emblem-ok-symbolic')
            status_icon.add_css_class('success')
        elif status == 'failed':
            status_icon.set_from_icon_name('dialog-error-symbolic')
            status_icon.add_css_class('error')
        else:
            status_icon.set_from_icon_name('media-playback-pause-symbolic')
        
        row.add_prefix(status_icon)
        
        # Progress bar
        if status == 'running':
            progress_bar = Gtk.ProgressBar()
            progress_bar.set_fraction(progress / 100.0)
            progress_bar.set_valign(Gtk.Align.CENTER)
            progress_bar.set_hexpand(True)
            row.add_suffix(progress_bar)
        
        # Action buttons
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        
        if status == 'running':
            pause_button = Gtk.Button(label="Pause")
            pause_button.set_valign(Gtk.Align.CENTER)
            pause_button.connect('clicked', lambda _: self.on_pause_task(task_data))
            button_box.append(pause_button)
        
        cancel_button = Gtk.Button(label="Cancel")
        cancel_button.set_valign(Gtk.Align.CENTER)
        cancel_button.add_css_class('destructive-action')
        cancel_button.connect('clicked', lambda _: self.on_cancel_task(task_data))
        button_box.append(cancel_button)
        
        row.add_suffix(button_box)
        
        return row
    
    def refresh(self):
        """Refresh task list."""
        # Clear existing tasks
        child = self.tasks_listbox.get_first_child()
        while child:
            next_child = child.get_next_sibling()
            self.tasks_listbox.remove(child)
            child = next_child
        
        # Load tasks
        self.tasks = self.load_tasks_from_backend()
        
        if self.tasks:
            for task in self.tasks:
                row = self.create_task_row(task)
                self.tasks_listbox.append(row)
        else:
            status = self.create_status_page(
                "No Active Tasks",
                "Create a new task or use a template to get started",
                "view-list-symbolic"
            )
            self.tasks_listbox.append(status)
    
    def load_tasks_from_backend(self):
        """Load tasks from backend.
        
        Returns:
            list: List of task dicts
        """
        # TODO: Load from actual backend
        return [
            {
                'id': 'task-001',
                'name': 'Research AI trends',
                'status': 'running',
                'progress': 45,
            },
            {
                'id': 'task-002',
                'name': 'Generate report',
                'status': 'queued',
                'progress': 0,
            },
        ]
    
    def on_concurrent_changed(self, spin_button):
        """Handle concurrent tasks change."""
        self.config.task_max_concurrent = int(spin_button.get_value())
    
    def on_history_changed(self, spin_button):
        """Handle history retention change."""
        self.config.task_history_days = int(spin_button.get_value())
    
    def on_new_task(self, button):
        """Create a new task."""
        # TODO: Show task creation dialog
        print("Create new task")
    
    def on_use_template(self, template):
        """Use a task template."""
        print(f"Use template: {template['name']}")
    
    def on_view_history(self, button):
        """View task history."""
        print("View task history")
    
    def on_clear_history(self, button):
        """Clear task history."""
        # TODO: Show confirmation dialog
        print("Clear task history")
    
    def on_pause_task(self, task_data):
        """Pause a task."""
        print(f"Pause task: {task_data['name']}")
        self.refresh()
    
    def on_cancel_task(self, task_data):
        """Cancel a task."""
        print(f"Cancel task: {task_data['name']}")
        self.refresh()

# Made with Bob
