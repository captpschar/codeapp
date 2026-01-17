"""
Phase 3: Review dashboard with three-pane layout.
"""

from nicegui import ui
from pathlib import Path
from typing import Optional
import base64
import io
import fitz
import shutil
from datetime import datetime

from ..app import get_app_state, notify_success, notify_error, notify_warning
from ...core.inspection_item import InspectionItem, ItemStatus, SearchStatus


class ReviewPage:
    """Phase 3 review dashboard."""

    def __init__(self):
        self._app_state = get_app_state()
        self._current_item: Optional[InspectionItem] = None
        self._pdf_doc: Optional[fitz.Document] = None
        self._current_page: int = 0

        # UI elements
        self._items_container = None
        self._photo_element = None
        self._pdf_element = None
        self._search_input = None
        self._approval_checkbox = None
        self._snapshot_element = None

    def render(self) -> None:
        """Render the review dashboard."""
        with ui.splitter(value=25).classes('w-full h-full') as outer_split:
            # Left panel: Item list + Photo
            with outer_split.before:
                self._render_left_panel()

            # Right panels: Data + PDF
            with outer_split.after:
                with ui.splitter(value=40).classes('w-full h-full') as inner_split:
                    # Center: Data panel
                    with inner_split.before:
                        self._render_data_panel()

                    # Right: PDF viewer
                    with inner_split.after:
                        self._render_pdf_panel()

    def _render_left_panel(self) -> None:
        """Render the left panel with item list and photo."""
        with ui.column().classes('w-full h-full p-2'):
            ui.label('Review Items').classes('text-lg font-bold')

            # Item list
            with ui.scroll_area().classes('h-40'):
                self._items_container = ui.column().classes('w-full')
                self._refresh_items()

            ui.separator()

            # Photo display
            ui.label('Photo').classes('text-lg font-bold')

            with ui.scroll_area().classes('flex-grow'):
                self._photo_element = ui.image('').classes('w-full')
                self._photo_element.visible = False
                self._photo_placeholder = ui.label('Select an item').classes('text-gray-400 py-10')

    def _render_data_panel(self) -> None:
        """Render the center data panel."""
        with ui.column().classes('w-full h-full p-2 gap-4'):
            ui.label('Item Data').classes('text-lg font-bold')

            # Location and description
            with ui.card().classes('w-full'):
                self._location_label = ui.label('Location: -').classes('font-medium')
                self._description_label = ui.label('Description: -').classes('text-sm text-gray-600')

            # AI Results
            with ui.card().classes('w-full'):
                ui.label('AI Analysis').classes('font-bold mb-2')

                self._code_ref_label = ui.label('Code Reference: -')
                self._violation_label = ui.label('Violation: -').classes('text-sm')
                self._confidence_label = ui.label('Confidence: -').classes('text-sm text-gray-500')

            # Search
            with ui.card().classes('w-full'):
                ui.label('PDF Search').classes('font-bold mb-2')

                with ui.row().classes('w-full items-center gap-2'):
                    self._search_input = ui.input(placeholder='Search term...').classes('flex-grow')
                    ui.button(icon='search', on_click=self._do_search).props('flat')

                self._search_status_label = ui.label('').classes('text-sm')

            # Snapshot
            with ui.card().classes('w-full'):
                ui.label('Code Snapshot').classes('font-bold mb-2')

                self._snapshot_element = ui.image('').classes('w-full max-h-32 object-contain')
                self._snapshot_element.visible = False
                self._snapshot_placeholder = ui.label('No snapshot').classes('text-gray-400')

            # Approval
            with ui.card().classes('w-full'):
                self._approval_checkbox = ui.checkbox(
                    'Approve for Export',
                    on_change=self._on_approval_changed
                )

            # Actions
            with ui.row().classes('w-full gap-2'):
                ui.button('Resend to AI', icon='refresh', on_click=self._resend_to_ai).props('flat')

    def _render_pdf_panel(self) -> None:
        """Render the PDF viewer panel."""
        with ui.column().classes('w-full h-full p-2'):
            ui.label('Code Book').classes('text-lg font-bold')

            # PDF toolbar
            with ui.row().classes('w-full items-center gap-2'):
                ui.button(icon='first_page', on_click=self._first_page).props('flat dense')
                ui.button(icon='chevron_left', on_click=self._prev_page).props('flat dense')
                self._page_label = ui.label('0 / 0').classes('mx-2')
                ui.button(icon='chevron_right', on_click=self._next_page).props('flat dense')
                ui.button(icon='last_page', on_click=self._last_page).props('flat dense')

                ui.space()

                ui.button('Snapshot', icon='photo_camera', on_click=self._take_snapshot).props('flat')

            # PDF display
            with ui.scroll_area().classes('flex-grow'):
                self._pdf_element = ui.image('').classes('w-full')
                self._pdf_element.visible = False
                self._pdf_placeholder = ui.label('No PDF loaded').classes('text-gray-400 py-10')

    def _refresh_items(self) -> None:
        """Refresh the items list."""
        self._items_container.clear()

        items = [i for i in self._app_state.queue.get_all_items()
                if i.status in (ItemStatus.REVIEW_READY, ItemStatus.APPROVED)]

        with self._items_container:
            if not items:
                ui.label('No items ready for review').classes('text-gray-400')
                return

            for item in items:
                is_selected = self._current_item and item.id == self._current_item.id
                icon = 'check_circle' if item.final_approval else 'visibility'
                color = 'green' if item.final_approval else 'orange'

                with ui.card().classes(
                    f'w-full cursor-pointer {"bg-blue-100" if is_selected else ""}'
                ).on('click', lambda i=item: self._select_item(i)):
                    with ui.row().classes('items-center gap-2'):
                        ui.icon(icon).classes(f'text-{color}-500')
                        ui.label(item.user_location or 'No location').classes('text-sm')

    def _select_item(self, item: InspectionItem) -> None:
        """Select an item for review."""
        self._current_item = item
        self._refresh_items()

        # Load photo
        photo_path = item.photo_edited_path or item.photo_original_path
        if photo_path and Path(photo_path).exists():
            with open(photo_path, 'rb') as f:
                b64 = base64.b64encode(f.read()).decode()
            self._photo_element.source = f'data:image/jpeg;base64,{b64}'
            self._photo_element.visible = True
            self._photo_placeholder.visible = False
        else:
            self._photo_element.visible = False
            self._photo_placeholder.visible = True

        # Update data panel
        self._location_label.text = f'Location: {item.user_location}'
        self._description_label.text = f'Description: {item.user_description or "-"}'
        self._code_ref_label.text = f'Code Reference: {item.ai_code_reference or "-"}'
        self._violation_label.text = f'Violation: {item.ai_violation_description or "-"}'
        self._confidence_label.text = f'Confidence: {item.ai_confidence:.0%}' if item.ai_confidence else 'Confidence: -'

        # Set search input from AI suggestions
        if item.ai_search_terms:
            self._search_input.value = item.ai_search_terms[0] if item.ai_search_terms else ''

        # Update search status
        if item.search_status == SearchStatus.FOUND:
            self._search_status_label.text = 'Found in PDF'
            self._search_status_label.classes('text-green-600', remove='text-red-600')
        elif item.search_status == SearchStatus.NOT_FOUND:
            self._search_status_label.text = 'Not found in PDF'
            self._search_status_label.classes('text-red-600', remove='text-green-600')
        else:
            self._search_status_label.text = ''

        # Load snapshot if available
        if item.snapshot_path and Path(item.snapshot_path).exists():
            with open(item.snapshot_path, 'rb') as f:
                b64 = base64.b64encode(f.read()).decode()
            self._snapshot_element.source = f'data:image/png;base64,{b64}'
            self._snapshot_element.visible = True
            self._snapshot_placeholder.visible = False
        else:
            self._snapshot_element.visible = False
            self._snapshot_placeholder.visible = True

        # Update approval checkbox
        self._approval_checkbox.value = item.final_approval

        # Load PDF
        self._load_pdf_for_item(item)

    def _load_pdf_for_item(self, item: InspectionItem) -> None:
        """Load the PDF for the selected item."""
        if not item.selected_code_folder or not item.selected_chapter_file:
            return

        pdf_path = self._app_state.get_pdf_path(
            item.selected_code_folder,
            item.selected_chapter_file
        )

        if not pdf_path.exists():
            return

        try:
            if self._pdf_doc:
                self._pdf_doc.close()

            self._pdf_doc = fitz.open(str(pdf_path))
            self._current_page = 0

            # Jump to search result page if available
            if item.search_result_page is not None:
                self._current_page = item.search_result_page

            self._render_pdf_page()

        except Exception as ex:
            notify_error(f'Failed to load PDF: {ex}')

    def _render_pdf_page(self) -> None:
        """Render the current PDF page."""
        if not self._pdf_doc:
            return

        page = self._pdf_doc[self._current_page]

        # Render at 150 DPI
        zoom = 150 / 72.0
        mat = fitz.Matrix(zoom, zoom)

        if page.rotation != 0:
            mat = page.derotation_matrix * mat

        pix = page.get_pixmap(matrix=mat)
        img_data = pix.tobytes("png")
        b64 = base64.b64encode(img_data).decode()

        self._pdf_element.source = f'data:image/png;base64,{b64}'
        self._pdf_element.visible = True
        self._pdf_placeholder.visible = False

        self._page_label.text = f'{self._current_page + 1} / {len(self._pdf_doc)}'

    def _first_page(self) -> None:
        """Go to first page."""
        if self._pdf_doc:
            self._current_page = 0
            self._render_pdf_page()

    def _last_page(self) -> None:
        """Go to last page."""
        if self._pdf_doc:
            self._current_page = len(self._pdf_doc) - 1
            self._render_pdf_page()

    def _prev_page(self) -> None:
        """Go to previous page."""
        if self._pdf_doc and self._current_page > 0:
            self._current_page -= 1
            self._render_pdf_page()

    def _next_page(self) -> None:
        """Go to next page."""
        if self._pdf_doc and self._current_page < len(self._pdf_doc) - 1:
            self._current_page += 1
            self._render_pdf_page()

    def _do_search(self) -> None:
        """Search for text in PDF."""
        if not self._pdf_doc or not self._current_item:
            return

        search_text = self._search_input.value
        if not search_text:
            return

        # Search through pages
        for page_num in range(len(self._pdf_doc)):
            page = self._pdf_doc[page_num]
            matches = page.search_for(search_text)

            if matches:
                self._current_page = page_num
                self._render_pdf_page()

                self._current_item.search_status = SearchStatus.FOUND
                self._current_item.active_search_term = search_text
                self._current_item.search_result_page = page_num
                self._app_state.queue.update_item(self._current_item)

                self._search_status_label.text = f'Found on page {page_num + 1}'
                self._search_status_label.classes('text-green-600', remove='text-red-600')
                notify_success(f'Found on page {page_num + 1}')
                return

        # Not found
        self._current_item.search_status = SearchStatus.NOT_FOUND
        self._app_state.queue.update_item(self._current_item)

        self._search_status_label.text = 'Not found'
        self._search_status_label.classes('text-red-600', remove='text-green-600')
        notify_warning('Text not found in PDF')

    def _take_snapshot(self) -> None:
        """Take a snapshot of the current PDF page."""
        if not self._pdf_doc or not self._current_item:
            return

        try:
            page = self._pdf_doc[self._current_page]

            # Render at high DPI
            zoom = 300 / 72.0
            mat = fitz.Matrix(zoom, zoom)

            if page.rotation != 0:
                mat = page.derotation_matrix * mat

            pix = page.get_pixmap(matrix=mat)

            # Save to output directory
            output_dir = self._app_state.get_output_dir() / "snapshots"
            output_dir.mkdir(parents=True, exist_ok=True)

            original_name = Path(self._current_item.photo_original_path).stem
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            snapshot_name = f"{original_name}_code_snap_{timestamp}.png"
            snapshot_path = output_dir / snapshot_name

            pix.save(str(snapshot_path))

            # Update item
            self._current_item.snapshot_path = str(snapshot_path)
            self._app_state.queue.update_item(self._current_item)

            # Update display
            img_data = pix.tobytes("png")
            b64 = base64.b64encode(img_data).decode()
            self._snapshot_element.source = f'data:image/png;base64,{b64}'
            self._snapshot_element.visible = True
            self._snapshot_placeholder.visible = False

            notify_success('Snapshot captured')

        except Exception as ex:
            notify_error(f'Failed to capture snapshot: {ex}')

    def _on_approval_changed(self, e) -> None:
        """Handle approval checkbox change."""
        if not self._current_item:
            return

        if e.value:
            self._app_state.state_machine.approve(self._current_item)
        else:
            self._app_state.state_machine.unapprove(self._current_item)

        self._app_state.queue.update_item(self._current_item)
        self._refresh_items()

    def _resend_to_ai(self) -> None:
        """Resend item to AI for reprocessing."""
        if not self._current_item:
            return

        self._current_item.status = ItemStatus.PENDING
        self._app_state.queue.update_item(self._current_item)
        self._refresh_items()
        notify_info('Item queued for reprocessing')
