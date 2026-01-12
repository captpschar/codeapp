"""
Global application state container.
"""

from pathlib import Path
from typing import Optional
from PyQt6.QtCore import QObject
from .inspection_queue import InspectionQueue
from .state_machine import ItemStateMachine
from .config_manager import ConfigManager, AppConfig
from .error_handler import ErrorHandler
from ..signals.state_signals import StateSignals


class AppState(QObject):
    """Central application state management."""

    def __init__(self, config_path: str = "settings.json"):
        super().__init__()

        # Load configuration
        self._config_manager = ConfigManager(config_path)
        self._config = self._config_manager.load()

        # Initialize components
        output_path = Path(self._config.output_directory)
        output_path.mkdir(parents=True, exist_ok=True)

        self._queue = InspectionQueue(
            persistence_path=output_path / "queue.json"
        )
        self._state_machine = ItemStateMachine()
        self._error_handler = ErrorHandler(
            log_dir=output_path / "logs"
        )

        # Signals for UI updates
        self.signals = StateSignals()

        # Current selection
        self._current_item_id: Optional[str] = None

        # Register queue change callback
        self._queue.register_change_callback(self._on_queue_changed)

    @property
    def config(self) -> AppConfig:
        """Get application configuration."""
        return self._config

    @property
    def queue(self) -> InspectionQueue:
        """Get inspection queue."""
        return self._queue

    @property
    def state_machine(self) -> ItemStateMachine:
        """Get state machine."""
        return self._state_machine

    @property
    def error_handler(self) -> ErrorHandler:
        """Get error handler."""
        return self._error_handler

    @property
    def current_item_id(self) -> Optional[str]:
        """Get currently selected item ID."""
        return self._current_item_id

    def select_item(self, item_id: str) -> None:
        """Select an item for viewing/editing."""
        self._current_item_id = item_id
        self.signals.item_selected.emit(item_id)

    def get_pdf_path(self, chapter_filename: str) -> Path:
        """Get full path to a code book chapter."""
        return Path(self._config.code_book_directory) / chapter_filename

    def get_output_dir(self) -> Path:
        """Get output directory path."""
        return Path(self._config.output_directory)

    def list_available_chapters(self) -> list[str]:
        """List available code book PDF files."""
        code_dir = Path(self._config.code_book_directory)
        if code_dir.exists():
            return [f.name for f in code_dir.glob("*.pdf")]
        return []

    def save(self) -> None:
        """Save current state to disk."""
        self._queue._persist()

    def load(self) -> None:
        """Load state from disk."""
        self._queue.load_from_disk()

    def _on_queue_changed(self) -> None:
        """Handle queue changes - emit signal for UI."""
        self.signals.queue_updated.emit()
