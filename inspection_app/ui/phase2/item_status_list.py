"""
Per-item status display for batch processing.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QScrollArea, QLabel, QHBoxLayout
)
from PyQt6.QtCore import Qt
from typing import List, Dict
from ...core.inspection_item import InspectionItem, ItemStatus


class ItemStatusList(QWidget):
    """List showing status of each item during processing."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._item_widgets: Dict[str, QWidget] = {}
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Create list UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )

        # Container for items
        self._container = QWidget()
        self._container_layout = QVBoxLayout(self._container)
        self._container_layout.setSpacing(4)
        self._container_layout.addStretch()

        scroll.setWidget(self._container)
        layout.addWidget(scroll)

    def set_items(self, items: List[InspectionItem]) -> None:
        """Set items to display."""
        # Clear existing
        self._clear_items()

        # Add new items
        for item in items:
            widget = self._create_item_widget(item)
            self._item_widgets[item.id] = widget
            self._container_layout.insertWidget(
                self._container_layout.count() - 1,
                widget
            )

    def _create_item_widget(self, item: InspectionItem) -> QWidget:
        """Create widget for a single item."""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(8, 4, 8, 4)

        # Status icon
        icon_label = QLabel(self._get_status_icon(item.status))
        icon_label.setObjectName("icon")
        layout.addWidget(icon_label)

        # Location
        location_label = QLabel(item.user_location or "Unknown")
        location_label.setObjectName("location")
        layout.addWidget(location_label)

        layout.addStretch()

        # Status text
        status_label = QLabel(item.status.value)
        status_label.setObjectName("status")
        status_label.setStyleSheet(self._get_status_style(item.status))
        layout.addWidget(status_label)

        widget.setStyleSheet(
            "background-color: #f5f5f5; border-radius: 4px;"
        )
        return widget

    def update_item_status(self, item_id: str, status: ItemStatus) -> None:
        """Update status for a specific item."""
        if item_id in self._item_widgets:
            widget = self._item_widgets[item_id]

            # Update icon
            icon_label = widget.findChild(QLabel, "icon")
            if icon_label:
                icon_label.setText(self._get_status_icon(status))

            # Update status text
            status_label = widget.findChild(QLabel, "status")
            if status_label:
                status_label.setText(status.value)
                status_label.setStyleSheet(self._get_status_style(status))

    def _get_status_icon(self, status: ItemStatus) -> str:
        """Get icon for status."""
        icons = {
            ItemStatus.PENDING: "⏳",
            ItemStatus.PROCESSING: "🔄",
            ItemStatus.REVIEW_READY: "✅",
            ItemStatus.APPROVED: "✅",
            ItemStatus.ERROR: "❌",
        }
        return icons.get(status, "•")

    def _get_status_style(self, status: ItemStatus) -> str:
        """Get style for status label."""
        colors = {
            ItemStatus.PENDING: "#9E9E9E",
            ItemStatus.PROCESSING: "#2196F3",
            ItemStatus.REVIEW_READY: "#4CAF50",
            ItemStatus.APPROVED: "#4CAF50",
            ItemStatus.ERROR: "#F44336",
        }
        color = colors.get(status, "#666")
        return f"color: {color}; font-weight: bold;"

    def _clear_items(self) -> None:
        """Clear all item widgets."""
        for widget in self._item_widgets.values():
            widget.deleteLater()
        self._item_widgets.clear()

    def clear(self) -> None:
        """Clear the list."""
        self._clear_items()
