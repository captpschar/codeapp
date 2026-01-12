"""
Data panel for AI results and controls.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QLabel,
    QTextEdit, QPushButton, QCheckBox, QHBoxLayout
)
from PyQt6.QtCore import pyqtSignal
from .search_bar import SearchBar
from .snapshot_thumbnail import SnapshotThumbnail
from ..common.status_badge import StatusBadge
from ...core.inspection_item import InspectionItem, SearchStatus


class DataPanel(QWidget):
    """Panel showing AI results and verification controls."""

    search_requested = pyqtSignal(str)
    approval_toggled = pyqtSignal(bool)
    resend_requested = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_item: InspectionItem = None
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Create panel UI."""
        layout = QVBoxLayout(self)

        # Header with status
        header = QHBoxLayout()
        header.addWidget(QLabel("Item Details"))
        self._status_badge = StatusBadge()
        header.addWidget(self._status_badge)
        header.addStretch()
        layout.addLayout(header)

        # Form for item data
        form = QFormLayout()

        self._location_label = QLabel("-")
        form.addRow("Location:", self._location_label)

        self._description_text = QTextEdit()
        self._description_text.setReadOnly(True)
        self._description_text.setMaximumHeight(60)
        form.addRow("Description:", self._description_text)

        layout.addLayout(form)

        # AI Results section
        ai_header = QLabel("AI Analysis")
        ai_header.setStyleSheet("font-weight: bold; margin-top: 10px;")
        layout.addWidget(ai_header)

        ai_form = QFormLayout()

        self._match_type_label = QLabel("-")
        ai_form.addRow("Match Type:", self._match_type_label)

        self._reference_label = QLabel("-")
        self._reference_label.setStyleSheet("font-weight: bold;")
        ai_form.addRow("Reference:", self._reference_label)

        self._confidence_label = QLabel("-")
        ai_form.addRow("Confidence:", self._confidence_label)

        self._reasoning_text = QTextEdit()
        self._reasoning_text.setReadOnly(True)
        self._reasoning_text.setMaximumHeight(80)
        ai_form.addRow("Reasoning:", self._reasoning_text)

        layout.addLayout(ai_form)

        # Search bar
        search_label = QLabel("Verify Reference")
        search_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        layout.addWidget(search_label)

        self._search_bar = SearchBar()
        self._search_bar.search_requested.connect(self.search_requested.emit)
        layout.addWidget(self._search_bar)

        # Snapshot thumbnail
        self._snapshot_thumb = SnapshotThumbnail()
        layout.addWidget(self._snapshot_thumb)

        layout.addStretch()

        # Approval controls
        approval_layout = QHBoxLayout()

        self._approve_checkbox = QCheckBox("Approve Item")
        self._approve_checkbox.toggled.connect(self.approval_toggled.emit)
        approval_layout.addWidget(self._approve_checkbox)

        approval_layout.addStretch()

        self._resend_btn = QPushButton("🔄 Resend to AI")
        self._resend_btn.clicked.connect(self._on_resend)
        approval_layout.addWidget(self._resend_btn)

        layout.addLayout(approval_layout)

    def load_item(self, item: InspectionItem) -> None:
        """Load item data into panel."""
        self._current_item = item

        self._location_label.setText(item.user_location or "-")
        self._description_text.setPlainText(item.user_description or "")
        self._status_badge.set_status(item.status)

        # AI results
        if item.llm_match_type:
            self._match_type_label.setText(item.llm_match_type.value)
        else:
            self._match_type_label.setText("-")

        self._reference_label.setText(item.llm_suggested_term or "-")

        if item.llm_confidence:
            self._confidence_label.setText(item.llm_confidence.value)
        else:
            self._confidence_label.setText("-")

        self._reasoning_text.setPlainText(item.llm_reasoning or "")

        # Search bar
        self._search_bar.set_term(item.active_search_term or "")
        self._update_search_status(item.search_status)

        # Snapshot
        if item.snapshot_path:
            self._snapshot_thumb.set_snapshot(item.snapshot_path)
        else:
            self._snapshot_thumb.clear()

        # Approval
        self._approve_checkbox.setChecked(item.final_approval)

    def _update_search_status(self, status: SearchStatus) -> None:
        """Update search bar visual state."""
        if status == SearchStatus.FOUND:
            self._search_bar.set_found_state()
        elif status == SearchStatus.NOT_FOUND:
            self._search_bar.set_not_found_state()
        else:
            self._search_bar.set_normal_state()

    def update_search_status(self, found: bool) -> None:
        """Update search status after search."""
        if found:
            self._search_bar.set_found_state()
        else:
            self._search_bar.set_not_found_state()

    def show_snapshot_thumbnail(self, path: str) -> None:
        """Show snapshot thumbnail."""
        self._snapshot_thumb.set_snapshot(path)

    def _on_resend(self) -> None:
        """Handle resend to AI button."""
        # Could add feedback input dialog here
        self.resend_requested.emit("")

    def clear(self) -> None:
        """Clear all fields."""
        self._current_item = None
        self._location_label.setText("-")
        self._description_text.clear()
        self._match_type_label.setText("-")
        self._reference_label.setText("-")
        self._confidence_label.setText("-")
        self._reasoning_text.clear()
        self._search_bar.set_term("")
        self._search_bar.set_normal_state()
        self._snapshot_thumb.clear()
        self._approve_checkbox.setChecked(False)
