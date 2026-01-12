"""
Create snapshots from PDF regions.
"""

from pathlib import Path
from typing import Tuple, Optional
from PIL import Image


class SnapshotCreator:
    """Create and save PDF region snapshots."""

    def __init__(self, page_renderer, snapshot_dpi: int = 300):
        self._renderer = page_renderer
        self._dpi = snapshot_dpi

    def create_snapshot(
        self,
        page_num: int,
        rect: Tuple[float, float, float, float],
        output_dir: Path,
        base_filename: str
    ) -> Optional[Path]:
        """
        Create snapshot from PDF region and save immediately.

        Args:
            page_num: Page number (0-indexed)
            rect: PDF coordinates (x0, y0, x1, y1)
            output_dir: Directory to save snapshot
            base_filename: Original photo filename for naming

        Returns:
            Path to saved snapshot, or None on failure
        """
        # Render the region
        img = self._renderer.render_region(page_num, rect, self._dpi)
        if not img:
            return None

        # Generate output filename
        snapshot_name = self._generate_snapshot_name(base_filename)
        output_path = output_dir / snapshot_name

        # Ensure directory exists
        output_dir.mkdir(parents=True, exist_ok=True)

        # Save immediately
        img.save(str(output_path), quality=95)

        return output_path

    def _generate_snapshot_name(self, base_filename: str) -> str:
        """Generate snapshot filename. Format: {original}_code_snap.png"""
        stem = Path(base_filename).stem
        return f"{stem}_code_snap.png"

    def create_from_pil_image(
        self,
        image: Image.Image,
        output_dir: Path,
        base_filename: str
    ) -> Optional[Path]:
        """Create snapshot from existing PIL image."""
        if not image:
            return None

        snapshot_name = self._generate_snapshot_name(base_filename)
        output_path = output_dir / snapshot_name

        output_dir.mkdir(parents=True, exist_ok=True)
        image.save(str(output_path), quality=95)

        return output_path
