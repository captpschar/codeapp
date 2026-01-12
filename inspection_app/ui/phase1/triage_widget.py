"""
Phase 1: Triage widget - main container.
"""

from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QSplitter,
    QPushButton, QFileDialog
)
from PyQt6.QtCore import Qt
from pathlib import Path
from .image_viewer import ImageViewer
from .edit_toolbar import EditToolbar
from .metadata_form import MetadataForm
from .queue_panel import QueuePanel
from ...core.inspection_item import InspectionItem, ItemStatus
from ...services.image_service.image_editor import ImageEditor
from ...services.image_service.file_manager import ImageFileManager


class TriageWidget(QWidget):
    """Phase 1 triage interface."""

    def __init__(self, app_state):
        super().__init__()
        self._app_state = app_state
        self._image_editor = ImageEditor()
        self._file_manager = ImageFileManager(app_state.get_output_dir())
        self._current_image_path: str = ""
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self) -> None:
        """Create triage UI."""
        layout = QHBoxLayout(self)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left: Image editing area
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)

        # Load image button
        load_btn = QPushButton("📷 Load Image...")
        load_btn.clicked.connect(self._on_load_image)
        left_layout.addWidget(load_btn)

        # Edit toolbar
        self._toolbar = EditToolbar()
        self._toolbar.set_enabled(False)
        left_layout.addWidget(self._toolbar)

        # Image viewer
        self._image_viewer = ImageViewer()
        left_layout.addWidget(self._image_viewer)

        splitter.addWidget(left_widget)

        # Right: Metadata and queue
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)

        # Metadata form
        self._metadata_form = MetadataForm()
        self._metadata_form.set_chapters(self._app_state.list_available_chapters())
        right_layout.addWidget(self._metadata_form)

        # Queue panel
        self._queue_panel = QueuePanel()
        right_layout.addWidget(self._queue_panel)

        splitter.addWidget(right_widget)

        splitter.setSizes([600, 300])
        layout.addWidget(splitter)

    def _connect_signals(self) -> None:
        """Connect internal signals."""
        # Toolbar signals
        self._toolbar.crop_clicked.connect(self._on_crop_mode)
        self._toolbar.rotate_left_clicked.connect(lambda: self._rotate(-90))
        self._toolbar.rotate_right_clicked.connect(lambda: self._rotate(90))
        self._toolbar.brightness_changed.connect(self._on_brightness)
        self._toolbar.contrast_changed.connect(self._on_contrast)
        self._toolbar.reset_clicked.connect(self._on_reset)
        self._toolbar.save_clicked.connect(self._on_save)

        # Image viewer signals
        self._image_viewer.crop_selected.connect(self._on_crop)

        # Form signals
        self._metadata_form.add_to_queue_clicked.connect(self._on_add_to_queue)

        # Queue signals
        self._queue_panel.item_selected.connect(self._on_item_selected)

        # App state signals
        self._app_state.signals.queue_updated.connect(self._refresh_queue)

    def _on_load_image(self) -> None:
        """Handle load image button."""
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Inspection Photo",
            "",
            "Images (*.jpg *.jpeg *.png *.bmp *.gif)"
        )
        if path:
            self._load_image(path)

    def _load_image(self, path: str) -> None:
        """Load image into editor."""
        self._current_image_path = path
        self._image_editor.load(path)
        self._image_viewer.load_image(path)
        self._toolbar.set_enabled(True)

    def _on_crop_mode(self) -> None:
        """Toggle crop mode."""
        is_crop = self._toolbar._crop_btn.isChecked()
        self._image_viewer.set_crop_mode(is_crop)

    def _on_crop(self, rect: tuple) -> None:
        """Apply crop."""
        self._image_editor.crop(rect)
        self._update_preview()
        self._toolbar.set_crop_mode(False)
        self._image_viewer.set_crop_mode(False)

    def _rotate(self, degrees: float) -> None:
        """Rotate image."""
        self._image_editor.rotate(degrees)
        self._update_preview()

    def _on_brightness(self, factor: float) -> None:
        """Adjust brightness."""
        self._image_editor.reset()
        self._image_editor.adjust_brightness(factor)
        self._update_preview()

    def _on_contrast(self, factor: float) -> None:
        """Adjust contrast."""
        self._image_editor.adjust_contrast(factor)
        self._update_preview()

    def _on_reset(self) -> None:
        """Reset image edits."""
        self._image_editor.reset()
        self._update_preview()

    def _update_preview(self) -> None:
        """Update image preview."""
        from PyQt6.QtGui import QPixmap, QImage
        img = self._image_editor.get_current_image()
        if img:
            data = img.tobytes("raw", "RGB")
            qimg = QImage(data, img.width, img.height, QImage.Format.Format_RGB888)
            self._image_viewer.set_pixmap(QPixmap.fromImage(qimg))

    def _on_save(self) -> None:
        """Save edited image."""
        if not self._current_image_path:
            return

        edited_path = self._file_manager.get_edited_path(self._current_image_path)
        self._file_manager.ensure_edited_dir(self._current_image_path)
        self._image_editor.save(edited_path)

    def _on_add_to_queue(self) -> None:
        """Add current item to queue."""
        if not self._metadata_form.is_valid():
            return
        if not self._current_image_path:
            return

        # Save edited image
        edited_path = self._file_manager.get_edited_path(self._current_image_path)
        self._file_manager.ensure_edited_dir(self._current_image_path)
        self._image_editor.save(edited_path)

        # Create inspection item
        item = InspectionItem()
        item.photo_original_path = self._current_image_path
        item.photo_edited_path = str(edited_path)
        item.user_location = self._metadata_form.get_location()
        item.user_description = self._metadata_form.get_description()
        item.selected_chapter_file = self._metadata_form.get_selected_chapter()
        item.status = ItemStatus.PENDING

        # Add to queue
        self._app_state.queue.add_item(item)

        # Clear form
        self._metadata_form.clear()
        self._image_viewer.clear()
        self._toolbar.set_enabled(False)
        self._current_image_path = ""

    def _on_item_selected(self, item_id: str) -> None:
        """Handle queue item selection."""
        self._app_state.select_item(item_id)

    def _refresh_queue(self) -> None:
        """Refresh queue display."""
        items = self._app_state.queue.get_all_items()
        self._queue_panel.update_items(items)
