"""
Centralized error handling and logging.
"""

import logging
from typing import Optional, Callable
from datetime import datetime
from pathlib import Path
from .exceptions import (
    AIRateLimitError, AIConnectionError, AIHallucinationError,
    ExportNetworkError, ExportPartialError, StateTransitionError
)


class ErrorHandler:
    """Central error handling service."""

    def __init__(self, log_dir: Optional[Path] = None):
        self._log_dir = log_dir or Path("./logs")
        self._log_dir.mkdir(parents=True, exist_ok=True)
        self._setup_logging()
        self._error_callbacks: list[Callable] = []

    def _setup_logging(self) -> None:
        """Configure logging."""
        log_file = self._log_dir / f"app_{datetime.now().strftime('%Y%m%d')}.log"

        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self._logger = logging.getLogger("InspectionApp")

    def handle_error(self, error: Exception, context: str = "") -> dict:
        """Handle an exception and return appropriate response."""
        error_info = {
            "recoverable": True,
            "message": str(error),
            "action": "none",
            "wait_seconds": 0
        }

        self._logger.error(f"{context}: {error}", exc_info=True)

        if isinstance(error, AIRateLimitError):
            error_info["action"] = "wait_and_retry"
            error_info["wait_seconds"] = error.wait_seconds
            error_info["message"] = f"Rate limited. Waiting {error.wait_seconds}s..."

        elif isinstance(error, AIConnectionError):
            error_info["action"] = "retry"
            error_info["message"] = "Connection failed. Click to retry."

        elif isinstance(error, AIHallucinationError):
            error_info["action"] = "user_input"
            error_info["message"] = (
                f"AI suggestion '{error.reference}' not found. Please verify manually."
            )

        elif isinstance(error, ExportNetworkError):
            error_info["action"] = "retry"
            error_info["message"] = "Network error during export. Click to retry."

        elif isinstance(error, ExportPartialError):
            error_info["recoverable"] = True
            error_info["action"] = "partial_retry"
            error_info["message"] = error.args[0]

        elif isinstance(error, StateTransitionError):
            error_info["recoverable"] = False
            error_info["action"] = "none"
            error_info["message"] = f"Invalid operation: {error}"

        for callback in self._error_callbacks:
            callback(error_info)

        return error_info

    def on_error(self, callback: Callable) -> None:
        """Register error callback for UI updates."""
        self._error_callbacks.append(callback)

    def log_info(self, message: str) -> None:
        """Log info message."""
        self._logger.info(message)

    def log_warning(self, message: str) -> None:
        """Log warning message."""
        self._logger.warning(message)
