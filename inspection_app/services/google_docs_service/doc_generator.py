"""
Google Docs document generation.
"""

from typing import List, Tuple
from googleapiclient.discovery import build
from .auth_manager import GoogleAuthManager
from .image_uploader import ImageUploader
from ...core.inspection_item import InspectionItem


class GoogleDocGenerator:
    """Generate inspection reports as Google Docs."""

    def __init__(self, auth_manager: GoogleAuthManager):
        self._auth = auth_manager
        self._service = None

    def _get_service(self):
        """Get or create Docs API service."""
        if not self._service:
            creds = self._auth.get_credentials()
            self._service = build('docs', 'v1', credentials=creds)
        return self._service

    def create_report(
        self,
        title: str,
        items: List[InspectionItem],
        image_uploader: ImageUploader
    ) -> Tuple[str, List[str]]:
        """Create inspection report document."""
        service = self._get_service()
        errors = []

        # Create empty document
        doc = service.documents().create(body={'title': title}).execute()
        doc_id = doc['documentId']

        # Build content requests
        requests = []
        insert_index = 1

        for item in items:
            try:
                item_requests, new_index = self._build_item_content(
                    item, insert_index, image_uploader
                )
                requests.extend(item_requests)
                insert_index = new_index
            except Exception as e:
                errors.append(f"Item {item.id}: {str(e)}")
                continue

        # Execute batch update
        if requests:
            service.documents().batchUpdate(
                documentId=doc_id,
                body={'requests': requests}
            ).execute()

        return (doc_id, errors)

    def _build_item_content(
        self,
        item: InspectionItem,
        start_index: int,
        image_uploader: ImageUploader
    ) -> Tuple[list, int]:
        """Build document requests for a single item."""
        requests = []
        idx = start_index

        # Header: Location + Description
        header_text = f"{item.user_location}: {item.user_description}\n\n"
        requests.append({
            'insertText': {'location': {'index': idx}, 'text': header_text}
        })
        idx += len(header_text)

        # Insert edited photo
        if item.photo_edited_path:
            photo_uri = image_uploader.upload_image(item.photo_edited_path)
            if photo_uri:
                requests.append({
                    'insertInlineImage': {
                        'location': {'index': idx},
                        'uri': photo_uri,
                        'objectSize': {
                            'width': {'magnitude': 400, 'unit': 'PT'},
                            'height': {'magnitude': 300, 'unit': 'PT'}
                        }
                    }
                })
                idx += 1

        requests.append({
            'insertText': {'location': {'index': idx}, 'text': '\n'}
        })
        idx += 1

        # Insert code snapshot
        if item.snapshot_path:
            snap_uri = image_uploader.upload_image(item.snapshot_path)
            if snap_uri:
                requests.append({
                    'insertInlineImage': {
                        'location': {'index': idx},
                        'uri': snap_uri,
                        'objectSize': {
                            'width': {'magnitude': 400, 'unit': 'PT'},
                            'height': {'magnitude': 300, 'unit': 'PT'}
                        }
                    }
                })
                idx += 1

        # Add code reference text
        if item.llm_suggested_term:
            ref_text = f"\nCode Reference: {item.llm_suggested_term}\n"
            requests.append({
                'insertText': {'location': {'index': idx}, 'text': ref_text}
            })
            idx += len(ref_text)

        # Add separator
        requests.append({
            'insertText': {'location': {'index': idx}, 'text': '\n---\n\n'}
        })
        idx += 6

        return (requests, idx)

    def get_document_url(self, doc_id: str) -> str:
        """Get the URL for a document."""
        return f"https://docs.google.com/document/d/{doc_id}/edit"
