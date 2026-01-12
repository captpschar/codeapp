"""
Image file management utilities.
"""

from pathlib import Path
from typing import List
import shutil


class ImageFileManager:
    """Manage image file paths and operations."""

    def __init__(self, base_output_dir: Path):
        self._base_dir = base_output_dir
        self._edited_subdir = "edited"

    def get_edited_path(self, original_path: str | Path) -> Path:
        """Generate path for edited version of image."""
        original = Path(original_path)
        edited_dir = original.parent / self._edited_subdir
        new_name = f"{original.stem}_crop{original.suffix}"
        return edited_dir / new_name

    def ensure_edited_dir(self, original_path: str | Path) -> Path:
        """Create edited subdirectory if needed."""
        original = Path(original_path)
        edited_dir = original.parent / self._edited_subdir
        edited_dir.mkdir(parents=True, exist_ok=True)
        return edited_dir

    def copy_original(self, source: str | Path, dest_dir: Path) -> Path:
        """Copy original image to destination."""
        source_path = Path(source)
        dest_path = dest_dir / source_path.name
        shutil.copy2(source_path, dest_path)
        return dest_path

    def list_images_in_dir(self, directory: Path) -> List[Path]:
        """List all image files in directory."""
        extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}
        images = []
        for ext in extensions:
            images.extend(directory.glob(f"*{ext}"))
            images.extend(directory.glob(f"*{ext.upper()}"))
        return sorted(images)

    def file_exists(self, path: str | Path) -> bool:
        """Check if file exists."""
        return Path(path).exists()

    def delete_if_exists(self, path: str | Path) -> bool:
        """Delete file if it exists, return True if deleted."""
        p = Path(path)
        if p.exists():
            p.unlink()
            return True
        return False

    def get_snapshot_dir(self, original_path: str | Path) -> Path:
        """Get directory for snapshots (same as edited dir)."""
        return self.ensure_edited_dir(original_path)
