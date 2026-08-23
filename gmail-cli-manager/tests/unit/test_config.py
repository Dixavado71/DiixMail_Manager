"""Unit tests for configuration."""

import pytest

from gmail_manager.config import Settings, get_settings, reset_settings


def test_default_settings() -> None:
    """Test default settings values."""
    reset_settings()
    settings = get_settings()

    assert settings.imap_host == "imap.gmail.com"
    assert settings.imap_port == 993
    assert settings.smtp_host == "smtp.gmail.com"
    assert settings.smtp_port == 465
    assert settings.batch_size == 50
    assert settings.log_level == "INFO"


def test_email_validation() -> None:
    """Test email validation."""
    # Valid emails should work
    settings = Settings(email="test@gmail.com")
    assert settings.email == "test@gmail.com"

    # Email should be lowercased
    settings = Settings(email="Test@Gmail.Com")
    assert settings.email == "test@gmail.com"


def test_is_authenticated() -> None:
    """Test authentication check."""
    settings = Settings()
    assert not settings.is_authenticated()

    settings = Settings(email="test@gmail.com", app_password="test123")
    assert settings.is_authenticated()


def test_config_path() -> None:
    """Test config path generation."""
    settings = Settings()
    assert "gmail-manager" in str(settings.config_path)
    assert "credentials.json" in str(settings.credentials_path)
