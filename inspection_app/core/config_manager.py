"""
Configuration loading and validation.
"""

import json
from pathlib import Path
from typing import Optional
from pydantic import BaseModel, field_validator


class AISettings(BaseModel):
    """AI service configuration."""
    model_name: str = "gemini-3-flash-preview"
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
    """Complete application configuration."""
    gemini_api_key: str
    google_docs_credentials_path: str
    code_book_directory: str
    output_directory: str = "./output"
    ai_settings: AISettings = AISettings()
    pdf_settings: PDFSettings = PDFSettings()
    ui_settings: UISettings = UISettings()

    @field_validator('code_book_directory')
    @classmethod
    def validate_code_book_dir(cls, v):
        path = Path(v)
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
        return v

    @field_validator('output_directory')
    @classmethod
    def validate_output_dir(cls, v):
        path = Path(v)
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
        return v


class ConfigManager:
    """Load and manage application configuration."""

    def __init__(self, config_path: str | Path = "settings.json"):
        self._config_path = Path(config_path)
        self._config: Optional[AppConfig] = None

    def load(self) -> AppConfig:
        """Load configuration from file."""
        if not self._config_path.exists():
            raise FileNotFoundError(f"Config file not found: {self._config_path}")

        with open(self._config_path) as f:
            data = json.load(f)

        self._config = AppConfig(**data)
        return self._config

    def get(self) -> AppConfig:
        """Get loaded config or load if needed."""
        if not self._config:
            self.load()
        return self._config

    def save(self, config: AppConfig) -> None:
        """Save configuration to file."""
        with open(self._config_path, 'w') as f:
            json.dump(config.model_dump(), f, indent=2)
        self._config = config

    def create_default(self) -> None:
        """Create default configuration file."""
        default = {
            "gemini_api_key": "YOUR_API_KEY_HERE",
            "google_docs_credentials_path": "./credentials.json",
            "code_book_directory": "./code_books/",
            "output_directory": "./output/",
            "ai_settings": AISettings().model_dump(),
            "pdf_settings": PDFSettings().model_dump(),
            "ui_settings": UISettings().model_dump()
        }
        with open(self._config_path, 'w') as f:
            json.dump(default, f, indent=2)
