"""
Phase 3: Three-pane verification dashboard.
"""

from PyQt6.QtWidgets import QWidget, QHBoxLayout, QSplitter, QListWidget, QListWidgetItem, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt
from pathlib import Path
import shutil
from .photo_panel import PhotoPanel
from .data_panel import DataPanel
from .pdf_viewer import PDFViewer
from ...core.inspection_item import InspectionItem, ItemStatus, SearchStatus


class DashboardWidget(QWidget):
    """Phase 3 verification dashboard."""

    def __init__(self, app_state):
        super().__init__()
        self._app_state = app_state
        self._current_item: InspectionItem = None
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self) -> None:
        """Create three-pane layout."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        # Main splitter
        main_splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left panel: Item list + Photo
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)

        # Item list
        list_label = QLabel("Review Items")
        list_label.setStyleSheet("font-weight: bold;")
        left_layout.addWidget(list_label)

        self._item_list = QListWidget()
        self._item_list.itemClicked.connect(self._on_item_clicked)
        self._item_list.setMaximumHeight(150)
        left_layout.addWidget(self._item_list)

        # Photo panel
        self._photo_panel = PhotoPanel()
        left_layout.addWidget(self._photo_panel)

        main_splitter.addWidget(left_widget)

        # Center: Data panel
        self._data_panel = DataPanel()
        main_splitter.addWidget(self._data_panel)

        # Right: PDF viewer
        self._pdf_viewer = PDFViewer()
        main_splitter.addWidget(self._pdf_viewer)

        # Set initial sizes (25%, 25%, 50%)
        main_splitter.setSizes([250, 250, 500])

        layout.addWidget(main_splitter)

    def _connect_signals(self) -> None:
        """Connect internal signals."""
        # App state signals
        self._app_state.signals.queue_updated.connect(self._refresh_items)
        self._app_state.signals.item_selected.connect(self._on_item_selected)

        # Data panel signals
        self._data_panel.search_requested.connect(self._on_search_requested)
        self._data_panel.approval_toggled.connect(self._on_approval_toggled)
        self._data_panel.resend_requested.connect(self._on_resend_requested)

        # PDF viewer signals
        self._pdf_viewer.snapshot_created.connect(self._on_snapshot_created)

    def _refresh_items(self) -> None:
        """Refresh item list."""
        self._item_list.clear()

        # Get items that are ready for review
        items = [
            i for i in self._app_state.queue.get_all_items()
            if i.status in (ItemStatus.REVIEW_READY, ItemStatus.APPROVED)
        ]

        for item in items:
            list_item = QListWidgetItem()
            list_item.setData(Qt.ItemDataRole.UserRole, item.id)

            icon = "✅" if item.final_approval else "👁"
            list_item.setText(f"{icon} {item.user_location}")

            self._item_list.addItem(list_item)

    def _on_item_clicked(self, list_item: QListWidgetItem) -> None:
        """Handle item list click."""
        item_id = list_item.data(Qt.ItemDataRole.UserRole)
        self._app_state.select_item(item_id)

    def _on_item_selected(self, item_id: str) -> None:
        """Load selected item into dashboard."""
        item = self._app_state.queue.get_item_by_id(item_id)
        if not item:
            return

        self._current_item = item

        # Load photo
        self._photo_panel.load_image(item.photo_edited_path or item.photo_original_path)

        # Load data panel
        self._data_panel.load_item(item)

        # Load PDF
        pdf_path = self._app_state.get_pdf_path(item.selected_chapter_file)
        if pdf_path.exists():
            self._pdf_viewer.open_pdf(pdf_path)

            # Jump to search result page if available
            if item.search_result_page is not None:
                self._pdf_viewer.go_to_page(item.search_result_page)

    def _on_search_requested(self, search_term: str) -> None:
        """Handle search bar search request."""
        if not self._current_item:
            return

        result = self._pdf_viewer.search_text(search_term)

        if result:
            self._current_item.search_status = SearchStatus.FOUND
            self._current_item.active_search_term = search_term
            self._current_item.search_result_page = result[0]
            self._data_panel.update_search_status(found=True)
        else:
            self._current_item.search_status = SearchStatus.NOT_FOUND
            self._data_panel.update_search_status(found=False)

        self._app_state.queue.update_item(self._current_item)

    def _on_snapshot_created(self, temp_path: str) -> None:
        """Handle snapshot creation from PDF."""
        if not self._current_item:
            return

        # Move snapshot to proper location
        output_dir = self._app_state.get_output_dir() / "snapshots"
        output_dir.mkdir(parents=True, exist_ok=True)

        original_name = Path(self._current_item.photo_original_path).stem
        snapshot_name = f"{original_name}_code_snap.png"
        final_path = output_dir / snapshot_name

        shutil.copy(temp_path, final_path)

        # Update item
        self._current_item.snapshot_path = str(final_path)
        self._app_state.queue.update_item(self._current_item)

        # Update UI
        self._data_panel.show_snapshot_thumbnail(str(final_path))

    def _on_approval_toggled(self, approved: bool) -> None:
        """Handle approval checkbox toggle."""
        if not self._current_item:
            return

        if approved:
            self._app_state.state_machine.approve(self._current_item)
        else:
            self._app_state.state_machine.unapprove(self._current_item)

        self._app_state.queue.update_item(self._current_item)
        self._refresh_items()

    def _on_resend_requested(self, feedback: str) -> None:
        """Resend item to AI with user feedback."""
        if not self._current_item:
            return

        self._current_item.status = ItemStatus.PENDING
        if feedback:
            self._current_item.error_message = f"USER_FEEDBACK:{feedback}"

        self._app_state.queue.update_item(self._current_item)
        self._refresh_items()

    def showEvent(self, event) -> None:
        """Handle widget shown."""
        super().showEvent(event)
        self._refresh_items()
