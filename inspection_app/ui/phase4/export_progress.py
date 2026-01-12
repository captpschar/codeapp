"""
Export progress display.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QProgressBar, QTextEdit
)
from PyQt6.QtCore import Qt
from typing import Optional
from ...services.google_docs_service.error_recovery import ExportResult


class ExportProgress(QWidget):
    """Display export progress and results."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Create progress UI."""
        layout = QVBoxLayout(self)

        # Status
        self._status_label = QLabel("Ready to export")
        self._status_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(self._status_label)

        # Progress bar
        self._progress_bar = QProgressBar()
        self._progress_bar.setMinimum(0)
        self._progress_bar.setMaximum(100)
        layout.addWidget(self._progress_bar)

        # Current item
        self._current_label = QLabel("")
        self._current_label.setStyleSheet("color: #666;")
        layout.addWidget(self._current_label)

        # Result area
        self._result_text = QTextEdit()
        self._result_text.setReadOnly(True)
        self._result_text.setMaximumHeight(100)
        self._result_text.hide()
        layout.addWidget(self._result_text)

        # Document link
        self._link_label = QLabel("")
        self._link_label.setOpenExternalLinks(True)
        self._link_label.setStyleSheet("color: #2196F3;")
        self._link_label.hide()
        layout.addWidget(self._link_label)

    def set_status(self, status: str) -> None:
        """Set status message."""
        self._status_label.setText(status)

    def set_progress(self, current: int, total: int) -> None:
        """Update progress."""
        self._progress_bar.setMaximum(total)
        self._progress_bar.setValue(current)
        self._current_label.setText(f"Processing item {current} of {total}...")

    def show_exporting(self) -> None:
        """Show exporting state."""
        self.set_status("📤 Exporting to Google Docs...")
        self._progress_bar.setMaximum(0)  # Indeterminate
        self._result_text.hide()
        self._link_label.hide()

    def show_result(self, result: ExportResult) -> None:
        """Show export result."""
        self._progress_bar.setMaximum(100)
        self._progress_bar.setValue(100)

        if result.success:
            self._status_label.setText("✅ Export Complete!")
            self._status_label.setStyleSheet(
                "font-weight: bold; font-size: 14px; color: #4CAF50;"
            )
        else:
            self._status_label.setText("⚠️ Export Completed with Errors")
            self._status_label.setStyleSheet(
                "font-weight: bold; font-size: 14px; color: #FF9800;"
            )

        # Show summary
        summary = (
            f"Total items: {result.total_items}\n"
            f"Successful: {result.successful_items}\n"
            f"Failed: {result.failed_items}"
        )
        self._result_text.setPlainText(summary)
        self._result_text.show()

        # Show document link
        if result.document_url:
            self._link_label.setText(
                f'<a href="{result.document_url}">Open Document in Google Docs</a>'
            )
            self._link_label.show()

        self._current_label.setText("")

    def show_error(self, message: str) -> None:
        """Show error state."""
        self._status_label.setText("❌ Export Failed")
        self._status_label.setStyleSheet(
            "font-weight: bold; font-size: 14px; color: #F44336;"
        )
        self._progress_bar.setValue(0)
        self._result_text.setPlainText(message)
        self._result_text.show()
        self._link_label.hide()

    def reset(self) -> None:
        """Reset to initial state."""
        self._status_label.setText("Ready to export")
        self._status_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        self._progress_bar.setValue(0)
        self._progress_bar.setMaximum(100)
        self._current_label.setText("")
        self._result_text.hide()
        self._link_label.hide()
