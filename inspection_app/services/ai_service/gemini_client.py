"""
Gemini API client wrapper.
"""

from pathlib import Path
from typing import Optional
from google import genai
from google.genai import types
from core.exceptions import AIConnectionError, AIRateLimitError, AIResponseParseError


class GeminiClient:
    """Client for Gemini AI API."""

    def __init__(
        self,
        api_key: str,
        model_name: str = "gemini-2.5-flash",
        thinking_level: str = "medium"
    ):
        self._api_key = api_key
        self._model_name = model_name
        self._thinking_level = thinking_level.lower()
        self._client: Optional[genai.Client] = None

    def _get_client(self) -> genai.Client:
        """Get or create Gemini client."""
        if not self._client:
            self._client = genai.Client(api_key=self._api_key)
        return self._client

    def _build_config(self, system_prompt: str) -> types.GenerateContentConfig:
        """Build generation config based on model type."""
        model_lower = self._model_name.lower()

        # Gemini 3 and 2.5 models support thinking
        if "3" in model_lower or "2.5" in model_lower:
            # Use string thinking_level (works for both 2.5 and 3)
            # Valid values: "minimal", "low", "medium", "high"
            return types.GenerateContentConfig(
                system_instruction=system_prompt,
                thinking_config=types.ThinkingConfig(
                    thinking_level=self._thinking_level
                )
            )
        else:
            # Other models don't support thinking
            return types.GenerateContentConfig(
                system_instruction=system_prompt
            )

    def generate_with_image(
        self,
        system_prompt: str,
        user_prompt: str,
        image_path: str,
        cached_content_id: Optional[str] = None
    ) -> str:
        """Generate response with image input."""
        try:
            client = self._get_client()

            # Load image
            image_data = self._load_image(image_path)

            # Build content parts
            contents = [
                types.Content(
                    role="user",
                    parts=[
                        types.Part.from_bytes(
                            data=image_data,
                            mime_type=self._get_mime_type(image_path)
                        ),
                        types.Part.from_text(user_prompt)
                    ]
                )
            ]

            # Configure generation
            config = self._build_config(system_prompt)

            # Add cached content if available
            if cached_content_id:
                config.cached_content = cached_content_id

            # Generate response
            response = client.models.generate_content(
                model=self._model_name,
                contents=contents,
                config=config
            )

            return response.text

        except Exception as e:
            error_str = str(e).lower()
            if "rate" in error_str or "quota" in error_str:
                raise AIRateLimitError(wait_seconds=60, message=str(e))
            elif "connection" in error_str or "network" in error_str:
                raise AIConnectionError(str(e))
            else:
                raise AIResponseParseError(f"API error: {e}")

    def generate_text(self, system_prompt: str, user_prompt: str) -> str:
        """Generate text-only response."""
        try:
            client = self._get_client()

            config = self._build_config(system_prompt)

            response = client.models.generate_content(
                model=self._model_name,
                contents=user_prompt,
                config=config
            )

            return response.text

        except Exception as e:
            raise AIResponseParseError(f"API error: {e}")

    def _load_image(self, image_path: str) -> bytes:
        """Load image file as bytes."""
        path = Path(image_path)
        if not path.exists():
            raise FileNotFoundError(f"Image not found: {path}")
        return path.read_bytes()

    def _get_mime_type(self, image_path: str) -> str:
        """Get MIME type from file extension."""
        ext = Path(image_path).suffix.lower()
        mime_types = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.webp': 'image/webp'
        }
        return mime_types.get(ext, 'image/jpeg')
