"""Custom exceptions for Gmail Manager."""


class GmailManagerError(Exception):
    """Base exception for Gmail Manager."""


class AuthenticationError(GmailManagerError):
    """Authentication failed."""


class ConnectionError(GmailManagerError):
    """Connection to server failed."""


class IMAPError(GmailManagerError):
    """IMAP operation failed."""


class SMTPError(GmailManagerError):
    """SMTP operation failed."""


class FolderNotFoundError(GmailManagerError):
    """Folder not found."""


class MessageNotFoundError(GmailManagerError):
    """Message not found."""


class ConfigurationError(GmailManagerError):
    """Configuration error."""
