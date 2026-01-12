"""
Confirmation prompt dialogs.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
)


class ConfirmationDialog(QDialog):
    """Modal dialog for confirmation prompts."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Create dialog UI."""
        self.setWindowTitle("Confirm")
        self.setMinimumWidth(300)
        self.setModal(True)

        layout = QVBoxLayout(self)

        # Message
        self._message_label = QLabel()
        self._message_label.setWordWrap(True)
        layout.addWidget(self._message_label)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self._cancel_btn = QPushButton("Cancel")
        self._cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self._cancel_btn)

        self._confirm_btn = QPushButton("Confirm")
        self._confirm_btn.clicked.connect(self.accept)
        self._confirm_btn.setDefault(True)
        button_layout.addWidget(self._confirm_btn)

        layout.addLayout(button_layout)

    def ask(
        self,
        message: str,
        confirm_text: str = "Confirm",
        cancel_text: str = "Cancel"
    ) -> bool:
        """Show confirmation dialog and return True if confirmed."""
        self._message_label.setText(message)
        self._confirm_btn.setText(confirm_text)
        self._cancel_btn.setText(cancel_text)

        result = self.exec()
        return result == QDialog.DialogCode.Accepted

    @staticmethod
    def confirm(parent, message: str, title: str = "Confirm") -> bool:
        """Static method for quick confirmation."""
        dialog = ConfirmationDialog(parent)
        dialog.setWindowTitle(title)
        return dialog.ask(message)

    @staticmethod
    def confirm_delete(parent, item_name: str = "this item") -> bool:
        """Confirm deletion dialog."""
        dialog = ConfirmationDialog(parent)
        dialog.setWindowTitle("Confirm Delete")
        return dialog.ask(
            f"Are you sure you want to delete {item_name}?",
            confirm_text="Delete",
            cancel_text="Keep"
        )
