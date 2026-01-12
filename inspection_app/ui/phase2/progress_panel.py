"""
Progress bar and status display for batch processing.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QProgressBar, QLabel, QHBoxLayout
)
from PyQt6.QtCore import Qt


class ProgressPanel(QWidget):
    """Progress display for AI processing."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Create progress UI."""
        layout = QVBoxLayout(self)

        # Status label
        self._status_label = QLabel("Ready to process")
        self._status_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(self._status_label)

        # Progress bar
        self._progress_bar = QProgressBar()
        self._progress_bar.setMinimum(0)
        self._progress_bar.setMaximum(100)
        self._progress_bar.setValue(0)
        layout.addWidget(self._progress_bar)

        # Count labels
        count_layout = QHBoxLayout()

        self._processed_label = QLabel("Processed: 0")
        count_layout.addWidget(self._processed_label)

        count_layout.addStretch()

        self._total_label = QLabel("Total: 0")
        count_layout.addWidget(self._total_label)

        layout.addLayout(count_layout)

        # Rate limit warning
        self._rate_limit_label = QLabel("")
        self._rate_limit_label.setStyleSheet("color: #FF9800;")
        self._rate_limit_label.setVisible(False)
        layout.addWidget(self._rate_limit_label)

    def set_status(self, status: str) -> None:
        """Set status message."""
        self._status_label.setText(status)

    def set_progress(self, current: int, total: int) -> None:
        """Update progress display."""
        self._progress_bar.setMaximum(total)
        self._progress_bar.setValue(current)
        self._processed_label.setText(f"Processed: {current}")
        self._total_label.setText(f"Total: {total}")

        if total > 0:
            percent = int((current / total) * 100)
            self.set_status(f"Processing... {percent}%")

    def show_rate_limit(self, wait_seconds: int) -> None:
        """Show rate limit warning."""
        self._rate_limit_label.setText(
            f"⚠️ Rate limited. Waiting {wait_seconds} seconds..."
        )
        self._rate_limit_label.setVisible(True)

    def hide_rate_limit(self) -> None:
        """Hide rate limit warning."""
        self._rate_limit_label.setVisible(False)

    def set_completed(self) -> None:
        """Set completed state."""
        self.set_status("✅ Processing complete!")
        self._rate_limit_label.setVisible(False)

    def set_error(self, message: str) -> None:
        """Set error state."""
        self.set_status(f"❌ Error: {message}")

    def reset(self) -> None:
        """Reset to initial state."""
        self._progress_bar.setValue(0)
        self._processed_label.setText("Processed: 0")
        self._total_label.setText("Total: 0")
        self._rate_limit_label.setVisible(False)
        self.set_status("Ready to process")
