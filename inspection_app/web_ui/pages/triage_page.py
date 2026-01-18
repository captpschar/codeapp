"""
Phase 1: Triage page for image editing and metadata entry.
"""

from nicegui import ui, run
from pathlib import Path
from typing import Optional, List, Set
import base64
import io
from PIL import Image, ImageEnhance

from web_ui.app import get_app_state, notify_success, notify_error, notify_warning, notify_info


class TriagePage:
    """Phase 1 triage interface with batch folder loading."""

    def __init__(self):
        self._app_state = get_app_state()

        # Image batch state
        self._image_folder: Optional[Path] = None
        self._image_files: List[Path] = []
        self._current_index: int = 0

        # Current image state
        self._original_image: Optional[Image.Image] = None
        self._current_image: Optional[Image.Image] = None
        self._brightness: float = 1.0
        self._contrast: float = 1.0
        self._rotation: int = 0

        # Zoom/crop state
        self._zoom_level: float = 1.0
        self._crop_aspect: Optional[str] = None  # None = free, "4:3", "16:9", "1:1"

        # Selected code folders (multi-select)
        self._selected_folders: Set[str] = set()

        # Selected chapters
        self._selected_chapters: List[str] = []

        # UI elements
        self._image_element = None
        self._image_placeholder = None
        self._location_input = None
        self._description_input = None
        self._nav_label = None
        self._folder_checkboxes = {}
        self._chapter_dialog = None
        self._chapters_container = None
        self._selected_chapters_label = None
        self._queue_container = None
        self._brightness_slider = None
        self._contrast_slider = None
        self._zoom_slider = None

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
        with ui.column().classes('w-full h-full p-4 gap-2'):
            # Folder loading controls
            with ui.row().classes('w-full items-center gap-2'):
                ui.button('Load Folder', icon='folder_open', on_click=self._browse_folder).props('outline')

                ui.space()

                # Navigation controls
                ui.button(icon='skip_previous', on_click=self._prev_image).props('flat dense')
                self._nav_label = ui.label('0 / 0').classes('min-w-20 text-center')
                ui.button(icon='skip_next', on_click=self._next_image).props('flat dense')

            # Image adjustment toolbar
            with ui.card().classes('w-full'):
                with ui.row().classes('w-full items-center gap-2 flex-wrap'):
                    # Rotation
                    ui.button(icon='rotate_left', on_click=lambda: self._rotate(-90)).props('flat dense')
                    ui.button(icon='rotate_right', on_click=lambda: self._rotate(90)).props('flat dense')

                    ui.separator().props('vertical')

                    # Brightness
                    ui.label('Brightness:').classes('text-xs')
                    self._brightness_slider = ui.slider(
                        min=0.5, max=2.0, step=0.1, value=1.0,
                        on_change=lambda e: self._set_brightness(e.value)
                    ).classes('w-20')

                    # Contrast
                    ui.label('Contrast:').classes('text-xs')
                    self._contrast_slider = ui.slider(
                        min=0.5, max=2.0, step=0.1, value=1.0,
                        on_change=lambda e: self._set_contrast(e.value)
                    ).classes('w-20')

                    ui.separator().props('vertical')

                    # Zoom
                    ui.label('Zoom:').classes('text-xs')
                    self._zoom_slider = ui.slider(
                        min=0.5, max=3.0, step=0.1, value=1.0,
                        on_change=lambda e: self._set_zoom(e.value)
                    ).classes('w-20')

                    # Aspect ratio for crop
                    ui.label('Aspect:').classes('text-xs')
                    ui.select(
                        options=['Free', '4:3', '16:9', '1:1', '3:2'],
                        value='Free',
                        on_change=lambda e: self._set_aspect(e.value)
                    ).props('dense').classes('w-20')

                    ui.separator().props('vertical')

                    ui.button('Reset', icon='refresh', on_click=self._reset_image).props('flat dense')

            # Image display area
            with ui.card().classes('w-full flex-grow'):
                with ui.scroll_area().classes('w-full h-full'):
                    with ui.column().classes('w-full items-center justify-center min-h-80'):
                        self._image_element = ui.image('').classes('max-w-full object-contain')
                        self._image_element.visible = False

                        self._image_placeholder = ui.label('Load a folder to begin').classes(
                            'text-gray-400 text-lg py-20'
                        )

    def _render_metadata_panel(self) -> None:
        """Render the metadata entry panel."""
        with ui.column().classes('w-full h-full p-4 gap-3'):
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
            ).classes('w-full').props('rows=3')

            # Code folders selection (checkbox grid)
            ui.label('Code Folders').classes('text-sm font-medium mt-2')
            with ui.card().classes('w-full p-2'):
                self._render_folder_checkboxes()

            # Chapter selection button and display
            with ui.row().classes('w-full items-center gap-2'):
                ui.button('Select Chapters', icon='menu_book', on_click=self._show_chapter_dialog).props('outline')
                self._selected_chapters_label = ui.label('No chapters selected').classes('text-sm text-gray-500')

            # Create chapter selection dialog
            self._create_chapter_dialog()

            # Add to queue button
            ui.button(
                'Add to Queue',
                icon='add',
                on_click=self._add_to_queue
            ).classes('w-full').props('color=primary')

            ui.separator()

            # Queue preview
            with ui.row().classes('w-full items-center'):
                ui.label('Queue').classes('text-lg font-bold')
                ui.space()
                self._queue_count_label = ui.label('0 items').classes('text-sm text-gray-500')

            with ui.scroll_area().classes('flex-grow'):
                self._queue_container = ui.column().classes('w-full')
                self._refresh_queue()

    def _render_folder_checkboxes(self) -> None:
        """Render checkbox grid for code folders."""
        folder_names = self._app_state.list_code_folder_names()

        if not folder_names:
            ui.label('No code folders configured').classes('text-gray-400 text-sm')
            ui.label('Add folders in Settings').classes('text-gray-400 text-xs')
            return

        with ui.grid(columns=2).classes('w-full gap-1'):
            for name in folder_names:
                cb = ui.checkbox(
                    name,
                    value=name in self._selected_folders,
                    on_change=lambda e, n=name: self._toggle_folder(n, e.value)
                ).classes('text-sm')
                self._folder_checkboxes[name] = cb

    def _toggle_folder(self, folder_name: str, selected: bool) -> None:
        """Toggle folder selection."""
        if selected:
            self._selected_folders.add(folder_name)
        else:
            self._selected_folders.discard(folder_name)
        # Clear chapter selection when folders change
        self._selected_chapters = []
        self._update_chapters_label()

    def _create_chapter_dialog(self) -> None:
        """Create the chapter selection dialog."""
        with ui.dialog() as self._chapter_dialog:
            with ui.card().classes('w-96 max-h-96'):
                ui.label('Select Chapters').classes('text-lg font-bold mb-2')

                with ui.scroll_area().classes('h-64'):
                    self._chapters_container = ui.column().classes('w-full')

                with ui.row().classes('w-full justify-end gap-2 mt-4'):
                    ui.button('Clear All', on_click=self._clear_chapters).props('flat')
                    ui.button('Done', on_click=self._chapter_dialog.close).props('color=primary')

    def _show_chapter_dialog(self) -> None:
        """Show chapter selection dialog."""
        if not self._selected_folders:
            notify_warning('Please select at least one code folder first')
            return

        # Populate chapters from selected folders
        self._chapters_container.clear()

        with self._chapters_container:
            for folder_name in sorted(self._selected_folders):
                ui.label(folder_name).classes('font-medium text-sm mt-2 mb-1')

                chapters = self._app_state.list_chapters_in_folder(folder_name)
                if not chapters:
                    ui.label('No chapters found').classes('text-gray-400 text-xs ml-2')
                    continue

                with ui.grid(columns=1).classes('w-full gap-0 ml-2'):
                    for chapter in chapters:
                        chapter_key = f"{folder_name}:{chapter}"
                        ui.checkbox(
                            chapter,
                            value=chapter_key in self._selected_chapters,
                            on_change=lambda e, ck=chapter_key: self._toggle_chapter(ck, e.value)
                        ).classes('text-xs')

        self._chapter_dialog.open()

    def _toggle_chapter(self, chapter_key: str, selected: bool) -> None:
        """Toggle chapter selection."""
        if selected:
            if chapter_key not in self._selected_chapters:
                self._selected_chapters.append(chapter_key)
        else:
            if chapter_key in self._selected_chapters:
                self._selected_chapters.remove(chapter_key)
        self._update_chapters_label()

    def _clear_chapters(self) -> None:
        """Clear all chapter selections."""
        self._selected_chapters = []
        self._update_chapters_label()
        # Refresh dialog content
        self._show_chapter_dialog()

    def _update_chapters_label(self) -> None:
        """Update the chapters label."""
        count = len(self._selected_chapters)
        if count == 0:
            self._selected_chapters_label.text = 'No chapters selected'
        elif count == 1:
            self._selected_chapters_label.text = '1 chapter selected'
        else:
            self._selected_chapters_label.text = f'{count} chapters selected'

    async def _browse_folder(self) -> None:
        """Open folder browser to select image folder."""
        folder_path = await run.io_bound(self._select_folder_dialog)

        if folder_path:
            self._load_folder(folder_path)

    def _select_folder_dialog(self) -> Optional[str]:
        """Open native folder selection dialog."""
        try:
            import tkinter as tk
            from tkinter import filedialog

            root = tk.Tk()
            root.withdraw()
            root.attributes('-topmost', True)
            root.focus_force()

            folder_path = filedialog.askdirectory(title="Select Image Folder")
            root.destroy()

            return folder_path if folder_path else None
        except Exception:
            return None

    def _load_folder(self, folder_path: str) -> None:
        """Load all images from the selected folder."""
        folder = Path(folder_path)

        if not folder.exists() or not folder.is_dir():
            notify_error('Invalid folder path')
            return

        # Find all image files
        image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}
        self._image_files = sorted([
            f for f in folder.iterdir()
            if f.is_file() and f.suffix.lower() in image_extensions
        ])

        if not self._image_files:
            notify_warning('No images found in folder')
            return

        self._image_folder = folder
        self._current_index = 0

        notify_success(f'Loaded {len(self._image_files)} images')
        self._load_current_image()

    def _load_current_image(self) -> None:
        """Load the current image from the batch."""
        if not self._image_files or self._current_index >= len(self._image_files):
            return

        try:
            image_path = self._image_files[self._current_index]
            self._original_image = Image.open(image_path)

            if self._original_image.mode != 'RGB':
                self._original_image = self._original_image.convert('RGB')

            # Reset adjustments
            self._brightness = 1.0
            self._contrast = 1.0
            self._rotation = 0
            self._zoom_level = 1.0

            if self._brightness_slider:
                self._brightness_slider.value = 1.0
            if self._contrast_slider:
                self._contrast_slider.value = 1.0
            if self._zoom_slider:
                self._zoom_slider.value = 1.0

            self._current_image = self._original_image.copy()
            self._update_image_display()
            self._update_nav_label()

        except Exception as ex:
            notify_error(f'Failed to load image: {ex}')

    def _prev_image(self) -> None:
        """Go to previous image."""
        if not self._image_files:
            return
        self._current_index = (self._current_index - 1) % len(self._image_files)
        self._load_current_image()

    def _next_image(self) -> None:
        """Go to next image."""
        if not self._image_files:
            return
        self._current_index = (self._current_index + 1) % len(self._image_files)
        self._load_current_image()

    def _update_nav_label(self) -> None:
        """Update navigation label."""
        if self._image_files:
            self._nav_label.text = f'{self._current_index + 1} / {len(self._image_files)}'
        else:
            self._nav_label.text = '0 / 0'

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

        # Apply zoom (resize)
        if self._zoom_level != 1.0:
            new_width = int(img.width * self._zoom_level)
            new_height = int(img.height * self._zoom_level)
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

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

    def _set_zoom(self, value: float) -> None:
        """Set zoom level."""
        if self._original_image is None:
            return
        self._zoom_level = value
        self._update_image_display()

    def _set_aspect(self, value: str) -> None:
        """Set crop aspect ratio."""
        if value == 'Free':
            self._crop_aspect = None
        else:
            self._crop_aspect = value

    def _reset_image(self) -> None:
        """Reset all image adjustments."""
        if self._original_image is None:
            return
        self._brightness = 1.0
        self._contrast = 1.0
        self._rotation = 0
        self._zoom_level = 1.0

        if self._brightness_slider:
            self._brightness_slider.value = 1.0
        if self._contrast_slider:
            self._contrast_slider.value = 1.0
        if self._zoom_slider:
            self._zoom_slider.value = 1.0

        self._current_image = self._original_image.copy()
        self._update_image_display()

    def _add_to_queue(self) -> None:
        """Add current item to the queue."""
        # Validate inputs
        if not self._current_image:
            notify_warning('Please load an image first')
            return

        if not self._location_input.value:
            notify_warning('Please enter a location')
            return

        if not self._selected_folders:
            notify_warning('Please select at least one code folder')
            return

        if not self._selected_chapters:
            notify_warning('Please select at least one chapter')
            return

        try:
            # Save edited image
            output_dir = self._app_state.get_output_dir() / "edited"
            output_dir.mkdir(parents=True, exist_ok=True)

            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            edited_path = output_dir / f"edited_{timestamp}.jpg"
            self._current_image.save(str(edited_path), quality=95)

            # Get original path
            original_path = str(self._image_files[self._current_index]) if self._image_files else ""

            # Import here to avoid circular imports
            from core.inspection_item import InspectionItem, ItemStatus

            # Create inspection item
            item = InspectionItem()
            item.photo_original_path = original_path
            item.photo_edited_path = str(edited_path)
            item.user_location = self._location_input.value
            item.user_description = self._description_input.value or ""
            item.selected_code_folders = list(self._selected_folders)
            item.selected_chapters = self._selected_chapters.copy()
            item.status = ItemStatus.PENDING

            # Add to queue
            self._app_state.queue.add_item(item)

            # Move to next image automatically
            if self._image_files and len(self._image_files) > 1:
                self._next_image()

            # Clear text inputs but keep folder/chapter selections
            self._location_input.value = ""
            self._description_input.value = ""

            self._refresh_queue()
            notify_success('Item added to queue')

        except Exception as ex:
            notify_error(f'Failed to add item: {ex}')

    def _refresh_queue(self) -> None:
        """Refresh the queue display."""
        self._queue_container.clear()

        items = self._app_state.queue.get_all_items()

        if hasattr(self, '_queue_count_label'):
            self._queue_count_label.text = f'{len(items)} items'

        with self._queue_container:
            if not items:
                ui.label('No items in queue').classes('text-gray-400 text-sm')
                return

            # Import here to avoid circular imports
            from core.inspection_item import ItemStatus

            for item in items[-10:]:  # Show last 10
                with ui.card().classes('w-full mb-1 p-2'):
                    with ui.row().classes('items-center gap-2'):
                        # Status icon
                        icon = self._get_status_icon(item.status)
                        ui.icon(icon).classes('text-sm')

                        with ui.column().classes('flex-grow gap-0'):
                            ui.label(item.user_location or 'No location').classes('text-sm font-medium')
                            chapters_count = len(getattr(item, 'selected_chapters', []) or [])
                            ui.label(f'{chapters_count} chapters').classes('text-xs text-gray-400')

                        ui.badge(item.status.value).props('dense')

    def _get_status_icon(self, status) -> str:
        """Get icon for status."""
        from core.inspection_item import ItemStatus
        icons = {
            ItemStatus.PENDING: 'hourglass_empty',
            ItemStatus.PROCESSING: 'sync',
            ItemStatus.REVIEW_READY: 'visibility',
            ItemStatus.APPROVED: 'check_circle',
            ItemStatus.EXPORTED: 'cloud_done',
            ItemStatus.ERROR: 'error',
        }
        return icons.get(status, 'help')
