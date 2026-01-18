"""
Configuration loading and validation with flexible paths.
"""

import json
from pathlib import Path
from typing import Optional, Dict, List
from pydantic import BaseModel


class CodeFolder(BaseModel):
    """A named code book folder."""
    name: str
    path: str

    def exists(self) -> bool:
        """Check if the folder path exists."""
        return Path(self.path).exists() if self.path else False

    def list_pdfs(self) -> List[str]:
        """List PDF files in this folder."""
        folder = Path(self.path)
        if folder.exists():
            return [f.name for f in folder.glob("*.pdf")]
        return []


class AISettings(BaseModel):
    """AI service configuration."""
    model_config = {"protected_namespaces": ()}

    model_name: str = "gemini-2.5-flash"
    thinking_level: str = "high"
    max_retries: int = 3
    retry_delay_seconds: int = 5
    cache_ttl_minutes: int = 60


class PDFSettings(BaseModel):
    """PDF service configuration."""
    render_dpi: int = 150
    snapshot_dpi: int = 300


class UISettings(BaseModel):
    """UI configuration."""
    default_window_width: int = 1400
    default_window_height: int = 900
    auto_save_interval_seconds: int = 30


class AppConfig(BaseModel):
    """Complete application configuration with optional paths."""
    # API credentials - can be empty strings initially
    gemini_api_key: str = ""
    google_docs_credentials_path: str = ""

    # Multiple named code folders
    code_folders: List[CodeFolder] = []

    # Output directory - defaults to ./output
    output_directory: str = "./output"

    # Sub-settings
    ai_settings: AISettings = AISettings()
    pdf_settings: PDFSettings = PDFSettings()
    ui_settings: UISettings = UISettings()

    def get_code_folder(self, name: str) -> Optional[CodeFolder]:
        """Get a code folder by name."""
        for folder in self.code_folders:
            if folder.name == name:
                return folder
        return None

    def add_code_folder(self, name: str, path: str) -> None:
        """Add a new code folder."""
        # Remove existing with same name
        self.code_folders = [f for f in self.code_folders if f.name != name]
        self.code_folders.append(CodeFolder(name=name, path=path))

    def remove_code_folder(self, name: str) -> None:
        """Remove a code folder by name."""
        self.code_folders = [f for f in self.code_folders if f.name != name]

    def list_code_folder_names(self) -> List[str]:
        """Get list of all code folder names."""
        return [f.name for f in self.code_folders]

    def is_configured(self) -> bool:
        """Check if minimum configuration is present."""
        return bool(self.gemini_api_key)

    def has_valid_code_folders(self) -> bool:
        """Check if at least one valid code folder exists."""
        return any(f.exists() for f in self.code_folders)


class ConfigManager:
    """Load and manage application configuration."""

    def __init__(self, config_path: str | Path = "settings.json"):
        self._config_path = Path(config_path)
        self._config: Optional[AppConfig] = None

    def load(self) -> AppConfig:
        """Load configuration from file, creating default if needed."""
        if not self._config_path.exists():
            self.create_default()

        with open(self._config_path) as f:
            data = json.load(f)

        # Handle migration from old single code_book_directory format
        if "code_book_directory" in data and "code_folders" not in data:
            old_path = data.pop("code_book_directory")
            if old_path:
                data["code_folders"] = [{"name": "Default", "path": old_path}]

        self._config = AppConfig(**data)
        return self._config

    def get(self) -> AppConfig:
        """Get loaded config or load if needed."""
        if not self._config:
            self.load()
        return self._config

    def save(self, config: Optional[AppConfig] = None) -> None:
        """Save configuration to file."""
        if config:
            self._config = config
        if self._config:
            with open(self._config_path, 'w') as f:
                json.dump(self._config.model_dump(), f, indent=2)

    def update(self, **kwargs) -> AppConfig:
        """Update specific config values and save."""
        if not self._config:
            self.load()

        for key, value in kwargs.items():
            if hasattr(self._config, key):
                setattr(self._config, key, value)

        self.save()
        return self._config

    def create_default(self) -> None:
        """Create default configuration file."""
        default = AppConfig()
        self._config = default
        self.save()

    @property
    def config_path(self) -> Path:
        """Get the config file path."""
        return self._config_path
