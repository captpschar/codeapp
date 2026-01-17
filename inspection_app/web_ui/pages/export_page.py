"""
Phase 4: Export page for Google Docs export.
"""

from nicegui import ui
from pathlib import Path
from typing import Optional, List
import asyncio

from ..app import get_app_state, notify_success, notify_error, notify_warning, notify_info
from ...core.inspection_item import InspectionItem, ItemStatus


class ExportPage:
    """Phase 4 export interface."""

    def __init__(self):
        self._app_state = get_app_state()
        self._is_exporting = False
        self._items_container = None
        self._progress_bar = None
        self._status_label = None

    def render(self) -> None:
        """Render the export page."""
        with ui.column().classes('w-full max-w-4xl mx-auto p-4 gap-6'):
            ui.label('Export to Google Docs').classes('text-2xl font-bold')

            # Preflight check
            with ui.card().classes('w-full'):
                ui.label('Preflight Check').classes('text-lg font-bold mb-4')

                self._preflight_container = ui.column().classes('w-full gap-2')
                self._run_preflight()

            # Approved items
            with ui.card().classes('w-full'):
                with ui.row().classes('w-full items-center mb-4'):
                    ui.label('Approved Items').classes('text-lg font-bold')
                    ui.space()

                    approved_count = len([i for i in self._app_state.queue.get_all_items()
                                         if i.status == ItemStatus.APPROVED])
                    ui.badge(f'{approved_count} items').classes('bg-green-100')

                with ui.scroll_area().classes('h-64'):
                    self._items_container = ui.column().classes('w-full')
                    self._refresh_items()

            # Export controls
            with ui.card().classes('w-full'):
                ui.label('Export').classes('text-lg font-bold mb-4')

                with ui.row().classes('w-full items-center gap-4'):
                    self._export_btn = ui.button(
                        'Export to Google Docs',
                        icon='cloud_upload',
                        on_click=self._start_export
                    )

                    self._stop_btn = ui.button(
                        'Stop',
                        icon='stop',
                        on_click=self._stop_export
                    ).props('color=negative')
                    self._stop_btn.visible = False

                self._progress_bar = ui.linear_progress(value=0).classes('w-full mt-4')
                self._progress_bar.visible = False

                self._status_label = ui.label('').classes('text-sm text-gray-600 mt-2')

            # Export history
            with ui.card().classes('w-full'):
                ui.label('Export History').classes('text-lg font-bold mb-4')

                self._history_container = ui.column().classes('w-full')
                self._show_history()

    def _run_preflight(self) -> None:
        """Run preflight checks."""
        self._preflight_container.clear()

        config = self._app_state.config
        checks = []

        # Check API key
        has_api_key = bool(config.gemini_api_key)
        checks.append(('Gemini API Key', has_api_key))

        # Check Google credentials
        creds_path = config.google_docs_credentials_path
        has_creds = creds_path and Path(creds_path).exists()
        checks.append(('Google Credentials', has_creds))

        # Check approved items
        approved = [i for i in self._app_state.queue.get_all_items()
                   if i.status == ItemStatus.APPROVED]
        has_items = len(approved) > 0
        checks.append((f'Approved Items ({len(approved)})', has_items))

        # Check items have snapshots
        items_with_snapshots = [i for i in approved
                               if i.snapshot_path and Path(i.snapshot_path).exists()]
        all_have_snapshots = len(items_with_snapshots) == len(approved) if approved else False
        checks.append((f'Items with Snapshots ({len(items_with_snapshots)}/{len(approved)})', all_have_snapshots))

        with self._preflight_container:
            for name, passed in checks:
                with ui.row().classes('items-center gap-2'):
                    if passed:
                        ui.icon('check_circle').classes('text-green-500')
                    else:
                        ui.icon('cancel').classes('text-red-500')
                    ui.label(name)

            # Overall status
            all_passed = all(passed for _, passed in checks)

            if all_passed:
                ui.label('Ready for export').classes('text-green-600 font-bold mt-4')
            else:
                ui.label('Please resolve issues before exporting').classes('text-red-600 font-bold mt-4')

    def _refresh_items(self) -> None:
        """Refresh the approved items list."""
        self._items_container.clear()

        items = [i for i in self._app_state.queue.get_all_items()
                if i.status == ItemStatus.APPROVED]

        with self._items_container:
            if not items:
                ui.label('No approved items').classes('text-gray-400 py-4')
                return

            for item in items:
                self._render_item_row(item)

    def _render_item_row(self, item: InspectionItem) -> None:
        """Render a single item row."""
        has_snapshot = item.snapshot_path and Path(item.snapshot_path).exists()

        with ui.card().classes('w-full mb-2'):
            with ui.row().classes('w-full items-center gap-3'):
                ui.icon('check_circle').classes('text-green-500')

                with ui.column().classes('flex-grow'):
                    ui.label(item.user_location or 'No location').classes('font-medium')
                    ui.label(item.ai_code_reference or 'No code reference').classes('text-sm text-gray-500')

                if has_snapshot:
                    ui.icon('image').classes('text-blue-500').tooltip('Has snapshot')
                else:
                    ui.icon('image_not_supported').classes('text-red-500').tooltip('No snapshot')

    def _show_history(self) -> None:
        """Show export history."""
        self._history_container.clear()

        exported = [i for i in self._app_state.queue.get_all_items()
                   if i.status == ItemStatus.EXPORTED]

        with self._history_container:
            if not exported:
                ui.label('No exports yet').classes('text-gray-400')
                return

            for item in exported:
                with ui.row().classes('w-full items-center gap-2'):
                    ui.icon('cloud_done').classes('text-teal-500')
                    ui.label(item.user_location or 'Unknown')

                    if item.google_doc_url:
                        ui.link('View Doc', item.google_doc_url, new_tab=True).classes('text-blue-500')

    async def _start_export(self) -> None:
        """Start the export process."""
        if self._is_exporting:
            return

        # Get approved items
        items = [i for i in self._app_state.queue.get_all_items()
                if i.status == ItemStatus.APPROVED]

        if not items:
            notify_warning('No approved items to export')
            return

        # Check credentials
        config = self._app_state.config
        if not config.google_docs_credentials_path:
            notify_error('Google credentials not configured')
            return

        creds_path = Path(config.google_docs_credentials_path)
        if not creds_path.exists():
            notify_error('Google credentials file not found')
            return

        self._is_exporting = True
        self._export_btn.visible = False
        self._stop_btn.visible = True
        self._progress_bar.visible = True
        self._progress_bar.value = 0

        try:
            # Import services
            from ...services.google_docs_service.auth_manager import GoogleAuthManager
            from ...services.google_docs_service.doc_generator import GoogleDocGenerator
            from ...services.google_docs_service.image_uploader import ImageUploader

            # Authenticate
            self._status_label.text = 'Authenticating with Google...'
            auth_manager = GoogleAuthManager(creds_path)

            try:
                credentials = await asyncio.to_thread(auth_manager.get_credentials)
            except Exception as ex:
                notify_error(f'Authentication failed: {ex}')
                return

            # Create document generator
            doc_generator = GoogleDocGenerator(credentials)
            image_uploader = ImageUploader(credentials)

            # Create the document
            self._status_label.text = 'Creating Google Doc...'

            from datetime import datetime
            doc_title = f"Inspection Report - {datetime.now().strftime('%Y-%m-%d %H:%M')}"

            doc_id = await asyncio.to_thread(doc_generator.create_document, doc_title)

            if not doc_id:
                notify_error('Failed to create Google Doc')
                return

            doc_url = f"https://docs.google.com/document/d/{doc_id}/edit"

            # Export each item
            total = len(items)
            for idx, item in enumerate(items):
                if not self._is_exporting:
                    break

                self._status_label.text = f'Exporting item {idx + 1} of {total}...'
                self._progress_bar.value = idx / total

                await self._export_item(item, doc_generator, image_uploader, doc_id)

                # Mark as exported
                item.status = ItemStatus.EXPORTED
                item.google_doc_url = doc_url
                self._app_state.queue.update_item(item)

            self._progress_bar.value = 1.0
            self._status_label.text = 'Export complete!'

            notify_success(f'Exported {total} items to Google Docs')

            # Refresh displays
            self._refresh_items()
            self._show_history()
            self._run_preflight()

        except Exception as ex:
            notify_error(f'Export failed: {ex}')
            self._status_label.text = f'Error: {ex}'

        finally:
            self._is_exporting = False
            self._export_btn.visible = True
            self._stop_btn.visible = False

    async def _export_item(
        self,
        item: InspectionItem,
        doc_generator,
        image_uploader,
        doc_id: str
    ) -> None:
        """Export a single item to the document."""
        # Add heading
        await asyncio.to_thread(
            doc_generator.add_heading,
            doc_id,
            item.user_location or 'Inspection Item'
        )

        # Add description
        if item.user_description:
            await asyncio.to_thread(
                doc_generator.add_paragraph,
                doc_id,
                f"Description: {item.user_description}"
            )

        # Add code reference
        if item.ai_code_reference:
            await asyncio.to_thread(
                doc_generator.add_paragraph,
                doc_id,
                f"Code Reference: {item.ai_code_reference}"
            )

        # Add violation
        if item.ai_violation_description:
            await asyncio.to_thread(
                doc_generator.add_paragraph,
                doc_id,
                f"Violation: {item.ai_violation_description}"
            )

        # Add photo
        photo_path = item.photo_edited_path or item.photo_original_path
        if photo_path and Path(photo_path).exists():
            try:
                image_url = await asyncio.to_thread(
                    image_uploader.upload_image,
                    photo_path
                )
                if image_url:
                    await asyncio.to_thread(
                        doc_generator.add_image,
                        doc_id,
                        image_url
                    )
            except Exception:
                pass  # Continue even if image upload fails

        # Add snapshot
        if item.snapshot_path and Path(item.snapshot_path).exists():
            try:
                image_url = await asyncio.to_thread(
                    image_uploader.upload_image,
                    item.snapshot_path
                )
                if image_url:
                    await asyncio.to_thread(
                        doc_generator.add_image,
                        doc_id,
                        image_url
                    )
            except Exception:
                pass

        # Add separator
        await asyncio.to_thread(
            doc_generator.add_paragraph,
            doc_id,
            "---"
        )

    def _stop_export(self) -> None:
        """Stop the export process."""
        self._is_exporting = False
        notify_info('Export stopped')
