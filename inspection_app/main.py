"""
Main entry point for the Inspection App (NiceGUI version).
"""

from nicegui import ui, app
from pathlib import Path

from .web_ui.app import get_app_state
from .web_ui.pages.triage_page import TriagePage
from .web_ui.pages.processing_page import ProcessingPage
from .web_ui.pages.review_page import ReviewPage
from .web_ui.pages.export_page import ExportPage
from .web_ui.pages.settings_page import SettingsPage


def create_app():
    """Create and configure the NiceGUI application."""

    @ui.page('/')
    def index():
        """Main application page."""
        app_state = get_app_state()

        # Header
        with ui.header().classes('bg-blue-800 text-white items-center'):
            ui.label('Inspection Photo Review').classes('text-xl font-bold')
            ui.space()

            # Queue count badge
            queue_count = len(app_state.queue.get_all_items())
            ui.badge(f'{queue_count} items').classes('bg-blue-600')

        # Navigation drawer
        with ui.left_drawer().classes('bg-gray-100') as drawer:
            ui.label('Navigation').classes('text-lg font-bold mb-4')

            with ui.column().classes('w-full gap-2'):
                ui.button(
                    '1. Triage',
                    icon='photo_camera',
                    on_click=lambda: ui.navigate.to('/triage')
                ).classes('w-full justify-start')

                ui.button(
                    '2. Processing',
                    icon='psychology',
                    on_click=lambda: ui.navigate.to('/processing')
                ).classes('w-full justify-start')

                ui.button(
                    '3. Review',
                    icon='fact_check',
                    on_click=lambda: ui.navigate.to('/review')
                ).classes('w-full justify-start')

                ui.button(
                    '4. Export',
                    icon='cloud_upload',
                    on_click=lambda: ui.navigate.to('/export')
                ).classes('w-full justify-start')

                ui.separator()

                ui.button(
                    'Settings',
                    icon='settings',
                    on_click=lambda: ui.navigate.to('/settings')
                ).classes('w-full justify-start')

        # Main content - welcome page
        with ui.column().classes('w-full max-w-4xl mx-auto p-8'):
            ui.label('Welcome to Inspection Photo Review').classes('text-3xl font-bold mb-4')

            ui.markdown('''
            This application helps you manage inspection photos and match them with building code references.

            **Workflow:**

            1. **Triage** - Load photos, edit them, add location/description, and queue for processing
            2. **Processing** - AI analyzes photos and suggests code references
            3. **Review** - Verify AI suggestions against code books, capture snapshots
            4. **Export** - Export approved items to Google Docs

            **Getting Started:**

            - First, go to **Settings** to configure your API keys and code book folders
            - Then start with **Triage** to add your first inspection photos
            ''')

            # Quick status
            with ui.card().classes('w-full mt-8'):
                ui.label('Quick Status').classes('text-lg font-bold mb-4')

                with ui.row().classes('w-full gap-8'):
                    # Pending count
                    from .core.inspection_item import ItemStatus
                    pending = len([i for i in app_state.queue.get_all_items()
                                  if i.status == ItemStatus.PENDING])
                    with ui.column().classes('items-center'):
                        ui.label(str(pending)).classes('text-3xl font-bold text-gray-600')
                        ui.label('Pending').classes('text-sm text-gray-500')

                    # Review ready count
                    review_ready = len([i for i in app_state.queue.get_all_items()
                                       if i.status == ItemStatus.REVIEW_READY])
                    with ui.column().classes('items-center'):
                        ui.label(str(review_ready)).classes('text-3xl font-bold text-orange-600')
                        ui.label('Ready for Review').classes('text-sm text-gray-500')

                    # Approved count
                    approved = len([i for i in app_state.queue.get_all_items()
                                   if i.status == ItemStatus.APPROVED])
                    with ui.column().classes('items-center'):
                        ui.label(str(approved)).classes('text-3xl font-bold text-green-600')
                        ui.label('Approved').classes('text-sm text-gray-500')

                    # Exported count
                    exported = len([i for i in app_state.queue.get_all_items()
                                   if i.status == ItemStatus.EXPORTED])
                    with ui.column().classes('items-center'):
                        ui.label(str(exported)).classes('text-3xl font-bold text-teal-600')
                        ui.label('Exported').classes('text-sm text-gray-500')

            # Config status warning
            if not app_state.config.is_configured():
                with ui.card().classes('w-full mt-4 bg-yellow-50'):
                    with ui.row().classes('items-center gap-2'):
                        ui.icon('warning').classes('text-yellow-600')
                        ui.label('API not configured. Please go to Settings.').classes('text-yellow-800')

    @ui.page('/triage')
    def triage():
        """Triage page."""
        _create_page_layout('Triage', TriagePage)

    @ui.page('/processing')
    def processing():
        """Processing page."""
        _create_page_layout('Processing', ProcessingPage)

    @ui.page('/review')
    def review():
        """Review page."""
        _create_page_layout('Review', ReviewPage)

    @ui.page('/export')
    def export():
        """Export page."""
        _create_page_layout('Export', ExportPage)

    @ui.page('/settings')
    def settings():
        """Settings page."""
        _create_page_layout('Settings', SettingsPage)


def _create_page_layout(title: str, page_class):
    """Create a standard page layout with navigation."""
    app_state = get_app_state()

    # Header
    with ui.header().classes('bg-blue-800 text-white items-center'):
        ui.button(icon='menu', on_click=lambda: drawer.toggle()).props('flat color=white')
        ui.label(f'Inspection App - {title}').classes('text-xl font-bold')
        ui.space()

        queue_count = len(app_state.queue.get_all_items())
        ui.badge(f'{queue_count} items').classes('bg-blue-600')

    # Navigation drawer
    with ui.left_drawer().classes('bg-gray-100') as drawer:
        ui.label('Navigation').classes('text-lg font-bold mb-4')

        with ui.column().classes('w-full gap-2'):
            ui.button(
                'Home',
                icon='home',
                on_click=lambda: ui.navigate.to('/')
            ).classes('w-full justify-start')

            ui.button(
                '1. Triage',
                icon='photo_camera',
                on_click=lambda: ui.navigate.to('/triage')
            ).classes('w-full justify-start' + (' bg-blue-200' if title == 'Triage' else ''))

            ui.button(
                '2. Processing',
                icon='psychology',
                on_click=lambda: ui.navigate.to('/processing')
            ).classes('w-full justify-start' + (' bg-blue-200' if title == 'Processing' else ''))

            ui.button(
                '3. Review',
                icon='fact_check',
                on_click=lambda: ui.navigate.to('/review')
            ).classes('w-full justify-start' + (' bg-blue-200' if title == 'Review' else ''))

            ui.button(
                '4. Export',
                icon='cloud_upload',
                on_click=lambda: ui.navigate.to('/export')
            ).classes('w-full justify-start' + (' bg-blue-200' if title == 'Export' else ''))

            ui.separator()

            ui.button(
                'Settings',
                icon='settings',
                on_click=lambda: ui.navigate.to('/settings')
            ).classes('w-full justify-start' + (' bg-blue-200' if title == 'Settings' else ''))

    # Page content
    page = page_class()
    page.render()


def run():
    """Run the application."""
    create_app()
    ui.run(
        title='Inspection Photo Review',
        host='127.0.0.1',
        port=8080,
        reload=False,
        show=True
    )


if __name__ == '__main__':
    run()
