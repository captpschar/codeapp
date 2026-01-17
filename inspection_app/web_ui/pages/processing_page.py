"""
Phase 2: Processing page for AI analysis monitoring.
"""

from nicegui import ui
from typing import Optional, List
import asyncio

from web_ui.app import get_app_state, notify_success, notify_error, notify_info
from core.inspection_item import InspectionItem, ItemStatus


class ProcessingPage:
    """Phase 2 AI processing interface."""

    def __init__(self):
        self._app_state = get_app_state()
        self._is_processing = False
        self._progress_container = None
        self._items_container = None
        self._current_item_label = None
        self._progress_bar = None

    def render(self) -> None:
        """Render the processing page."""
        with ui.column().classes('w-full max-w-4xl mx-auto p-4 gap-6'):
            ui.label('AI Processing').classes('text-2xl font-bold')

            # Control panel
            with ui.card().classes('w-full'):
                with ui.row().classes('w-full items-center gap-4'):
                    self._start_btn = ui.button(
                        'Start Processing',
                        icon='play_arrow',
                        on_click=self._start_processing
                    )

                    self._stop_btn = ui.button(
                        'Stop',
                        icon='stop',
                        on_click=self._stop_processing
                    ).props('color=negative')
                    self._stop_btn.visible = False

                    ui.space()

                    # Stats
                    pending = len([i for i in self._app_state.queue.get_all_items()
                                  if i.status == ItemStatus.PENDING])
                    self._pending_label = ui.label(f'Pending: {pending}').classes('text-gray-600')

            # Progress section
            with ui.card().classes('w-full') as self._progress_container:
                ui.label('Progress').classes('text-lg font-bold mb-2')

                self._current_item_label = ui.label('Waiting to start...').classes('text-gray-600')

                self._progress_bar = ui.linear_progress(value=0).classes('w-full')

            # Items list
            with ui.card().classes('w-full'):
                ui.label('Queue Items').classes('text-lg font-bold mb-2')

                with ui.scroll_area().classes('h-96'):
                    self._items_container = ui.column().classes('w-full')
                    self._refresh_items()

    def _refresh_items(self) -> None:
        """Refresh the items list."""
        self._items_container.clear()

        items = self._app_state.queue.get_all_items()

        with self._items_container:
            if not items:
                ui.label('No items in queue').classes('text-gray-400 py-4')
                return

            for item in items:
                self._render_item_row(item)

    def _render_item_row(self, item: InspectionItem) -> None:
        """Render a single item row."""
        status_config = self._get_status_config(item.status)

        with ui.card().classes('w-full mb-2'):
            with ui.row().classes('w-full items-center gap-3'):
                # Status icon
                ui.icon(status_config['icon']).classes(f'text-{status_config["color"]}-500')

                # Location
                with ui.column().classes('flex-grow'):
                    ui.label(item.user_location or 'No location').classes('font-medium')
                    ui.label(item.user_description[:50] + '...' if len(item.user_description or '') > 50
                            else item.user_description or '').classes('text-sm text-gray-500')

                # Status badge
                ui.badge(status_config['label']).props(f'color={status_config["color"]}')

                # Error message if present
                if item.status == ItemStatus.ERROR and item.error_message:
                    ui.icon('info', color='red').tooltip(item.error_message)

    def _get_status_config(self, status: ItemStatus) -> dict:
        """Get status display configuration."""
        configs = {
            ItemStatus.PENDING: {'icon': 'hourglass_empty', 'color': 'grey', 'label': 'Pending'},
            ItemStatus.PROCESSING: {'icon': 'sync', 'color': 'blue', 'label': 'Processing'},
            ItemStatus.REVIEW_READY: {'icon': 'visibility', 'color': 'orange', 'label': 'Ready for Review'},
            ItemStatus.APPROVED: {'icon': 'check_circle', 'color': 'green', 'label': 'Approved'},
            ItemStatus.EXPORTED: {'icon': 'cloud_done', 'color': 'teal', 'label': 'Exported'},
            ItemStatus.ERROR: {'icon': 'error', 'color': 'red', 'label': 'Error'},
        }
        return configs.get(status, {'icon': 'help', 'color': 'grey', 'label': 'Unknown'})

    async def _start_processing(self) -> None:
        """Start processing pending items."""
        if self._is_processing:
            return

        self._is_processing = True
        self._start_btn.visible = False
        self._stop_btn.visible = True

        try:
            pending_items = [i for i in self._app_state.queue.get_all_items()
                           if i.status == ItemStatus.PENDING]

            if not pending_items:
                notify_info('No pending items to process')
                return

            total = len(pending_items)

            for idx, item in enumerate(pending_items):
                if not self._is_processing:
                    break

                # Update UI
                self._current_item_label.text = f'Processing: {item.user_location}'
                self._progress_bar.value = idx / total

                # Process item
                await self._process_item(item)

                # Refresh display
                self._refresh_items()
                self._update_pending_count()

            self._current_item_label.text = 'Processing complete'
            self._progress_bar.value = 1.0
            notify_success('Processing complete')

        except Exception as ex:
            notify_error(f'Processing error: {ex}')

        finally:
            self._is_processing = False
            self._start_btn.visible = True
            self._stop_btn.visible = False

    async def _process_item(self, item: InspectionItem) -> None:
        """Process a single item with AI."""
        try:
            # Mark as processing
            item.status = ItemStatus.PROCESSING
            self._app_state.queue.update_item(item)
            self._refresh_items()

            # Check if AI is configured
            if not self._app_state.config.gemini_api_key:
                item.status = ItemStatus.ERROR
                item.error_message = "Gemini API key not configured"
                self._app_state.queue.update_item(item)
                return

            # Import and use AI service
            from services.ai_service.gemini_client import GeminiClient
            from services.ai_service.prompt_templates import PromptTemplates
            from services.ai_service.response_parser import ResponseParser

            client = GeminiClient(
                api_key=self._app_state.config.gemini_api_key,
                model_name=self._app_state.config.ai_settings.model_name
            )

            # Build prompt
            prompt = PromptTemplates.inspection_analysis(
                location=item.user_location,
                description=item.user_description,
                chapter_hint=item.selected_chapter_file
            )

            # Call AI with image
            response = await asyncio.to_thread(
                client.analyze_image,
                item.photo_edited_path or item.photo_original_path,
                prompt
            )

            # Parse response
            parsed = ResponseParser.parse_inspection_response(response)

            # Update item with results
            item.ai_code_reference = parsed.get('code_reference', '')
            item.ai_violation_description = parsed.get('violation_description', '')
            item.ai_search_terms = parsed.get('search_terms', [])
            item.ai_confidence = parsed.get('confidence', 0.0)
            item.status = ItemStatus.REVIEW_READY

            self._app_state.queue.update_item(item)

        except Exception as ex:
            item.status = ItemStatus.ERROR
            item.error_message = str(ex)
            self._app_state.queue.update_item(item)

    def _stop_processing(self) -> None:
        """Stop processing."""
        self._is_processing = False
        notify_info('Processing stopped')

    def _update_pending_count(self) -> None:
        """Update the pending count label."""
        pending = len([i for i in self._app_state.queue.get_all_items()
                      if i.status == ItemStatus.PENDING])
        self._pending_label.text = f'Pending: {pending}'
