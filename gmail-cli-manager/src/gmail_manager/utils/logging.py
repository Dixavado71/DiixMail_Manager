"""Utility functions for logging with Rich."""

import logging
import sys
from typing import Any

from rich.console import Console
from rich.logging import RichHandler
from rich.text import Text

console = Console()


class GmailLogger:
    """Custom logger with Rich formatting."""

    def __init__(self, name: str = "gmail_manager", level: int = logging.INFO) -> None:
        """Initialize logger with Rich handler."""
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)

        # Remove existing handlers
        self.logger.handlers.clear()

        # Add Rich handler
        handler = RichHandler(
            console=console,
            rich_tracebacks=True,
            tracebacks_show_locals=False,
            markup=False,
        )
        formatter = logging.Formatter("[%(name)s] %(message)s")
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

    def info(self, message: str) -> None:
        """Log info message."""
        self.logger.info(message)

    def debug(self, message: str) -> None:
        """Log debug message."""
        self.logger.debug(message)

    def warning(self, message: str) -> None:
        """Log warning message."""
        self.logger.warning(message)

    def error(self, message: str) -> None:
        """Log error message."""
        self.logger.error(message)

    def critical(self, message: str) -> None:
        """Log critical message."""
        self.logger.critical(message)

    def success(self, message: str) -> None:
        """Log success message with green checkmark."""
        self.logger.info(f"✓ {message}")

    def failure(self, message: str) -> None:
        """Log failure message with red X."""
        self.logger.error(f"✗ {message}")


def get_logger(name: str = "gmail_manager", level: str = "INFO") -> GmailLogger:
    """Get a configured GmailLogger instance."""
    log_level = getattr(logging, level.upper(), logging.INFO)
    return GmailLogger(name=name, level=log_level)


# Global logger instance
logger = get_logger()


def print_success(message: str) -> None:
    """Print success message with green checkmark."""
    console.print(f"[green]✓[/green] {message}")


def print_error(message: str) -> None:
    """Print error message with red X."""
    console.print(f"[red]✗[/red] {message}")


def print_info(message: str) -> None:
    """Print info message."""
    console.print(f"[blue]ℹ[/blue] {message}")


def print_warning(message: str) -> None:
    """Print warning message with yellow exclamation."""
    console.print(f"[yellow]⚠[/yellow] {message}")


def print_table(headers: list[str], rows: list[list[str]]) -> None:
    """Print a formatted table."""
    from rich.table import Table

    table = Table(show_header=True, header_style="bold magenta")
    for header in headers:
        table.add_column(header)

    for row in rows:
        table.add_row(*row)

    console.print(table)


def print_progress(iterable: list[Any], description: str = "Processing") -> Any:
    """Print progress bar for iterable."""
    from rich.progress import track

    return track(iterable, description=description)
