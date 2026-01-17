"""
PDF chapter selector dropdown.
"""

from nicegui import ui
from typing import Optional, Callable, List


class ChapterSelector:
    """Dropdown for selecting a code book chapter (PDF file)."""

    def __init__(
        self,
        on_chapter_changed: Optional[Callable[[str], None]] = None,
        label: str = "Code Chapter"
    ):
        self._on_chapter_changed = on_chapter_changed
        self._label = label
        self._chapters: List[str] = []
        self._selected: str = ""
        self._select_element = None
        self._container = None

    def render(self) -> ui.element:
        """Render the chapter selector."""
        with ui.column().classes('w-full') as self._container:
            self._select_element = ui.select(
                options=self._chapters,
                label=self._label,
                value=self._selected,
                on_change=self._on_change
            ).classes('w-full')

        return self._container

    def _on_change(self, e) -> None:
        """Handle selection change."""
        self._selected = e.value or ""
        if self._on_chapter_changed and self._selected:
            self._on_chapter_changed(self._selected)

    def set_chapters(self, chapters: List[str]) -> None:
        """Set available chapter filenames."""
        self._chapters = chapters
        if self._select_element:
            self._select_element.options = chapters
            self._select_element.update()

    def get_selected(self) -> str:
        """Get currently selected chapter filename."""
        return self._selected

    def set_selected(self, chapter: str) -> None:
        """Set selected chapter."""
        if chapter in self._chapters:
            self._selected = chapter
            if self._select_element:
                self._select_element.value = chapter

    def set_enabled(self, enabled: bool) -> None:
        """Enable/disable the selector."""
        if self._select_element:
            self._select_element.props(f'{"" if enabled else "disable"}')

    def clear(self) -> None:
        """Clear the selection."""
        self._selected = ""
        if self._select_element:
            self._select_element.value = None
