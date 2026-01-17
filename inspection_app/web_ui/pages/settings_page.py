"""
Settings page for configuring the application.
"""

from nicegui import ui, events
from pathlib import Path
from typing import Optional
from ..app import get_app_state, notify_success, notify_error


class SettingsPage:
    """Settings configuration page."""

    def __init__(self):
        self._app_state = get_app_state()
        self._api_key_input = None
        self._credentials_path_input = None
        self._output_dir_input = None
        self._folders_container = None

    def render(self) -> None:
        """Render the settings page."""
        config = self._app_state.config

        with ui.column().classes('w-full max-w-4xl mx-auto p-4 gap-6'):
            ui.label('Settings').classes('text-2xl font-bold')

            # API Configuration
            with ui.card().classes('w-full'):
                ui.label('API Configuration').classes('text-lg font-bold mb-4')

                with ui.column().classes('w-full gap-4'):
                    self._api_key_input = ui.input(
                        label='Gemini API Key',
                        value=config.gemini_api_key,
                        password=True,
                        password_toggle_button=True
                    ).classes('w-full')

                    with ui.row().classes('w-full items-end gap-2'):
                        self._credentials_path_input = ui.input(
                            label='Google Docs Credentials File',
                            value=config.google_docs_credentials_path
                        ).classes('flex-grow')

                        ui.upload(
                            label='Browse',
                            auto_upload=True,
                            on_upload=self._on_credentials_upload
                        ).classes('w-32').props('accept=.json')

            # Output Directory
            with ui.card().classes('w-full'):
                ui.label('Output Directory').classes('text-lg font-bold mb-4')

                self._output_dir_input = ui.input(
                    label='Output Directory Path',
                    value=config.output_directory
                ).classes('w-full')

                ui.label(
                    'This is where edited images, snapshots, and queue data will be saved.'
                ).classes('text-sm text-gray-500')

            # Code Folders
            with ui.card().classes('w-full'):
                with ui.row().classes('w-full items-center mb-4'):
                    ui.label('Code Book Folders').classes('text-lg font-bold')
                    ui.space()
                    ui.button('Add Folder', icon='add', on_click=self._add_folder).props('flat')

                self._folders_container = ui.column().classes('w-full gap-2')
                self._render_folders()

            # AI Settings
            with ui.card().classes('w-full'):
                ui.label('AI Settings').classes('text-lg font-bold mb-4')

                with ui.row().classes('w-full gap-4'):
                    ui.input(
                        label='Model Name',
                        value=config.ai_settings.model_name
                    ).classes('flex-grow').bind_value(config.ai_settings, 'model_name')

                    ui.select(
                        label='Thinking Level',
                        options=['low', 'medium', 'high'],
                        value=config.ai_settings.thinking_level
                    ).classes('w-40').bind_value(config.ai_settings, 'thinking_level')

            # PDF Settings
            with ui.card().classes('w-full'):
                ui.label('PDF Settings').classes('text-lg font-bold mb-4')

                with ui.row().classes('w-full gap-4'):
                    ui.number(
                        label='Render DPI',
                        value=config.pdf_settings.render_dpi,
                        min=72,
                        max=300
                    ).classes('w-40').bind_value(config.pdf_settings, 'render_dpi')

                    ui.number(
                        label='Snapshot DPI',
                        value=config.pdf_settings.snapshot_dpi,
                        min=150,
                        max=600
                    ).classes('w-40').bind_value(config.pdf_settings, 'snapshot_dpi')

            # Save button
            with ui.row().classes('w-full justify-end'):
                ui.button('Save Settings', icon='save', on_click=self._save_settings)

    def _render_folders(self) -> None:
        """Render the code folders list."""
        self._folders_container.clear()

        with self._folders_container:
            if not self._app_state.config.code_folders:
                ui.label('No code folders configured').classes('text-gray-400 py-2')
                return

            for folder in self._app_state.config.code_folders:
                self._render_folder_row(folder.name, folder.path)

    def _render_folder_row(self, name: str, path: str) -> None:
        """Render a single folder row."""
        exists = Path(path).exists() if path else False

        with ui.card().classes('w-full'):
            with ui.row().classes('w-full items-center gap-2'):
                # Status indicator
                if exists:
                    ui.icon('check_circle').classes('text-green-500')
                else:
                    ui.icon('error').classes('text-red-500')

                # Name input
                name_input = ui.input(
                    label='Name',
                    value=name
                ).classes('w-48')

                # Path input
                path_input = ui.input(
                    label='Path',
                    value=path
                ).classes('flex-grow')

                # PDF count
                if exists:
                    pdf_count = len(list(Path(path).glob('*.pdf')))
                    ui.badge(f'{pdf_count} PDFs').classes('bg-blue-100')

                # Remove button
                ui.button(
                    icon='delete',
                    on_click=lambda n=name: self._remove_folder(n)
                ).props('flat color=negative')

    def _add_folder(self) -> None:
        """Add a new code folder."""
        # Generate a unique name
        existing_names = self._app_state.config.list_code_folder_names()
        new_name = "New Folder"
        counter = 1
        while new_name in existing_names:
            new_name = f"New Folder {counter}"
            counter += 1

        self._app_state.config.add_code_folder(new_name, "")
        self._render_folders()

    def _remove_folder(self, name: str) -> None:
        """Remove a code folder."""
        self._app_state.config.remove_code_folder(name)
        self._render_folders()

    def _on_credentials_upload(self, e: events.UploadEventArguments) -> None:
        """Handle credentials file upload."""
        try:
            # Save the uploaded file
            content = e.content.read()
            output_dir = self._app_state.get_output_dir()
            creds_path = output_dir / "credentials.json"
            creds_path.write_bytes(content)

            self._credentials_path_input.value = str(creds_path)
            notify_success('Credentials file uploaded')
        except Exception as ex:
            notify_error(f'Failed to upload: {ex}')

    def _save_settings(self) -> None:
        """Save all settings."""
        try:
            config = self._app_state.config

            # Update values from inputs
            config.gemini_api_key = self._api_key_input.value or ""
            config.google_docs_credentials_path = self._credentials_path_input.value or ""
            config.output_directory = self._output_dir_input.value or "./output"

            # Save to disk
            self._app_state.config_manager.save()

            notify_success('Settings saved successfully')
        except Exception as ex:
            notify_error(f'Failed to save settings: {ex}')
