"""
Phase 4: Export widget.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QFormLayout
)
from PyQt6.QtCore import Qt
from pathlib import Path
from datetime import datetime
from .preflight_checker import PreflightChecker
from .export_progress import ExportProgress
from ...workers.export_worker import ExportWorker


class ExportWidget(QWidget):
    """Phase 4 export interface."""

    def __init__(self, app_state):
        super().__init__()
        self._app_state = app_state
        self._worker = None
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self) -> None:
        """Create export UI."""
        layout = QVBoxLayout(self)

        # Header
        header = QLabel("Export to Google Docs")
        header.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(header)

        info = QLabel(
            "Export all approved items to a Google Docs report."
        )
        info.setStyleSheet("color: #666;")
        layout.addWidget(info)

        # Document settings
        settings_form = QFormLayout()

        self._title_input = QLineEdit()
        self._title_input.setText(
            f"Inspection Report - {datetime.now().strftime('%Y-%m-%d')}"
        )
        settings_form.addRow("Document Title:", self._title_input)

        layout.addLayout(settings_form)

        # Preflight checker
        check_label = QLabel("Pre-Export Check")
        check_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        layout.addWidget(check_label)

        self._preflight_checker = PreflightChecker()
        layout.addWidget(self._preflight_checker)

        # Progress display
        self._export_progress = ExportProgress()
        layout.addWidget(self._export_progress)

        layout.addStretch()

        # Control buttons
        button_layout = QHBoxLayout()

        self._check_btn = QPushButton("🔍 Check Items")
        self._check_btn.clicked.connect(self._on_check)
        button_layout.addWidget(self._check_btn)

        self._export_btn = QPushButton("📤 Export to Google Docs")
        self._export_btn.setMinimumHeight(40)
        self._export_btn.clicked.connect(self._on_export)
        button_layout.addWidget(self._export_btn)

        layout.addLayout(button_layout)

    def _connect_signals(self) -> None:
        """Connect app state signals."""
        self._app_state.signals.queue_updated.connect(self._on_queue_updated)

    def _on_queue_updated(self) -> None:
        """Handle queue updates."""
        # Could refresh preflight status
        pass

    def _on_check(self) -> None:
        """Run preflight check."""
        items = self._app_state.queue.get_approved_items()

        if not items:
            self._preflight_checker._status_label.setText("No approved items")
            self._preflight_checker._summary_label.setText(
                "Approve items in Phase 3 before exporting."
            )
            return

        ready = self._preflight_checker.check_items(items)
        self._export_btn.setEnabled(ready)

    def _on_export(self) -> None:
        """Start export."""
        items = self._app_state.queue.get_approved_items()

        if not items:
            self._export_progress.show_error("No approved items to export")
            return

        # Get credentials path
        config = self._app_state.config
        creds_path = Path(config.google_docs_credentials_path)

        if not creds_path.exists():
            self._export_progress.show_error(
                f"Credentials file not found: {creds_path}\n"
                "Please set up Google API credentials."
            )
            return

        # Create worker
        self._worker = ExportWorker(
            queue=self._app_state.queue,
            credentials_path=creds_path
        )
        self._worker.set_document_title(self._title_input.text())

        # Connect signals
        self._worker.signals.export_started.connect(self._on_export_started)
        self._worker.signals.export_item_completed.connect(
            self._on_item_completed
        )
        self._worker.signals.export_progress.connect(self._on_progress)
        self._worker.signals.export_completed.connect(self._on_export_completed)
        self._worker.signals.export_network_error.connect(
            self._on_network_error
        )

        # Update UI
        self._export_btn.setEnabled(False)
        self._check_btn.setEnabled(False)
        self._export_progress.show_exporting()

        # Start worker
        self._worker.start()

    def _on_export_started(self) -> None:
        """Handle export started."""
        self._export_progress.set_status("Connecting to Google...")

    def _on_item_completed(self, item_id: str) -> None:
        """Handle item export completed."""
        pass

    def _on_progress(self, current: int, total: int) -> None:
        """Handle progress update."""
        self._export_progress.set_progress(current, total)

    def _on_export_completed(self, result) -> None:
        """Handle export completed."""
        self._export_progress.show_result(result)
        self._reset_buttons()

    def _on_network_error(self) -> None:
        """Handle network error."""
        self._export_progress.show_error(
            "Network error. Check your internet connection."
        )
        self._reset_buttons()

    def _reset_buttons(self) -> None:
        """Reset button states."""
        self._export_btn.setEnabled(True)
        self._check_btn.setEnabled(True)
        self._worker = None

    def showEvent(self, event) -> None:
        """Handle widget shown."""
        super().showEvent(event)
        self._on_check()
