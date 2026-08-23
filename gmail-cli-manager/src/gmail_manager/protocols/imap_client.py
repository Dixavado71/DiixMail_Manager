"""Protocol definitions for IMAP and SMTP clients."""

from abc import ABC, abstractmethod
from email.message import Message
from typing import Any, Protocol


class FolderInfo(Protocol):
    """Protocol for folder information."""

    name: str
    delimiter: str | None
    attributes: tuple[str, ...]
    selectability: str  # \HasNoChildren, \Selectable, etc.


class MessageSummary(Protocol):
    """Protocol for message summary information."""

    id: str
    uid: int
    subject: str
    from_address: str
    to_address: str
    date: str
    flags: tuple[str, ...]
    size: int
    has_attachments: bool


class IMAPClientProtocol(ABC):
    """Abstract protocol for IMAP client operations."""

    @abstractmethod
    def connect(self) -> bool:
        """Connect to IMAP server."""

    @abstractmethod
    def disconnect(self) -> None:
        """Disconnect from IMAP server."""

    @abstractmethod
    def login(self, email: str, password: str) -> bool:
        """Authenticate with IMAP server."""

    @abstractmethod
    def is_connected(self) -> bool:
        """Check if connected to server."""

    @abstractmethod
    def list_folders(self) -> list[FolderInfo]:
        """List all folders/mailboxes."""

    @abstractmethod
    def select_folder(self, folder_name: str) -> int:
        """Select a folder and return message count."""

    @abstractmethod
    def search(self, criteria: str) -> list[int]:
        """Search messages by criteria."""

    @abstractmethod
    def fetch_message(self, message_id: int) -> Message | None:
        """Fetch a complete message."""

    @abstractmethod
    def fetch_summary(self, message_id: int) -> MessageSummary | None:
        """Fetch message summary (headers only)."""

    @abstractmethod
    def move_message(self, message_id: int, destination_folder: str) -> bool:
        """Move a message to another folder."""

    @abstractmethod
    def copy_message(self, message_id: int, destination_folder: str) -> bool:
        """Copy a message to another folder."""

    @abstractmethod
    def delete_message(self, message_id: int) -> bool:
        """Mark a message for deletion."""

    @abstractmethod
    def mark_as_read(self, message_id: int) -> bool:
        """Mark a message as read."""

    @abstractmethod
    def mark_as_unread(self, message_id: int) -> bool:
        """Mark a message as unread."""

    @abstractmethod
    def expunge(self) -> int:
        """Permanently remove deleted messages."""

    @abstractmethod
    def create_folder(self, folder_name: str) -> bool:
        """Create a new folder."""

    @abstractmethod
    def delete_folder(self, folder_name: str) -> bool:
        """Delete a folder."""

    @abstractmethod
    def get_quota(self) -> dict[str, Any] | None:
        """Get mailbox quota information."""


class SMTPClientProtocol(ABC):
    """Abstract protocol for SMTP client operations."""

    @abstractmethod
    def connect(self) -> bool:
        """Connect to SMTP server."""

    @abstractmethod
    def disconnect(self) -> None:
        """Disconnect from SMTP server."""

    @abstractmethod
    def login(self, email: str, password: str) -> bool:
        """Authenticate with SMTP server."""

    @abstractmethod
    def is_connected(self) -> bool:
        """Check if connected to server."""

    @abstractmethod
    def send_message(self, message: Message) -> bool:
        """Send an email message."""

    @abstractmethod
    def send_simple(
        self,
        subject: str,
        body: str,
        to_addresses: list[str],
        from_address: str | None = None,
        html: bool = False,
        attachments: list[str] | None = None,
    ) -> bool:
        """Send a simple email."""
