"""
Metadata input form for inspection items.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QLineEdit,
    QTextEdit, QPushButton
)
from PyQt6.QtCore import pyqtSignal
from ..common.chapter_selector import ChapterSelector


class MetadataForm(QWidget):
    """Form for entering item metadata."""

    add_to_queue_clicked = pyqtSignal()
    data_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Create form UI."""
        layout = QVBoxLayout(self)

        form = QFormLayout()

        # Location input
        self._location_input = QLineEdit()
        self._location_input.setPlaceholderText("e.g., South Deck, Basement Stairs")
        self._location_input.textChanged.connect(self.data_changed.emit)
        form.addRow("Location:", self._location_input)

        # Description input
        self._description_input = QTextEdit()
        self._description_input.setPlaceholderText(
            "Describe the observed condition or violation..."
        )
        self._description_input.setMaximumHeight(100)
        self._description_input.textChanged.connect(self.data_changed.emit)
        form.addRow("Description:", self._description_input)

        # Chapter selector
        self._chapter_selector = ChapterSelector()
        self._chapter_selector.chapter_changed.connect(
            lambda: self.data_changed.emit()
        )
        form.addRow("Code Chapter:", self._chapter_selector)

        layout.addLayout(form)
        layout.addStretch()

        # Add to queue button
        self._add_btn = QPushButton("Add to Queue")
        self._add_btn.setMinimumHeight(40)
        self._add_btn.clicked.connect(self.add_to_queue_clicked.emit)
        layout.addWidget(self._add_btn)

    def get_location(self) -> str:
        """Get location text."""
        return self._location_input.text().strip()

    def get_description(self) -> str:
        """Get description text."""
        return self._description_input.toPlainText().strip()

    def get_selected_chapter(self) -> str:
        """Get selected chapter."""
        return self._chapter_selector.get_selected()

    def set_chapters(self, chapters: list) -> None:
        """Set available chapters."""
        self._chapter_selector.set_chapters(chapters)

    def set_data(self, location: str, description: str, chapter: str) -> None:
        """Set form data."""
        self._location_input.setText(location)
        self._description_input.setPlainText(description)
        self._chapter_selector.set_selected(chapter)

    def clear(self) -> None:
        """Clear all form fields."""
        self._location_input.clear()
        self._description_input.clear()

    def is_valid(self) -> bool:
        """Check if form has required data."""
        return bool(
            self.get_location() and
            self.get_description() and
            self.get_selected_chapter()
        )

    def set_enabled(self, enabled: bool) -> None:
        """Enable/disable form."""
        self._location_input.setEnabled(enabled)
        self._description_input.setEnabled(enabled)
        self._chapter_selector.set_enabled(enabled)
        self._add_btn.setEnabled(enabled)
