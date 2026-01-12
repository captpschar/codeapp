"""
Signals for application state changes.
"""

from PyQt6.QtCore import QObject, pyqtSignal


class StateSignals(QObject):
    """Signals emitted by application state."""

    # Queue signals
    queue_updated = pyqtSignal()
    item_added = pyqtSignal(str)
    item_updated = pyqtSignal(str)
    item_removed = pyqtSignal(str)

    # Selection signals
    item_selected = pyqtSignal(str)

    # Phase signals
    phase_changed = pyqtSignal(int)

    # Status signals
    status_message = pyqtSignal(str)
    error_occurred = pyqtSignal(str, str)
