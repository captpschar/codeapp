"""
Base class for background worker threads.
"""

from PyQt6.QtCore import QThread, QMutex, QWaitCondition
from ..signals.worker_signals import WorkerSignals


class BaseWorker(QThread):
    """Base class for background workers with pause/resume support."""

    def __init__(self):
        super().__init__()
        self.signals = WorkerSignals()
        self._mutex = QMutex()
        self._pause_condition = QWaitCondition()
        self._is_paused = False
        self._is_cancelled = False

    def pause(self) -> None:
        """Pause worker execution."""
        self._mutex.lock()
        self._is_paused = True
        self._mutex.unlock()

    def resume(self) -> None:
        """Resume paused worker."""
        self._mutex.lock()
        self._is_paused = False
        self._pause_condition.wakeAll()
        self._mutex.unlock()

    def cancel(self) -> None:
        """Cancel worker execution."""
        self._mutex.lock()
        self._is_cancelled = True
        self._is_paused = False
        self._pause_condition.wakeAll()
        self._mutex.unlock()

    def check_pause(self) -> None:
        """Check if paused and wait if needed. Call in run() loop."""
        self._mutex.lock()
        while self._is_paused and not self._is_cancelled:
            self._pause_condition.wait(self._mutex)
        self._mutex.unlock()

    def is_cancelled(self) -> bool:
        """Check if worker was cancelled."""
        return self._is_cancelled

    def is_paused(self) -> bool:
        """Check if worker is paused."""
        return self._is_paused

    def reset(self) -> None:
        """Reset worker state for reuse."""
        self._mutex.lock()
        self._is_paused = False
        self._is_cancelled = False
        self._mutex.unlock()

    def run(self) -> None:
        """Override in subclass. Call check_pause() in processing loop."""
        raise NotImplementedError("Subclasses must implement run()")
