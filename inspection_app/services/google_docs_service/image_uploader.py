"""
Upload images to Google Drive for document embedding.
"""

from pathlib import Path
from typing import Optional, List
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from .auth_manager import GoogleAuthManager


class ImageUploader:
    """Upload images to Google Drive for Docs embedding."""

    def __init__(self, auth_manager: GoogleAuthManager):
        self._auth = auth_manager
        self._service = None
        self._uploaded_ids: List[str] = []

    def _get_service(self):
        """Get or create Drive API service."""
        if not self._service:
            creds = self._auth.get_credentials()
            self._service = build('drive', 'v3', credentials=creds)
        return self._service

    def upload_image(self, image_path: str | Path) -> Optional[str]:
        """Upload image to Drive and return embeddable URI."""
        path = Path(image_path)
        if not path.exists():
            return None

        service = self._get_service()

        # Determine MIME type
        mime_types = {
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.gif': 'image/gif'
        }
        mime_type = mime_types.get(path.suffix.lower(), 'image/png')

        # Upload file
        file_metadata = {'name': path.name}
        media = MediaFileUpload(str(path), mimetype=mime_type)

        file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id,webContentLink'
        ).execute()

        file_id = file['id']
        self._uploaded_ids.append(file_id)

        # Make file publicly accessible for embedding
        service.permissions().create(
            fileId=file_id,
            body={'type': 'anyone', 'role': 'reader'}
        ).execute()

        return file.get(
            'webContentLink',
            f"https://drive.google.com/uc?id={file_id}"
        )

    def cleanup_uploaded_files(self) -> None:
        """Delete all uploaded files from Drive."""
        service = self._get_service()
        for file_id in self._uploaded_ids:
            try:
                service.files().delete(fileId=file_id).execute()
            except Exception:
                pass
        self._uploaded_ids.clear()

    @property
    def uploaded_count(self) -> int:
        """Get count of uploaded files."""
        return len(self._uploaded_ids)
