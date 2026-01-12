"""
Image editing toolbar.
"""

from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QPushButton, QSlider, QLabel
)
from PyQt6.QtCore import Qt, pyqtSignal


class EditToolbar(QWidget):
    """Toolbar for image editing operations."""

    crop_clicked = pyqtSignal()
    rotate_left_clicked = pyqtSignal()
    rotate_right_clicked = pyqtSignal()
    brightness_changed = pyqtSignal(float)
    contrast_changed = pyqtSignal(float)
    reset_clicked = pyqtSignal()
    save_clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Create toolbar UI."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        # Crop button
        self._crop_btn = QPushButton("✂ Crop")
        self._crop_btn.setCheckable(True)
        self._crop_btn.clicked.connect(self.crop_clicked.emit)
        layout.addWidget(self._crop_btn)

        # Rotate buttons
        self._rotate_left_btn = QPushButton("↺ Rotate Left")
        self._rotate_left_btn.clicked.connect(self.rotate_left_clicked.emit)
        layout.addWidget(self._rotate_left_btn)

        self._rotate_right_btn = QPushButton("↻ Rotate Right")
        self._rotate_right_btn.clicked.connect(self.rotate_right_clicked.emit)
        layout.addWidget(self._rotate_right_btn)

        layout.addWidget(QLabel("|"))

        # Brightness slider
        layout.addWidget(QLabel("Brightness:"))
        self._brightness_slider = QSlider(Qt.Orientation.Horizontal)
        self._brightness_slider.setRange(50, 150)
        self._brightness_slider.setValue(100)
        self._brightness_slider.setMaximumWidth(100)
        self._brightness_slider.valueChanged.connect(self._on_brightness_changed)
        layout.addWidget(self._brightness_slider)

        # Contrast slider
        layout.addWidget(QLabel("Contrast:"))
        self._contrast_slider = QSlider(Qt.Orientation.Horizontal)
        self._contrast_slider.setRange(50, 150)
        self._contrast_slider.setValue(100)
        self._contrast_slider.setMaximumWidth(100)
        self._contrast_slider.valueChanged.connect(self._on_contrast_changed)
        layout.addWidget(self._contrast_slider)

        layout.addStretch()

        # Reset button
        self._reset_btn = QPushButton("Reset")
        self._reset_btn.clicked.connect(self._on_reset)
        layout.addWidget(self._reset_btn)

        # Save button
        self._save_btn = QPushButton("💾 Save")
        self._save_btn.clicked.connect(self.save_clicked.emit)
        layout.addWidget(self._save_btn)

    def _on_brightness_changed(self, value: int) -> None:
        """Handle brightness slider change."""
        factor = value / 100.0
        self.brightness_changed.emit(factor)

    def _on_contrast_changed(self, value: int) -> None:
        """Handle contrast slider change."""
        factor = value / 100.0
        self.contrast_changed.emit(factor)

    def _on_reset(self) -> None:
        """Reset sliders and emit signal."""
        self._brightness_slider.setValue(100)
        self._contrast_slider.setValue(100)
        self.reset_clicked.emit()

    def set_crop_mode(self, enabled: bool) -> None:
        """Set crop button checked state."""
        self._crop_btn.setChecked(enabled)

    def set_enabled(self, enabled: bool) -> None:
        """Enable/disable all controls."""
        for child in self.findChildren(QWidget):
            child.setEnabled(enabled)
