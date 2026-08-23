"""IMAP client implementation using imaplib."""

import email
import logging
import re
import socket
import ssl
from dataclasses import dataclass
from datetime import datetime
from email.message import Message
from imaplib import IMAP4_SSL
from typing import Any

from tenacity import retry, stop_after_attempt, wait_exponential

from ..config import Settings
from ..exceptions import AuthenticationError, ConnectionError, IMAPError
from ..protocols.imap_client import FolderInfo, IMAPClientProtocol, MessageSummary

logger = logging.getLogger(__name__)


@dataclass
class GmailFolderInfo:
    """Folder information data class."""

    name: str
    delimiter: str | None
    attributes: tuple[str, ...]
    selectability: str


@dataclass
class GmailMessageSummary:
    """Message summary data class."""

    id: str
    uid: int
    subject: str
    from_address: str
    to_address: str
    date: str
    flags: tuple[str, ...]
    size: int
    has_attachments: bool


class GmailIMAPClient(IMAPClientProtocol):
    """IMAP client for Gmail operations."""

    def __init__(self, settings: Settings) -> None:
        """Initialize IMAP client with settings."""
        self.settings = settings
        self._client: IMAP4_SSL | None = None
        self._selected_folder: str | None = None
        self._last_error: str | None = None

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
    def connect(self) -> bool:
        """Connect to IMAP server with retry logic."""
        try:
            logger.info(f"Connecting to {self.settings.imap_host}:{self.settings.imap_port}")
            self._client = IMAP4_SSL(
                host=self.settings.imap_host,
                port=self.settings.imap_port,
                timeout=30,
            )
            logger.info("Connected to IMAP server")
            return True
        except (socket.error, ssl.SSLError, OSError) as e:
            logger.error(f"Connection failed: {e}")
            raise ConnectionError(f"Failed to connect to IMAP server: {e}") from e

    def disconnect(self) -> None:
        """Disconnect from IMAP server."""
        if self._client:
            try:
                self._client.close()
                self._client.logout()
                logger.info("Disconnected from IMAP server")
            except Exception as e:
                logger.warning(f"Error during disconnect: {e}")
            finally:
                self._client = None
                self._selected_folder = None

    def login(self, email: str, password: str) -> bool:
        """Authenticate with IMAP server."""
        if not self._client:
            raise ConnectionError("Not connected to server")

        try:
            logger.info(f"Authenticating as {email}")
            self._client.login(email, password)
            logger.info("Authentication successful")
            return True
        except IMAP4_SSL.error as e:
            error_msg = str(e).lower()
            if "invalid credentials" in error_msg or "authentication failed" in error_msg:
                logger.error("Authentication failed: invalid credentials")
                raise AuthenticationError("Invalid email or app password") from e
            logger.error(f"Authentication error: {e}")
            raise AuthenticationError(f"Authentication failed: {e}") from e
        except Exception as e:
            logger.error(f"Unexpected login error: {e}")
            raise AuthenticationError(f"Login failed: {e}") from e

    def is_connected(self) -> bool:
        """Check if connected and authenticated to server."""
        if not self._client:
            return False
        try:
            # Try a noop command to verify connection
            self._client.noop()
            return True
        except Exception:
            return False

    def _ensure_connected(self) -> None:
        """Ensure client is connected."""
        if not self.is_connected():
            raise ConnectionError("Not connected to IMAP server")

    def list_folders(self) -> list[FolderInfo]:
        """List all folders/mailboxes available."""
        self._ensure_connected()

        try:
            status, data = self._client.list()
            if status != "OK":
                raise IMAPError(f"Failed to list folders: {data}")

            folders = []
            for folder_bytes in data:
                # Parse folder response: (attributes) delimiter "name"
                match = re.match(r'\(([^)]*)\)\s+"?(.+?)"?\s+"?(.+?)"?$', folder_bytes.decode("utf-8"))
                if match:
                    attrs_str, delimiter, name = match.groups()
                    attrs = tuple(attrs_str.split()) if attrs_str else ()
                    folders.append(
                        GmailFolderInfo(
                            name=name,
                            delimiter=delimiter if delimiter != "NIL" else None,
                            attributes=attrs,
                            selectability="selectable" if "\\NoSelect" not in attrs else "noselect",
                        )
                    )

            logger.info(f"Found {len(folders)} folders")
            return folders
        except Exception as e:
            logger.error(f"Error listing folders: {e}")
            raise IMAPError(f"Failed to list folders: {e}") from e

    def select_folder(self, folder_name: str) -> int:
        """Select a folder and return message count."""
        self._ensure_connected()

        try:
            status, data = self._client.select(folder_name, readonly=False)
            if status != "OK":
                raise IMAPError(f"Failed to select folder '{folder_name}': {data[0].decode() if data else 'Unknown error'}")

            self._selected_folder = folder_name
            msg_count = int(data[0]) if data and data[0].isdigit() else 0
            logger.info(f"Selected folder '{folder_name}' with {msg_count} messages")
            return msg_count
        except Exception as e:
            logger.error(f"Error selecting folder: {e}")
            raise IMAPError(f"Failed to select folder: {e}") from e

    def search(self, criteria: str) -> list[int]:
        """Search messages by IMAP criteria."""
        self._ensure_connected()

        try:
            # Encode criteria properly
            status, data = self._client.search(None, criteria)
            if status != "OK":
                raise IMAPError(f"Search failed: {data}")

            if not data or not data[0]:
                return []

            message_ids = [int(x) for x in data[0].split()]
            logger.info(f"Search found {len(message_ids)} messages")
            return message_ids
        except Exception as e:
            logger.error(f"Error searching: {e}")
            raise IMAPError(f"Search failed: {e}") from e

    def fetch_message(self, message_id: int) -> Message | None:
        """Fetch a complete message by ID."""
        self._ensure_connected()

        try:
            status, data = self._client.fetch(str(message_id), "(RFC822)")
            if status != "OK":
                raise IMAPError(f"Fetch failed: {data}")

            if not data or len(data) < 2:
                return None

            # Parse the email message
            raw_email = data[1][1] if isinstance(data[1], tuple) else data[0][1]
            msg = email.message_from_bytes(raw_email)
            return msg
        except Exception as e:
            logger.error(f"Error fetching message: {e}")
            raise IMAPError(f"Failed to fetch message: {e}") from e

    def fetch_summary(self, message_id: int) -> MessageSummary | None:
        """Fetch message summary (headers only)."""
        self._ensure_connected()

        try:
            status, data = self._client.fetch(
                str(message_id),
                "(UID FLAGS INTERNALDATE RFC822.HEADER)",
            )
            if status != "OK":
                raise IMAPError(f"Fetch summary failed: {data}")

            if not data or len(data) < 2:
                return None

            # Parse response
            response_data = data[0] if isinstance(data[0], bytes) else data[0][0]
            response_str = response_data.decode("utf-8") if isinstance(response_data, bytes) else response_data

            # Extract UID
            uid_match = re.search(r"UID (\d+)", response_str)
            uid = int(uid_match.group(1)) if uid_match else 0

            # Extract flags
            flags_match = re.search(r"FLAGS \(([^)]*)\)", response_str)
            flags = tuple(flags_match.group(1).split()) if flags_match else ()

            # Extract date
            date_match = re.search(r'INTERNALDATE "(\d+-\w+-\d+ \d+:\d+:\d+ [+-]\d+)"', response_str)
            date_str = date_match.group(1) if date_match else ""

            # Get headers
            header_start = response_str.find("{") + 1
            header_end = response_str.find("}\r\n", header_start)
            if header_start > 0 and header_end > header_start:
                header_bytes = response_str[header_end + 3 :].encode("utf-8")
                headers = email.message_from_bytes(header_bytes)

                subject = headers.get("Subject", "")
                from_addr = headers.get("From", "")
                to_addr = headers.get("To", "")

                # Check for attachments
                has_attachments = any(
                    part.get_content_disposition() == "attachment"
                    for part in headers.walk()
                )

                # Estimate size
                size = len(header_bytes)

                return GmailMessageSummary(
                    id=str(message_id),
                    uid=uid,
                    subject=subject,
                    from_address=from_addr,
                    to_address=to_addr,
                    date=date_str,
                    flags=flags,
                    size=size,
                    has_attachments=has_attachments,
                )
            else:
                return GmailMessageSummary(
                    id=str(message_id),
                    uid=uid,
                    subject="",
                    from_address="",
                    to_address="",
                    date=date_str,
                    flags=flags,
                    size=0,
                    has_attachments=False,
                )
        except Exception as e:
            logger.error(f"Error fetching summary: {e}")
            raise IMAPError(f"Failed to fetch message summary: {e}") from e

    def move_message(self, message_id: int, destination_folder: str) -> bool:
        """Move a message to another folder."""
        self._ensure_connected()

        try:
            # Copy to destination
            status, data = self._client.copy(str(message_id), destination_folder)
            if status != "OK":
                raise IMAPError(f"Copy failed: {data}")

            # Mark original for deletion
            self._client.store(str(message_id), "+FLAGS", r"(\Deleted)")

            # Expunge to remove
            self._client.expunge()

            logger.info(f"Moved message {message_id} to {destination_folder}")
            return True
        except Exception as e:
            logger.error(f"Error moving message: {e}")
            raise IMAPError(f"Failed to move message: {e}") from e

    def copy_message(self, message_id: int, destination_folder: str) -> bool:
        """Copy a message to another folder."""
        self._ensure_connected()

        try:
            status, data = self._client.copy(str(message_id), destination_folder)
            if status != "OK":
                raise IMAPError(f"Copy failed: {data}")

            logger.info(f"Copied message {message_id} to {destination_folder}")
            return True
        except Exception as e:
            logger.error(f"Error copying message: {e}")
            raise IMAPError(f"Failed to copy message: {e}") from e

    def delete_message(self, message_id: int) -> bool:
        """Mark a message for deletion."""
        self._ensure_connected()

        try:
            self._client.store(str(message_id), "+FLAGS", r"(\Deleted)")
            logger.info(f"Marked message {message_id} for deletion")
            return True
        except Exception as e:
            logger.error(f"Error marking message for deletion: {e}")
            raise IMAPError(f"Failed to delete message: {e}") from e

    def mark_as_read(self, message_id: int) -> bool:
        """Mark a message as read."""
        self._ensure_connected()

        try:
            self._client.store(str(message_id), "-FLAGS", r"(\Unseen)")
            logger.info(f"Marked message {message_id} as read")
            return True
        except Exception as e:
            logger.error(f"Error marking message as read: {e}")
            raise IMAPError(f"Failed to mark message as read: {e}") from e

    def mark_as_unread(self, message_id: int) -> bool:
        """Mark a message as unread."""
        self._ensure_connected()

        try:
            self._client.store(str(message_id), "+FLAGS", r"(\Unseen)")
            logger.info(f"Marked message {message_id} as unread")
            return True
        except Exception as e:
            logger.error(f"Error marking message as unread: {e}")
            raise IMAPError(f"Failed to mark message as unread: {e}") from e

    def expunge(self) -> int:
        """Permanently remove deleted messages."""
        self._ensure_connected()

        try:
            result = self._client.expunge()
            deleted_count = len(result[1]) if result and len(result) > 1 else 0
            logger.info(f"Expunged {deleted_count} messages")
            return deleted_count
        except Exception as e:
            logger.error(f"Error expunging messages: {e}")
            raise IMAPError(f"Failed to expunge messages: {e}") from e

    def create_folder(self, folder_name: str) -> bool:
        """Create a new folder."""
        self._ensure_connected()

        try:
            status, data = self._client.create(folder_name)
            if status != "OK":
                raise IMAPError(f"Failed to create folder: {data}")

            logger.info(f"Created folder '{folder_name}'")
            return True
        except Exception as e:
            logger.error(f"Error creating folder: {e}")
            raise IMAPError(f"Failed to create folder: {e}") from e

    def delete_folder(self, folder_name: str) -> bool:
        """Delete a folder."""
        self._ensure_connected()

        try:
            status, data = self._client.delete(folder_name)
            if status != "OK":
                raise IMAPError(f"Failed to delete folder: {data}")

            logger.info(f"Deleted folder '{folder_name}'")
            return True
        except Exception as e:
            logger.error(f"Error deleting folder: {e}")
            raise IMAPError(f"Failed to delete folder: {e}") from e

    def get_quota(self) -> dict[str, Any] | None:
        """Get mailbox quota information."""
        self._ensure_connected()

        try:
            status, data = self._client.getquotaroot("INBOX")
            if status != "OK":
                return None

            # Parse quota response
            # Format: ('QUOTAROOT', 'INBOX', 'INBOX') ('QUOTA', 'INBOX', ('STORAGE', used, limit))
            for item in data:
                if isinstance(item, bytes):
                    item_str = item.decode("utf-8")
                    if b"STORAGE" in item:
                        match = re.search(r"STORAGE\s+(\d+)\s+(\d+)", item_str)
                        if match:
                            used = int(match.group(1))
                            limit = int(match.group(2))
                            return {
                                "used": used,
                                "limit": limit,
                                "percent_used": (used / limit * 100) if limit > 0 else 0,
                            }
            return None
        except Exception as e:
            logger.debug(f"Quota check failed: {e}")
            return None

    def get_last_error(self) -> str | None:
        """Get the last error message."""
        return self._last_error
