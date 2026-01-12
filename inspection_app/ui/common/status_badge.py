"""
Status indicator badge widget.
"""

from PyQt6.QtWidgets import QLabel
from PyQt6.QtCore import Qt
from ...core.inspection_item import ItemStatus


class StatusBadge(QLabel):
    """Visual status indicator."""

    STYLES = {
        ItemStatus.PENDING: "background-color: #9E9E9E; color: white;",
        ItemStatus.PROCESSING: "background-color: #2196F3; color: white;",
        ItemStatus.REVIEW_READY: "background-color: #FF9800; color: white;",
        ItemStatus.APPROVED: "background-color: #4CAF50; color: white;",
        ItemStatus.ERROR: "background-color: #F44336; color: white;",
    }

    LABELS = {
        ItemStatus.PENDING: "Pending",
        ItemStatus.PROCESSING: "Processing",
        ItemStatus.REVIEW_READY: "Review",
        ItemStatus.APPROVED: "Approved",
        ItemStatus.ERROR: "Error",
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self._status: ItemStatus = ItemStatus.PENDING
        self._setup_ui()
        self.set_status(ItemStatus.PENDING)

    def _setup_ui(self) -> None:
        """Setup badge appearance."""
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMinimumWidth(80)
        self.setMaximumHeight(24)
        base_style = (
            "border-radius: 4px; padding: 2px 8px; "
            "font-weight: bold; font-size: 11px;"
        )
        self.setStyleSheet(base_style)

    def set_status(self, status: ItemStatus) -> None:
        """Set the displayed status."""
        self._status = status
        self.setText(self.LABELS.get(status, "Unknown"))

        base_style = (
            "border-radius: 4px; padding: 2px 8px; "
            "font-weight: bold; font-size: 11px; "
        )
        status_style = self.STYLES.get(status, "")
        self.setStyleSheet(base_style + status_style)

    def get_status(self) -> ItemStatus:
        """Get current status."""
        return self._status
