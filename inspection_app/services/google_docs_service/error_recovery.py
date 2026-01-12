"""
Export error handling and recovery.
"""

from typing import List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from ...core.inspection_item import InspectionItem


@dataclass
class ExportError:
    """Record of a single export failure."""
    item_id: str
    error_type: str
    error_message: str
    timestamp: datetime = field(default_factory=datetime.now)
    retry_count: int = 0
    is_recoverable: bool = True


@dataclass
class ExportResult:
    """Overall export operation result."""
    success: bool
    document_id: Optional[str]
    document_url: Optional[str]
    total_items: int
    successful_items: int
    failed_items: int
    errors: List[ExportError] = field(default_factory=list)


class ExportErrorRecovery:
    """Manage export error tracking and recovery."""

    def __init__(self, retry_limit: int = 3):
        self._errors: List[ExportError] = []
        self._retry_limit = retry_limit

    def record_error(
        self,
        item: InspectionItem,
        error_type: str,
        message: str
    ) -> None:
        """Record an export error for an item."""
        self._errors.append(ExportError(
            item_id=item.id,
            error_type=error_type,
            error_message=message
        ))

    def get_errors(self) -> List[ExportError]:
        """Get all recorded errors."""
        return list(self._errors)

    def get_recoverable_errors(self) -> List[ExportError]:
        """Get errors that can be retried."""
        return [
            e for e in self._errors
            if e.is_recoverable and e.retry_count < self._retry_limit
        ]

    def get_failed_item_ids(self) -> List[str]:
        """Get IDs of items that failed to export."""
        return [e.item_id for e in self._errors]

    def mark_retry(self, item_id: str) -> bool:
        """Mark an error for retry. Returns True if retry allowed."""
        for error in self._errors:
            if error.item_id == item_id:
                if error.retry_count >= self._retry_limit:
                    error.is_recoverable = False
                    return False
                error.retry_count += 1
                return True
        return False

    def clear_error(self, item_id: str) -> None:
        """Remove error record (after successful retry)."""
        self._errors = [e for e in self._errors if e.item_id != item_id]

    def clear_all(self) -> None:
        """Clear all error records."""
        self._errors.clear()

    def build_result(
        self,
        doc_id: Optional[str],
        total_items: int,
        successful_items: int
    ) -> ExportResult:
        """Build final export result object."""
        doc_url = None
        if doc_id:
            doc_url = f"https://docs.google.com/document/d/{doc_id}/edit"

        return ExportResult(
            success=len(self._errors) == 0,
            document_id=doc_id,
            document_url=doc_url,
            total_items=total_items,
            successful_items=successful_items,
            failed_items=len(self._errors),
            errors=list(self._errors)
        )
