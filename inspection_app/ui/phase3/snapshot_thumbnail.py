"""
Snapshot thumbnail preview widget.
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap


class SnapshotThumbnail(QWidget):
    """Thumbnail preview of captured snapshot."""

    clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._path: str = ""
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Create thumbnail UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        # Label
        self._label = QLabel("Code Snapshot")
        self._label.setStyleSheet("font-size: 11px; color: #666;")
        layout.addWidget(self._label)

        # Thumbnail image
        self._thumbnail = QLabel()
        self._thumbnail.setFixedSize(150, 100)
        self._thumbnail.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._thumbnail.setStyleSheet(
            "background-color: #f0f0f0; border: 1px solid #ccc;"
        )
        self._thumbnail.setText("No snapshot")
        layout.addWidget(self._thumbnail)

        self.setMaximumHeight(140)

    def set_snapshot(self, path: str) -> None:
        """Set snapshot image from path."""
        self._path = path
        if not path:
            self.clear()
            return

        pixmap = QPixmap(path)
        if pixmap.isNull():
            self._thumbnail.setText("Load failed")
            return

        scaled = pixmap.scaled(
            self._thumbnail.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        self._thumbnail.setPixmap(scaled)

    def get_path(self) -> str:
        """Get snapshot path."""
        return self._path

    def clear(self) -> None:
        """Clear thumbnail."""
        self._path = ""
        self._thumbnail.clear()
        self._thumbnail.setText("No snapshot")

    def has_snapshot(self) -> bool:
        """Check if snapshot is set."""
        return bool(self._path)

    def mousePressEvent(self, event) -> None:
        """Handle click to emit signal."""
        super().mousePressEvent(event)
        if self._path:
            self.clicked.emit()
