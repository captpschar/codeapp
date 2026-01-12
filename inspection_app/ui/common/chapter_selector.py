"""
PDF chapter selection dropdown.
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QComboBox, QLabel
from PyQt6.QtCore import pyqtSignal
from typing import List


class ChapterSelector(QWidget):
    """Dropdown for selecting code book chapter."""

    chapter_changed = pyqtSignal(str)  # Emits chapter filename

    def __init__(self, parent=None):
        super().__init__(parent)
        self._chapters: List[str] = []
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Create UI elements."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._label = QLabel("Code Chapter:")
        layout.addWidget(self._label)

        self._combo = QComboBox()
        self._combo.setPlaceholderText("Select a chapter...")
        self._combo.currentTextChanged.connect(self._on_selection_changed)
        layout.addWidget(self._combo)

    def set_chapters(self, chapters: List[str]) -> None:
        """Set available chapters."""
        self._chapters = chapters
        self._combo.clear()
        self._combo.addItems(chapters)

    def get_selected(self) -> str:
        """Get currently selected chapter."""
        return self._combo.currentText()

    def set_selected(self, chapter: str) -> None:
        """Set selected chapter."""
        index = self._combo.findText(chapter)
        if index >= 0:
            self._combo.setCurrentIndex(index)

    def _on_selection_changed(self, text: str) -> None:
        """Handle selection change."""
        if text:
            self.chapter_changed.emit(text)

    def set_enabled(self, enabled: bool) -> None:
        """Enable/disable the selector."""
        self._combo.setEnabled(enabled)
