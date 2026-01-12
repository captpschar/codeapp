"""
PyQt6 signals for worker thread communication.
"""

from PyQt6.QtCore import QObject, pyqtSignal


class WorkerSignals(QObject):
    """Signals emitted by background workers."""

    # AI Processing signals
    ai_started = pyqtSignal()
    ai_item_started = pyqtSignal(str)
    ai_item_completed = pyqtSignal(str, object)
    ai_item_error = pyqtSignal(str, str)
    ai_progress = pyqtSignal(int, int)
    ai_completed = pyqtSignal()
    ai_rate_limited = pyqtSignal(int)

    # PDF Search signals
    search_started = pyqtSignal(str)
    search_found = pyqtSignal(str, int, object)
    search_not_found = pyqtSignal(str)
    search_error = pyqtSignal(str)

    # Export signals
    export_started = pyqtSignal()
    export_item_completed = pyqtSignal(str)
    export_item_error = pyqtSignal(str, str)
    export_progress = pyqtSignal(int, int)
    export_completed = pyqtSignal(object)
    export_network_error = pyqtSignal()
