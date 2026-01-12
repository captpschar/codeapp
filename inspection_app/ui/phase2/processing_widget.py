"""
Phase 2: Batch processing widget.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QHBoxLayout, QLabel
)
from PyQt6.QtCore import Qt
from pathlib import Path
from .progress_panel import ProgressPanel
from .item_status_list import ItemStatusList
from ...core.inspection_item import ItemStatus
from ...workers.ai_processing_worker import AIProcessingWorker
from ...services.ai_service.gemini_client import GeminiClient
from ...services.ai_service.context_cache import ContextCacheManager


class ProcessingWidget(QWidget):
    """Phase 2 batch processing interface."""

    def __init__(self, app_state):
        super().__init__()
        self._app_state = app_state
        self._worker = None
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self) -> None:
        """Create processing UI."""
        layout = QVBoxLayout(self)

        # Header
        header = QLabel("AI Batch Processing")
        header.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(header)

        info = QLabel(
            "Process all pending items through AI to get code references."
        )
        info.setStyleSheet("color: #666;")
        layout.addWidget(info)

        # Progress panel
        self._progress_panel = ProgressPanel()
        layout.addWidget(self._progress_panel)

        # Item status list
        list_label = QLabel("Items:")
        list_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(list_label)

        self._item_list = ItemStatusList()
        layout.addWidget(self._item_list)

        # Control buttons
        button_layout = QHBoxLayout()

        self._start_btn = QPushButton("▶ Start Processing")
        self._start_btn.setMinimumHeight(40)
        self._start_btn.clicked.connect(self._on_start)
        button_layout.addWidget(self._start_btn)

        self._pause_btn = QPushButton("⏸ Pause")
        self._pause_btn.setEnabled(False)
        self._pause_btn.clicked.connect(self._on_pause)
        button_layout.addWidget(self._pause_btn)

        self._cancel_btn = QPushButton("⏹ Cancel")
        self._cancel_btn.setEnabled(False)
        self._cancel_btn.clicked.connect(self._on_cancel)
        button_layout.addWidget(self._cancel_btn)

        layout.addLayout(button_layout)

    def _connect_signals(self) -> None:
        """Connect app state signals."""
        self._app_state.signals.queue_updated.connect(self._refresh_items)

    def _refresh_items(self) -> None:
        """Refresh item list."""
        items = self._app_state.queue.get_pending_items()
        self._item_list.set_items(items)

    def _on_start(self) -> None:
        """Start batch processing."""
        config = self._app_state.config

        # Create services
        gemini_client = GeminiClient(
            api_key=config.gemini_api_key,
            model_name=config.ai_settings.model_name,
            thinking_level=config.ai_settings.thinking_level
        )

        cache_manager = ContextCacheManager(
            api_key=config.gemini_api_key,
            model_name=config.ai_settings.model_name,
            cache_ttl_minutes=config.ai_settings.cache_ttl_minutes
        )

        # Create worker
        self._worker = AIProcessingWorker(
            queue=self._app_state.queue,
            gemini_client=gemini_client,
            cache_manager=cache_manager,
            pdf_base_path=Path(config.code_book_directory)
        )

        # Connect worker signals
        self._worker.signals.ai_started.connect(self._on_processing_started)
        self._worker.signals.ai_item_started.connect(self._on_item_started)
        self._worker.signals.ai_item_completed.connect(self._on_item_completed)
        self._worker.signals.ai_item_error.connect(self._on_item_error)
        self._worker.signals.ai_progress.connect(self._on_progress)
        self._worker.signals.ai_completed.connect(self._on_processing_completed)
        self._worker.signals.ai_rate_limited.connect(self._on_rate_limited)

        # Update UI
        self._start_btn.setEnabled(False)
        self._pause_btn.setEnabled(True)
        self._cancel_btn.setEnabled(True)

        # Refresh items and start
        self._refresh_items()
        self._worker.start()

    def _on_pause(self) -> None:
        """Pause/resume processing."""
        if self._worker:
            if self._worker.is_paused():
                self._worker.resume()
                self._pause_btn.setText("⏸ Pause")
            else:
                self._worker.pause()
                self._pause_btn.setText("▶ Resume")

    def _on_cancel(self) -> None:
        """Cancel processing."""
        if self._worker:
            self._worker.cancel()
            self._reset_ui()

    def _on_processing_started(self) -> None:
        """Handle processing started."""
        self._progress_panel.set_status("Processing started...")

    def _on_item_started(self, item_id: str) -> None:
        """Handle item processing started."""
        self._item_list.update_item_status(item_id, ItemStatus.PROCESSING)

    def _on_item_completed(self, item_id: str, item) -> None:
        """Handle item completed."""
        self._item_list.update_item_status(item_id, ItemStatus.REVIEW_READY)

    def _on_item_error(self, item_id: str, error: str) -> None:
        """Handle item error."""
        self._item_list.update_item_status(item_id, ItemStatus.ERROR)

    def _on_progress(self, current: int, total: int) -> None:
        """Handle progress update."""
        self._progress_panel.set_progress(current, total)

    def _on_processing_completed(self) -> None:
        """Handle all processing completed."""
        self._progress_panel.set_completed()
        self._reset_ui()

    def _on_rate_limited(self, wait_seconds: int) -> None:
        """Handle rate limiting."""
        self._progress_panel.show_rate_limit(wait_seconds)

    def _reset_ui(self) -> None:
        """Reset UI to initial state."""
        self._start_btn.setEnabled(True)
        self._pause_btn.setEnabled(False)
        self._pause_btn.setText("⏸ Pause")
        self._cancel_btn.setEnabled(False)
        self._worker = None

    def showEvent(self, event) -> None:
        """Handle widget shown."""
        super().showEvent(event)
        self._refresh_items()
