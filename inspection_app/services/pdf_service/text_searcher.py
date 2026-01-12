"""
PDF text search implementation.
"""

from typing import Optional, List, Tuple
from dataclasses import dataclass
from .pdf_reader import PDFReader


@dataclass
class SearchResult:
    """Result of a text search."""
    term: str
    page_num: int
    rect: tuple  # (x0, y0, x1, y1)
    context: str = ""


class PDFTextSearcher:
    """Search for text within PDF documents."""

    def __init__(self, reader: PDFReader):
        self._reader = reader

    def search(self, term: str, max_results: int = 50) -> List[SearchResult]:
        """Search entire document for term."""
        results = []
        if not self._reader.is_open:
            return results

        for page_num in range(self._reader.page_count):
            rects = self._reader.search_page(page_num, term)
            for rect in rects:
                results.append(SearchResult(
                    term=term,
                    page_num=page_num,
                    rect=(rect.x0, rect.y0, rect.x1, rect.y1)
                ))
                if len(results) >= max_results:
                    return results
        return results

    def search_first(self, term: str) -> Optional[SearchResult]:
        """Find first occurrence of term."""
        results = self.search(term, max_results=1)
        return results[0] if results else None

    def verify_reference_exists(self, reference: str) -> Tuple[bool, Optional[int]]:
        """Check if reference exists, return (exists, page_num)."""
        result = self.search_first(reference)
        if result:
            return (True, result.page_num)
        return (False, None)

    def search_page_only(self, page_num: int, term: str) -> List[SearchResult]:
        """Search only on specific page."""
        results = []
        rects = self._reader.search_page(page_num, term)
        for rect in rects:
            results.append(SearchResult(
                term=term,
                page_num=page_num,
                rect=(rect.x0, rect.y0, rect.x1, rect.y1)
            ))
        return results

    def get_context(self, page_num: int, rect: tuple, chars: int = 50) -> str:
        """Get text context around a search result."""
        text = self._reader.get_text(page_num)
        # Simple context extraction - just return nearby text
        return text[:200] if text else ""
