"""
Thread-safe queue manager with persistence.
"""

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

    def remove_item(self, item_id: str) -> bool:
        """Remove item by ID. Returns True if removed."""
        for idx, item in enumerate(self._items):
            if item.id == item_id:
                del self._items[idx]
                self._notify_change()
                self._persist()
                return True
        return False

    def get_all_items(self) -> List[InspectionItem]:
        """Return all items (copy to prevent mutation)."""
        return list(self._items)

    def get_approved_items(self) -> List[InspectionItem]:
        """Get items ready for export."""
        return [i for i in self._items if i.final_approval]

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
            self._persistence_path.parent.mkdir(parents=True, exist_ok=True)
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
        """Clear all items."""
        self._items = []
        self._notify_change()
        self._persist()
