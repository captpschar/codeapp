"""
Map between screen coordinates and PDF coordinates.
"""

from typing import Tuple, Optional


class CoordinateMapper:
    """Map coordinates between PDF space and screen/widget space."""

    def __init__(self):
        self._pdf_width: float = 0
        self._pdf_height: float = 0
        self._widget_width: int = 0
        self._widget_height: int = 0
        self._scale: float = 1.0
        self._offset_x: float = 0
        self._offset_y: float = 0

    def set_pdf_size(self, width: float, height: float) -> None:
        """Set PDF page dimensions."""
        self._pdf_width = width
        self._pdf_height = height
        self._update_scale()

    def set_widget_size(self, width: int, height: int) -> None:
        """Set widget display dimensions."""
        self._widget_width = width
        self._widget_height = height
        self._update_scale()

    def _update_scale(self) -> None:
        """Calculate scale factor to fit PDF in widget."""
        if self._pdf_width == 0 or self._pdf_height == 0:
            return
        if self._widget_width == 0 or self._widget_height == 0:
            return

        scale_x = self._widget_width / self._pdf_width
        scale_y = self._widget_height / self._pdf_height
        self._scale = min(scale_x, scale_y)

        # Center the content
        scaled_width = self._pdf_width * self._scale
        scaled_height = self._pdf_height * self._scale
        self._offset_x = (self._widget_width - scaled_width) / 2
        self._offset_y = (self._widget_height - scaled_height) / 2

    def screen_to_pdf(self, x: int, y: int) -> Tuple[float, float]:
        """Convert screen coordinates to PDF coordinates."""
        if self._scale == 0:
            return (0, 0)
        pdf_x = (x - self._offset_x) / self._scale
        pdf_y = (y - self._offset_y) / self._scale
        return (pdf_x, pdf_y)

    def pdf_to_screen(self, x: float, y: float) -> Tuple[int, int]:
        """Convert PDF coordinates to screen coordinates."""
        screen_x = int(x * self._scale + self._offset_x)
        screen_y = int(y * self._scale + self._offset_y)
        return (screen_x, screen_y)

    def screen_rect_to_pdf(
        self,
        x1: int, y1: int, x2: int, y2: int
    ) -> Tuple[float, float, float, float]:
        """Convert screen rectangle to PDF rectangle."""
        pdf_x1, pdf_y1 = self.screen_to_pdf(x1, y1)
        pdf_x2, pdf_y2 = self.screen_to_pdf(x2, y2)
        # Ensure proper ordering
        return (
            min(pdf_x1, pdf_x2),
            min(pdf_y1, pdf_y2),
            max(pdf_x1, pdf_x2),
            max(pdf_y1, pdf_y2)
        )

    def pdf_rect_to_screen(
        self,
        x1: float, y1: float, x2: float, y2: float
    ) -> Tuple[int, int, int, int]:
        """Convert PDF rectangle to screen rectangle."""
        s_x1, s_y1 = self.pdf_to_screen(x1, y1)
        s_x2, s_y2 = self.pdf_to_screen(x2, y2)
        return (s_x1, s_y1, s_x2, s_y2)

    @property
    def scale(self) -> float:
        """Get current scale factor."""
        return self._scale
