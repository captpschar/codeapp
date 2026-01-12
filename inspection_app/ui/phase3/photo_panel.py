"""
Photo display panel for Phase 3 dashboard.
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QScrollArea
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap


class PhotoPanel(QWidget):
    """Panel for displaying edited inspection photo."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Create panel UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Header
        header = QLabel("Inspection Photo")
        header.setStyleSheet("font-weight: bold; padding: 4px;")
        layout.addWidget(header)

        # Scroll area for image
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._image_label = QLabel()
        self._image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._image_label.setStyleSheet("background-color: #2a2a2a;")
        scroll.setWidget(self._image_label)

        layout.addWidget(scroll)

    def load_image(self, path: str) -> bool:
        """Load and display image from path."""
        if not path:
            self.clear()
            return False

        pixmap = QPixmap(path)
        if pixmap.isNull():
            self.clear()
            return False

        # Scale to fit
        scaled = pixmap.scaled(
            self._image_label.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        self._image_label.setPixmap(scaled)
        return True

    def clear(self) -> None:
        """Clear displayed image."""
        self._image_label.clear()
        self._image_label.setText("No image loaded")

    def resizeEvent(self, event) -> None:
        """Handle resize."""
        super().resizeEvent(event)
        # Re-scale image if loaded
        pixmap = self._image_label.pixmap()
        if pixmap and not pixmap.isNull():
            scaled = pixmap.scaled(
                self._image_label.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self._image_label.setPixmap(scaled)
