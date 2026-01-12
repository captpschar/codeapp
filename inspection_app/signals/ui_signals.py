"""
UI event signals.
"""

from PyQt6.QtCore import QObject, pyqtSignal


class UISignals(QObject):
    """Signals for UI events."""

    # Image editing signals
    crop_requested = pyqtSignal(tuple)
    rotate_requested = pyqtSignal(float)
    brightness_changed = pyqtSignal(float)
    contrast_changed = pyqtSignal(float)
    image_saved = pyqtSignal(str)

    # Form signals
    metadata_changed = pyqtSignal(str, str)
    chapter_selected = pyqtSignal(str)

    # Action signals
    add_to_queue_requested = pyqtSignal()
    process_batch_requested = pyqtSignal()
    export_requested = pyqtSignal()

    # Navigation signals
    next_item_requested = pyqtSignal()
    prev_item_requested = pyqtSignal()
