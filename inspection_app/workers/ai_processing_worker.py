"""
Background worker for batch AI processing.
"""

import time
from typing import List, Dict, Optional
from pathlib import Path
from .base_worker import BaseWorker
from ..core.inspection_item import InspectionItem, ItemStatus, SearchStatus
from ..core.inspection_queue import InspectionQueue
from ..core.exceptions import AIRateLimitError
from ..services.ai_service.gemini_client import GeminiClient
from ..services.ai_service.context_cache import ContextCacheManager
from ..services.ai_service.prompt_templates import (
    SYSTEM_PROMPT_CODE_ANALYSIS,
    build_analysis_prompt
)
from ..services.ai_service.response_parser import parse_analysis_response, extract_search_term
from ..services.pdf_service.pdf_reader import PDFReader
from ..services.pdf_service.text_searcher import PDFTextSearcher


class AIProcessingWorker(BaseWorker):
    """Process queue items through Gemini AI."""

    def __init__(
        self,
        queue: InspectionQueue,
        gemini_client: GeminiClient,
        cache_manager: ContextCacheManager,
        pdf_base_path: Path
    ):
        super().__init__()
        self._queue = queue
        self._client = gemini_client
        self._cache = cache_manager
        self._pdf_base = pdf_base_path
        self._retry_delay = 5
        self._max_retries = 3

    def run(self) -> None:
        """Process all pending items grouped by chapter."""
        self.signals.ai_started.emit()

        pending_items = self._queue.get_pending_items()
        total = len(pending_items)

        if total == 0:
            self.signals.ai_completed.emit()
            return

        # Group by chapter for cache efficiency
        by_chapter = self._group_by_chapter(pending_items)

        processed = 0
        for chapter_file, items in by_chapter.items():
            if self.is_cancelled():
                break

            # Get or create cache for this chapter
            pdf_path = self._pdf_base / chapter_file
            cache_id = self._cache.get_or_create_cache(str(pdf_path))

            for item in items:
                if self.is_cancelled():
                    break

                self.check_pause()
                self.signals.ai_item_started.emit(item.id)

                try:
                    self._process_item(item, cache_id, pdf_path)
                    processed += 1
                    self.signals.ai_progress.emit(processed, total)
                    self.signals.ai_item_completed.emit(item.id, item)
                except AIRateLimitError as e:
                    self._handle_rate_limit(e.wait_seconds)
                except Exception as e:
                    item.status = ItemStatus.ERROR
                    item.error_message = str(e)
                    self._queue.update_item(item)
                    self.signals.ai_item_error.emit(item.id, str(e))

        self.signals.ai_completed.emit()

    def _process_item(
        self,
        item: InspectionItem,
        cache_id: Optional[str],
        pdf_path: Path
    ) -> None:
        """Process single item through AI and pre-validate."""
        item.status = ItemStatus.PROCESSING
        self._queue.update_item(item)

        # Build prompt
        prompt = build_analysis_prompt(item.user_description, item.user_location)

        # Call Gemini
        response = self._client.generate_with_image(
            system_prompt=SYSTEM_PROMPT_CODE_ANALYSIS,
            user_prompt=prompt,
            image_path=item.photo_edited_path or item.photo_original_path,
            cached_content_id=cache_id
        )

        # Parse response
        result = parse_analysis_response(response)

        # Update item with AI results
        item.llm_match_type = result.match_type
        item.llm_suggested_term = result.reference
        item.llm_reasoning = result.reasoning
        item.llm_confidence = result.confidence

        # Pre-validate: search PDF for the suggested term
        if result.is_valid:
            search_term = extract_search_term(result.reference, result.match_type)
            item.active_search_term = search_term
            self._verify_in_pdf(item, pdf_path, search_term)
        else:
            item.search_status = SearchStatus.NOT_FOUND

        item.status = ItemStatus.REVIEW_READY
        self._queue.update_item(item)

    def _verify_in_pdf(
        self,
        item: InspectionItem,
        pdf_path: Path,
        search_term: str
    ) -> None:
        """Verify reference exists in PDF."""
        reader = PDFReader()
        try:
            reader.open(pdf_path)
            searcher = PDFTextSearcher(reader)
            exists, page_num = searcher.verify_reference_exists(search_term)

            if exists:
                item.search_status = SearchStatus.FOUND
                item.search_result_page = page_num
                item.current_page_view = page_num or 0
            else:
                item.search_status = SearchStatus.NOT_FOUND
        finally:
            reader.close()

    def _group_by_chapter(
        self,
        items: List[InspectionItem]
    ) -> Dict[str, List[InspectionItem]]:
        """Group items by chapter file for cache efficiency."""
        grouped: Dict[str, List[InspectionItem]] = {}
        for item in items:
            chapter = item.selected_chapter_file
            if chapter not in grouped:
                grouped[chapter] = []
            grouped[chapter].append(item)
        return grouped

    def _handle_rate_limit(self, wait_seconds: int) -> None:
        """Handle rate limiting with pause."""
        self.signals.ai_rate_limited.emit(wait_seconds)
        for _ in range(wait_seconds):
            if self.is_cancelled():
                return
            time.sleep(1)
