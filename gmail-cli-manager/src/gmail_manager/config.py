"""Configuration management using pydantic-settings."""

import os
from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables and .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Email credentials
    email: str = Field(default="", description="Gmail address")
    app_password: str = Field(default="", description="App password for Gmail")

    # IMAP settings
    imap_host: str = Field(default="imap.gmail.com", description="IMAP server host")
    imap_port: int = Field(default=993, description="IMAP server port")
    imap_ssl: bool = Field(default=True, description="Use SSL for IMAP")

    # SMTP settings
    smtp_host: str = Field(default="smtp.gmail.com", description="SMTP server host")
    smtp_port: int = Field(default=465, description="SMTP server port")
    smtp_ssl: bool = Field(default=True, description="Use SSL for SMTP")
    smtp_starttls: bool = Field(default=False, description="Use STARTTLS for SMTP")

    # Application settings
    download_dir: Path = Field(default=Path("./downloads"), description="Download directory")
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO", description="Logging level"
    )
    batch_size: int = Field(default=50, ge=1, le=500, description="Batch size for bulk operations")

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        """Validate email format."""
        if v and "@" not in v:
            raise ValueError("Invalid email format")
        return v.lower().strip() if v else v

    @field_validator("download_dir")
    @classmethod
    def validate_download_dir(cls, v: Path) -> Path:
        """Ensure download directory path is absolute or relative to cwd."""
        return v.expanduser()

    @property
    def config_path(self) -> Path:
        """Return the path to the configuration directory."""
        return Path.home() / ".gmail-manager"

    @property
    def credentials_path(self) -> Path:
        """Return the path to the credentials file."""
        return self.config_path / "credentials.json"

    def ensure_config_dir(self) -> None:
        """Ensure configuration directory exists."""
        self.config_path.mkdir(parents=True, exist_ok=True)

    def is_authenticated(self) -> bool:
        """Check if credentials are configured."""
        return bool(self.email and self.app_password)


# Global settings instance
_settings: Settings | None = None


def get_settings() -> Settings:
    """Get or create global settings instance."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def reset_settings() -> None:
    """Reset global settings instance (useful for testing)."""
    global _settings
    _settings = None
