"""
Google OAuth2 authentication management.
"""

from pathlib import Path
from typing import Optional
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

SCOPES = [
    'https://www.googleapis.com/auth/documents',
    'https://www.googleapis.com/auth/drive.file',
    # Required for setting public sharing permissions on uploaded images
    'https://www.googleapis.com/auth/drive'
]


class GoogleAuthManager:
    """Manage Google API authentication."""

    def __init__(
        self,
        credentials_path: Path,
        token_path: Optional[Path] = None
    ):
        self._credentials_path = Path(credentials_path)
        self._token_path = token_path or self._credentials_path.parent / "token.json"
        self._credentials: Optional[Credentials] = None

    def get_credentials(self) -> Credentials:
        """Get valid credentials, prompting for auth if needed."""
        # Try to load existing token
        if self._token_path.exists():
            self._credentials = Credentials.from_authorized_user_file(
                str(self._token_path), SCOPES
            )

        # Refresh or get new credentials
        if not self._credentials or not self._credentials.valid:
            if (self._credentials and
                self._credentials.expired and
                self._credentials.refresh_token):
                self._credentials.refresh(Request())
            else:
                self._credentials = self._run_auth_flow()

            self._save_token()

        return self._credentials

    def _run_auth_flow(self) -> Credentials:
        """Run OAuth2 authorization flow."""
        if not self._credentials_path.exists():
            raise FileNotFoundError(
                f"Credentials file not found: {self._credentials_path}"
            )

        flow = InstalledAppFlow.from_client_secrets_file(
            str(self._credentials_path), SCOPES
        )
        return flow.run_local_server(port=0)

    def _save_token(self) -> None:
        """Save credentials to token file."""
        if self._credentials:
            self._token_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self._token_path, 'w') as f:
                f.write(self._credentials.to_json())

    def revoke(self) -> None:
        """Revoke current credentials."""
        if self._token_path.exists():
            self._token_path.unlink()
        self._credentials = None

    @property
    def is_authenticated(self) -> bool:
        """Check if valid credentials exist."""
        try:
            creds = self.get_credentials()
            return creds is not None and creds.valid
        except Exception:
            return False
