"""
Image editing operations.
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
        """Crop image to region. box: (left, top, right, bottom)"""
        if self._current_image:
            self._current_image = self._current_image.crop(box)

    def rotate(self, degrees: float, expand: bool = True) -> None:
        """Rotate image by degrees (counter-clockwise)."""
        if self._current_image:
            self._current_image = self._current_image.rotate(
                degrees, expand=expand, resample=Image.BICUBIC
            )

    def adjust_brightness(self, factor: float) -> None:
        """Adjust brightness. 1.0 = original, < 1.0 darker, > 1.0 brighter"""
        if self._current_image:
            enhancer = ImageEnhance.Brightness(self._current_image)
            self._current_image = enhancer.enhance(factor)

    def adjust_contrast(self, factor: float) -> None:
        """Adjust contrast. 1.0 = original"""
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
        """Save current image to file."""
        if not self._current_image:
            raise ValueError("No image loaded")

        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        self._current_image.save(str(path), quality=quality)
        return path

    @property
    def source_path(self) -> Optional[Path]:
        """Get source file path."""
        return self._source_path
