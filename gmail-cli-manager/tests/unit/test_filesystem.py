"""Unit tests for filesystem utilities."""

from pathlib import Path

from gmail_manager.utils.filesystem import (
    format_size,
    get_unique_path,
    sanitize_filename,
)


def test_sanitize_filename_basic() -> None:
    """Test basic filename sanitization."""
    assert sanitize_filename("normal.txt") == "normal.txt"
    assert sanitize_filename("file with spaces.txt") == "file with spaces.txt"


def test_sanitize_filename_invalid_chars() -> None:
    """Test removal of invalid characters."""
    assert sanitize_filename("file<name>.txt") == "file_name_.txt"
    assert sanitize_filename('file"name.txt') == "filename.txt"
    assert sanitize_filename("file/name.txt") == "file_name.txt"


def test_sanitize_filename_unicode() -> None:
    """Test unicode normalization."""
    # Unicode characters should be normalized to ASCII
    result = sanitize_filename("café.txt")
    assert "caf" in result


def test_sanitize_filename_length() -> None:
    """Test filename length limiting."""
    long_name = "a" * 300 + ".txt"
    result = sanitize_filename(long_name)
    assert len(result) <= 255


def test_sanitize_filename_empty() -> None:
    """Test empty filename handling."""
    assert sanitize_filename("") == "unnamed"
    assert sanitize_filename("   ") == "unnamed"


def test_format_size() -> None:
    """Test size formatting."""
    assert format_size(100) == "100.0 B"
    assert format_size(1024) == "1.0 KB"
    assert format_size(1048576) == "1.0 MB"
    assert format_size(1073741824) == "1.0 GB"


def test_get_unique_path(tmp_path: Path) -> None:
    """Test unique path generation."""
    base = tmp_path / "test.txt"
    base.write_text("content")

    unique = get_unique_path(base)
    assert unique != base
    assert unique.name == "test_1.txt"


def test_get_unique_path_not_exists(tmp_path: Path) -> None:
    """Test unique path when file doesn't exist."""
    base = tmp_path / "new.txt"
    unique = get_unique_path(base)
    assert unique == base
