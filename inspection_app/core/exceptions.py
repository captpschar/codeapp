"""
Application-specific exceptions.
"""


class InspectionAppError(Exception):
    """Base exception for application."""
    pass


# AI Service Errors
class AIServiceError(InspectionAppError):
    """Base for AI-related errors."""
    pass


class AIRateLimitError(AIServiceError):
    """API rate limit exceeded."""
    def __init__(self, wait_seconds: int, message: str = "Rate limited"):
        super().__init__(message)
        self.wait_seconds = wait_seconds


class AIConnectionError(AIServiceError):
    """Network connection to AI service failed."""
    pass


class AIResponseParseError(AIServiceError):
    """Failed to parse AI response."""
    pass


class AIHallucinationError(AIServiceError):
    """AI returned reference that doesn't exist."""
    def __init__(self, reference: str):
        super().__init__(f"Reference not found: {reference}")
        self.reference = reference


# PDF Service Errors
class PDFServiceError(InspectionAppError):
    """Base for PDF-related errors."""
    pass


class PDFNotFoundError(PDFServiceError):
    """PDF file not found."""
    pass


class PDFSearchError(PDFServiceError):
    """Error during PDF text search."""
    pass


class PDFRenderError(PDFServiceError):
    """Error rendering PDF page."""
    pass


# Export Errors
class ExportError(InspectionAppError):
    """Base for export-related errors."""
    pass


class ExportAuthError(ExportError):
    """Google authentication failed."""
    pass


class ExportNetworkError(ExportError):
    """Network error during export."""
    pass


class ExportPartialError(ExportError):
    """Some items failed to export."""
    def __init__(self, successful: int, failed: int, errors: list):
        super().__init__(
            f"Export completed with errors: {successful} succeeded, {failed} failed"
        )
        self.successful = successful
        self.failed = failed
        self.errors = errors


# State Errors
class StateError(InspectionAppError):
    """Invalid state or transition."""
    pass


class StateTransitionError(StateError):
    """Invalid state transition attempted."""
    pass
