"""
Image display widget with zoom and pan.
"""

from PyQt6.QtWidgets import QLabel, QScrollArea, QWidget, QVBoxLayout
from PyQt6.QtCore import Qt, pyqtSignal, QPoint, QRect
from PyQt6.QtGui import QPixmap, QPainter, QPen, QMouseEvent
from typing import Optional, Tuple


class ImageViewer(QScrollArea):
    """Scrollable image viewer with crop selection."""

    crop_selected = pyqtSignal(tuple)  # (x1, y1, x2, y2)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._pixmap: Optional[QPixmap] = None
        self._crop_mode = False
        self._crop_start: Optional[QPoint] = None
        self._crop_rect: Optional[QRect] = None
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Setup viewer UI."""
        self.setWidgetResizable(True)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._image_label = QLabel()
        self._image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._image_label.setStyleSheet("background-color: #2a2a2a;")
        self.setWidget(self._image_label)

    def load_image(self, path: str) -> bool:
        """Load image from file path."""
        pixmap = QPixmap(path)
        if pixmap.isNull():
            return False

        self._pixmap = pixmap
        self._update_display()
        return True

    def set_pixmap(self, pixmap: QPixmap) -> None:
        """Set image from QPixmap."""
        self._pixmap = pixmap
        self._update_display()

    def _update_display(self) -> None:
        """Update displayed image."""
        if self._pixmap:
            # Scale to fit while maintaining aspect ratio
            scaled = self._pixmap.scaled(
                self.viewport().size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self._image_label.setPixmap(scaled)

    def set_crop_mode(self, enabled: bool) -> None:
        """Enable/disable crop selection mode."""
        self._crop_mode = enabled
        if enabled:
            self._image_label.setCursor(Qt.CursorShape.CrossCursor)
        else:
            self._image_label.setCursor(Qt.CursorShape.ArrowCursor)
            self._crop_rect = None

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """Handle mouse press for crop selection."""
        if self._crop_mode and event.button() == Qt.MouseButton.LeftButton:
            self._crop_start = event.pos()
            self._crop_rect = QRect(self._crop_start, self._crop_start)
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        """Handle mouse move for crop selection."""
        if self._crop_mode and self._crop_start:
            self._crop_rect = QRect(self._crop_start, event.pos()).normalized()
            self._update_display()
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        """Handle mouse release for crop selection."""
        if self._crop_mode and self._crop_rect and self._pixmap:
            # Convert to image coordinates
            crop_tuple = self._screen_to_image_rect(self._crop_rect)
            if crop_tuple:
                self.crop_selected.emit(crop_tuple)
            self._crop_start = None
        super().mouseReleaseEvent(event)

    def _screen_to_image_rect(self, rect: QRect) -> Optional[Tuple[int, int, int, int]]:
        """Convert screen rect to image coordinates."""
        if not self._pixmap:
            return None

        # Get display scale
        label_pixmap = self._image_label.pixmap()
        if not label_pixmap:
            return None

        scale_x = self._pixmap.width() / label_pixmap.width()
        scale_y = self._pixmap.height() / label_pixmap.height()

        return (
            int(rect.x() * scale_x),
            int(rect.y() * scale_y),
            int(rect.right() * scale_x),
            int(rect.bottom() * scale_y)
        )

    def clear(self) -> None:
        """Clear displayed image."""
        self._pixmap = None
        self._image_label.clear()

    def resizeEvent(self, event) -> None:
        """Handle resize to update displayed image."""
        super().resizeEvent(event)
        self._update_display()
