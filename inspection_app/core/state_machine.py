"""
State machine for InspectionItem status transitions.
"""

from typing import Callable, Dict, Set
from datetime import datetime
from .inspection_item import InspectionItem, ItemStatus
from .exceptions import StateTransitionError


# Valid state transitions
VALID_TRANSITIONS: Dict[ItemStatus, Set[ItemStatus]] = {
    ItemStatus.PENDING: {ItemStatus.PROCESSING, ItemStatus.ERROR},
    ItemStatus.PROCESSING: {ItemStatus.REVIEW_READY, ItemStatus.ERROR},
    ItemStatus.REVIEW_READY: {ItemStatus.APPROVED, ItemStatus.PROCESSING, ItemStatus.ERROR},
    ItemStatus.APPROVED: {ItemStatus.REVIEW_READY},
    ItemStatus.ERROR: {ItemStatus.PENDING},
}


class ItemStateMachine:
    """Manage InspectionItem state transitions."""

    def __init__(self):
        self._on_transition_callbacks: list[Callable] = []

    def can_transition(self, item: InspectionItem, new_status: ItemStatus) -> bool:
        """Check if transition is valid."""
        valid_targets = VALID_TRANSITIONS.get(item.status, set())
        return new_status in valid_targets

    def transition(self, item: InspectionItem, new_status: ItemStatus) -> None:
        """Transition item to new status."""
        if not self.can_transition(item, new_status):
            raise StateTransitionError(
                f"Cannot transition from {item.status.value} to {new_status.value}"
            )

        old_status = item.status
        item.status = new_status
        self._apply_side_effects(item, old_status, new_status)

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
            item.final_approval = False
            item.approved_at = None

        elif new_status == ItemStatus.PENDING and old_status == ItemStatus.ERROR:
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
