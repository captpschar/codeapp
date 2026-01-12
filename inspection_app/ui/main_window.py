"""
Main application window.
"""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QStackedWidget,
    QStatusBar, QMenuBar, QMenu, QMessageBox
)
from PyQt6.QtCore import Qt
from .phase_navigator import PhaseNavigator
from .phase1.triage_widget import TriageWidget
from .phase2.processing_widget import ProcessingWidget
from .phase3.dashboard_widget import DashboardWidget
from .phase4.export_widget import ExportWidget


class MainWindow(QMainWindow):
    """Main application window."""

    def __init__(self, app_state):
        super().__init__()
        self._app_state = app_state
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self) -> None:
        """Initialize UI components."""
        self.setWindowTitle("Inspection Photo Review - Code Matching")
        self.setMinimumSize(1200, 800)

        # Get UI settings from config
        config = self._app_state.config
        self.resize(
            config.ui_settings.default_window_width,
            config.ui_settings.default_window_height
        )

        # Central widget with stack
        central = QWidget()
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Phase navigator (tabs)
        self._navigator = PhaseNavigator()
        layout.addWidget(self._navigator)

        # Stacked widget for phases
        self._stack = QStackedWidget()

        self._phase1 = TriageWidget(self._app_state)
        self._phase2 = ProcessingWidget(self._app_state)
        self._phase3 = DashboardWidget(self._app_state)
        self._phase4 = ExportWidget(self._app_state)

        self._stack.addWidget(self._phase1)
        self._stack.addWidget(self._phase2)
        self._stack.addWidget(self._phase3)
        self._stack.addWidget(self._phase4)

        layout.addWidget(self._stack)
        self.setCentralWidget(central)

        # Status bar
        self._status_bar = QStatusBar()
        self.setStatusBar(self._status_bar)

        # Menu bar
        self._setup_menus()

        # Initial status
        self._update_status_bar()

    def _setup_menus(self) -> None:
        """Create menu bar."""
        menu_bar = self.menuBar()

        # File menu
        file_menu = menu_bar.addMenu("File")
        file_menu.addAction("Save Project", self._on_save_project, "Ctrl+S")
        file_menu.addSeparator()
        file_menu.addAction("Settings...", self._on_settings)
        file_menu.addSeparator()
        file_menu.addAction("Exit", self.close, "Alt+F4")

        # View menu
        view_menu = menu_bar.addMenu("View")
        view_menu.addAction("Phase 1: Triage", lambda: self._goto_phase(0), "Ctrl+1")
        view_menu.addAction("Phase 2: Process", lambda: self._goto_phase(1), "Ctrl+2")
        view_menu.addAction("Phase 3: Verify", lambda: self._goto_phase(2), "Ctrl+3")
        view_menu.addAction("Phase 4: Export", lambda: self._goto_phase(3), "Ctrl+4")

        # Help menu
        help_menu = menu_bar.addMenu("Help")
        help_menu.addAction("About", self._on_about)

    def _connect_signals(self) -> None:
        """Connect phase navigation signals."""
        self._navigator.phase_changed.connect(self._on_phase_changed)

        # App state signals
        self._app_state.signals.queue_updated.connect(self._update_status_bar)
        self._app_state.signals.status_message.connect(self._show_status)

    def _on_phase_changed(self, phase_index: int) -> None:
        """Handle phase navigation."""
        self._stack.setCurrentIndex(phase_index)

    def _goto_phase(self, index: int) -> None:
        """Navigate to specific phase."""
        self._navigator.set_phase(index)

    def _on_save_project(self) -> None:
        """Handle save project action."""
        self._app_state.save()
        self._show_status("Project saved")

    def _on_settings(self) -> None:
        """Open settings dialog."""
        QMessageBox.information(
            self,
            "Settings",
            "Edit settings.json file to configure the application."
        )

    def _on_about(self) -> None:
        """Show about dialog."""
        QMessageBox.about(
            self,
            "About",
            "Inspection Photo Review & Code Matching\n\n"
            "Version 3.0\n\n"
            "A tool for reviewing inspection photos and matching "
            "them to building code references using AI."
        )

    def _update_status_bar(self) -> None:
        """Update status bar with queue info."""
        queue = self._app_state.queue
        total = queue.count()
        pending = queue.count_by_status(
            self._app_state.queue.get_pending_items()[0].status
            if queue.get_pending_items() else None
        ) if queue.get_pending_items() else 0
        approved = len(queue.get_approved_items())

        self._status_bar.showMessage(
            f"Queue: {total} items | Pending: {pending} | Approved: {approved}"
        )

    def _show_status(self, message: str) -> None:
        """Show temporary status message."""
        self._status_bar.showMessage(message, 5000)

    def closeEvent(self, event) -> None:
        """Handle window close."""
        # Save state
        self._app_state.save()
        event.accept()
