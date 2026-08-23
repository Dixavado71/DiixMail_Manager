"""Módulo IMAP para conexão com Gmail."""

from .client import IMAPClient
from .folders import FolderManager
from .messages import MessageManager
from .search import SearchManager

__all__ = ["IMAPClient", "FolderManager", "MessageManager", "SearchManager"]
