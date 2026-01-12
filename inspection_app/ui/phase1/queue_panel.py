"""
Queue status display panel.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QListWidget, QListWidgetItem,
    QPushButton, QHBoxLayout
)
from PyQt6.QtCore import pyqtSignal, Qt
from typing import List
from ...core.inspection_item import InspectionItem, ItemStatus


class QueuePanel(QWidget):
    """Panel showing queue items and status."""

    item_selected = pyqtSignal(str)  # item ID
    item_removed = pyqtSignal(str)  # item ID

    def __init__(self, parent=None):
        super().__init__(parent)
        self._items: List[InspectionItem] = []
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Create panel UI."""
        layout = QVBoxLayout(self)

        # Header
        header = QHBoxLayout()
        self._title_label = QLabel("Queue (0 items)")
        self._title_label.setStyleSheet("font-weight: bold;")
        header.addWidget(self._title_label)
        header.addStretch()
        layout.addLayout(header)

        # Item list
        self._list = QListWidget()
        self._list.itemClicked.connect(self._on_item_clicked)
        layout.addWidget(self._list)

        # Status summary
        self._status_label = QLabel("Pending: 0 | Ready: 0 | Approved: 0")
        self._status_label.setStyleSheet("color: #666; font-size: 11px;")
        layout.addWidget(self._status_label)

        # Remove button
        self._remove_btn = QPushButton("Remove Selected")
        self._remove_btn.clicked.connect(self._on_remove_clicked)
        self._remove_btn.setEnabled(False)
        layout.addWidget(self._remove_btn)

    def update_items(self, items: List[InspectionItem]) -> None:
        """Update displayed items."""
        self._items = items
        self._list.clear()

        for item in items:
            list_item = QListWidgetItem()
            list_item.setData(Qt.ItemDataRole.UserRole, item.id)

            # Build display text
            location = item.user_location or "No location"
            status_icon = self._get_status_icon(item.status)
            list_item.setText(f"{status_icon} {location}")

            self._list.addItem(list_item)

        self._update_header()
        self._update_status_summary()

    def _get_status_icon(self, status: ItemStatus) -> str:
        """Get emoji icon for status."""
        icons = {
            ItemStatus.PENDING: "⏳",
            ItemStatus.PROCESSING: "🔄",
            ItemStatus.REVIEW_READY: "👁",
            ItemStatus.APPROVED: "✅",
            ItemStatus.ERROR: "❌",
        }
        return icons.get(status, "•")

    def _update_header(self) -> None:
        """Update header with count."""
        count = len(self._items)
        self._title_label.setText(f"Queue ({count} item{'s' if count != 1 else ''})")

    def _update_status_summary(self) -> None:
        """Update status counts."""
        pending = sum(1 for i in self._items if i.status == ItemStatus.PENDING)
        ready = sum(1 for i in self._items if i.status == ItemStatus.REVIEW_READY)
        approved = sum(1 for i in self._items if i.final_approval)

        self._status_label.setText(
            f"Pending: {pending} | Ready: {ready} | Approved: {approved}"
        )

    def _on_item_clicked(self, item: QListWidgetItem) -> None:
        """Handle item click."""
        item_id = item.data(Qt.ItemDataRole.UserRole)
        self._remove_btn.setEnabled(True)
        self.item_selected.emit(item_id)

    def _on_remove_clicked(self) -> None:
        """Handle remove button click."""
        current = self._list.currentItem()
        if current:
            item_id = current.data(Qt.ItemDataRole.UserRole)
            self.item_removed.emit(item_id)

    def get_selected_id(self) -> str:
        """Get selected item ID."""
        current = self._list.currentItem()
        if current:
            return current.data(Qt.ItemDataRole.UserRole)
        return ""

    def clear_selection(self) -> None:
        """Clear list selection."""
        self._list.clearSelection()
        self._remove_btn.setEnabled(False)
