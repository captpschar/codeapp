"""
PDF context caching for Gemini API.
"""

from pathlib import Path
from typing import Dict, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from google import genai
from google.genai import types


@dataclass
class CacheEntry:
    """Cached content entry."""
    cache_id: str
    pdf_path: str
    created_at: datetime
    expires_at: datetime


class ContextCacheManager:
    """Manage PDF context caching for AI requests."""

    def __init__(
        self,
        api_key: str,
        model_name: str = "gemini-3-flash-preview",
        cache_ttl_minutes: int = 60
    ):
        self._api_key = api_key
        self._model_name = model_name
        self._ttl = timedelta(minutes=cache_ttl_minutes)
        self._caches: Dict[str, CacheEntry] = {}
        self._client: Optional[genai.Client] = None

    def _get_client(self) -> genai.Client:
        """Get or create client."""
        if not self._client:
            self._client = genai.Client(api_key=self._api_key)
        return self._client

    def get_or_create_cache(self, pdf_path: str) -> Optional[str]:
        """Get existing cache or create new one for PDF."""
        # Check existing cache
        if pdf_path in self._caches:
            entry = self._caches[pdf_path]
            if datetime.now() < entry.expires_at:
                return entry.cache_id
            else:
                # Cache expired, remove it
                self._remove_cache(pdf_path)

        # Create new cache
        return self._create_cache(pdf_path)

    def _create_cache(self, pdf_path: str) -> Optional[str]:
        """Create new cache for PDF content."""
        try:
            path = Path(pdf_path)
            if not path.exists():
                return None

            client = self._get_client()

            # Read PDF content
            pdf_bytes = path.read_bytes()

            # Create cached content
            cached_content = client.caches.create(
                model=self._model_name,
                config=types.CreateCachedContentConfig(
                    contents=[
                        types.Content(
                            role="user",
                            parts=[
                                types.Part.from_bytes(
                                    data=pdf_bytes,
                                    mime_type="application/pdf"
                                )
                            ]
                        )
                    ],
                    ttl=f"{int(self._ttl.total_seconds())}s",
                    display_name=path.name
                )
            )

            # Store cache entry
            now = datetime.now()
            self._caches[pdf_path] = CacheEntry(
                cache_id=cached_content.name,
                pdf_path=pdf_path,
                created_at=now,
                expires_at=now + self._ttl
            )

            return cached_content.name

        except Exception as e:
            print(f"Cache creation failed: {e}")
            return None

    def _remove_cache(self, pdf_path: str) -> None:
        """Remove cache entry."""
        if pdf_path in self._caches:
            try:
                client = self._get_client()
                entry = self._caches[pdf_path]
                client.caches.delete(name=entry.cache_id)
            except Exception:
                pass
            del self._caches[pdf_path]

    def clear_all_caches(self) -> None:
        """Clear all cached content."""
        for pdf_path in list(self._caches.keys()):
            self._remove_cache(pdf_path)

    def get_cache_info(self, pdf_path: str) -> Optional[CacheEntry]:
        """Get cache info for a PDF."""
        return self._caches.get(pdf_path)
