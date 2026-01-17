"""
Image viewer component with editing controls.
"""

from nicegui import ui
from pathlib import Path
from typing import Optional, Callable
import base64
from PIL import Image
import io


class ImageViewer:
    """Interactive image viewer with basic editing."""

    def __init__(self, on_image_edited: Optional[Callable] = None):
        self._on_image_edited = on_image_edited
        self._current_path: str = ""
        self._original_image: Optional[Image.Image] = None
        self._current_image: Optional[Image.Image] = None
        self._brightness: float = 1.0
        self._contrast: float = 1.0
        self._rotation: int = 0
        self._image_element = None
        self._container = None

    def render(self) -> ui.element:
        """Render the image viewer component."""
        with ui.card().classes('w-full') as self._container:
            # Toolbar
            with ui.row().classes('w-full items-center gap-2 mb-2'):
                ui.button(icon='rotate_left', on_click=lambda: self._rotate(-90)).props('flat')
                ui.button(icon='rotate_right', on_click=lambda: self._rotate(90)).props('flat')

                ui.separator().props('vertical')

                ui.label('Brightness:').classes('text-sm')
                ui.slider(min=0.5, max=2.0, step=0.1, value=1.0,
                         on_change=lambda e: self._set_brightness(e.value)).classes('w-24')

                ui.label('Contrast:').classes('text-sm')
                ui.slider(min=0.5, max=2.0, step=0.1, value=1.0,
                         on_change=lambda e: self._set_contrast(e.value)).classes('w-24')

                ui.separator().props('vertical')

                ui.button('Reset', on_click=self._reset).props('flat')

            # Image display
            with ui.row().classes('w-full justify-center'):
                self._image_element = ui.image('').classes('max-h-96 object-contain')
                self._image_element.visible = False

                self._placeholder = ui.label('No image loaded').classes('text-gray-400 py-20')

        return self._container

    def load_image(self, path: str) -> None:
        """Load an image from path."""
        if not path or not Path(path).exists():
            return

        self._current_path = path
        self._original_image = Image.open(path)
        if self._original_image.mode != 'RGB':
            self._original_image = self._original_image.convert('RGB')
        self._current_image = self._original_image.copy()
        self._brightness = 1.0
        self._contrast = 1.0
        self._rotation = 0
        self._update_display()

    def _update_display(self) -> None:
        """Update the displayed image."""
        if self._current_image is None:
            return

        # Apply transformations
        img = self._original_image.copy()

        # Apply rotation
        if self._rotation != 0:
            img = img.rotate(-self._rotation, expand=True)

        # Apply brightness/contrast
        if self._brightness != 1.0 or self._contrast != 1.0:
            from PIL import ImageEnhance
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
        self._placeholder.visible = False

        if self._on_image_edited:
            self._on_image_edited()

    def _rotate(self, degrees: int) -> None:
        """Rotate the image."""
        if self._original_image is None:
            return
        self._rotation = (self._rotation + degrees) % 360
        self._update_display()

    def _set_brightness(self, value: float) -> None:
        """Set brightness level."""
        if self._original_image is None:
            return
        self._brightness = value
        self._update_display()

    def _set_contrast(self, value: float) -> None:
        """Set contrast level."""
        if self._original_image is None:
            return
        self._contrast = value
        self._update_display()

    def _reset(self) -> None:
        """Reset all adjustments."""
        if self._original_image is None:
            return
        self._brightness = 1.0
        self._contrast = 1.0
        self._rotation = 0
        self._current_image = self._original_image.copy()
        self._update_display()

    def get_current_image(self) -> Optional[Image.Image]:
        """Get the current edited image."""
        return self._current_image

    def save_current(self, path: str) -> bool:
        """Save the current image to path."""
        if self._current_image is None:
            return False
        try:
            Path(path).parent.mkdir(parents=True, exist_ok=True)
            self._current_image.save(path, quality=95)
            return True
        except Exception:
            return False

    def clear(self) -> None:
        """Clear the current image."""
        self._current_path = ""
        self._original_image = None
        self._current_image = None
        if self._image_element:
            self._image_element.visible = False
        if self._placeholder:
            self._placeholder.visible = True
