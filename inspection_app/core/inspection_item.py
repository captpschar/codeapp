"""
Central data model for inspection items.
"""

from dataclasses import dataclass, field
from typing import Optional
from enum import Enum
import uuid
from datetime import datetime


class ItemStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    REVIEW_READY = "review_ready"
    APPROVED = "approved"
    EXPORTED = "exported"
    ERROR = "error"


class MatchType(Enum):
    SECTION = "Section"
    TABLE = "Table"
    FIGURE = "Figure"


class SearchStatus(Enum):
    NOT_SEARCHED = "not_searched"
    FOUND = "found"
    NOT_FOUND = "not_found"
    MANUAL_OVERRIDE = "manual_override"


class ConfidenceLevel(Enum):
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


@dataclass
class InspectionItem:
    """Central data object for a single inspection finding."""

    # Identity
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=datetime.now)

    # Status
    status: ItemStatus = ItemStatus.PENDING
    error_message: Optional[str] = None

    # File Paths
    photo_original_path: str = ""
    photo_edited_path: str = ""
    snapshot_path: Optional[str] = None

    # User Inputs (Phase 1)
    user_description: str = ""
    user_location: str = ""
    selected_code_version: str = ""
    selected_code_folder: str = ""  # Name of the code folder
    selected_chapter_file: str = ""

    # AI Outputs (Phase 2)
    llm_match_type: Optional[MatchType] = None
    llm_suggested_term: str = ""
    llm_reasoning: str = ""
    llm_confidence: Optional[ConfidenceLevel] = None

    # New AI outputs
    ai_code_reference: str = ""
    ai_violation_description: str = ""
    ai_search_terms: list = field(default_factory=list)
    ai_confidence: float = 0.0

    # Verification State (Phase 3)
    search_status: SearchStatus = SearchStatus.NOT_SEARCHED
    active_search_term: str = ""
    current_page_view: int = 0
    search_result_page: Optional[int] = None
    search_result_rect: Optional[tuple] = None

    # Final Decision
    final_approval: bool = False
    approved_at: Optional[datetime] = None

    # Export (Phase 4)
    google_doc_url: Optional[str] = None
    exported_at: Optional[datetime] = None

    def to_dict(self) -> dict:
        """Serialize for JSON storage."""
        return {
            "id": self.id,
            "created_at": self.created_at.isoformat(),
            "status": self.status.value,
            "error_message": self.error_message,
            "photo_original_path": self.photo_original_path,
            "photo_edited_path": self.photo_edited_path,
            "snapshot_path": self.snapshot_path,
            "user_description": self.user_description,
            "user_location": self.user_location,
            "selected_code_version": self.selected_code_version,
            "selected_code_folder": self.selected_code_folder,
            "selected_chapter_file": self.selected_chapter_file,
            "llm_match_type": self.llm_match_type.value if self.llm_match_type else None,
            "llm_suggested_term": self.llm_suggested_term,
            "llm_reasoning": self.llm_reasoning,
            "llm_confidence": self.llm_confidence.value if self.llm_confidence else None,
            "ai_code_reference": self.ai_code_reference,
            "ai_violation_description": self.ai_violation_description,
            "ai_search_terms": self.ai_search_terms,
            "ai_confidence": self.ai_confidence,
            "search_status": self.search_status.value,
            "active_search_term": self.active_search_term,
            "current_page_view": self.current_page_view,
            "search_result_page": self.search_result_page,
            "search_result_rect": self.search_result_rect,
            "final_approval": self.final_approval,
            "approved_at": self.approved_at.isoformat() if self.approved_at else None,
            "google_doc_url": self.google_doc_url,
            "exported_at": self.exported_at.isoformat() if self.exported_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "InspectionItem":
        """Deserialize from JSON storage."""
        item = cls()
        item.id = data["id"]
        item.created_at = datetime.fromisoformat(data["created_at"])
        item.status = ItemStatus(data["status"])
        item.error_message = data.get("error_message")
        item.photo_original_path = data.get("photo_original_path", "")
        item.photo_edited_path = data.get("photo_edited_path", "")
        item.snapshot_path = data.get("snapshot_path")
        item.user_description = data.get("user_description", "")
        item.user_location = data.get("user_location", "")
        item.selected_code_version = data.get("selected_code_version", "")
        item.selected_code_folder = data.get("selected_code_folder", "")
        item.selected_chapter_file = data.get("selected_chapter_file", "")
        if data.get("llm_match_type"):
            item.llm_match_type = MatchType(data["llm_match_type"])
        item.llm_suggested_term = data.get("llm_suggested_term", "")
        item.llm_reasoning = data.get("llm_reasoning", "")
        if data.get("llm_confidence"):
            item.llm_confidence = ConfidenceLevel(data["llm_confidence"])
        item.ai_code_reference = data.get("ai_code_reference", "")
        item.ai_violation_description = data.get("ai_violation_description", "")
        item.ai_search_terms = data.get("ai_search_terms", [])
        item.ai_confidence = data.get("ai_confidence", 0.0)
        item.search_status = SearchStatus(data.get("search_status", "not_searched"))
        item.active_search_term = data.get("active_search_term", "")
        item.current_page_view = data.get("current_page_view", 0)
        item.search_result_page = data.get("search_result_page")
        item.search_result_rect = data.get("search_result_rect")
        item.final_approval = data.get("final_approval", False)
        if data.get("approved_at"):
            item.approved_at = datetime.fromisoformat(data["approved_at"])
        item.google_doc_url = data.get("google_doc_url")
        if data.get("exported_at"):
            item.exported_at = datetime.fromisoformat(data["exported_at"])
        return item
