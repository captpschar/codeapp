"""
Code folder selector dropdown.
"""

from nicegui import ui
from typing import Optional, Callable, List


class CodeFolderSelector:
    """Dropdown for selecting a code folder."""

    def __init__(
        self,
        on_folder_changed: Optional[Callable[[str], None]] = None,
        label: str = "Code Folder"
    ):
        self._on_folder_changed = on_folder_changed
        self._label = label
        self._folders: List[str] = []
        self._selected: str = ""
        self._select_element = None
        self._container = None

    def render(self) -> ui.element:
        """Render the code folder selector."""
        with ui.column().classes('w-full') as self._container:
            self._select_element = ui.select(
                options=self._folders,
                label=self._label,
                value=self._selected,
                on_change=self._on_change
            ).classes('w-full')

        return self._container

    def _on_change(self, e) -> None:
        """Handle selection change."""
        self._selected = e.value or ""
        if self._on_folder_changed and self._selected:
            self._on_folder_changed(self._selected)

    def set_folders(self, folders: List[str]) -> None:
        """Set available folder names."""
        self._folders = folders
        if self._select_element:
            self._select_element.options = folders
            self._select_element.update()

    def get_selected(self) -> str:
        """Get currently selected folder name."""
        return self._selected

    def set_selected(self, folder: str) -> None:
        """Set selected folder."""
        if folder in self._folders:
            self._selected = folder
            if self._select_element:
                self._select_element.value = folder

    def set_enabled(self, enabled: bool) -> None:
        """Enable/disable the selector."""
        if self._select_element:
            self._select_element.props(f'{"" if enabled else "disable"}')

    def clear(self) -> None:
        """Clear the selection."""
        self._selected = ""
        if self._select_element:
            self._select_element.value = None
