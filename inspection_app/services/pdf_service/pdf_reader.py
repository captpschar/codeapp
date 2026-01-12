"""
PyMuPDF wrapper for PDF operations.
"""

from pathlib import Path
from typing import Optional
import fitz  # PyMuPDF


class PDFReader:
    """PDF document reader using PyMuPDF."""

    def __init__(self):
        self._doc: Optional[fitz.Document] = None
        self._path: Optional[Path] = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def open(self, pdf_path: str | Path) -> None:
        """Open PDF file."""
        self.close()
        path = Path(pdf_path)
        if not path.exists():
            raise FileNotFoundError(f"PDF not found: {path}")
        self._doc = fitz.open(str(path))
        self._path = path

    def close(self) -> None:
        """Close current PDF."""
        if self._doc:
            self._doc.close()
            self._doc = None
            self._path = None

    @property
    def is_open(self) -> bool:
        """Check if document is open."""
        return self._doc is not None

    @property
    def page_count(self) -> int:
        """Get total page count."""
        if self._doc:
            return len(self._doc)
        return 0

    @property
    def path(self) -> Optional[Path]:
        """Get current file path."""
        return self._path

    def get_page(self, page_num: int) -> Optional[fitz.Page]:
        """Get page by number (0-indexed)."""
        if self._doc and 0 <= page_num < len(self._doc):
            return self._doc[page_num]
        return None

    def get_page_size(self, page_num: int) -> tuple[float, float]:
        """Get page dimensions (width, height)."""
        page = self.get_page(page_num)
        if page:
            rect = page.rect
            return (rect.width, rect.height)
        return (0, 0)

    def get_text(self, page_num: int) -> str:
        """Extract text from page."""
        page = self.get_page(page_num)
        if page:
            return page.get_text()
        return ""

    def search_page(self, page_num: int, term: str) -> list[fitz.Rect]:
        """Search for term on page, return list of rectangles."""
        page = self.get_page(page_num)
        if page:
            return page.search_for(term)
        return []
