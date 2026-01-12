"""
Error display modal dialog.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTextEdit
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon


class ErrorDialog(QDialog):
    """Modal dialog for displaying errors."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Create dialog UI."""
        self.setWindowTitle("Error")
        self.setMinimumSize(400, 200)
        self.setModal(True)

        layout = QVBoxLayout(self)

        # Error icon and title
        header = QHBoxLayout()
        self._icon_label = QLabel("⚠️")
        self._icon_label.setStyleSheet("font-size: 24px;")
        header.addWidget(self._icon_label)

        self._title_label = QLabel("An error occurred")
        self._title_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        header.addWidget(self._title_label)
        header.addStretch()
        layout.addLayout(header)

        # Error message
        self._message_text = QTextEdit()
        self._message_text.setReadOnly(True)
        self._message_text.setMaximumHeight(100)
        layout.addWidget(self._message_text)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self._retry_btn = QPushButton("Retry")
        self._retry_btn.clicked.connect(self.accept)
        self._retry_btn.setVisible(False)
        button_layout.addWidget(self._retry_btn)

        self._close_btn = QPushButton("Close")
        self._close_btn.clicked.connect(self.reject)
        button_layout.addWidget(self._close_btn)

        layout.addLayout(button_layout)

    def show_error(
        self,
        title: str,
        message: str,
        recoverable: bool = False
    ) -> bool:
        """Show error dialog and return True if retry clicked."""
        self._title_label.setText(title)
        self._message_text.setPlainText(message)
        self._retry_btn.setVisible(recoverable)

        result = self.exec()
        return result == QDialog.DialogCode.Accepted

    @staticmethod
    def show_simple_error(parent, title: str, message: str) -> None:
        """Show a simple non-recoverable error."""
        dialog = ErrorDialog(parent)
        dialog.show_error(title, message, recoverable=False)
