"""
Settings page for configuring the application.
"""

from nicegui import ui, run
from pathlib import Path
from typing import Optional, Dict
from web_ui.app import get_app_state, notify_success, notify_error


def _select_folder() -> Optional[str]:
    """Open native folder selection dialog."""
    import tkinter as tk
    from tkinter import filedialog

    root = tk.Tk()
    root.withdraw()
    root.attributes('-topmost', True)
    root.focus_force()

    folder_path = filedialog.askdirectory(
        title="Select Folder"
    )

    root.destroy()
    return folder_path if folder_path else None


def _select_file(filetypes: list = None) -> Optional[str]:
    """Open native file selection dialog."""
    import tkinter as tk
    from tkinter import filedialog

    root = tk.Tk()
    root.withdraw()
    root.attributes('-topmost', True)
    root.focus_force()

    file_path = filedialog.askopenfilename(
        title="Select File",
        filetypes=filetypes or [("All files", "*.*")]
    )

    root.destroy()
    return file_path if file_path else None


class SettingsPage:
    """Settings configuration page."""

    def __init__(self):
        self._app_state = get_app_state()
        self._api_key_input = None
        self._credentials_path_input = None
        self._output_dir_input = None
        self._folders_container = None
        self._folder_inputs: Dict[str, tuple] = {}

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

                    ui.label('Google Docs Credentials File (.json)').classes('text-sm font-medium mt-2')
                    with ui.row().classes('w-full items-center gap-2'):
                        self._credentials_path_input = ui.input(
                            placeholder='Path to credentials.json',
                            value=config.google_docs_credentials_path
                        ).classes('flex-grow')

                        ui.button('Browse...', on_click=self._browse_credentials_file).props('flat')

            # Output Directory
            with ui.card().classes('w-full'):
                ui.label('Output Directory').classes('text-lg font-bold mb-4')

                ui.label('Output Directory Path').classes('text-sm font-medium')
                with ui.row().classes('w-full items-center gap-2'):
                    self._output_dir_input = ui.input(
                        placeholder='Path to output folder',
                        value=config.output_directory
                    ).classes('flex-grow')

                    ui.button('Browse...', on_click=self._browse_output_dir).props('flat')

                ui.label(
                    'This is where edited images, snapshots, and queue data will be saved.'
                ).classes('text-sm text-gray-500 mt-2')

            # Code Folders
            with ui.card().classes('w-full'):
                with ui.row().classes('w-full items-center mb-4'):
                    ui.label('Code Book Folders').classes('text-lg font-bold')
                    ui.space()
                    ui.button('+ Add Folder', on_click=self._add_folder).props('flat color=primary')

                ui.label(
                    'Add folders containing your PDF code books. Give each a descriptive name.'
                ).classes('text-sm text-gray-500 mb-4')

                self._folders_container = ui.column().classes('w-full gap-3')
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
            with ui.row().classes('w-full justify-end gap-2'):
                ui.button('Save Settings', icon='save', on_click=self._save_settings).props('color=primary')

    def _render_folders(self) -> None:
        """Render the code folders list."""
        self._folders_container.clear()
        self._folder_inputs.clear()

        with self._folders_container:
            if not self._app_state.config.code_folders:
                ui.label('No code folders configured. Click "+ Add Folder" to add one.').classes('text-gray-400 py-4')
                return

            for folder in self._app_state.config.code_folders:
                self._render_folder_row(folder.name, folder.path)

    def _render_folder_row(self, name: str, path: str) -> None:
        """Render a single folder row."""
        exists = Path(path).exists() if path else False
        pdf_count = len(list(Path(path).glob('*.pdf'))) if exists else 0

        with ui.card().classes('w-full p-3'):
            # First row: status + name
            with ui.row().classes('w-full items-center gap-2 mb-2'):
                if exists:
                    ui.icon('check_circle', color='green').tooltip('Folder exists')
                    if pdf_count > 0:
                        ui.label(f'{pdf_count} PDFs').classes('text-sm text-green-600')
                else:
                    ui.icon('error', color='red').tooltip('Folder not found')
                    ui.label('Not found').classes('text-sm text-red-600')

                ui.space()

                ui.button('Remove', on_click=lambda n=name: self._remove_folder(n)).props('flat color=negative size=sm')

            # Name input
            name_input = ui.input(
                label='Folder Name',
                value=name
            ).classes('w-full mb-2')

            # Path input with browse button
            ui.label('Folder Path').classes('text-sm font-medium')
            with ui.row().classes('w-full items-center gap-2'):
                path_input = ui.input(
                    placeholder='Click Browse to select folder...',
                    value=path
                ).classes('flex-grow')

                ui.button('Browse...', on_click=lambda n=name: self._browse_folder_path(n)).props('flat')

            # Store references for saving
            self._folder_inputs[name] = (name_input, path_input)

    async def _browse_credentials_file(self) -> None:
        """Open file browser for credentials file."""
        file_path = await run.io_bound(
            _select_file,
            [("JSON files", "*.json"), ("All files", "*.*")]
        )
        if file_path:
            self._credentials_path_input.value = file_path
            notify_success(f'Selected: {Path(file_path).name}')

    async def _browse_output_dir(self) -> None:
        """Open folder browser for output directory."""
        folder_path = await run.io_bound(_select_folder)
        if folder_path:
            self._output_dir_input.value = folder_path
            notify_success(f'Selected: {folder_path}')

    async def _browse_folder_path(self, folder_name: str) -> None:
        """Open folder browser for a code folder path."""
        folder_path = await run.io_bound(_select_folder)
        if folder_path and folder_name in self._folder_inputs:
            name_input, path_input = self._folder_inputs[folder_name]
            path_input.value = folder_path

            # Update the config immediately
            current_name = name_input.value
            self._app_state.config.remove_code_folder(folder_name)
            self._app_state.config.add_code_folder(current_name, folder_path)

            # Refresh to show PDF count
            self._render_folders()
            notify_success(f'Selected: {folder_path}')

    def _add_folder(self) -> None:
        """Add a new code folder."""
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

    def _save_settings(self) -> None:
        """Save all settings."""
        try:
            config = self._app_state.config

            # Update API settings
            config.gemini_api_key = self._api_key_input.value or ""
            config.google_docs_credentials_path = self._credentials_path_input.value or ""
            config.output_directory = self._output_dir_input.value or "./output"

            # Update folder names and paths from inputs
            new_folders = []
            for old_name, (name_input, path_input) in self._folder_inputs.items():
                new_name = name_input.value or old_name
                new_path = path_input.value or ""
                new_folders.append((new_name, new_path))

            # Clear and re-add folders
            config.code_folders = []
            for name, path in new_folders:
                config.add_code_folder(name, path)

            # Save to disk
            self._app_state.config_manager.save()

            # Refresh display
            self._render_folders()

            notify_success('Settings saved successfully')
        except Exception as ex:
            notify_error(f'Failed to save settings: {ex}')
