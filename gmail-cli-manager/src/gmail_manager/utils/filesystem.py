"""Filesystem utilities for safe file operations."""

import os
import re
import unicodedata
from pathlib import Path
from typing import Any

import orjson


def sanitize_filename(filename: str, max_length: int = 255) -> str:
    """
    Sanitize a filename by removing invalid characters.

    Args:
        filename: Original filename
        max_length: Maximum length of filename

    Returns:
        Sanitized filename
    """
    # Normalize unicode characters
    filename = unicodedata.normalize("NFKD", filename)
    filename = filename.encode("ascii", "ignore").decode("ascii")

    # Remove or replace invalid characters
    filename = re.sub(r'[<>:"/\\|?*]', "_", filename)

    # Remove leading/trailing spaces and dots
    filename = filename.strip(" .")

    # Replace multiple spaces with single space
    filename = re.sub(r"\s+", " ", filename)

    # Limit length
    if len(filename) > max_length:
        name, ext = os.path.splitext(filename)
        filename = name[: max_length - len(ext)] + ext

    # Ensure not empty
    if not filename:
        filename = "unnamed"

    return filename


def ensure_directory(path: Path) -> None:
    """Ensure directory exists, creating if necessary."""
    path.mkdir(parents=True, exist_ok=True)


def get_unique_path(base_path: Path) -> Path:
    """
    Get a unique file path by appending number if file exists.

    Args:
        base_path: Base path to check

    Returns:
        Unique path that doesn't exist
    """
    if not base_path.exists():
        return base_path

    counter = 1
    stem = base_path.stem
    suffix = base_path.suffix
    parent = base_path.parent

    while True:
        new_path = parent / f"{stem}_{counter}{suffix}"
        if not new_path.exists():
            return new_path
        counter += 1


def write_json_safe(path: Path, data: dict[str, Any], indent: bool = True) -> None:
    """
    Write JSON data safely with proper encoding.

    Args:
        path: File path
        data: Data to write
        indent: Whether to indent output
    """
    ensure_directory(path.parent)

    options = orjson.OPT_INDENT_2 if indent else 0
    content = orjson.dumps(data, option=options).decode("utf-8")

    path.write_text(content, encoding="utf-8")


def read_json_safe(path: Path) -> dict[str, Any]:
    """
    Read JSON file safely.

    Args:
        path: File path

    Returns:
        Parsed JSON data
    """
    content = path.read_text(encoding="utf-8")
    return orjson.loads(content)  # type: ignore[no-any-return]


def format_size(size_bytes: int) -> str:
    """
    Format byte size to human readable string.

    Args:
        size_bytes: Size in bytes

    Returns:
        Formatted size string (e.g., "1.5 MB")
    """
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if abs(size_bytes) < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} PB"


def is_path_safe(path: Path, base_dir: Path | None = None) -> bool:
    """
    Check if path is safe (doesn't escape base directory).

    Args:
        path: Path to check
        base_dir: Base directory (defaults to cwd)

    Returns:
        True if path is safe
    """
    if base_dir is None:
        base_dir = Path.cwd()

    try:
        resolved_path = path.resolve()
        resolved_base = base_dir.resolve()
        return resolved_base in resolved_path.parents or resolved_path == resolved_base
    except (OSError, ValueError):
        return False
