# Program Architecture Document: Inspection Photo Review & Code Matching App (v3.0)

**Version:** 3.0  
**Purpose:** Complete technical architecture enabling independent parallel development  
**Target Audience:** Software developers implementing individual modules

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [Technical Stack](#2-technical-stack)
3. [Project File Structure](#3-project-file-structure)
4. [Data Structures & Schemas](#4-data-structures--schemas)
5. [Module Specifications](#5-module-specifications)
6. [Service Interface Contracts](#6-service-interface-contracts)
7. [Threading & Concurrency Model](#7-threading--concurrency-model)
8. [State Machine Definition](#8-state-machine-definition)
9. [UI Component Specifications](#9-ui-component-specifications)
10. [Error Handling Framework](#10-error-handling-framework)
11. [Configuration Management](#11-configuration-management)
12. [Integration Patterns](#12-integration-patterns)
13. [Testing Strategy](#13-testing-strategy)

---

## 1. System Overview

### 1.1 Architecture Pattern

The application uses a **Model-View-Controller (MVC)** pattern with **Worker Threads** for background processing:

```
┌─────────────────────────────────────────────────────────────────────┐
│                           GUI THREAD                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────┐  │
│  │   Views      │  │  Controllers │  │   State Manager          │  │
│  │  (PyQt6)     │◄─┤  (Handlers)  │◄─┤  (InspectionQueue)       │  │
│  └──────────────┘  └──────────────┘  └──────────────────────────┘  │
│         ▲                                        │                   │
│         │              PyQt Signals              │                   │
│         └────────────────────────────────────────┘                   │
└─────────────────────────────────────────────────────────────────────┘
                              │ Signals
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        WORKER THREADS                                │
│  ┌──────────────────┐  ┌──────────────────┐  ┌─────────────────┐   │
│  │  AI Processing   │  │   PDF Search     │  │  Export Worker  │   │
│  │  Worker          │  │   Worker         │  │                 │   │
│  └──────────────────┘  └──────────────────┘  └─────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         SERVICES LAYER                               │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────────┐    │
│  │ AI       │  │ PDF      │  │ Image    │  │ Google Docs      │    │
│  │ Service  │  │ Service  │  │ Service  │  │ Service          │    │
│  └──────────┘  └──────────┘  └──────────┘  └──────────────────┘    │
└─────────────────────────────────────────────────────────────────────┘
```

### 1.2 Phase Overview

| Phase | Thread | Primary Components | Output |
|-------|--------|-------------------|--------|
| Phase 1: Triage | GUI | ImageEditor, MetadataForm | InspectionItem added to queue |
| Phase 2: Batch | Worker | AIProcessingWorker, GeminiService | Items updated with AI suggestions |
| Phase 3: Verify | GUI | DashboardWidget, PDFViewer, SnapshotTool | Items approved with snapshots |
| Phase 4: Export | Worker | ExportWorker, GoogleDocsService | Google Doc generated |

---

## 2. Technical Stack

### 2.1 Required Dependencies

```
# requirements.txt
PyQt6==6.6.1
PyMuPDF==1.23.8
Pillow==10.2.0
google-genai==0.4.0
google-api-python-client==2.116.0
google-auth-oauthlib==1.2.0
pydantic==2.5.3
```

### 2.2 AI Configuration

| Setting | Value | Notes |
|---------|-------|-------|
| Model | `gemini-2.0-pro` | Use Gemini 2.0 Pro (latest stable) |
| SDK | `google-genai` | Official Google GenAI SDK |
| Thinking | `thinking_config={"thinking_budget": 10000}` | Extended reasoning for code analysis |
| Context Caching | Enabled | Cache PDF chapters to reduce API calls |

### 2.3 System Requirements

- Python 3.10+
- 8GB RAM minimum (PDF rendering)
- Network access for Gemini API and Google Docs API

---

## 3. Project File Structure

```
inspection_app/
│
├── main.py                          # Entry point (50 lines max)
├── requirements.txt
├── settings.json                    # User configuration
│
├── core/                            # Core application logic
│   ├── __init__.py
│   ├── app_state.py                 # Global state container (100 lines)
│   ├── inspection_item.py           # Data model (80 lines)
│   ├── inspection_queue.py          # Queue manager (120 lines)
│   ├── state_machine.py             # Status transitions (60 lines)
│   ├── config_manager.py            # Settings loader (80 lines)
│   └── exceptions.py                # Custom exceptions (40 lines)
│
├── services/                        # External service interfaces
│   ├── __init__.py
│   ├── ai_service/
│   │   ├── __init__.py
│   │   ├── gemini_client.py         # API client wrapper (100 lines)
│   │   ├── context_cache.py         # PDF caching logic (80 lines)
│   │   ├── prompt_templates.py      # All prompts (60 lines)
│   │   └── response_parser.py       # Parse AI responses (70 lines)
│   │
│   ├── pdf_service/
│   │   ├── __init__.py
│   │   ├── pdf_reader.py            # PyMuPDF wrapper (100 lines)
│   │   ├── text_searcher.py         # Search implementation (80 lines)
│   │   ├── page_renderer.py         # Render pages to images (70 lines)
│   │   └── coordinate_mapper.py     # Map search to coords (60 lines)
│   │
│   ├── image_service/
│   │   ├── __init__.py
│   │   ├── image_editor.py          # Crop, brighten, rotate (100 lines)
│   │   ├── snapshot_creator.py      # PDF region capture (60 lines)
│   │   └── file_manager.py          # Save/load images (50 lines)
│   │
│   └── google_docs_service/
│       ├── __init__.py
│       ├── auth_manager.py          # OAuth flow (80 lines)
│       ├── doc_generator.py         # Create documents (120 lines)
│       ├── image_uploader.py        # Upload images to Drive (70 lines)
│       └── error_recovery.py        # Partial failure logic (60 lines)
│
├── workers/                         # Background thread workers
│   ├── __init__.py
│   ├── base_worker.py               # QThread base class (60 lines)
│   ├── ai_processing_worker.py      # Batch AI processing (150 lines)
│   ├── pdf_search_worker.py         # Async PDF search (80 lines)
│   └── export_worker.py             # Google Docs export (100 lines)
│
├── ui/                              # PyQt6 UI components
│   ├── __init__.py
│   ├── main_window.py               # Main window shell (100 lines)
│   ├── phase_navigator.py           # Phase switching logic (60 lines)
│   │
│   ├── phase1/                      # Triage phase UI
│   │   ├── __init__.py
│   │   ├── triage_widget.py         # Main container (80 lines)
│   │   ├── image_viewer.py          # Photo display/edit (120 lines)
│   │   ├── edit_toolbar.py          # Crop/brightness tools (80 lines)
│   │   ├── metadata_form.py         # Description/location (100 lines)
│   │   └── queue_panel.py           # Queue status display (70 lines)
│   │
│   ├── phase2/                      # Batch processing UI
│   │   ├── __init__.py
│   │   ├── processing_widget.py     # Main container (60 lines)
│   │   ├── progress_panel.py        # Progress bar + status (80 lines)
│   │   └── item_status_list.py      # Per-item status icons (70 lines)
│   │
│   ├── phase3/                      # Verification dashboard UI
│   │   ├── __init__.py
│   │   ├── dashboard_widget.py      # Three-pane layout (100 lines)
│   │   ├── photo_panel.py           # Edited photo display (60 lines)
│   │   ├── data_panel.py            # AI results + controls (120 lines)
│   │   ├── search_bar.py            # Active search bar (80 lines)
│   │   ├── pdf_viewer.py            # PDF display widget (150 lines)
│   │   ├── rubber_band_tool.py      # Snapshot selection (100 lines)
│   │   └── snapshot_thumbnail.py    # Snapshot preview (50 lines)
│   │
│   ├── phase4/                      # Export UI
│   │   ├── __init__.py
│   │   ├── export_widget.py         # Export controls (80 lines)
│   │   ├── preflight_checker.py     # Approval validation (60 lines)
│   │   └── export_progress.py       # Export status display (70 lines)
│   │
│   └── common/                      # Shared UI components
│       ├── __init__.py
│       ├── chapter_selector.py      # PDF chapter dropdown (60 lines)
│       ├── status_badge.py          # Status indicator widget (40 lines)
│       ├── error_dialog.py          # Error display modal (50 lines)
│       └── confirmation_dialog.py   # Confirmation prompts (40 lines)
│
├── signals/                         # PyQt signal definitions
│   ├── __init__.py
│   ├── worker_signals.py            # Worker thread signals (50 lines)
│   ├── ui_signals.py                # UI event signals (40 lines)
│   └── state_signals.py             # State change signals (40 lines)
│
└── tests/                           # Unit and integration tests
    ├── __init__.py
    ├── test_inspection_item.py
    ├── test_state_machine.py
    ├── test_gemini_client.py
    ├── test_pdf_searcher.py
    ├── test_image_editor.py
    └── test_export_worker.py
```

**File Size Guidelines:**
- Maximum 150 lines per file
- Each file handles ONE responsibility
- Complex operations split across multiple files
- Easy for LLM context windows

---

## 4. Data Structures & Schemas

### 4.1 InspectionItem (core/inspection_item.py)

```python
from dataclasses import dataclass, field
from typing import Optional, Literal
from enum import Enum
import uuid
from datetime import datetime

class ItemStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    REVIEW_READY = "review_ready"
    APPROVED = "approved"
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
    selected_code_version: str = ""  # e.g., "IRC_2021"
    selected_chapter_file: str = ""  # e.g., "IRC_2021_Ch3.pdf"
    
    # AI Outputs (Phase 2)
    llm_match_type: Optional[MatchType] = None
    llm_suggested_term: str = ""
    llm_reasoning: str = ""
    llm_confidence: Optional[ConfidenceLevel] = None
    
    # Verification State (Phase 3)
    search_status: SearchStatus = SearchStatus.NOT_SEARCHED
    active_search_term: str = ""
    current_page_view: int = 0
    search_result_page: Optional[int] = None
    search_result_rect: Optional[tuple[float, float, float, float]] = None
    
    # Final Decision
    final_approval: bool = False
    approved_at: Optional[datetime] = None
    
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
            "selected_chapter_file": self.selected_chapter_file,
            "llm_match_type": self.llm_match_type.value if self.llm_match_type else None,
            "llm_suggested_term": self.llm_suggested_term,
            "llm_reasoning": self.llm_reasoning,
            "llm_confidence": self.llm_confidence.value if self.llm_confidence else None,
            "search_status": self.search_status.value,
            "active_search_term": self.active_search_term,
            "current_page_view": self.current_page_view,
            "search_result_page": self.search_result_page,
            "search_result_rect": self.search_result_rect,
            "final_approval": self.final_approval,
            "approved_at": self.approved_at.isoformat() if self.approved_at else None,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "InspectionItem":
        """Deserialize from JSON storage."""
        item = cls()
        item.id = data["id"]
        item.created_at = datetime.fromisoformat(data["created_at"])
        item.status = ItemStatus(data["status"])
        item.error_message = data.get("error_message")
        item.photo_original_path = data["photo_original_path"]
        item.photo_edited_path = data["photo_edited_path"]
        item.snapshot_path = data.get("snapshot_path")
        item.user_description = data["user_description"]
        item.user_location = data["user_location"]
        item.selected_code_version = data["selected_code_version"]
        item.selected_chapter_file = data["selected_chapter_file"]
        if data.get("llm_match_type"):
            item.llm_match_type = MatchType(data["llm_match_type"])
        item.llm_suggested_term = data.get("llm_suggested_term", "")
        item.llm_reasoning = data.get("llm_reasoning", "")
        if data.get("llm_confidence"):
            item.llm_confidence = ConfidenceLevel(data["llm_confidence"])
        item.search_status = SearchStatus(data.get("search_status", "not_searched"))
        item.active_search_term = data.get("active_search_term", "")
        item.current_page_view = data.get("current_page_view", 0)
        item.search_result_page = data.get("search_result_page")
        item.search_result_rect = data.get("search_result_rect")
        item.final_approval = data.get("final_approval", False)
        if data.get("approved_at"):
            item.approved_at = datetime.fromisoformat(data["approved_at"])
        return item
```

### 4.2 Configuration Schema (settings.json)

```json
{
  "gemini_api_key": "your-api-key-here",
  "google_docs_credentials_path": "./credentials.json",
  "code_book_directory": "./code_books/",
  "output_directory": "./output/",
  "ai_settings": {
    "model_name": "gemini-2.0-pro",
    "thinking_budget": 10000,
    "max_retries": 3,
    "retry_delay_seconds": 5,
    "cache_ttl_minutes": 60
  },
  "pdf_settings": {
    "render_dpi": 150,
    "snapshot_dpi": 300
  },
  "ui_settings": {
    "default_window_width": 1400,
    "default_window_height": 900,
    "auto_save_interval_seconds": 30
  }
}
```

### 4.3 Queue State Persistence (core/inspection_queue.py)

```python
from typing import List, Optional, Callable
from pathlib import Path
import json
from .inspection_item import InspectionItem, ItemStatus

class InspectionQueue:
    """Thread-safe queue manager with persistence."""
    
    def __init__(self, persistence_path: Optional[Path] = None):
        self._items: List[InspectionItem] = []
        self._persistence_path = persistence_path
        self._change_callbacks: List[Callable] = []
    
    def add_item(self, item: InspectionItem) -> None:
        """Add item and persist immediately."""
        self._items.append(item)
        self._notify_change()
        self._persist()
    
    def get_item_by_id(self, item_id: str) -> Optional[InspectionItem]:
        """Retrieve item by UUID."""
        for item in self._items:
            if item.id == item_id:
                return item
        return None
    
    def get_pending_items(self) -> List[InspectionItem]:
        """Get all items ready for AI processing."""
        return [i for i in self._items if i.status == ItemStatus.PENDING]
    
    def get_items_by_status(self, status: ItemStatus) -> List[InspectionItem]:
        """Filter items by status."""
        return [i for i in self._items if i.status == status]
    
    def get_items_by_chapter(self, chapter_file: str) -> List[InspectionItem]:
        """Group items by PDF chapter for batch processing."""
        return [i for i in self._items if i.selected_chapter_file == chapter_file]
    
    def update_item(self, item: InspectionItem) -> None:
        """Update item in place and persist."""
        for idx, existing in enumerate(self._items):
            if existing.id == item.id:
                self._items[idx] = item
                break
        self._notify_change()
        self._persist()
    
    def get_all_items(self) -> List[InspectionItem]:
        """Return all items (copy to prevent mutation)."""
        return list(self._items)
    
    def get_approved_items(self) -> List[InspectionItem]:
        """Get items ready for export."""
        return [i for i in self._items if i.final_approval]
    
    def get_unapproved_items(self) -> List[InspectionItem]:
        """Get items needing approval before export."""
        return [i for i in self._items if not i.final_approval]
    
    def count(self) -> int:
        """Total item count."""
        return len(self._items)
    
    def count_by_status(self, status: ItemStatus) -> int:
        """Count items with specific status."""
        return len(self.get_items_by_status(status))
    
    def register_change_callback(self, callback: Callable) -> None:
        """Register callback for queue changes (for UI updates)."""
        self._change_callbacks.append(callback)
    
    def _notify_change(self) -> None:
        """Notify all registered callbacks."""
        for callback in self._change_callbacks:
            callback()
    
    def _persist(self) -> None:
        """Save queue state to disk."""
        if self._persistence_path:
            data = [item.to_dict() for item in self._items]
            with open(self._persistence_path, 'w') as f:
                json.dump(data, f, indent=2)
    
    def load_from_disk(self) -> None:
        """Restore queue from persistence file."""
        if self._persistence_path and self._persistence_path.exists():
            with open(self._persistence_path) as f:
                data = json.load(f)
            self._items = [InspectionItem.from_dict(d) for d in data]
            self._notify_change()
    
    def clear(self) -> None:
        """Clear all items (with confirmation in UI)."""
        self._items = []
        self._notify_change()
        self._persist()
```
### 5.3 Image Service Module

#### image_editor.py

```python
"""
Image editing operations.
Handles: Crop, rotate, brightness, contrast.
"""

from PIL import Image, ImageEnhance
from pathlib import Path
from typing import Tuple, Optional

class ImageEditor:
    """Image editing operations using PIL."""
    
    def __init__(self):
        self._current_image: Optional[Image.Image] = None
        self._original_image: Optional[Image.Image] = None
        self._source_path: Optional[Path] = None
    
    def load(self, image_path: str | Path) -> None:
        """Load image from file."""
        path = Path(image_path)
        if not path.exists():
            raise FileNotFoundError(f"Image not found: {path}")
        
        self._original_image = Image.open(path).convert("RGB")
        self._current_image = self._original_image.copy()
        self._source_path = path
    
    def reset(self) -> None:
        """Reset to original image."""
        if self._original_image:
            self._current_image = self._original_image.copy()
    
    def crop(self, box: Tuple[int, int, int, int]) -> None:
        """
        Crop image to region.
        
        Args:
            box: (left, top, right, bottom) in pixels
        """
        if self._current_image:
            self._current_image = self._current_image.crop(box)
    
    def rotate(self, degrees: float, expand: bool = True) -> None:
        """Rotate image by degrees (counter-clockwise)."""
        if self._current_image:
            self._current_image = self._current_image.rotate(
                degrees, expand=expand, resample=Image.BICUBIC
            )
    
    def adjust_brightness(self, factor: float) -> None:
        """
        Adjust brightness.
        
        Args:
            factor: 1.0 = original, < 1.0 darker, > 1.0 brighter
        """
        if self._current_image:
            enhancer = ImageEnhance.Brightness(self._current_image)
            self._current_image = enhancer.enhance(factor)
    
    def adjust_contrast(self, factor: float) -> None:
        """
        Adjust contrast.
        
        Args:
            factor: 1.0 = original, < 1.0 less contrast, > 1.0 more contrast
        """
        if self._current_image:
            enhancer = ImageEnhance.Contrast(self._current_image)
            self._current_image = enhancer.enhance(factor)
    
    def get_current_image(self) -> Optional[Image.Image]:
        """Get current edited image."""
        return self._current_image
    
    def get_dimensions(self) -> Tuple[int, int]:
        """Get current image dimensions (width, height)."""
        if self._current_image:
            return self._current_image.size
        return (0, 0)
    
    def save(self, output_path: str | Path, quality: int = 95) -> Path:
        """
        Save current image to file.
        
        Args:
            output_path: Destination path
            quality: JPEG quality (1-100)
            
        Returns:
            Path to saved file
        """
        if not self._current_image:
            raise ValueError("No image loaded")
        
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        self._current_image.save(str(path), quality=quality)
        return path
```

#### snapshot_creator.py

```python
"""
Create snapshots from PDF regions.
Handles: Capture, naming, immediate save.
"""

from pathlib import Path
from typing import Tuple, Optional
from PIL import Image
from datetime import datetime

class SnapshotCreator:
    """Create and save PDF region snapshots."""
    
    def __init__(self, page_renderer: "PDFPageRenderer", snapshot_dpi: int = 300):
        self._renderer = page_renderer
        self._dpi = snapshot_dpi
    
    def create_snapshot(
        self,
        page_num: int,
        rect: Tuple[float, float, float, float],
        output_dir: Path,
        base_filename: str
    ) -> Optional[Path]:
        """
        Create snapshot from PDF region and save immediately.
        
        Args:
            page_num: Page number (0-indexed)
            rect: PDF coordinates (x0, y0, x1, y1)
            output_dir: Directory to save snapshot
            base_filename: Original photo filename for naming
            
        Returns:
            Path to saved snapshot, or None on failure
            
        Note:
            Saves IMMEDIATELY per spec requirement.
        """
        # Render the region
        img = self._renderer.render_page_region(page_num, rect, self._dpi)
        if not img:
            return None
        
        # Generate output filename
        snapshot_name = self._generate_snapshot_name(base_filename)
        output_path = output_dir / snapshot_name
        
        # Ensure directory exists
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Save immediately (per spec: "saved directly to the source folder immediately")
        img.save(str(output_path), quality=95)
        
        return output_path
    
    def _generate_snapshot_name(self, base_filename: str) -> str:
        """
        Generate snapshot filename per spec convention.
        
        Format: {original_filename}_code_snap.png
        """
        # Remove extension from base filename
        stem = Path(base_filename).stem
        return f"{stem}_code_snap.png"
```

#### file_manager.py

```python
"""
Image file management utilities.
Handles: Path generation, file operations, cleanup.
"""

from pathlib import Path
from typing import Optional, List
import shutil

class ImageFileManager:
    """Manage image file paths and operations."""
    
    def __init__(self, base_output_dir: Path):
        self._base_dir = base_output_dir
        self._edited_subdir = "edited"
    
    def get_edited_path(self, original_path: str | Path) -> Path:
        """
        Generate path for edited version of image.
        
        Args:
            original_path: Path to original image
            
        Returns:
            Path in edited subdirectory
        """
        original = Path(original_path)
        edited_dir = original.parent / self._edited_subdir
        
        # Add suffix to filename
        new_name = f"{original.stem}_crop{original.suffix}"
        return edited_dir / new_name
    
    def ensure_edited_dir(self, original_path: str | Path) -> Path:
        """Create edited subdirectory if needed."""
        original = Path(original_path)
        edited_dir = original.parent / self._edited_subdir
        edited_dir.mkdir(parents=True, exist_ok=True)
        return edited_dir
    
    def copy_original(self, source: str | Path, dest_dir: Path) -> Path:
        """Copy original image to destination."""
        source_path = Path(source)
        dest_path = dest_dir / source_path.name
        shutil.copy2(source_path, dest_path)
        return dest_path
    
    def list_images_in_dir(self, directory: Path) -> List[Path]:
        """List all image files in directory."""
        extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}
        images = []
        for ext in extensions:
            images.extend(directory.glob(f"*{ext}"))
            images.extend(directory.glob(f"*{ext.upper()}"))
        return sorted(images)
    
    def file_exists(self, path: str | Path) -> bool:
        """Check if file exists."""
        return Path(path).exists()
    
    def delete_if_exists(self, path: str | Path) -> bool:
        """Delete file if it exists, return True if deleted."""
        p = Path(path)
        if p.exists():
            p.unlink()
            return True
        return False
```

### 5.4 Google Docs Service Module

#### auth_manager.py

```python
"""
Google OAuth2 authentication management.
Handles: Token storage, refresh, initial auth flow.
"""

from pathlib import Path
from typing import Optional
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import json

SCOPES = [
    'https://www.googleapis.com/auth/documents',
    'https://www.googleapis.com/auth/drive.file'
]

class GoogleAuthManager:
    """Manage Google API authentication."""
    
    def __init__(self, credentials_path: Path, token_path: Optional[Path] = None):
        self._credentials_path = credentials_path
        self._token_path = token_path or credentials_path.parent / "token.json"
        self._credentials: Optional[Credentials] = None
    
    def get_credentials(self) -> Credentials:
        """
        Get valid credentials, prompting for auth if needed.
        
        Returns:
            Valid Google credentials
        """
        # Try to load existing token
        if self._token_path.exists():
            self._credentials = Credentials.from_authorized_user_file(
                str(self._token_path), SCOPES
            )
        
        # Refresh or get new credentials
        if not self._credentials or not self._credentials.valid:
            if self._credentials and self._credentials.expired and self._credentials.refresh_token:
                self._credentials.refresh(Request())
            else:
                self._credentials = self._run_auth_flow()
            
            # Save token for next time
            self._save_token()
        
        return self._credentials
    
    def _run_auth_flow(self) -> Credentials:
        """Run OAuth2 authorization flow."""
        flow = InstalledAppFlow.from_client_secrets_file(
            str(self._credentials_path), SCOPES
        )
        return flow.run_local_server(port=0)
    
    def _save_token(self) -> None:
        """Save credentials to token file."""
        if self._credentials:
            with open(self._token_path, 'w') as f:
                f.write(self._credentials.to_json())
    
    def revoke(self) -> None:
        """Revoke current credentials."""
        if self._token_path.exists():
            self._token_path.unlink()
        self._credentials = None
    
    @property
    def is_authenticated(self) -> bool:
        """Check if valid credentials exist."""
        try:
            creds = self.get_credentials()
            return creds is not None and creds.valid
        except Exception:
            return False
```

#### doc_generator.py

```python
"""
Google Docs document generation.
Handles: Document creation, content insertion, formatting.
"""

from typing import List, Optional
from googleapiclient.discovery import build
from .auth_manager import GoogleAuthManager
from ..core.inspection_item import InspectionItem

class GoogleDocGenerator:
    """Generate inspection reports as Google Docs."""
    
    def __init__(self, auth_manager: GoogleAuthManager):
        self._auth = auth_manager
        self._service = None
    
    def _get_service(self):
        """Get or create Docs API service."""
        if not self._service:
            creds = self._auth.get_credentials()
            self._service = build('docs', 'v1', credentials=creds)
        return self._service
    
    def create_report(
        self, 
        title: str, 
        items: List[InspectionItem],
        image_uploader: "ImageUploader"
    ) -> tuple[str, List[str]]:
        """
        Create inspection report document.
        
        Args:
            title: Document title
            items: List of approved inspection items
            image_uploader: Service for uploading images
            
        Returns:
            Tuple of (document_id, list_of_errors)
        """
        service = self._get_service()
        errors = []
        
        # Create empty document
        doc = service.documents().create(body={'title': title}).execute()
        doc_id = doc['documentId']
        
        # Build content requests
        requests = []
        insert_index = 1  # Start after title
        
        for item in items:
            try:
                item_requests, new_index = self._build_item_content(
                    item, insert_index, image_uploader
                )
                requests.extend(item_requests)
                insert_index = new_index
            except Exception as e:
                # Log error but continue with other items (partial failure recovery)
                errors.append(f"Item {item.id}: {str(e)}")
                continue
        
        # Execute batch update
        if requests:
            service.documents().batchUpdate(
                documentId=doc_id,
                body={'requests': requests}
            ).execute()
        
        return (doc_id, errors)
    
    def _build_item_content(
        self, 
        item: InspectionItem, 
        start_index: int,
        image_uploader: "ImageUploader"
    ) -> tuple[list, int]:
        """
        Build document requests for a single item.
        
        Returns:
            Tuple of (requests_list, new_insert_index)
        """
        requests = []
        idx = start_index
        
        # Header: Location + Description
        header_text = f"{item.user_location}: {item.user_description}\n\n"
        requests.append({
            'insertText': {'location': {'index': idx}, 'text': header_text}
        })
        idx += len(header_text)
        
        # Insert edited photo
        if item.photo_edited_path:
            photo_uri = image_uploader.upload_image(item.photo_edited_path)
            if photo_uri:
                requests.append({
                    'insertInlineImage': {
                        'location': {'index': idx},
                        'uri': photo_uri,
                        'objectSize': {
                            'width': {'magnitude': 400, 'unit': 'PT'},
                            'height': {'magnitude': 300, 'unit': 'PT'}
                        }
                    }
                })
                idx += 1  # Image takes 1 index position
        
        requests.append({
            'insertText': {'location': {'index': idx}, 'text': '\n'}
        })
        idx += 1
        
        # Insert code snapshot
        if item.snapshot_path:
            snap_uri = image_uploader.upload_image(item.snapshot_path)
            if snap_uri:
                requests.append({
                    'insertInlineImage': {
                        'location': {'index': idx},
                        'uri': snap_uri,
                        'objectSize': {
                            'width': {'magnitude': 400, 'unit': 'PT'},
                            'height': {'magnitude': 300, 'unit': 'PT'}
                        }
                    }
                })
                idx += 1
        
        # Add separator
        requests.append({
            'insertText': {'location': {'index': idx}, 'text': '\n\n---\n\n'}
        })
        idx += 6
        
        return (requests, idx)
```

#### image_uploader.py

```python
"""
Upload images to Google Drive for document embedding.
Handles: File upload, URI generation, cleanup.
"""

from pathlib import Path
from typing import Optional
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from .auth_manager import GoogleAuthManager

class ImageUploader:
    """Upload images to Google Drive for Docs embedding."""
    
    def __init__(self, auth_manager: GoogleAuthManager):
        self._auth = auth_manager
        self._service = None
        self._uploaded_ids: list[str] = []  # Track for cleanup
    
    def _get_service(self):
        """Get or create Drive API service."""
        if not self._service:
            creds = self._auth.get_credentials()
            self._service = build('drive', 'v3', credentials=creds)
        return self._service
    
    def upload_image(self, image_path: str | Path) -> Optional[str]:
        """
        Upload image to Drive and return embeddable URI.
        
        Args:
            image_path: Path to image file
            
        Returns:
            URI string for embedding in Docs, or None on failure
        """
        path = Path(image_path)
        if not path.exists():
            return None
        
        service = self._get_service()
        
        # Determine MIME type
        mime_types = {
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.gif': 'image/gif'
        }
        mime_type = mime_types.get(path.suffix.lower(), 'image/png')
        
        # Upload file
        file_metadata = {'name': path.name}
        media = MediaFileUpload(str(path), mimetype=mime_type)
        
        file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id,webContentLink'
        ).execute()
        
        file_id = file['id']
        self._uploaded_ids.append(file_id)
        
        # Make file publicly accessible for embedding
        service.permissions().create(
            fileId=file_id,
            body={'type': 'anyone', 'role': 'reader'}
        ).execute()
        
        # Get direct content link
        return file.get('webContentLink', f"https://drive.google.com/uc?id={file_id}")
    
    def cleanup_uploaded_files(self) -> None:
        """Delete all uploaded files from Drive."""
        service = self._get_service()
        for file_id in self._uploaded_ids:
            try:
                service.files().delete(fileId=file_id).execute()
            except Exception:
                pass  # Ignore cleanup failures
        self._uploaded_ids.clear()
```

#### error_recovery.py

```python
"""
Export error handling and recovery.
Handles: Partial failures, retry logic, error logging.
"""

from typing import List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from ..core.inspection_item import InspectionItem

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
    
    def __init__(self):
        self._errors: List[ExportError] = []
        self._retry_limit = 3
    
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
        return [e for e in self._errors if e.is_recoverable and e.retry_count < self._retry_limit]
    
    def get_failed_item_ids(self) -> List[str]:
        """Get IDs of items that failed to export."""
        return [e.item_id for e in self._errors]
    
    def mark_retry(self, item_id: str) -> bool:
        """
        Mark an error for retry.
        
        Returns:
            True if retry is allowed, False if limit exceeded
        """
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
        doc_url = f"https://docs.google.com/document/d/{doc_id}/edit" if doc_id else None
        
        return ExportResult(
            success=len(self._errors) == 0,
            document_id=doc_id,
            document_url=doc_url,
            total_items=total_items,
            successful_items=successful_items,
            failed_items=len(self._errors),
            errors=list(self._errors)
        )
```

---

## 6. Service Interface Contracts

### 6.1 AI Service Interface

```python
# services/ai_service/__init__.py

from abc import ABC, abstractmethod
from typing import Optional, Tuple
from PIL import Image

class IAIService(ABC):
    """Interface for AI code analysis service."""
    
    @abstractmethod
    def analyze_photo(
        self,
        image_path: str,
        description: str,
        location: str,
        pdf_chapter_path: str
    ) -> "AIAnalysisResult":
        """
        Analyze inspection photo against code chapter.
        
        Args:
            image_path: Path to inspection photo
            description: User's violation description
            location: Location in building
            pdf_chapter_path: Path to relevant code chapter PDF
            
        Returns:
            AIAnalysisResult with match details
        """
        pass
    
    @abstractmethod
    def reanalyze_with_feedback(
        self,
        image_path: str,
        description: str,
        location: str,
        pdf_chapter_path: str,
        user_feedback: str
    ) -> "AIAnalysisResult":
        """Re-analyze after hallucination with user feedback."""
        pass
```

### 6.2 PDF Service Interface

```python
# services/pdf_service/__init__.py

from abc import ABC, abstractmethod
from typing import List, Optional, Tuple
from PIL import Image

class IPDFService(ABC):
    """Interface for PDF operations."""
    
    @abstractmethod
    def open(self, pdf_path: str) -> None:
        """Open PDF file."""
        pass
    
    @abstractmethod
    def close(self) -> None:
        """Close current PDF."""
        pass
    
    @abstractmethod
    def search_text(self, term: str) -> List["SearchResult"]:
        """Search for text in PDF."""
        pass
    
    @abstractmethod
    def verify_reference(self, reference: str) -> Tuple[bool, Optional[int]]:
        """Check if reference exists, return (exists, page_num)."""
        pass
    
    @abstractmethod
    def render_page(self, page_num: int, dpi: int = 150) -> Optional[Image.Image]:
        """Render page to image."""
        pass
    
    @abstractmethod
    def render_region(
        self, 
        page_num: int, 
        rect: Tuple[float, float, float, float],
        dpi: int = 300
    ) -> Optional[Image.Image]:
        """Render specific region for snapshot."""
        pass
    
    @abstractmethod
    def get_page_count(self) -> int:
        """Get total page count."""
        pass
```

### 6.3 Image Service Interface

```python
# services/image_service/__init__.py

from abc import ABC, abstractmethod
from typing import Tuple, Optional
from pathlib import Path
from PIL import Image

class IImageService(ABC):
    """Interface for image editing operations."""
    
    @abstractmethod
    def load(self, path: str) -> None:
        """Load image from file."""
        pass
    
    @abstractmethod
    def crop(self, box: Tuple[int, int, int, int]) -> None:
        """Crop to region."""
        pass
    
    @abstractmethod
    def rotate(self, degrees: float) -> None:
        """Rotate image."""
        pass
    
    @abstractmethod
    def adjust_brightness(self, factor: float) -> None:
        """Adjust brightness."""
        pass
    
    @abstractmethod
    def save(self, output_path: str) -> Path:
        """Save edited image."""
        pass
    
    @abstractmethod
    def get_image(self) -> Optional[Image.Image]:
        """Get current image."""
        pass
```

### 6.4 Export Service Interface

```python
# services/google_docs_service/__init__.py

from abc import ABC, abstractmethod
from typing import List
from ..core.inspection_item import InspectionItem

class IExportService(ABC):
    """Interface for export operations."""
    
    @abstractmethod
    def authenticate(self) -> bool:
        """Authenticate with Google."""
        pass
    
    @abstractmethod
    def is_authenticated(self) -> bool:
        """Check authentication status."""
        pass
    
    @abstractmethod
    def create_report(
        self, 
        title: str, 
        items: List[InspectionItem]
    ) -> "ExportResult":
        """Create inspection report."""
        pass
    
    @abstractmethod
    def retry_failed_items(
        self, 
        items: List[InspectionItem]
    ) -> "ExportResult":
        """Retry previously failed items."""
        pass
```
## 7. Threading & Concurrency Model

### 7.1 Thread Architecture

```
┌────────────────────────────────────────────────────────┐
│                    MAIN/GUI THREAD                      │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────┐  │
│  │ Event Loop   │  │ UI Widgets   │  │ Signal      │  │
│  │ (PyQt6)      │  │ (PyQt6)      │  │ Handlers    │  │
│  └──────────────┘  └──────────────┘  └─────────────┘  │
│                           │                            │
│                    emit signals                        │
│                           ▼                            │
└────────────────────────────────────────────────────────┘
                            │
              ┌─────────────┼─────────────┐
              │             │             │
              ▼             ▼             ▼
       ┌───────────┐ ┌───────────┐ ┌───────────┐
       │ AI Worker │ │PDF Worker │ │Export     │
       │ Thread    │ │ Thread    │ │Worker     │
       │           │ │           │ │Thread     │
       │ Gemini API│ │ PyMuPDF   │ │ Google API│
       └───────────┘ └───────────┘ └───────────┘
```

### 7.2 Signal Definitions (signals/worker_signals.py)

```python
"""
PyQt6 signals for worker thread communication.
"""

from PyQt6.QtCore import QObject, pyqtSignal
from ..core.inspection_item import InspectionItem

class WorkerSignals(QObject):
    """Signals emitted by background workers."""
    
    # AI Processing signals
    ai_started = pyqtSignal()                        # Batch processing started
    ai_item_started = pyqtSignal(str)                # Item ID started
    ai_item_completed = pyqtSignal(str, object)      # Item ID, AIResult
    ai_item_error = pyqtSignal(str, str)             # Item ID, error message
    ai_progress = pyqtSignal(int, int)               # current, total
    ai_completed = pyqtSignal()                      # All items done
    ai_rate_limited = pyqtSignal(int)                # Wait seconds
    
    # PDF Search signals
    search_started = pyqtSignal(str)                 # Search term
    search_found = pyqtSignal(str, int, object)      # Term, page, rect
    search_not_found = pyqtSignal(str)               # Term
    search_error = pyqtSignal(str)                   # Error message
    
    # Export signals
    export_started = pyqtSignal()
    export_item_completed = pyqtSignal(str)          # Item ID
    export_item_error = pyqtSignal(str, str)         # Item ID, error
    export_progress = pyqtSignal(int, int)           # current, total
    export_completed = pyqtSignal(object)            # ExportResult
    export_network_error = pyqtSignal()              # Connection lost
```

### 7.3 Base Worker Class (workers/base_worker.py)

```python
"""
Base class for background worker threads.
"""

from PyQt6.QtCore import QThread, QMutex, QWaitCondition
from typing import Optional
from ..signals.worker_signals import WorkerSignals

class BaseWorker(QThread):
    """Base class for background workers with pause/resume support."""
    
    def __init__(self):
        super().__init__()
        self.signals = WorkerSignals()
        self._mutex = QMutex()
        self._pause_condition = QWaitCondition()
        self._is_paused = False
        self._is_cancelled = False
    
    def pause(self) -> None:
        """Pause worker execution."""
        self._mutex.lock()
        self._is_paused = True
        self._mutex.unlock()
    
    def resume(self) -> None:
        """Resume paused worker."""
        self._mutex.lock()
        self._is_paused = False
        self._pause_condition.wakeAll()
        self._mutex.unlock()
    
    def cancel(self) -> None:
        """Cancel worker execution."""
        self._mutex.lock()
        self._is_cancelled = True
        self._is_paused = False
        self._pause_condition.wakeAll()
        self._mutex.unlock()
    
    def check_pause(self) -> None:
        """Check if paused and wait if needed. Call in run() loop."""
        self._mutex.lock()
        while self._is_paused and not self._is_cancelled:
            self._pause_condition.wait(self._mutex)
        self._mutex.unlock()
    
    def is_cancelled(self) -> bool:
        """Check if worker was cancelled."""
        return self._is_cancelled
    
    def run(self) -> None:
        """Override in subclass. Call check_pause() in processing loop."""
        raise NotImplementedError
```

### 7.4 AI Processing Worker (workers/ai_processing_worker.py)

```python
"""
Background worker for batch AI processing.
"""

import time
from typing import List, Dict
from pathlib import Path
from .base_worker import BaseWorker
from ..core.inspection_item import InspectionItem, ItemStatus, SearchStatus
from ..core.inspection_queue import InspectionQueue
from ..services.ai_service.gemini_client import GeminiClient
from ..services.ai_service.context_cache import ContextCacheManager
from ..services.ai_service.prompt_templates import (
    SYSTEM_PROMPT_CODE_ANALYSIS, 
    build_analysis_prompt
)
from ..services.ai_service.response_parser import parse_analysis_response, extract_search_term
from ..services.pdf_service.pdf_reader import PDFReader
from ..services.pdf_service.text_searcher import PDFTextSearcher
from ..core.exceptions import AIRateLimitError

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
        
        # Rate limiting
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
    
    def _process_item(self, item: InspectionItem, cache_id: str, pdf_path: Path) -> None:
        """Process single item through AI and pre-validate."""
        # Update status
        item.status = ItemStatus.PROCESSING
        self._queue.update_item(item)
        
        # Build prompt
        prompt = build_analysis_prompt(item.user_description, item.user_location)
        
        # Call Gemini
        response = self._client.generate_with_image(
            system_prompt=SYSTEM_PROMPT_CODE_ANALYSIS,
            user_prompt=prompt,
            image_path=item.photo_edited_path,
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
            
            with PDFReader() as reader:
                reader.open(pdf_path)
                searcher = PDFTextSearcher(reader)
                exists, page_num = searcher.verify_reference_exists(search_term)
                
                if exists:
                    item.search_status = SearchStatus.FOUND
                    item.search_result_page = page_num
                    item.current_page_view = page_num
                else:
                    item.search_status = SearchStatus.NOT_FOUND
        else:
            item.search_status = SearchStatus.NOT_FOUND
        
        item.status = ItemStatus.REVIEW_READY
        self._queue.update_item(item)
    
    def _group_by_chapter(self, items: List[InspectionItem]) -> Dict[str, List[InspectionItem]]:
        """Group items by chapter file for cache efficiency."""
        grouped = {}
        for item in items:
            chapter = item.selected_chapter_file
            if chapter not in grouped:
                grouped[chapter] = []
            grouped[chapter].append(item)
        return grouped
    
    def _handle_rate_limit(self, wait_seconds: int) -> None:
        """Handle rate limiting with exponential backoff."""
        self.signals.ai_rate_limited.emit(wait_seconds)
        self.pause()
        
        # Wait (can be interrupted by resume or cancel)
        for _ in range(wait_seconds):
            if self.is_cancelled():
                return
            time.sleep(1)
        
        self.resume()
```

### 7.5 Thread Safety for Queue Access

```python
# core/thread_safe_queue.py

from PyQt6.QtCore import QMutex, QMutexLocker
from .inspection_queue import InspectionQueue
from .inspection_item import InspectionItem
from typing import List, Optional

class ThreadSafeQueue:
    """Thread-safe wrapper around InspectionQueue."""
    
    def __init__(self, queue: InspectionQueue):
        self._queue = queue
        self._mutex = QMutex()
    
    def add_item(self, item: InspectionItem) -> None:
        with QMutexLocker(self._mutex):
            self._queue.add_item(item)
    
    def update_item(self, item: InspectionItem) -> None:
        with QMutexLocker(self._mutex):
            self._queue.update_item(item)
    
    def get_item_by_id(self, item_id: str) -> Optional[InspectionItem]:
        with QMutexLocker(self._mutex):
            return self._queue.get_item_by_id(item_id)
    
    def get_pending_items(self) -> List[InspectionItem]:
        with QMutexLocker(self._mutex):
            # Return copies to avoid modification issues
            return [InspectionItem.from_dict(i.to_dict()) 
                    for i in self._queue.get_pending_items()]
```

---

## 8. State Machine Definition

### 8.1 Item Status Transitions

```
                    ┌──────────────────────────────────────────┐
                    │                                          │
                    ▼                                          │
┌─────────┐    ┌────────────┐    ┌──────────────┐    ┌────────────┐
│ PENDING │───▶│ PROCESSING │───▶│ REVIEW_READY │───▶│  APPROVED  │
└─────────┘    └────────────┘    └──────────────┘    └────────────┘
     ▲              │                   │                   │
     │              │                   │                   │
     │              ▼                   │                   │
     │         ┌─────────┐              │                   │
     │         │  ERROR  │◀─────────────┘                   │
     │         └─────────┘                                  │
     │              │                                       │
     └──────────────┴───────────────────────────────────────┘
                    (Retry/Reset)
```

### 8.2 State Machine Implementation (core/state_machine.py)

```python
"""
State machine for InspectionItem status transitions.
Enforces valid transitions and triggers side effects.
"""

from typing import Optional, Callable, Dict, Set
from .inspection_item import InspectionItem, ItemStatus
from datetime import datetime

# Valid state transitions
VALID_TRANSITIONS: Dict[ItemStatus, Set[ItemStatus]] = {
    ItemStatus.PENDING: {ItemStatus.PROCESSING, ItemStatus.ERROR},
    ItemStatus.PROCESSING: {ItemStatus.REVIEW_READY, ItemStatus.ERROR},
    ItemStatus.REVIEW_READY: {ItemStatus.APPROVED, ItemStatus.PROCESSING, ItemStatus.ERROR},
    ItemStatus.APPROVED: {ItemStatus.REVIEW_READY},  # Allow un-approve
    ItemStatus.ERROR: {ItemStatus.PENDING},  # Retry resets to pending
}

class StateTransitionError(Exception):
    """Invalid state transition attempted."""
    pass

class ItemStateMachine:
    """Manage InspectionItem state transitions."""
    
    def __init__(self):
        self._on_transition_callbacks: list[Callable] = []
    
    def can_transition(self, item: InspectionItem, new_status: ItemStatus) -> bool:
        """Check if transition is valid."""
        valid_targets = VALID_TRANSITIONS.get(item.status, set())
        return new_status in valid_targets
    
    def transition(self, item: InspectionItem, new_status: ItemStatus) -> None:
        """
        Transition item to new status.
        
        Raises:
            StateTransitionError: If transition is invalid
        """
        if not self.can_transition(item, new_status):
            raise StateTransitionError(
                f"Cannot transition from {item.status.value} to {new_status.value}"
            )
        
        old_status = item.status
        item.status = new_status
        
        # Handle side effects
        self._apply_side_effects(item, old_status, new_status)
        
        # Notify listeners
        for callback in self._on_transition_callbacks:
            callback(item, old_status, new_status)
    
    def _apply_side_effects(
        self, 
        item: InspectionItem, 
        old_status: ItemStatus, 
        new_status: ItemStatus
    ) -> None:
        """Apply automatic changes based on transition."""
        if new_status == ItemStatus.APPROVED:
            item.final_approval = True
            item.approved_at = datetime.now()
        
        elif new_status == ItemStatus.REVIEW_READY and old_status == ItemStatus.APPROVED:
            # Un-approving
            item.final_approval = False
            item.approved_at = None
        
        elif new_status == ItemStatus.PENDING and old_status == ItemStatus.ERROR:
            # Reset for retry
            item.error_message = None
    
    def approve(self, item: InspectionItem) -> None:
        """Convenience method to approve item."""
        self.transition(item, ItemStatus.APPROVED)
    
    def unapprove(self, item: InspectionItem) -> None:
        """Convenience method to unapprove item."""
        self.transition(item, ItemStatus.REVIEW_READY)
    
    def retry(self, item: InspectionItem) -> None:
        """Reset errored item for retry."""
        if item.status == ItemStatus.ERROR:
            self.transition(item, ItemStatus.PENDING)
    
    def on_transition(self, callback: Callable) -> None:
        """Register callback for state transitions."""
        self._on_transition_callbacks.append(callback)
```

---

## 9. UI Component Specifications

### 9.1 Main Window Structure (ui/main_window.py)

```python
"""
Main application window.
Contains phase navigation and central widget stack.
"""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QStackedWidget,
    QStatusBar, QMenuBar, QMenu
)
from PyQt6.QtCore import Qt
from .phase_navigator import PhaseNavigator
from .phase1.triage_widget import TriageWidget
from .phase2.processing_widget import ProcessingWidget
from .phase3.dashboard_widget import DashboardWidget
from .phase4.export_widget import ExportWidget

class MainWindow(QMainWindow):
    """Main application window."""
    
    def __init__(self, app_state: "AppState"):
        super().__init__()
        self._app_state = app_state
        self._setup_ui()
        self._connect_signals()
    
    def _setup_ui(self) -> None:
        """Initialize UI components."""
        self.setWindowTitle("Inspection Photo Review - Code Matching")
        self.setMinimumSize(1200, 800)
        
        # Central widget with stack
        central = QWidget()
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Phase navigator (tabs/buttons)
        self._navigator = PhaseNavigator()
        layout.addWidget(self._navigator)
        
        # Stacked widget for phases
        self._stack = QStackedWidget()
        self._phase1 = TriageWidget(self._app_state)
        self._phase2 = ProcessingWidget(self._app_state)
        self._phase3 = DashboardWidget(self._app_state)
        self._phase4 = ExportWidget(self._app_state)
        
        self._stack.addWidget(self._phase1)
        self._stack.addWidget(self._phase2)
        self._stack.addWidget(self._phase3)
        self._stack.addWidget(self._phase4)
        
        layout.addWidget(self._stack)
        self.setCentralWidget(central)
        
        # Status bar
        self._status_bar = QStatusBar()
        self.setStatusBar(self._status_bar)
        
        # Menu bar
        self._setup_menus()
    
    def _setup_menus(self) -> None:
        """Create menu bar."""
        menu_bar = self.menuBar()
        
        # File menu
        file_menu = menu_bar.addMenu("File")
        file_menu.addAction("Open Project...", self._on_open_project)
        file_menu.addAction("Save Project", self._on_save_project)
        file_menu.addSeparator()
        file_menu.addAction("Settings...", self._on_settings)
        file_menu.addSeparator()
        file_menu.addAction("Exit", self.close)
        
        # Help menu
        help_menu = menu_bar.addMenu("Help")
        help_menu.addAction("About", self._on_about)
    
    def _connect_signals(self) -> None:
        """Connect phase navigation signals."""
        self._navigator.phase_changed.connect(self._on_phase_changed)
    
    def _on_phase_changed(self, phase_index: int) -> None:
        """Handle phase navigation."""
        self._stack.setCurrentIndex(phase_index)
    
    def _on_open_project(self) -> None:
        """Handle open project action."""
        pass
    
    def _on_save_project(self) -> None:
        """Handle save project action."""
        self._app_state.save()
    
    def _on_settings(self) -> None:
        """Open settings dialog."""
        pass
    
    def _on_about(self) -> None:
        """Show about dialog."""
        pass
    
    def update_status(self, message: str) -> None:
        """Update status bar message."""
        self._status_bar.showMessage(message, 5000)
```

### 9.2 Phase 3 Dashboard Layout (ui/phase3/dashboard_widget.py)

```python
"""
Three-pane verification dashboard.
Left: Edited photo | Center: Data & controls | Right: PDF viewer
"""

from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QSplitter
)
from PyQt6.QtCore import Qt
from .photo_panel import PhotoPanel
from .data_panel import DataPanel
from .pdf_viewer import PDFViewer
from ...core.inspection_item import SearchStatus, ItemStatus

class DashboardWidget(QWidget):
    """Phase 3 verification dashboard."""
    
    def __init__(self, app_state: "AppState"):
        super().__init__()
        self._app_state = app_state
        self._current_item = None
        self._setup_ui()
        self._connect_signals()
    
    def _setup_ui(self) -> None:
        """Create three-pane layout."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        
        # Use splitter for resizable panes
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left: Photo panel (25% width)
        self._photo_panel = PhotoPanel()
        splitter.addWidget(self._photo_panel)
        
        # Center: Data panel (25% width)
        self._data_panel = DataPanel()
        splitter.addWidget(self._data_panel)
        
        # Right: PDF viewer (50% width)
        self._pdf_viewer = PDFViewer()
        splitter.addWidget(self._pdf_viewer)
        
        # Set initial sizes
        splitter.setSizes([300, 300, 600])
        
        layout.addWidget(splitter)
    
    def _connect_signals(self) -> None:
        """Connect internal signals."""
        # Item selection from queue
        self._app_state.signals.item_selected.connect(self._on_item_selected)
        
        # Search bar updates
        self._data_panel.search_requested.connect(self._on_search_requested)
        
        # Snapshot creation
        self._pdf_viewer.snapshot_created.connect(self._on_snapshot_created)
        
        # Approval toggle
        self._data_panel.approval_toggled.connect(self._on_approval_toggled)
        
        # Resend to AI
        self._data_panel.resend_requested.connect(self._on_resend_requested)
    
    def _on_item_selected(self, item_id: str) -> None:
        """Load selected item into dashboard."""
        item = self._app_state.queue.get_item_by_id(item_id)
        if item:
            self._current_item = item
            self._photo_panel.load_image(item.photo_edited_path)
            self._data_panel.load_item(item)
            
            # Load PDF and jump to page
            pdf_path = self._app_state.get_pdf_path(item.selected_chapter_file)
            self._pdf_viewer.open_pdf(pdf_path)
            
            if item.search_result_page is not None:
                self._pdf_viewer.go_to_page(item.search_result_page)
    
    def _on_search_requested(self, search_term: str) -> None:
        """Handle search bar search request."""
        if self._current_item:
            result = self._pdf_viewer.search_text(search_term)
            if result:
                self._current_item.search_status = SearchStatus.FOUND
                self._current_item.active_search_term = search_term
                self._current_item.search_result_page = result.page_num
                self._data_panel.update_search_status(found=True)
            else:
                self._current_item.search_status = SearchStatus.NOT_FOUND
                self._data_panel.update_search_status(found=False)
            self._app_state.queue.update_item(self._current_item)
    
    def _on_snapshot_created(self, snapshot_path: str) -> None:
        """Handle snapshot creation from PDF."""
        if self._current_item:
            self._current_item.snapshot_path = snapshot_path
            self._app_state.queue.update_item(self._current_item)
            self._data_panel.show_snapshot_thumbnail(snapshot_path)
    
    def _on_approval_toggled(self, approved: bool) -> None:
        """Handle approval checkbox toggle."""
        if self._current_item:
            if approved:
                self._app_state.state_machine.approve(self._current_item)
            else:
                self._app_state.state_machine.unapprove(self._current_item)
            self._app_state.queue.update_item(self._current_item)
    
    def _on_resend_requested(self, feedback: str) -> None:
        """Resend item to AI with user feedback."""
        if self._current_item:
            self._current_item.status = ItemStatus.PENDING
            # Store feedback for next AI call
            self._current_item.error_message = f"USER_FEEDBACK:{feedback}"
            self._app_state.queue.update_item(self._current_item)
```

### 9.3 Search Bar Component (ui/phase3/search_bar.py)

```python
"""
Active search bar with visual state feedback.
"""

from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QLineEdit, QPushButton
)
from PyQt6.QtCore import pyqtSignal

class SearchBar(QWidget):
    """Search bar with found/not-found visual states."""
    
    search_requested = pyqtSignal(str)  # Emits search term
    
    # Style constants
    STYLE_NORMAL = "background-color: white; border: 1px solid #ccc;"
    STYLE_FOUND = "background-color: white; border: 2px solid #4CAF50;"
    STYLE_NOT_FOUND = "background-color: #FFF9C4; border: 2px solid #FFC107;"
    
    def __init__(self):
        super().__init__()
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """Create search bar UI."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText(
            "Enter code reference (e.g., R311.7 or Figure R507.2)"
        )
        self._search_input.returnPressed.connect(self._on_search)
        self._search_input.setStyleSheet(self.STYLE_NORMAL)
        layout.addWidget(self._search_input)
        
        self._search_btn = QPushButton("Search")
        self._search_btn.clicked.connect(self._on_search)
        layout.addWidget(self._search_btn)
    
    def set_term(self, term: str) -> None:
        """Set search term in input."""
        self._search_input.setText(term)
    
    def get_term(self) -> str:
        """Get current search term."""
        return self._search_input.text().strip()
    
    def set_found_state(self) -> None:
        """Set visual state to 'found' (green border)."""
        self._search_input.setStyleSheet(self.STYLE_FOUND)
    
    def set_not_found_state(self) -> None:
        """Set visual state to 'not found' (yellow background)."""
        self._search_input.setStyleSheet(self.STYLE_NOT_FOUND)
    
    def set_normal_state(self) -> None:
        """Reset to normal visual state."""
        self._search_input.setStyleSheet(self.STYLE_NORMAL)
    
    def _on_search(self) -> None:
        """Handle search action."""
        term = self.get_term()
        if term:
            self.search_requested.emit(term)
```
## 10. Error Handling Framework

### 10.1 Custom Exceptions (core/exceptions.py)

```python
"""
Application-specific exceptions.
"""

class InspectionAppError(Exception):
    """Base exception for application."""
    pass

# AI Service Errors
class AIServiceError(InspectionAppError):
    """Base for AI-related errors."""
    pass

class AIRateLimitError(AIServiceError):
    """API rate limit exceeded."""
    def __init__(self, wait_seconds: int, message: str = "Rate limited"):
        super().__init__(message)
        self.wait_seconds = wait_seconds

class AIConnectionError(AIServiceError):
    """Network connection to AI service failed."""
    pass

class AIResponseParseError(AIServiceError):
    """Failed to parse AI response."""
    pass

class AIHallucinationError(AIServiceError):
    """AI returned reference that doesn't exist."""
    def __init__(self, reference: str):
        super().__init__(f"Reference not found: {reference}")
        self.reference = reference

# PDF Service Errors
class PDFServiceError(InspectionAppError):
    """Base for PDF-related errors."""
    pass

class PDFNotFoundError(PDFServiceError):
    """PDF file not found."""
    pass

class PDFSearchError(PDFServiceError):
    """Error during PDF text search."""
    pass

class PDFRenderError(PDFServiceError):
    """Error rendering PDF page."""
    pass

# Export Errors
class ExportError(InspectionAppError):
    """Base for export-related errors."""
    pass

class ExportAuthError(ExportError):
    """Google authentication failed."""
    pass

class ExportNetworkError(ExportError):
    """Network error during export."""
    pass

class ExportPartialError(ExportError):
    """Some items failed to export."""
    def __init__(self, successful: int, failed: int, errors: list):
        super().__init__(
            f"Export completed with errors: {successful} succeeded, {failed} failed"
        )
        self.successful = successful
        self.failed = failed
        self.errors = errors

# State Errors
class StateError(InspectionAppError):
    """Invalid state or transition."""
    pass

class StateTransitionError(StateError):
    """Invalid state transition attempted."""
    pass
```

### 10.2 Error Handler Service (core/error_handler.py)

```python
"""
Centralized error handling and logging.
"""

import logging
from typing import Optional, Callable
from datetime import datetime
from pathlib import Path
from .exceptions import *

class ErrorHandler:
    """Central error handling service."""
    
    def __init__(self, log_dir: Optional[Path] = None):
        self._log_dir = log_dir or Path("./logs")
        self._log_dir.mkdir(parents=True, exist_ok=True)
        self._setup_logging()
        self._error_callbacks: list[Callable] = []
    
    def _setup_logging(self) -> None:
        """Configure logging."""
        log_file = self._log_dir / f"app_{datetime.now().strftime('%Y%m%d')}.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self._logger = logging.getLogger("InspectionApp")
    
    def handle_error(self, error: Exception, context: str = "") -> dict:
        """
        Handle an exception and return appropriate response.
        
        Args:
            error: The exception that occurred
            context: Description of where error occurred
            
        Returns:
            Dict with 'recoverable', 'message', 'action' keys
        """
        error_info = {
            "recoverable": True,
            "message": str(error),
            "action": "none",
            "wait_seconds": 0
        }
        
        # Log the error
        self._logger.error(f"{context}: {error}", exc_info=True)
        
        # Determine response based on error type
        if isinstance(error, AIRateLimitError):
            error_info["action"] = "wait_and_retry"
            error_info["wait_seconds"] = error.wait_seconds
            error_info["message"] = f"Rate limited. Waiting {error.wait_seconds}s..."
            
        elif isinstance(error, AIConnectionError):
            error_info["action"] = "retry"
            error_info["message"] = "Connection failed. Click to retry."
            
        elif isinstance(error, AIHallucinationError):
            error_info["action"] = "user_input"
            error_info["message"] = (
                f"AI suggestion '{error.reference}' not found. Please verify manually."
            )
            
        elif isinstance(error, ExportNetworkError):
            error_info["action"] = "retry"
            error_info["message"] = "Network error during export. Click to retry."
            
        elif isinstance(error, ExportPartialError):
            error_info["recoverable"] = True
            error_info["action"] = "partial_retry"
            error_info["message"] = error.args[0]
            
        elif isinstance(error, StateTransitionError):
            error_info["recoverable"] = False
            error_info["action"] = "none"
            error_info["message"] = f"Invalid operation: {error}"
        
        # Notify callbacks
        for callback in self._error_callbacks:
            callback(error_info)
        
        return error_info
    
    def on_error(self, callback: Callable) -> None:
        """Register error callback for UI updates."""
        self._error_callbacks.append(callback)
    
    def log_info(self, message: str) -> None:
        """Log info message."""
        self._logger.info(message)
    
    def log_warning(self, message: str) -> None:
        """Log warning message."""
        self._logger.warning(message)
```

### 10.3 Error Handling Matrix (Reference)

| Error Type | UI Behavior | Recovery Action | Auto-Retry |
|------------|-------------|-----------------|------------|
| `AIRateLimitError` | Progress bar pauses, countdown displayed | Wait then auto-resume | Yes |
| `AIConnectionError` | "Connection lost" message | "Retry" button | No |
| `AIHallucinationError` | Search bar turns yellow | User manually enters term | No |
| `AIResponseParseError` | Item marked as error | "Resend to AI" button | No |
| `PDFNotFoundError` | Error dialog | User selects correct file | No |
| `PDFSearchError` | Search bar turns yellow | User adjusts search term | No |
| `ExportAuthError` | Auth prompt displayed | Re-authenticate | No |
| `ExportNetworkError` | "Connection lost" modal | "Retry" button | No |
| `ExportPartialError` | "Completed with errors" | Fix items and re-export | No |

---

## 11. Configuration Management

### 11.1 Config Manager (core/config_manager.py)

```python
"""
Configuration loading and validation.
"""

import json
from pathlib import Path
from typing import Optional, Any
from dataclasses import dataclass
from pydantic import BaseModel, validator

class AISettings(BaseModel):
    """AI service configuration."""
    model_name: str = "gemini-2.0-pro"
    thinking_budget: int = 10000
    max_retries: int = 3
    retry_delay_seconds: int = 5
    cache_ttl_minutes: int = 60

class PDFSettings(BaseModel):
    """PDF service configuration."""
    render_dpi: int = 150
    snapshot_dpi: int = 300

class UISettings(BaseModel):
    """UI configuration."""
    default_window_width: int = 1400
    default_window_height: int = 900
    auto_save_interval_seconds: int = 30

class AppConfig(BaseModel):
    """Complete application configuration."""
    gemini_api_key: str
    google_docs_credentials_path: str
    code_book_directory: str
    output_directory: str = "./output"
    ai_settings: AISettings = AISettings()
    pdf_settings: PDFSettings = PDFSettings()
    ui_settings: UISettings = UISettings()
    
    @validator('code_book_directory')
    def validate_code_book_dir(cls, v):
        path = Path(v)
        if not path.exists():
            raise ValueError(f"Code book directory does not exist: {v}")
        return v
    
    @validator('google_docs_credentials_path')
    def validate_credentials(cls, v):
        path = Path(v)
        if not path.exists():
            raise ValueError(f"Credentials file not found: {v}")
        return v

class ConfigManager:
    """Load and manage application configuration."""
    
    def __init__(self, config_path: str | Path = "settings.json"):
        self._config_path = Path(config_path)
        self._config: Optional[AppConfig] = None
    
    def load(self) -> AppConfig:
        """
        Load configuration from file.
        
        Raises:
            FileNotFoundError: Config file doesn't exist
            ValueError: Invalid configuration
        """
        if not self._config_path.exists():
            raise FileNotFoundError(f"Config file not found: {self._config_path}")
        
        with open(self._config_path) as f:
            data = json.load(f)
        
        self._config = AppConfig(**data)
        return self._config
    
    def get(self) -> AppConfig:
        """Get loaded config or load if needed."""
        if not self._config:
            self.load()
        return self._config
    
    def save(self, config: AppConfig) -> None:
        """Save configuration to file."""
        with open(self._config_path, 'w') as f:
            json.dump(config.dict(), f, indent=2)
        self._config = config
    
    def create_default(self) -> None:
        """Create default configuration file."""
        default = {
            "gemini_api_key": "YOUR_API_KEY_HERE",
            "google_docs_credentials_path": "./credentials.json",
            "code_book_directory": "./code_books/",
            "output_directory": "./output/",
            "ai_settings": AISettings().dict(),
            "pdf_settings": PDFSettings().dict(),
            "ui_settings": UISettings().dict()
        }
        with open(self._config_path, 'w') as f:
            json.dump(default, f, indent=2)
```

---

## 12. Integration Patterns

### 12.1 Application State Container (core/app_state.py)

```python
"""
Global application state container.
Single source of truth for application data.
"""

from pathlib import Path
from typing import Optional
from PyQt6.QtCore import QObject, pyqtSignal
from .inspection_queue import InspectionQueue
from .state_machine import ItemStateMachine
from .config_manager import ConfigManager, AppConfig
from .error_handler import ErrorHandler
from ..signals.state_signals import StateSignals

class AppState(QObject):
    """Central application state management."""
    
    def __init__(self, config_path: str = "settings.json"):
        super().__init__()
        
        # Load configuration
        self._config_manager = ConfigManager(config_path)
        self._config = self._config_manager.load()
        
        # Initialize components
        self._queue = InspectionQueue(
            persistence_path=Path(self._config.output_directory) / "queue.json"
        )
        self._state_machine = ItemStateMachine()
        self._error_handler = ErrorHandler(
            log_dir=Path(self._config.output_directory) / "logs"
        )
        
        # Signals for UI updates
        self.signals = StateSignals()
        
        # Register queue change callback
        self._queue.register_change_callback(self._on_queue_changed)
    
    @property
    def config(self) -> AppConfig:
        """Get application configuration."""
        return self._config
    
    @property
    def queue(self) -> InspectionQueue:
        """Get inspection queue."""
        return self._queue
    
    @property
    def state_machine(self) -> ItemStateMachine:
        """Get state machine."""
        return self._state_machine
    
    @property
    def error_handler(self) -> ErrorHandler:
        """Get error handler."""
        return self._error_handler
    
    def get_pdf_path(self, chapter_filename: str) -> Path:
        """Get full path to a code book chapter."""
        return Path(self._config.code_book_directory) / chapter_filename
    
    def get_output_dir(self) -> Path:
        """Get output directory path."""
        return Path(self._config.output_directory)
    
    def list_available_chapters(self) -> list[str]:
        """List available code book PDF files."""
        code_dir = Path(self._config.code_book_directory)
        return [f.name for f in code_dir.glob("*.pdf")]
    
    def save(self) -> None:
        """Save current state to disk."""
        self._queue._persist()
    
    def load(self) -> None:
        """Load state from disk."""
        self._queue.load_from_disk()
    
    def _on_queue_changed(self) -> None:
        """Handle queue changes - emit signal for UI."""
        self.signals.queue_updated.emit()
```

### 12.2 State Signals (signals/state_signals.py)

```python
"""
Signals for application state changes.
"""

from PyQt6.QtCore import QObject, pyqtSignal

class StateSignals(QObject):
    """Signals emitted by application state."""
    
    # Queue signals
    queue_updated = pyqtSignal()              # Queue contents changed
    item_added = pyqtSignal(str)              # New item ID
    item_updated = pyqtSignal(str)            # Updated item ID
    item_removed = pyqtSignal(str)            # Removed item ID
    
    # Selection signals
    item_selected = pyqtSignal(str)           # Item ID selected for review
    
    # Phase signals
    phase_changed = pyqtSignal(int)           # New phase index
    
    # Status signals
    status_message = pyqtSignal(str)          # Status bar message
    error_occurred = pyqtSignal(str, str)     # Error type, message
```

### 12.3 Main Entry Point (main.py)

```python
"""
Application entry point.
"""

import sys
from pathlib import Path
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from core.app_state import AppState
from core.config_manager import ConfigManager
from ui.main_window import MainWindow

def main():
    """Main entry point."""
    # Enable high DPI scaling
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    
    app = QApplication(sys.argv)
    app.setApplicationName("Inspection Photo Review")
    app.setOrganizationName("InspectionApp")
    
    # Check for config file
    config_path = Path("settings.json")
    if not config_path.exists():
        config_manager = ConfigManager(config_path)
        config_manager.create_default()
        print(f"Created default config at {config_path}")
        print("Please edit settings.json with your API keys before running.")
        sys.exit(1)
    
    # Initialize application state
    try:
        app_state = AppState(str(config_path))
    except Exception as e:
        print(f"Failed to initialize: {e}")
        sys.exit(1)
    
    # Load any persisted data
    app_state.load()
    
    # Create and show main window
    window = MainWindow(app_state)
    window.show()
    
    # Run application
    exit_code = app.exec()
    
    # Save state on exit
    app_state.save()
    
    sys.exit(exit_code)

if __name__ == "__main__":
    main()
```

---

## 13. Testing Strategy

### 13.1 Unit Test Structure

```
tests/
├── conftest.py                 # Shared fixtures
├── test_inspection_item.py     # Data model tests
├── test_inspection_queue.py    # Queue operations
├── test_state_machine.py       # State transitions
├── test_gemini_client.py       # AI client (mocked)
├── test_response_parser.py     # Response parsing
├── test_pdf_searcher.py        # PDF search
├── test_image_editor.py        # Image operations
├── test_export_worker.py       # Export (mocked)
└── integration/
    ├── test_phase1_flow.py     # End-to-end triage
    ├── test_phase2_flow.py     # End-to-end batch
    └── test_full_workflow.py   # Complete workflow
```

### 13.2 Example Test Cases (tests/test_state_machine.py)

```python
"""
State machine transition tests.
"""

import pytest
from core.inspection_item import InspectionItem, ItemStatus
from core.state_machine import ItemStateMachine, StateTransitionError

class TestStateMachine:
    
    @pytest.fixture
    def machine(self):
        return ItemStateMachine()
    
    @pytest.fixture
    def pending_item(self):
        item = InspectionItem()
        item.status = ItemStatus.PENDING
        return item
    
    def test_valid_pending_to_processing(self, machine, pending_item):
        """Pending -> Processing is valid."""
        machine.transition(pending_item, ItemStatus.PROCESSING)
        assert pending_item.status == ItemStatus.PROCESSING
    
    def test_invalid_pending_to_approved(self, machine, pending_item):
        """Pending -> Approved should fail."""
        with pytest.raises(StateTransitionError):
            machine.transition(pending_item, ItemStatus.APPROVED)
    
    def test_approval_sets_flag(self, machine):
        """Approving item sets final_approval flag."""
        item = InspectionItem()
        item.status = ItemStatus.REVIEW_READY
        
        machine.approve(item)
        
        assert item.final_approval == True
        assert item.approved_at is not None
    
    def test_unapproval_clears_flag(self, machine):
        """Unapproving clears final_approval flag."""
        item = InspectionItem()
        item.status = ItemStatus.REVIEW_READY
        machine.approve(item)
        
        machine.unapprove(item)
        
        assert item.final_approval == False
        assert item.approved_at is None
    
    def test_error_retry_resets_to_pending(self, machine):
        """Retrying error resets to pending."""
        item = InspectionItem()
        item.status = ItemStatus.ERROR
        item.error_message = "Some error"
        
        machine.retry(item)
        
        assert item.status == ItemStatus.PENDING
        assert item.error_message is None
```

### 13.3 Mock Fixtures (tests/conftest.py)

```python
"""
Shared test fixtures.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, MagicMock
from core.inspection_item import InspectionItem, ItemStatus
from core.inspection_queue import InspectionQueue

@pytest.fixture
def temp_output_dir(tmp_path):
    """Create temporary output directory."""
    output = tmp_path / "output"
    output.mkdir()
    return output

@pytest.fixture
def sample_item():
    """Create sample inspection item."""
    item = InspectionItem()
    item.user_description = "Guardrail opening too wide"
    item.user_location = "South Deck"
    item.selected_code_version = "IRC_2021"
    item.selected_chapter_file = "IRC_2021_Ch3.pdf"
    item.photo_original_path = "/fake/path/photo.jpg"
    item.photo_edited_path = "/fake/path/edited/photo_crop.jpg"
    return item

@pytest.fixture
def mock_queue(temp_output_dir):
    """Create queue with temp persistence."""
    return InspectionQueue(
        persistence_path=temp_output_dir / "queue.json"
    )

@pytest.fixture
def mock_gemini_client():
    """Mock Gemini client."""
    client = Mock()
    client.generate_with_image.return_value = """
MATCH_TYPE: Figure
REFERENCE: Figure R312.1.3
CONFIDENCE: High
REASONING: The photo shows a guardrail with openings that appear to exceed 4 inches.
"""
    return client

@pytest.fixture
def mock_pdf_reader():
    """Mock PDF reader."""
    reader = Mock()
    reader.is_open = True
    reader.page_count = 100
    reader.get_page.return_value = Mock()
    return reader
```

---

## Appendix A: Sequence Diagrams

### A.1 Phase 2 Batch Processing Flow

```
User                 GUI                AIWorker           GeminiClient        PDFSearcher
  │                   │                    │                    │                   │
  │ Click "Process"   │                    │                    │                   │
  │──────────────────>│                    │                    │                   │
  │                   │ start()            │                    │                   │
  │                   │───────────────────>│                    │                   │
  │                   │                    │ Group by chapter   │                   │
  │                   │                    │                    │                   │
  │                   │                    │ For each chapter:  │                   │
  │                   │                    │ get_or_create_cache│                   │
  │                   │                    │───────────────────>│                   │
  │                   │                    │<───────────────────│ cache_id          │
  │                   │                    │                    │                   │
  │                   │                    │ For each item:     │                   │
  │                   │ ai_item_started    │ generate_with_image│                   │
  │                   │<───────────────────│───────────────────>│                   │
  │                   │                    │<───────────────────│ response          │
  │                   │                    │                    │                   │
  │                   │                    │ parse_response()   │                   │
  │                   │                    │ verify_reference() │                   │
  │                   │                    │──────────────────────────────────────>│
  │                   │                    │<──────────────────────────────────────│
  │                   │                    │                    │                   │
  │                   │ ai_item_completed  │                    │                   │
  │                   │<───────────────────│                    │                   │
  │ Update progress   │                    │                    │                   │
  │<──────────────────│                    │                    │                   │
  │                   │                    │                    │                   │
  │                   │ ai_completed       │                    │                   │
  │                   │<───────────────────│                    │                   │
  │ Show "Complete"   │                    │                    │                   │
  │<──────────────────│                    │                    │                   │
```

### A.2 Phase 3 Snapshot Flow

```
User                PDFViewer            CoordMapper        PageRenderer       SnapshotCreator
  │                     │                     │                  │                    │
  │ Enable Snapshot     │                     │                  │                    │
  │────────────────────>│                     │                  │                    │
  │                     │ Set cursor cross    │                  │                    │
  │                     │                     │                  │                    │
  │ Mouse press         │                     │                  │                    │
  │────────────────────>│ Store start point   │                  │                    │
  │                     │                     │                  │                    │
  │ Mouse move          │                     │                  │                    │
  │────────────────────>│ Update rubber band  │                  │                    │
  │ See red rectangle   │                     │                  │                    │
  │<────────────────────│                     │                  │                    │
  │                     │                     │                  │                    │
  │ Mouse release       │                     │                  │                    │
  │────────────────────>│                     │                  │                    │
  │                     │ screen_rect_to_pdf  │                  │                    │
  │                     │────────────────────>│                  │                    │
  │                     │<────────────────────│ pdf_rect         │                    │
  │                     │                     │                  │                    │
  │                     │ render_region()     │                  │                    │
  │                     │─────────────────────────────────────>│                    │
  │                     │<─────────────────────────────────────│ PIL Image          │
  │                     │                     │                  │                    │
  │                     │ create_snapshot()   │                  │                    │
  │                     │────────────────────────────────────────────────────────>│
  │                     │                     │                  │  SAVE IMMEDIATELY  │
  │                     │<────────────────────────────────────────────────────────│
  │                     │                     │                  │    snapshot_path   │
  │                     │                     │                  │                    │
  │                     │ Emit snapshot_created signal          │                    │
  │ See thumbnail       │                     │                  │                    │
  │<────────────────────│                     │                  │                    │
```

---

## Appendix B: Development Checklist

### Module Development Order

**Week 1: Core**
- [ ] `core/inspection_item.py`
- [ ] `core/inspection_queue.py`
- [ ] `core/state_machine.py`
- [ ] `core/config_manager.py`
- [ ] `core/exceptions.py`
- [ ] `core/app_state.py`

**Week 2: Services**
- [ ] `services/pdf_service/pdf_reader.py`
- [ ] `services/pdf_service/text_searcher.py`
- [ ] `services/pdf_service/page_renderer.py`
- [ ] `services/image_service/image_editor.py`
- [ ] `services/ai_service/gemini_client.py`
- [ ] `services/ai_service/context_cache.py`
- [ ] `services/ai_service/prompt_templates.py`
- [ ] `services/ai_service/response_parser.py`

**Week 3: Workers**
- [ ] `workers/base_worker.py`
- [ ] `workers/ai_processing_worker.py`
- [ ] `workers/export_worker.py`

**Weeks 3-4: UI**
- [ ] `ui/main_window.py`
- [ ] `ui/phase1/` widgets
- [ ] `ui/phase2/` widgets
- [ ] `ui/phase3/` widgets
- [ ] `ui/phase4/` widgets

**Week 5: Integration**
- [ ] End-to-end testing
- [ ] Error handling verification
- [ ] Performance optimization

---

## Appendix C: Key Corrections from Original Spec

| Original Document Issue | Corrected In Architecture |
|------------------------|---------------------------|
| Referenced "Grok 4.1" model | Changed to "Gemini 2.0 Pro" per spec |
| Missing context caching details | Added `ContextCacheManager` with TTL |
| No prompt templates defined | Added `prompt_templates.py` with exact prompts |
| Missing rubber band implementation | Added `CoordinateMapper` and UI mouse events |
| No signal definitions | Added complete `WorkerSignals` class |
| Missing state machine diagram | Added transition diagram and implementation |
| No error handling specifics | Added exception hierarchy and error matrix |
| Unclear threading model | Added architecture diagram and mutex details |

---

**Document Version:** 3.0  
**Last Updated:** 2025  
**Target:** Independent parallel development by multiple programmers
