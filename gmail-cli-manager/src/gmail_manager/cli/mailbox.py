"""Mailbox CLI commands."""

import typer
from rich.console import Console
from rich.table import Table

from ..auth.credentials import CredentialManager
from ..config import Settings, get_settings
from ..imap.client import GmailIMAPClient
from ..utils.formatting import format_date, format_flags, format_subject
from ..utils.logging import print_error, print_info

console = Console()

app = typer.Typer(help="Mailbox management commands")


def get_authenticated_client(settings: Settings) -> GmailIMAPClient:
    """Get authenticated IMAP client or exit."""
    cred_manager = CredentialManager(settings)
    creds = cred_manager.load_credentials()

    if not creds or not creds.get("email") or not creds.get("app_password"):
        print_error("Not authenticated. Run 'gmail-manager login' first.")
        raise typer.Exit(1)

    client = GmailIMAPClient(settings)
    try:
        client.connect()
        client.login(creds["email"], creds["app_password"])
        return client
    except Exception as e:
        print_error(f"Connection failed: {e}")
        raise typer.Exit(1)


@app.command()
def folders() -> None:
    """List all folders/mailboxes."""
    settings = get_settings()
    client = get_authenticated_client(settings)

    try:
        console.print("[bold blue]Folders[/bold blue]")
        console.print()

        folders = client.list_folders()

        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Name", style="cyan")
        table.add_column("Attributes", style="dim")
        table.add_column("Selectable", style="green")

        for folder in folders:
            attrs = " ".join(folder.attributes) if folder.attributes else "-"
            selectable = "✓" if folder.selectability == "selectable" else "✗"
            table.add_row(folder.name, attrs, selectable)

        console.print(table)
        console.print()
        print_info(f"Total: {len(folders)} folders")

    except Exception as e:
        print_error(f"Error listing folders: {e}")
        raise typer.Exit(1)
    finally:
        client.disconnect()


@app.command()
def inbox(
    limit: int = typer.Option(20, "--limit", "-l", help="Number of messages to show"),
) -> None:
    """Show inbox messages."""
    settings = get_settings()
    client = get_authenticated_client(settings)

    try:
        console.print("[bold blue]Inbox[/bold blue]")
        console.print()

        count = client.select_folder("INBOX")
        console.print(f"[dim]{count} messages total[/dim]")
        console.print()

        # Get message IDs (newest first)
        message_ids = client.search("ALL")
        message_ids = message_ids[-limit:] if len(message_ids) > limit else message_ids
        message_ids.reverse()  # Newest first

        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("ID", style="dim", width=5)
        table.add_column("Flags", width=8)
        table.add_column("From", style="cyan", width=30)
        table.add_column("Subject", style="white", width=50)
        table.add_column("Date", style="green", width=10)

        for msg_id in message_ids:
            summary = client.fetch_summary(msg_id)
            if summary:
                table.add_row(
                    str(msg_id),
                    format_flags(summary.flags),
                    format_subject(summary.from_address, 30),
                    format_subject(summary.subject, 50),
                    format_date(summary.date),
                )

        console.print(table)

    except Exception as e:
        print_error(f"Error: {e}")
        raise typer.Exit(1)
    finally:
        client.disconnect()


@app.command()
def read(
    message_id: int = typer.Argument(..., help="Message ID to read"),
    folder: str = typer.Option("INBOX", "--folder", "-f", help="Folder name"),
) -> None:
    """Read a specific message."""
    settings = get_settings()
    client = get_authenticated_client(settings)

    try:
        client.select_folder(folder)
        message = client.fetch_message(message_id)

        if not message:
            print_error(f"Message {message_id} not found")
            raise typer.Exit(1)

        console.print()
        console.print("[bold blue]═" * 60 + "[/bold blue]")
        console.print(f"[bold]From:[/bold]    {message.get('From', 'N/A')}")
        console.print(f"[bold]To:[/bold]      {message.get('To', 'N/A')}")
        console.print(f"[bold]Date:[/bold]    {message.get('Date', 'N/A')}")
        console.print(f"[bold]Subject:[/bold] {message.get('Subject', 'N/A')}")
        console.print("[bold blue]─" * 60 + "[/bold blue]")
        console.print()

        # Get body
        if message.is_multipart():
            for part in message.walk():
                if part.get_content_type() == "text/plain":
                    body = part.get_payload(decode=True)
                    if body:
                        console.print(body.decode(part.get_content_charset() or "utf-8", errors="replace"))
                        break
        else:
            body = message.get_payload(decode=True)
            if body:
                console.print(body.decode(message.get_content_charset() or "utf-8", errors="replace"))

        console.print()
        console.print("[bold blue]═" * 60 + "[/bold blue]")

    except Exception as e:
        print_error(f"Error reading message: {e}")
        raise typer.Exit(1)
    finally:
        client.disconnect()
