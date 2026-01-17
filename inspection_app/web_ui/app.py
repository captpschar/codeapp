"""
Main NiceGUI application setup.
"""

from nicegui import ui, app
from pathlib import Path
import base64

from ..core.app_state import AppState


# Global app state instance
_app_state: AppState = None


def get_app_state() -> AppState:
    """Get the global app state instance."""
    global _app_state
    if _app_state is None:
        _app_state = AppState()
    return _app_state


def create_header():
    """Create the application header."""
    with ui.header().classes('bg-blue-800 text-white'):
        with ui.row().classes('w-full items-center'):
            ui.label('Inspection Photo Review').classes('text-xl font-bold')
            ui.space()

            # Navigation tabs
            with ui.tabs().classes('text-white') as tabs:
                ui.tab('triage', label='1. Triage')
                ui.tab('processing', label='2. Processing')
                ui.tab('review', label='3. Review')
                ui.tab('export', label='4. Export')
                ui.tab('settings', label='Settings')

            return tabs


def create_footer():
    """Create the application footer."""
    with ui.footer().classes('bg-gray-100'):
        with ui.row().classes('w-full items-center justify-between'):
            state = get_app_state()

            # Status info
            queue_count = len(state.queue.get_all_items())
            ui.label(f'Queue: {queue_count} items').classes('text-sm text-gray-600')

            # Config status
            if state.config.is_configured():
                ui.label('API: Connected').classes('text-sm text-green-600')
            else:
                ui.label('API: Not configured').classes('text-sm text-red-600')


def encode_image_base64(path: str) -> str:
    """Encode image file to base64 for display."""
    try:
        with open(path, 'rb') as f:
            data = f.read()
        ext = Path(path).suffix.lower()
        mime = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.bmp': 'image/bmp'
        }.get(ext, 'image/jpeg')
        return f"data:{mime};base64,{base64.b64encode(data).decode()}"
    except Exception:
        return ""


def notify_success(message: str):
    """Show success notification."""
    ui.notify(message, type='positive')


def notify_error(message: str):
    """Show error notification."""
    ui.notify(message, type='negative')


def notify_warning(message: str):
    """Show warning notification."""
    ui.notify(message, type='warning')


def notify_info(message: str):
    """Show info notification."""
    ui.notify(message, type='info')
