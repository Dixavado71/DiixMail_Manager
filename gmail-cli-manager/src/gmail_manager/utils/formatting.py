"""Formatting utilities for display."""

from datetime import datetime
from email.utils import parsedate_to_datetime
from typing import Any


def format_date(date_str: str) -> str:
    """
    Format email date string to readable format.

    Args:
        date_str: Email date string (RFC 2822)

    Returns:
        Formatted date string
    """
    if not date_str:
        return ""

    try:
        dt = parsedate_to_datetime(date_str)
        now = datetime.now(dt.tzinfo)
        diff = now - dt

        # If today, show time
        if diff.days == 0:
            return dt.strftime("%H:%M")
        # If this week, show day name
        elif diff.days < 7:
            return dt.strftime("%A")
        # Otherwise show date
        else:
            return dt.strftime("%Y-%m-%d")
    except (ValueError, TypeError):
        return date_str


def format_email_address(address: str, max_length: int = 30) -> str:
    """
    Format email address for display.

    Args:
        address: Email address
        max_length: Maximum length

    Returns:
        Formatted address
    """
    if not address:
        return ""

    # Extract just the email from "Name <email>" format
    if "<" in address and ">" in address:
        start = address.find("<") + 1
        end = address.find(">")
        address = address[start:end]

    # Truncate if too long
    if len(address) > max_length:
        return address[: max_length - 3] + "..."

    return address


def format_subject(subject: str, max_length: int = 50) -> str:
    """
    Format subject for display.

    Args:
        subject: Subject line
        max_length: Maximum length

    Returns:
        Formatted subject
    """
    if not subject:
        return "(no subject)"

    # Remove Re:, Fwd:, etc. prefixes for cleaner display
    cleaned = subject
    while cleaned.lower().startswith(("re:", "fw:", "fwd:")):
        cleaned = cleaned.split(":", 1)[1].strip()

    # Truncate if too long
    if len(cleaned) > max_length:
        return cleaned[: max_length - 3] + "..."

    return cleaned


def format_flags(flags: tuple[str, ...]) -> str:
    """
    Format message flags for display.

    Args:
        flags: Tuple of flag strings

    Returns:
        Formatted flags string
    """
    icons = []
    if "\\Seen" not in flags:
        icons.append("📬")  # Unread
    if "\\Flagged" in flags:
        icons.append("🚩")  # Flagged
    if "\\Answered" in flags:
        icons.append("↩️")  # Answered
    if "$Forwarded" in flags or "Forwarded" in str(flags):
        icons.append("➡️")  # Forwarded

    return " ".join(icons) if icons else "📭"  # Read


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Truncate text to maximum length.

    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add if truncated

    Returns:
        Truncated text
    """
    if not text:
        return ""

    if len(text) <= max_length:
        return text

    return text[: max_length - len(suffix)] + suffix


def format_number(num: int) -> str:
    """
    Format large numbers with K, M, B suffixes.

    Args:
        num: Number to format

    Returns:
        Formatted number string
    """
    if num >= 1_000_000_000:
        return f"{num / 1_000_000_000:.1f}B"
    elif num >= 1_000_000:
        return f"{num / 1_000_000:.1f}M"
    elif num >= 1_000:
        return f"{num / 1_000:.1f}K"
    else:
        return str(num)
