"""
Phase navigation widget.
"""

from PyQt6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QButtonGroup
from PyQt6.QtCore import pyqtSignal


class PhaseNavigator(QWidget):
    """Tab-like navigation for phases."""

    phase_changed = pyqtSignal(int)  # Phase index (0-3)

    PHASES = [
        ("1. Triage", "Add and edit photos"),
        ("2. Process", "AI batch processing"),
        ("3. Verify", "Review and approve"),
        ("4. Export", "Generate report"),
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self._buttons = []
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Create navigator UI."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)

        self._button_group = QButtonGroup(self)
        self._button_group.setExclusive(True)

        for i, (name, tooltip) in enumerate(self.PHASES):
            btn = QPushButton(name)
            btn.setCheckable(True)
            btn.setToolTip(tooltip)
            btn.setMinimumHeight(36)
            btn.setStyleSheet(self._get_button_style(False))

            self._button_group.addButton(btn, i)
            self._buttons.append(btn)
            layout.addWidget(btn)

        # Set first phase as active
        self._buttons[0].setChecked(True)
        self._buttons[0].setStyleSheet(self._get_button_style(True))

        # Connect signals
        self._button_group.idClicked.connect(self._on_phase_clicked)

        layout.addStretch()

    def _get_button_style(self, active: bool) -> str:
        """Get button style."""
        if active:
            return """
                QPushButton {
                    background-color: #2196F3;
                    color: white;
                    border: none;
                    padding: 8px 16px;
                    font-weight: bold;
                    border-radius: 4px;
                }
            """
        else:
            return """
                QPushButton {
                    background-color: #e0e0e0;
                    color: #333;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: #d0d0d0;
                }
            """

    def _on_phase_clicked(self, index: int) -> None:
        """Handle phase button click."""
        # Update styles
        for i, btn in enumerate(self._buttons):
            btn.setStyleSheet(self._get_button_style(i == index))

        self.phase_changed.emit(index)

    def set_phase(self, index: int) -> None:
        """Set active phase."""
        if 0 <= index < len(self._buttons):
            self._buttons[index].setChecked(True)
            self._on_phase_clicked(index)

    def get_current_phase(self) -> int:
        """Get current phase index."""
        return self._button_group.checkedId()

    def set_phase_enabled(self, index: int, enabled: bool) -> None:
        """Enable/disable a phase button."""
        if 0 <= index < len(self._buttons):
            self._buttons[index].setEnabled(enabled)
