"""Módulo IMAP para conexão e operações com Gmail."""

from .client import IMAPClient
from .folders import FolderManager
from .messages import MessageManager
from .search import SearchEngine

__all__ = ["IMAPClient", "FolderManager", "MessageManager", "SearchEngine"]
