"""
PDF viewer component with page navigation and search.
"""

from nicegui import ui
from pathlib import Path
from typing import Optional, Callable, List, Tuple
import base64
import io
import fitz  # PyMuPDF
from PIL import Image


class PDFViewer:
    """PDF viewer with search and snapshot capabilities."""

    def __init__(
        self,
        on_snapshot: Optional[Callable[[str], None]] = None,
        render_dpi: int = 150
    ):
        self._on_snapshot = on_snapshot
        self._render_dpi = render_dpi
        self._doc: Optional[fitz.Document] = None
        self._current_page: int = 0
        self._total_pages: int = 0
        self._current_path: str = ""
        self._search_results: List[Tuple[int, fitz.Rect]] = []
        self._search_index: int = 0

        # UI elements
        self._page_image = None
        self._page_label = None
        self._container = None

    def render(self) -> ui.element:
        """Render the PDF viewer component."""
        with ui.card().classes('w-full h-full') as self._container:
            # Toolbar
            with ui.row().classes('w-full items-center gap-2 mb-2'):
                ui.button(icon='first_page', on_click=self._first_page).props('flat dense')
                ui.button(icon='chevron_left', on_click=self._prev_page).props('flat dense')

                self._page_label = ui.label('0 / 0').classes('mx-2')

                ui.button(icon='chevron_right', on_click=self._next_page).props('flat dense')
                ui.button(icon='last_page', on_click=self._last_page).props('flat dense')

                ui.separator().props('vertical')

                # Search
                self._search_input = ui.input(placeholder='Search...').classes('w-40')
                ui.button(icon='search', on_click=self._search).props('flat dense')
                ui.button(icon='arrow_upward', on_click=self._prev_result).props('flat dense')
                ui.button(icon='arrow_downward', on_click=self._next_result).props('flat dense')

                ui.separator().props('vertical')

                ui.button('Snapshot', icon='photo_camera', on_click=self._take_snapshot).props('flat')

            # PDF page display
            with ui.scroll_area().classes('w-full h-96'):
                self._page_image = ui.image('').classes('w-full')
                self._page_image.visible = False

                self._placeholder = ui.label('No PDF loaded').classes('text-gray-400 py-20 text-center w-full')

        return self._container

    def open_pdf(self, path: str | Path) -> bool:
        """Open a PDF file."""
        try:
            path = str(path)
            if not Path(path).exists():
                return False

            if self._doc:
                self._doc.close()

            self._doc = fitz.open(path)
            self._current_path = path
            self._total_pages = len(self._doc)
            self._current_page = 0
            self._search_results = []
            self._search_index = 0

            self._render_page()
            return True
        except Exception as e:
            print(f"Error opening PDF: {e}")
            return False

    def _render_page(self) -> None:
        """Render the current page."""
        if not self._doc or self._current_page >= self._total_pages:
            return

        page = self._doc[self._current_page]

        # Render at specified DPI
        zoom = self._render_dpi / 72.0
        mat = fitz.Matrix(zoom, zoom)

        # Handle rotation
        if page.rotation != 0:
            mat = page.derotation_matrix * mat

        pix = page.get_pixmap(matrix=mat)

        # Convert to base64
        img_data = pix.tobytes("png")
        b64 = base64.b64encode(img_data).decode()

        self._page_image.source = f'data:image/png;base64,{b64}'
        self._page_image.visible = True
        self._placeholder.visible = False

        # Update page label
        self._page_label.text = f'{self._current_page + 1} / {self._total_pages}'

    def go_to_page(self, page_num: int) -> None:
        """Go to a specific page (0-indexed)."""
        if self._doc and 0 <= page_num < self._total_pages:
            self._current_page = page_num
            self._render_page()

    def _first_page(self) -> None:
        """Go to first page."""
        self.go_to_page(0)

    def _last_page(self) -> None:
        """Go to last page."""
        if self._doc:
            self.go_to_page(self._total_pages - 1)

    def _prev_page(self) -> None:
        """Go to previous page."""
        if self._current_page > 0:
            self.go_to_page(self._current_page - 1)

    def _next_page(self) -> None:
        """Go to next page."""
        if self._current_page < self._total_pages - 1:
            self.go_to_page(self._current_page + 1)

    def _search(self) -> None:
        """Search for text in PDF."""
        if not self._doc:
            return

        search_text = self._search_input.value
        if not search_text:
            return

        self._search_results = []

        for page_num in range(self._total_pages):
            page = self._doc[page_num]
            matches = page.search_for(search_text)
            for rect in matches:
                self._search_results.append((page_num, rect))

        if self._search_results:
            self._search_index = 0
            page_num, _ = self._search_results[0]
            self.go_to_page(page_num)
            ui.notify(f'Found {len(self._search_results)} matches')
        else:
            ui.notify('No matches found', type='warning')

    def _prev_result(self) -> None:
        """Go to previous search result."""
        if not self._search_results:
            return

        self._search_index = (self._search_index - 1) % len(self._search_results)
        page_num, _ = self._search_results[self._search_index]
        self.go_to_page(page_num)

    def _next_result(self) -> None:
        """Go to next search result."""
        if not self._search_results:
            return

        self._search_index = (self._search_index + 1) % len(self._search_results)
        page_num, _ = self._search_results[self._search_index]
        self.go_to_page(page_num)

    def _take_snapshot(self) -> None:
        """Take a snapshot of the current page."""
        if not self._doc or not self._on_snapshot:
            return

        # Render at high DPI for snapshot
        page = self._doc[self._current_page]
        zoom = 300 / 72.0  # 300 DPI
        mat = fitz.Matrix(zoom, zoom)

        if page.rotation != 0:
            mat = page.derotation_matrix * mat

        pix = page.get_pixmap(matrix=mat)

        # Save to temp file
        import tempfile
        from datetime import datetime

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        temp_path = Path(tempfile.gettempdir()) / f"snapshot_{timestamp}.png"
        pix.save(str(temp_path))

        self._on_snapshot(str(temp_path))
        ui.notify('Snapshot captured')

    def search_text(self, text: str) -> Optional[Tuple[int, fitz.Rect]]:
        """Search for text and return first result."""
        if not self._doc or not text:
            return None

        for page_num in range(self._total_pages):
            page = self._doc[page_num]
            matches = page.search_for(text)
            if matches:
                self.go_to_page(page_num)
                return (page_num, matches[0])

        return None

    def close(self) -> None:
        """Close the PDF document."""
        if self._doc:
            self._doc.close()
            self._doc = None
        self._current_path = ""
        self._total_pages = 0
        self._current_page = 0

    @property
    def current_page(self) -> int:
        """Get current page number."""
        return self._current_page
