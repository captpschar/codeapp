"""
Phase 1: Triage page for image editing and metadata entry.
"""

from nicegui import ui, events
from pathlib import Path
from typing import Optional
import base64
import io
from PIL import Image, ImageEnhance

from ..app import get_app_state, notify_success, notify_error, notify_warning
from ...core.inspection_item import InspectionItem, ItemStatus


class TriagePage:
    """Phase 1 triage interface."""

    def __init__(self):
        self._app_state = get_app_state()
        self._current_image_path: str = ""
        self._original_image: Optional[Image.Image] = None
        self._current_image: Optional[Image.Image] = None
        self._brightness: float = 1.0
        self._contrast: float = 1.0
        self._rotation: int = 0

        # UI elements
        self._image_element = None
        self._location_input = None
        self._description_input = None
        self._folder_select = None
        self._chapter_select = None
        self._queue_container = None

    def render(self) -> None:
        """Render the triage page."""
        with ui.splitter(value=60).classes('w-full h-full') as splitter:
            # Left panel: Image editing
            with splitter.before:
                self._render_image_panel()

            # Right panel: Metadata and queue
            with splitter.after:
                self._render_metadata_panel()

    def _render_image_panel(self) -> None:
        """Render the image editing panel."""
        with ui.column().classes('w-full h-full p-4'):
            # Upload button
            with ui.row().classes('w-full items-center gap-2'):
                ui.upload(
                    label='Load Image',
                    auto_upload=True,
                    on_upload=self._on_image_upload
                ).props('accept=image/*').classes('flex-grow')

            # Toolbar
            with ui.card().classes('w-full'):
                with ui.row().classes('w-full items-center gap-2 flex-wrap'):
                    ui.button(icon='rotate_left', on_click=lambda: self._rotate(-90)).props('flat')
                    ui.button(icon='rotate_right', on_click=lambda: self._rotate(90)).props('flat')

                    ui.separator().props('vertical')

                    ui.label('Brightness:').classes('text-sm')
                    self._brightness_slider = ui.slider(
                        min=0.5, max=2.0, step=0.1, value=1.0,
                        on_change=lambda e: self._set_brightness(e.value)
                    ).classes('w-24')

                    ui.label('Contrast:').classes('text-sm')
                    self._contrast_slider = ui.slider(
                        min=0.5, max=2.0, step=0.1, value=1.0,
                        on_change=lambda e: self._set_contrast(e.value)
                    ).classes('w-24')

                    ui.separator().props('vertical')

                    ui.button('Reset', icon='refresh', on_click=self._reset_image).props('flat')

            # Image display
            with ui.scroll_area().classes('w-full flex-grow'):
                with ui.row().classes('w-full justify-center'):
                    self._image_element = ui.image('').classes('max-h-96 object-contain')
                    self._image_element.visible = False

                    self._image_placeholder = ui.label('No image loaded').classes(
                        'text-gray-400 py-20'
                    )

    def _render_metadata_panel(self) -> None:
        """Render the metadata entry panel."""
        with ui.column().classes('w-full h-full p-4 gap-4'):
            ui.label('Item Details').classes('text-lg font-bold')

            # Location input
            self._location_input = ui.input(
                label='Location',
                placeholder='e.g., Building A, Room 101'
            ).classes('w-full')

            # Description input
            self._description_input = ui.textarea(
                label='Description',
                placeholder='Describe what needs inspection...'
            ).classes('w-full')

            # Code folder selector
            folder_names = self._app_state.list_code_folder_names()
            self._folder_select = ui.select(
                label='Code Folder',
                options=folder_names,
                on_change=self._on_folder_changed
            ).classes('w-full')

            # Chapter selector
            self._chapter_select = ui.select(
                label='Code Chapter',
                options=[]
            ).classes('w-full')

            # Add to queue button
            ui.button(
                'Add to Queue',
                icon='add',
                on_click=self._add_to_queue
            ).classes('w-full')

            ui.separator()

            # Queue preview
            ui.label('Queue').classes('text-lg font-bold')

            self._queue_container = ui.column().classes('w-full')
            self._refresh_queue()

    def _on_image_upload(self, e: events.UploadEventArguments) -> None:
        """Handle image upload."""
        try:
            content = e.content.read()
            self._original_image = Image.open(io.BytesIO(content))

            if self._original_image.mode != 'RGB':
                self._original_image = self._original_image.convert('RGB')

            # Save to temp location
            output_dir = self._app_state.get_output_dir() / "uploads"
            output_dir.mkdir(parents=True, exist_ok=True)

            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            self._current_image_path = str(output_dir / f"upload_{timestamp}.jpg")
            self._original_image.save(self._current_image_path, quality=95)

            self._current_image = self._original_image.copy()
            self._brightness = 1.0
            self._contrast = 1.0
            self._rotation = 0

            self._update_image_display()
            notify_success('Image loaded')
        except Exception as ex:
            notify_error(f'Failed to load image: {ex}')

    def _update_image_display(self) -> None:
        """Update the displayed image with current edits."""
        if self._original_image is None:
            return

        # Apply transformations
        img = self._original_image.copy()

        # Apply rotation
        if self._rotation != 0:
            img = img.rotate(-self._rotation, expand=True)

        # Apply brightness/contrast
        if self._brightness != 1.0:
            enhancer = ImageEnhance.Brightness(img)
            img = enhancer.enhance(self._brightness)

        if self._contrast != 1.0:
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(self._contrast)

        self._current_image = img

        # Convert to base64 for display
        buffer = io.BytesIO()
        img.save(buffer, format='JPEG', quality=85)
        b64 = base64.b64encode(buffer.getvalue()).decode()

        self._image_element.source = f'data:image/jpeg;base64,{b64}'
        self._image_element.visible = True
        self._image_placeholder.visible = False

    def _rotate(self, degrees: int) -> None:
        """Rotate the image."""
        if self._original_image is None:
            return
        self._rotation = (self._rotation + degrees) % 360
        self._update_image_display()

    def _set_brightness(self, value: float) -> None:
        """Set brightness level."""
        if self._original_image is None:
            return
        self._brightness = value
        self._update_image_display()

    def _set_contrast(self, value: float) -> None:
        """Set contrast level."""
        if self._original_image is None:
            return
        self._contrast = value
        self._update_image_display()

    def _reset_image(self) -> None:
        """Reset all image adjustments."""
        if self._original_image is None:
            return
        self._brightness = 1.0
        self._contrast = 1.0
        self._rotation = 0
        self._brightness_slider.value = 1.0
        self._contrast_slider.value = 1.0
        self._current_image = self._original_image.copy()
        self._update_image_display()

    def _on_folder_changed(self, e) -> None:
        """Handle code folder selection change."""
        folder_name = e.value
        if folder_name:
            chapters = self._app_state.list_chapters_in_folder(folder_name)
            self._chapter_select.options = chapters
            self._chapter_select.update()

    def _add_to_queue(self) -> None:
        """Add current item to the queue."""
        # Validate inputs
        if not self._current_image:
            notify_warning('Please load an image first')
            return

        if not self._location_input.value:
            notify_warning('Please enter a location')
            return

        if not self._folder_select.value:
            notify_warning('Please select a code folder')
            return

        if not self._chapter_select.value:
            notify_warning('Please select a code chapter')
            return

        try:
            # Save edited image
            output_dir = self._app_state.get_output_dir() / "edited"
            output_dir.mkdir(parents=True, exist_ok=True)

            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            edited_path = output_dir / f"edited_{timestamp}.jpg"
            self._current_image.save(str(edited_path), quality=95)

            # Create inspection item
            item = InspectionItem()
            item.photo_original_path = self._current_image_path
            item.photo_edited_path = str(edited_path)
            item.user_location = self._location_input.value
            item.user_description = self._description_input.value or ""
            item.selected_code_folder = self._folder_select.value
            item.selected_chapter_file = self._chapter_select.value
            item.status = ItemStatus.PENDING

            # Add to queue
            self._app_state.queue.add_item(item)

            # Clear form
            self._clear_form()
            self._refresh_queue()

            notify_success('Item added to queue')
        except Exception as ex:
            notify_error(f'Failed to add item: {ex}')

    def _clear_form(self) -> None:
        """Clear the form after adding to queue."""
        self._current_image_path = ""
        self._original_image = None
        self._current_image = None
        self._brightness = 1.0
        self._contrast = 1.0
        self._rotation = 0

        self._image_element.visible = False
        self._image_placeholder.visible = True
        self._location_input.value = ""
        self._description_input.value = ""
        self._folder_select.value = None
        self._chapter_select.value = None
        self._chapter_select.options = []

    def _refresh_queue(self) -> None:
        """Refresh the queue display."""
        self._queue_container.clear()

        items = self._app_state.queue.get_all_items()

        with self._queue_container:
            if not items:
                ui.label('No items in queue').classes('text-gray-400')
                return

            for item in items[:10]:  # Show last 10
                with ui.card().classes('w-full mb-1'):
                    with ui.row().classes('items-center gap-2'):
                        # Status icon
                        icon = self._get_status_icon(item.status)
                        ui.icon(icon)

                        ui.label(item.user_location or 'No location').classes('font-medium')

                        ui.space()

                        ui.label(item.status.value).classes('text-xs text-gray-500')

    def _get_status_icon(self, status: ItemStatus) -> str:
        """Get icon for status."""
        icons = {
            ItemStatus.PENDING: 'hourglass_empty',
            ItemStatus.PROCESSING: 'sync',
            ItemStatus.REVIEW_READY: 'visibility',
            ItemStatus.APPROVED: 'check_circle',
            ItemStatus.EXPORTED: 'cloud_done',
            ItemStatus.ERROR: 'error',
        }
        return icons.get(status, 'help')
