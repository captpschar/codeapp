"""
Search bar with visual state feedback.
"""

from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLineEdit, QPushButton
from PyQt6.QtCore import pyqtSignal


class SearchBar(QWidget):
    """Search bar with found/not-found visual states."""

    search_requested = pyqtSignal(str)

    STYLE_NORMAL = "background-color: white; border: 1px solid #ccc; padding: 4px;"
    STYLE_FOUND = "background-color: white; border: 2px solid #4CAF50; padding: 4px;"
    STYLE_NOT_FOUND = "background-color: #FFF9C4; border: 2px solid #FFC107; padding: 4px;"

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Create search bar UI."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText(
            "Enter code reference (e.g., R311.7 or Figure R507.2)"
        )
        self._search_input.returnPressed.connect(self._on_search)
        self._search_input.setStyleSheet(self.STYLE_NORMAL)
        layout.addWidget(self._search_input)

        self._search_btn = QPushButton("Search")
        self._search_btn.clicked.connect(self._on_search)
        layout.addWidget(self._search_btn)

    def set_term(self, term: str) -> None:
        """Set search term in input."""
        self._search_input.setText(term)

    def get_term(self) -> str:
        """Get current search term."""
        return self._search_input.text().strip()

    def set_found_state(self) -> None:
        """Set visual state to 'found' (green border)."""
        self._search_input.setStyleSheet(self.STYLE_FOUND)

    def set_not_found_state(self) -> None:
        """Set visual state to 'not found' (yellow background)."""
        self._search_input.setStyleSheet(self.STYLE_NOT_FOUND)

    def set_normal_state(self) -> None:
        """Reset to normal visual state."""
        self._search_input.setStyleSheet(self.STYLE_NORMAL)

    def _on_search(self) -> None:
        """Handle search action."""
        term = self.get_term()
        if term:
            self.search_requested.emit(term)

    def set_enabled(self, enabled: bool) -> None:
        """Enable/disable the search bar."""
        self._search_input.setEnabled(enabled)
        self._search_btn.setEnabled(enabled)
