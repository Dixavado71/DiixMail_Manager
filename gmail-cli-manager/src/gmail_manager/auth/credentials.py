"""Credential management for secure storage and retrieval."""

import json
from pathlib import Path
from typing import TypedDict

from gmail_manager.config import Settings
from gmail_manager.exceptions import ConfigurationError


class CredentialsData(TypedDict, total=False):
    """Typed dictionary for credentials data."""

    email: str
    app_password: str
    imap_host: str
    imap_port: int
    smtp_host: str
    smtp_port: int


class CredentialManager:
    """Manages secure storage and retrieval of credentials."""

    def __init__(self, settings: Settings) -> None:
        """Initialize credential manager with settings."""
        self.settings = settings

    def save_credentials(
        self,
        email: str,
        app_password: str,
        imap_host: str | None = None,
        imap_port: int | None = None,
        smtp_host: str | None = None,
        smtp_port: int | None = None,
    ) -> None:
        """
        Save credentials to secure storage.

        Args:
            email: Gmail address
            app_password: App password
            imap_host: IMAP server host (optional)
            imap_port: IMAP server port (optional)
            smtp_host: SMTP server host (optional)
            smtp_port: SMTP server port (optional)
        """
        self.settings.ensure_config_dir()

        credentials: CredentialsData = {
            "email": email.lower().strip(),
            "app_password": app_password,
        }

        if imap_host:
            credentials["imap_host"] = imap_host
        if imap_port:
            credentials["imap_port"] = imap_port
        if smtp_host:
            credentials["smtp_host"] = smtp_host
        if smtp_port:
            credentials["smtp_port"] = smtp_port

        # Write with restricted permissions (Unix only)
        path = self.settings.credentials_path
        path.write_text(json.dumps(credentials, indent=2))

        try:
            path.chmod(0o600)  # Read/write for owner only
        except OSError:
            pass  # Windows may not support chmod

    def load_credentials(self) -> CredentialsData | None:
        """
        Load credentials from secure storage.

        Returns:
            CredentialsData if exists, None otherwise
        """
        path = self.settings.credentials_path
        if not path.exists():
            return None

        try:
            content = path.read_text()
            data = json.loads(content)
            return CredentialsData(
                email=data.get("email", ""),
                app_password=data.get("app_password", ""),
                imap_host=data.get("imap_host"),
                imap_port=data.get("imap_port"),
                smtp_host=data.get("smtp_host"),
                smtp_port=data.get("smtp_port"),
            )
        except (json.JSONDecodeError, KeyError):
            return None

    def delete_credentials(self) -> bool:
        """
        Delete stored credentials.

        Returns:
            True if credentials were deleted, False if they didn't exist
        """
        path = self.settings.credentials_path
        if path.exists():
            path.unlink()
            return True
        return False

    def has_credentials(self) -> bool:
        """Check if credentials exist in storage."""
        return self.settings.credentials_path.exists()

    def get_email(self) -> str | None:
        """Get stored email without password."""
        creds = self.load_credentials()
        return creds.get("email") if creds else None
