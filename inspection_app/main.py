"""
Application entry point.
"""

import sys
from pathlib import Path
from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtCore import Qt

from core.app_state import AppState
from core.config_manager import ConfigManager
from ui.main_window import MainWindow


def main():
    """Main entry point."""
    # Enable high DPI scaling
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName("Inspection Photo Review")
    app.setOrganizationName("InspectionApp")

    # Check for config file
    config_path = Path("settings.json")
    if not config_path.exists():
        config_manager = ConfigManager(config_path)
        config_manager.create_default()

        QMessageBox.information(
            None,
            "First Run",
            f"Created default config at {config_path}\n\n"
            "Please edit settings.json with your API keys before running.\n\n"
            "Required:\n"
            "- gemini_api_key: Your Google AI API key\n"
            "- google_docs_credentials_path: Path to OAuth credentials\n"
            "- code_book_directory: Directory containing PDF code books"
        )
        sys.exit(0)

    # Initialize application state
    try:
        app_state = AppState(str(config_path))
    except FileNotFoundError as e:
        QMessageBox.critical(
            None,
            "Configuration Error",
            f"Required file not found:\n{e}\n\n"
            "Please check your settings.json configuration."
        )
        sys.exit(1)
    except Exception as e:
        QMessageBox.critical(
            None,
            "Initialization Error",
            f"Failed to initialize:\n{e}"
        )
        sys.exit(1)

    # Load any persisted data
    try:
        app_state.load()
    except Exception as e:
        print(f"Warning: Could not load saved state: {e}")

    # Create and show main window
    window = MainWindow(app_state)
    window.show()

    # Run application
    exit_code = app.exec()

    # Save state on exit
    app_state.save()

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
