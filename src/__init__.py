"""Gmail Manager CLI - Módulo principal."""

from .config.settings import Settings
from .imap.client import IMAPClient
from .email.parser import EmailParser
from .attachments.downloader import AttachmentDownloader
from .cli.menu import Menu

__all__ = [
    "Settings",
    "IMAPClient",
    "EmailParser",
    "AttachmentDownloader",
    "Menu",
]
