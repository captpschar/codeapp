"""
Global application state container (framework-agnostic).
"""

from pathlib import Path
from typing import Optional, List, Callable, Set
from dataclasses import dataclass, field
from .inspection_queue import InspectionQueue
from .state_machine import ItemStateMachine
from .config_manager import ConfigManager, AppConfig, CodeFolder
from .error_handler import ErrorHandler


@dataclass
class TriageState:
    """State for triage page that persists across navigation."""
    image_folder: Optional[Path] = None
    image_files: List[Path] = field(default_factory=list)
    current_index: int = 0
    selected_folders: Set[str] = field(default_factory=set)
    selected_chapters: List[str] = field(default_factory=list)


class AppState:
    """Central application state management."""

    def __init__(self, config_path: str = "settings.json"):
        # Load configuration (creates default if missing)
        self._config_manager = ConfigManager(config_path)
        self._config = self._config_manager.load()

        # Initialize output directory
        output_path = Path(self._config.output_directory)
        output_path.mkdir(parents=True, exist_ok=True)

        # Initialize components
        self._queue = InspectionQueue(
            persistence_path=output_path / "queue.json"
        )
        self._state_machine = ItemStateMachine()
        self._error_handler = ErrorHandler(
            log_dir=output_path / "logs"
        )

        # Current selection
        self._current_item_id: Optional[str] = None

        # Triage page state (persists across navigation)
        self._triage_state = TriageState()

        # Callbacks for state changes (replaces Qt signals)
        self._queue_callbacks: List[Callable] = []
        self._item_selected_callbacks: List[Callable[[str], None]] = []
        self._config_changed_callbacks: List[Callable] = []

        # Register queue change callback
        self._queue.register_change_callback(self._on_queue_changed)

    @property
    def config(self) -> AppConfig:
        """Get application configuration."""
        return self._config

    @property
    def config_manager(self) -> ConfigManager:
        """Get config manager for saving changes."""
        return self._config_manager

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

    @property
    def triage_state(self) -> TriageState:
        """Get triage page state."""
        return self._triage_state

    # Callback registration methods
    def on_queue_updated(self, callback: Callable) -> None:
        """Register callback for queue updates."""
        self._queue_callbacks.append(callback)

    def on_item_selected(self, callback: Callable[[str], None]) -> None:
        """Register callback for item selection."""
        self._item_selected_callbacks.append(callback)

    def on_config_changed(self, callback: Callable) -> None:
        """Register callback for config changes."""
        self._config_changed_callbacks.append(callback)

    def select_item(self, item_id: str) -> None:
        """Select an item for viewing/editing."""
        self._current_item_id = item_id
        for callback in self._item_selected_callbacks:
            callback(item_id)

    def update_config(self, **kwargs) -> None:
        """Update configuration and notify listeners."""
        self._config = self._config_manager.update(**kwargs)
        for callback in self._config_changed_callbacks:
            callback()

    def reload_config(self) -> None:
        """Reload configuration from disk."""
        self._config = self._config_manager.load()
        for callback in self._config_changed_callbacks:
            callback()

    # Code folder methods
    def get_code_folder(self, name: str) -> Optional[CodeFolder]:
        """Get a code folder by name."""
        return self._config.get_code_folder(name)

    def list_code_folder_names(self) -> List[str]:
        """List all code folder names."""
        return self._config.list_code_folder_names()

    def get_pdf_path(self, folder_name: str, chapter_filename: str) -> Path:
        """Get full path to a code book chapter."""
        folder = self._config.get_code_folder(folder_name)
        if folder:
            return Path(folder.path) / chapter_filename
        return Path(chapter_filename)

    def list_chapters_in_folder(self, folder_name: str) -> List[str]:
        """List PDF files in a specific code folder."""
        folder = self._config.get_code_folder(folder_name)
        if folder:
            return folder.list_pdfs()
        return []

    def list_all_chapters(self) -> List[tuple]:
        """List all chapters from all folders as (folder_name, filename) tuples."""
        chapters = []
        for folder in self._config.code_folders:
            for pdf in folder.list_pdfs():
                chapters.append((folder.name, pdf))
        return chapters

    def get_output_dir(self) -> Path:
        """Get output directory path."""
        path = Path(self._config.output_directory)
        path.mkdir(parents=True, exist_ok=True)
        return path

    def save(self) -> None:
        """Save current state to disk."""
        self._queue._persist()
        self._config_manager.save()

    def load(self) -> None:
        """Load state from disk."""
        self._queue.load_from_disk()

    def _on_queue_changed(self) -> None:
        """Handle queue changes - notify callbacks."""
        for callback in self._queue_callbacks:
            callback()
