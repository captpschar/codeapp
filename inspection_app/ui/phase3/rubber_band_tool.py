"""
Rubber band selection tool for PDF snapshots.
"""

from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, QRect, QPoint, pyqtSignal
from PyQt6.QtGui import QPainter, QPen, QColor, QMouseEvent
from typing import Optional, Tuple


class RubberBandTool(QWidget):
    """Overlay widget for rubber band selection."""

    selection_completed = pyqtSignal(tuple)  # (x1, y1, x2, y2)
    selection_cancelled = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._start_point: Optional[QPoint] = None
        self._current_rect: Optional[QRect] = None
        self._is_selecting = False
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Setup overlay appearance."""
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        self.setMouseTracking(True)
        self.setCursor(Qt.CursorShape.CrossCursor)

    def start_selection(self) -> None:
        """Enable selection mode."""
        self._is_selecting = True
        self._start_point = None
        self._current_rect = None
        self.show()
        self.raise_()

    def cancel_selection(self) -> None:
        """Cancel current selection."""
        self._is_selecting = False
        self._start_point = None
        self._current_rect = None
        self.update()
        self.selection_cancelled.emit()

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """Handle mouse press to start selection."""
        if event.button() == Qt.MouseButton.LeftButton and self._is_selecting:
            self._start_point = event.pos()
            self._current_rect = QRect(self._start_point, self._start_point)
            self.update()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        """Handle mouse move to update selection."""
        if self._start_point and self._is_selecting:
            self._current_rect = QRect(
                self._start_point, event.pos()
            ).normalized()
            self.update()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        """Handle mouse release to complete selection."""
        if event.button() == Qt.MouseButton.LeftButton and self._current_rect:
            if self._current_rect.width() > 10 and self._current_rect.height() > 10:
                rect = (
                    self._current_rect.x(),
                    self._current_rect.y(),
                    self._current_rect.right(),
                    self._current_rect.bottom()
                )
                self.selection_completed.emit(rect)

            self._is_selecting = False
            self._start_point = None
            self._current_rect = None
            self.update()

    def keyPressEvent(self, event) -> None:
        """Handle escape to cancel."""
        if event.key() == Qt.Key.Key_Escape:
            self.cancel_selection()
        super().keyPressEvent(event)

    def paintEvent(self, event) -> None:
        """Draw the selection rectangle."""
        super().paintEvent(event)

        if self._current_rect:
            painter = QPainter(self)

            # Semi-transparent overlay
            overlay = QColor(0, 0, 0, 50)
            painter.fillRect(self.rect(), overlay)

            # Clear the selection area
            painter.setCompositionMode(
                QPainter.CompositionMode.CompositionMode_Clear
            )
            painter.fillRect(self._current_rect, Qt.GlobalColor.transparent)

            # Draw selection border
            painter.setCompositionMode(
                QPainter.CompositionMode.CompositionMode_SourceOver
            )
            pen = QPen(QColor(255, 0, 0), 2, Qt.PenStyle.DashLine)
            painter.setPen(pen)
            painter.drawRect(self._current_rect)

    def get_selection(self) -> Optional[Tuple[int, int, int, int]]:
        """Get current selection rectangle."""
        if self._current_rect:
            return (
                self._current_rect.x(),
                self._current_rect.y(),
                self._current_rect.right(),
                self._current_rect.bottom()
            )
        return None
