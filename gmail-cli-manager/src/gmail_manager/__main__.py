"""Main entry point for Gmail Manager CLI/TUI."""

import sys
from typing import Optional

import typer
from rich.console import Console

from gmail_manager.config import get_settings
from gmail_manager.tui.app import GmailManagerApp
from gmail_manager.utils.logging import print_error, print_success

console = Console()

app = typer.Typer(
    name="gmail-manager",
    help="Gmail CLI Manager - Manage Gmail via IMAP/SMTP without OAuth",
    add_completion=False,
)


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    version: bool = typer.Option(False, "--version", "-v", help="Show version"),
) -> None:
    """
    Gmail Manager - Main entry point.

    Opens the TUI dashboard by default.
    """
    from gmail_manager import __version__

    if version:
        console.print(f"[bold blue]Gmail Manager[/bold blue] v{__version__}")
        raise typer.Exit()

    # If no subcommand, open TUI
    if ctx.invoked_subcommand is None:
        run_tui()


def run_tui() -> None:
    """Run the Textual TUI application."""
    settings = get_settings()

    if not settings.is_authenticated():
        console.print("[yellow]⚠ Not authenticated. Run 'gmail-manager login' first.[/yellow]")
        console.print()
        console.print("Or set environment variables:")
        console.print("  EMAIL=your@gmail.com")
        console.print("  APP_PASSWORD=xxxx xxxx xxxx xxxx")
        raise typer.Exit(1)

    try:
        gmail_app = GmailManagerApp(settings=settings)
        gmail_app.run()
    except KeyboardInterrupt:
        console.print("\n[yellow]Exiting...[/yellow]")
        raise typer.Exit(0)
    except Exception as e:
        print_error(f"Error: {e}")
        raise typer.Exit(1)


# Import CLI commands
from .cli.auth import app as auth_app
from .cli.mailbox import app as mailbox_app
from .cli.search import app as search_app
from .cli.organize import app as organize_app
from .cli.bulk import app as bulk_app
from .cli.download import app as download_app

app.add_typer(auth_app, name="auth")
app.add_typer(mailbox_app, name="mailbox")
app.add_typer(search_app, name="search")
app.add_typer(organize_app, name="organize")
app.add_typer(bulk_app, name="bulk")
app.add_typer(download_app, name="download")


if __name__ == "__main__":
    app()
