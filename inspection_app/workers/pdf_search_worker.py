"""
Background worker for PDF text search.
"""

from typing import Optional
from pathlib import Path
from .base_worker import BaseWorker
from ..services.pdf_service.pdf_reader import PDFReader
from ..services.pdf_service.text_searcher import PDFTextSearcher


class PDFSearchWorker(BaseWorker):
    """Async PDF search worker."""

    def __init__(self):
        super().__init__()
        self._pdf_path: Optional[Path] = None
        self._search_term: str = ""
        self._reader: Optional[PDFReader] = None

    def setup(self, pdf_path: str | Path, search_term: str) -> None:
        """Setup search parameters."""
        self._pdf_path = Path(pdf_path)
        self._search_term = search_term

    def run(self) -> None:
        """Execute PDF search."""
        if not self._pdf_path or not self._search_term:
            self.signals.search_error.emit("Search not configured")
            return

        self.signals.search_started.emit(self._search_term)

        try:
            self._reader = PDFReader()
            self._reader.open(self._pdf_path)

            if self.is_cancelled():
                return

            searcher = PDFTextSearcher(self._reader)
            results = searcher.search(self._search_term)

            if self.is_cancelled():
                return

            if results:
                # Emit first result
                first = results[0]
                self.signals.search_found.emit(
                    self._search_term,
                    first.page_num,
                    first.rect
                )
            else:
                self.signals.search_not_found.emit(self._search_term)

        except Exception as e:
            self.signals.search_error.emit(str(e))
        finally:
            if self._reader:
                self._reader.close()
                self._reader = None

    def search_sync(self, pdf_path: str | Path, search_term: str) -> list:
        """Synchronous search (for testing or direct use)."""
        reader = PDFReader()
        try:
            reader.open(pdf_path)
            searcher = PDFTextSearcher(reader)
            return searcher.search(search_term)
        finally:
            reader.close()
