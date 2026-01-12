"""
PDF viewer widget with search and snapshot.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QScrollArea, QSpinBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap, QImage
from pathlib import Path
from typing import Optional, Tuple
from .rubber_band_tool import RubberBandTool
from ...services.pdf_service.pdf_reader import PDFReader
from ...services.pdf_service.page_renderer import PDFPageRenderer
from ...services.pdf_service.text_searcher import PDFTextSearcher
from ...services.pdf_service.coordinate_mapper import CoordinateMapper


class PDFViewer(QWidget):
    """PDF viewer with navigation, search, and snapshot."""

    snapshot_created = pyqtSignal(str)  # path to snapshot
    page_changed = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._reader: Optional[PDFReader] = None
        self._renderer: Optional[PDFPageRenderer] = None
        self._searcher: Optional[PDFTextSearcher] = None
        self._coord_mapper = CoordinateMapper()
        self._current_page = 0
        self._snapshot_mode = False
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Create viewer UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Navigation bar
        nav_layout = QHBoxLayout()

        self._prev_btn = QPushButton("◀ Prev")
        self._prev_btn.clicked.connect(self._go_prev)
        nav_layout.addWidget(self._prev_btn)

        self._page_spin = QSpinBox()
        self._page_spin.setMinimum(1)
        self._page_spin.valueChanged.connect(self._on_page_changed)
        nav_layout.addWidget(self._page_spin)

        self._page_label = QLabel("/ 0")
        nav_layout.addWidget(self._page_label)

        self._next_btn = QPushButton("Next ▶")
        self._next_btn.clicked.connect(self._go_next)
        nav_layout.addWidget(self._next_btn)

        nav_layout.addStretch()

        self._snapshot_btn = QPushButton("📷 Capture Snapshot")
        self._snapshot_btn.setCheckable(True)
        self._snapshot_btn.clicked.connect(self._toggle_snapshot_mode)
        nav_layout.addWidget(self._snapshot_btn)

        layout.addLayout(nav_layout)

        # PDF display area
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._page_label_widget = QLabel()
        self._page_label_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._page_label_widget.setStyleSheet("background-color: #404040;")
        self._scroll.setWidget(self._page_label_widget)

        layout.addWidget(self._scroll)

        # Rubber band overlay
        self._rubber_band = RubberBandTool(self._page_label_widget)
        self._rubber_band.hide()
        self._rubber_band.selection_completed.connect(self._on_selection)
        self._rubber_band.selection_cancelled.connect(self._cancel_snapshot)

    def open_pdf(self, path: str | Path) -> bool:
        """Open PDF file."""
        try:
            if self._reader:
                self._reader.close()

            self._reader = PDFReader()
            self._reader.open(path)
            self._renderer = PDFPageRenderer(self._reader)
            self._searcher = PDFTextSearcher(self._reader)

            page_count = self._reader.page_count
            self._page_spin.setMaximum(page_count)
            self._page_label.setText(f"/ {page_count}")

            self._current_page = 0
            self._render_page()
            return True

        except Exception as e:
            print(f"Failed to open PDF: {e}")
            return False

    def go_to_page(self, page_num: int) -> None:
        """Navigate to specific page (0-indexed)."""
        if self._reader and 0 <= page_num < self._reader.page_count:
            self._current_page = page_num
            self._page_spin.setValue(page_num + 1)
            self._render_page()

    def search_text(self, term: str) -> Optional[Tuple[int, Tuple]]:
        """Search for text and navigate to result."""
        if not self._searcher:
            return None

        results = self._searcher.search(term)
        if results:
            first = results[0]
            self.go_to_page(first.page_num)
            return (first.page_num, first.rect)
        return None

    def _render_page(self) -> None:
        """Render current page."""
        if not self._renderer:
            return

        img = self._renderer.render_page(self._current_page, dpi=150)
        if img:
            data = img.tobytes("raw", "RGB")
            qimg = QImage(
                data, img.width, img.height,
                img.width * 3,
                QImage.Format.Format_RGB888
            )
            pixmap = QPixmap.fromImage(qimg)
            self._page_label_widget.setPixmap(pixmap)
            self._page_label_widget.resize(pixmap.size())

            # Update rubber band size
            self._rubber_band.setGeometry(self._page_label_widget.rect())

    def _go_prev(self) -> None:
        """Go to previous page."""
        if self._current_page > 0:
            self.go_to_page(self._current_page - 1)

    def _go_next(self) -> None:
        """Go to next page."""
        if self._reader and self._current_page < self._reader.page_count - 1:
            self.go_to_page(self._current_page + 1)

    def _on_page_changed(self, value: int) -> None:
        """Handle page spinbox change."""
        self.go_to_page(value - 1)
        self.page_changed.emit(value - 1)

    def _toggle_snapshot_mode(self) -> None:
        """Toggle snapshot selection mode."""
        self._snapshot_mode = self._snapshot_btn.isChecked()
        if self._snapshot_mode:
            self._rubber_band.start_selection()
        else:
            self._rubber_band.hide()

    def _cancel_snapshot(self) -> None:
        """Cancel snapshot mode."""
        self._snapshot_mode = False
        self._snapshot_btn.setChecked(False)
        self._rubber_band.hide()

    def _on_selection(self, rect: tuple) -> None:
        """Handle snapshot selection."""
        if not self._renderer:
            return

        # Capture region at high DPI
        img = self._renderer.render_region(
            self._current_page, rect, dpi=300
        )
        if img:
            # Save to temp path (will be moved by caller)
            from pathlib import Path
            import tempfile
            temp_path = Path(tempfile.gettempdir()) / "snapshot_temp.png"
            img.save(str(temp_path))
            self.snapshot_created.emit(str(temp_path))

        self._cancel_snapshot()

    def close_pdf(self) -> None:
        """Close current PDF."""
        if self._reader:
            self._reader.close()
            self._reader = None
        self._page_label_widget.clear()

    @property
    def current_page(self) -> int:
        """Get current page number."""
        return self._current_page
