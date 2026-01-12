"""
PDF page rendering to images.
"""

from typing import Optional, Tuple
from PIL import Image
import io
from .pdf_reader import PDFReader


class PDFPageRenderer:
    """Render PDF pages to images."""

    def __init__(self, reader: PDFReader, default_dpi: int = 150):
        self._reader = reader
        self._default_dpi = default_dpi

    def render_page(
        self,
        page_num: int,
        dpi: Optional[int] = None
    ) -> Optional[Image.Image]:
        """Render entire page to PIL Image."""
        page = self._reader.get_page(page_num)
        if not page:
            return None

        dpi = dpi or self._default_dpi
        zoom = dpi / 72.0
        matrix = page.get_pixmap(matrix=page.derotation_matrix * page.transformation_matrix)
        matrix = page.get_pixmap(dpi=dpi)

        # Convert to PIL Image
        img_data = matrix.tobytes("ppm")
        return Image.open(io.BytesIO(img_data))

    def render_page_region(
        self,
        page_num: int,
        rect: Tuple[float, float, float, float],
        dpi: Optional[int] = None
    ) -> Optional[Image.Image]:
        """Render specific region of page."""
        page = self._reader.get_page(page_num)
        if not page:
            return None

        dpi = dpi or self._default_dpi
        import fitz
        clip = fitz.Rect(rect)
        matrix = fitz.Matrix(dpi / 72.0, dpi / 72.0)
        pixmap = page.get_pixmap(matrix=matrix, clip=clip)

        img_data = pixmap.tobytes("ppm")
        return Image.open(io.BytesIO(img_data))

    def get_page_as_qimage(self, page_num: int, dpi: Optional[int] = None):
        """Render page for Qt display."""
        from PyQt6.QtGui import QImage, QPixmap

        page = self._reader.get_page(page_num)
        if not page:
            return None

        dpi = dpi or self._default_dpi
        pixmap = page.get_pixmap(dpi=dpi)

        # Convert to QImage
        img = QImage(
            pixmap.samples,
            pixmap.width,
            pixmap.height,
            pixmap.stride,
            QImage.Format.Format_RGB888
        )
        return img.copy()  # Return copy to ensure data persists

    def get_page_as_qpixmap(self, page_num: int, dpi: Optional[int] = None):
        """Render page as QPixmap."""
        from PyQt6.QtGui import QPixmap
        qimg = self.get_page_as_qimage(page_num, dpi)
        if qimg:
            return QPixmap.fromImage(qimg)
        return None
