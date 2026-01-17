"""
Queue list component for displaying inspection items.
"""

from nicegui import ui
from typing import Optional, Callable, List
from core.inspection_item import InspectionItem, ItemStatus


class QueueList:
    """List component for displaying queue items."""

    def __init__(
        self,
        on_item_selected: Optional[Callable[[str], None]] = None,
        filter_statuses: Optional[List[ItemStatus]] = None
    ):
        self._on_item_selected = on_item_selected
        self._filter_statuses = filter_statuses
        self._items: List[InspectionItem] = []
        self._selected_id: Optional[str] = None
        self._container = None
        self._list_container = None

    def render(self) -> ui.element:
        """Render the queue list component."""
        with ui.card().classes('w-full') as self._container:
            ui.label('Queue Items').classes('text-lg font-bold mb-2')

            with ui.scroll_area().classes('h-64') as self._list_container:
                self._render_items()

        return self._container

    def _render_items(self) -> None:
        """Render the list of items."""
        if self._list_container:
            self._list_container.clear()

        with self._list_container:
            if not self._items:
                ui.label('No items in queue').classes('text-gray-400 py-4')
                return

            for item in self._items:
                # Apply filter if set
                if self._filter_statuses and item.status not in self._filter_statuses:
                    continue

                self._render_item_row(item)

    def _render_item_row(self, item: InspectionItem) -> None:
        """Render a single item row."""
        is_selected = item.id == self._selected_id

        with ui.card().classes(
            f'w-full cursor-pointer mb-1 {"bg-blue-100" if is_selected else ""}'
        ).on('click', lambda i=item: self._select_item(i.id)):
            with ui.row().classes('items-center gap-2'):
                # Status icon
                icon, color = self._get_status_display(item.status)
                ui.icon(icon).classes(f'text-{color}-500')

                # Location
                ui.label(item.user_location or 'No location').classes('font-medium')

                ui.space()

                # Approval badge
                if item.final_approval:
                    ui.badge('Approved', color='green')

    def _get_status_display(self, status: ItemStatus) -> tuple:
        """Get icon and color for status."""
        status_map = {
            ItemStatus.PENDING: ('hourglass_empty', 'gray'),
            ItemStatus.PROCESSING: ('sync', 'blue'),
            ItemStatus.REVIEW_READY: ('visibility', 'yellow'),
            ItemStatus.APPROVED: ('check_circle', 'green'),
            ItemStatus.EXPORTED: ('cloud_done', 'green'),
            ItemStatus.ERROR: ('error', 'red'),
        }
        return status_map.get(status, ('help', 'gray'))

    def _select_item(self, item_id: str) -> None:
        """Handle item selection."""
        self._selected_id = item_id
        self._render_items()

        if self._on_item_selected:
            self._on_item_selected(item_id)

    def update_items(self, items: List[InspectionItem]) -> None:
        """Update the list with new items."""
        self._items = items
        self._render_items()

    def set_selected(self, item_id: str) -> None:
        """Set the selected item."""
        self._selected_id = item_id
        self._render_items()

    def clear_selection(self) -> None:
        """Clear the current selection."""
        self._selected_id = None
        self._render_items()

    def set_filter(self, statuses: Optional[List[ItemStatus]]) -> None:
        """Set status filter."""
        self._filter_statuses = statuses
        self._render_items()
