"""
Background worker for Google Docs export.
"""

from typing import List, Optional
from pathlib import Path
from .base_worker import BaseWorker
from ..core.inspection_item import InspectionItem
from ..core.inspection_queue import InspectionQueue
from ..services.google_docs_service.auth_manager import GoogleAuthManager
from ..services.google_docs_service.doc_generator import GoogleDocGenerator
from ..services.google_docs_service.image_uploader import ImageUploader
from ..services.google_docs_service.error_recovery import (
    ExportErrorRecovery,
    ExportResult
)


class ExportWorker(BaseWorker):
    """Export approved items to Google Docs."""

    def __init__(
        self,
        queue: InspectionQueue,
        credentials_path: Path
    ):
        super().__init__()
        self._queue = queue
        self._credentials_path = credentials_path
        self._document_title: str = "Inspection Report"
        self._error_recovery = ExportErrorRecovery()

    def set_document_title(self, title: str) -> None:
        """Set the document title for export."""
        self._document_title = title

    def run(self) -> None:
        """Export all approved items to Google Doc."""
        self.signals.export_started.emit()
        self._error_recovery.clear_all()

        # Get approved items
        items = self._queue.get_approved_items()
        total = len(items)

        if total == 0:
            result = self._error_recovery.build_result(None, 0, 0)
            self.signals.export_completed.emit(result)
            return

        try:
            # Initialize services
            auth_manager = GoogleAuthManager(self._credentials_path)
            doc_generator = GoogleDocGenerator(auth_manager)
            image_uploader = ImageUploader(auth_manager)

            if self.is_cancelled():
                return

            # Create document
            doc_id, errors = doc_generator.create_report(
                title=self._document_title,
                items=items,
                image_uploader=image_uploader
            )

            # Track successful items
            successful = total - len(errors)

            # Record errors
            for error_msg in errors:
                # Parse item ID from error message
                parts = error_msg.split(":")
                if len(parts) >= 2:
                    item_id = parts[0].replace("Item ", "").strip()
                    item = self._queue.get_item_by_id(item_id)
                    if item:
                        self._error_recovery.record_error(
                            item,
                            "export_error",
                            error_msg
                        )

            # Emit progress for each item
            for i, item in enumerate(items):
                if item.id not in self._error_recovery.get_failed_item_ids():
                    self.signals.export_item_completed.emit(item.id)
                self.signals.export_progress.emit(i + 1, total)

            # Build and emit result
            result = self._error_recovery.build_result(doc_id, total, successful)
            self.signals.export_completed.emit(result)

        except Exception as e:
            self.signals.export_network_error.emit()
            result = self._error_recovery.build_result(None, total, 0)
            self.signals.export_completed.emit(result)

    def retry_failed_items(self) -> None:
        """Retry previously failed items."""
        failed_ids = self._error_recovery.get_failed_item_ids()
        items_to_retry: List[InspectionItem] = []

        for item_id in failed_ids:
            if self._error_recovery.mark_retry(item_id):
                item = self._queue.get_item_by_id(item_id)
                if item:
                    items_to_retry.append(item)

        if not items_to_retry:
            return

        # Re-run export for failed items
        self.signals.export_started.emit()

        try:
            auth_manager = GoogleAuthManager(self._credentials_path)
            doc_generator = GoogleDocGenerator(auth_manager)
            image_uploader = ImageUploader(auth_manager)

            doc_id, errors = doc_generator.create_report(
                title=f"{self._document_title} (Retry)",
                items=items_to_retry,
                image_uploader=image_uploader
            )

            # Clear successful items from error list
            for item in items_to_retry:
                if item.id not in [e.split(":")[0].replace("Item ", "").strip()
                                   for e in errors]:
                    self._error_recovery.clear_error(item.id)

            result = self._error_recovery.build_result(
                doc_id,
                len(items_to_retry),
                len(items_to_retry) - len(errors)
            )
            self.signals.export_completed.emit(result)

        except Exception as e:
            self.signals.export_network_error.emit()
