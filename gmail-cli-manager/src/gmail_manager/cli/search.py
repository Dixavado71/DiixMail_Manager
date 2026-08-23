"""Search CLI commands."""

import typer
from rich.console import Console
from rich.table import Table

from ..auth.credentials import CredentialManager
from ..config import Settings, get_settings
from ..imap.client import GmailIMAPClient
from ..utils.formatting import format_date, format_flags, format_subject
from ..utils.logging import print_error, print_info

console = Console()

app = typer.Typer(help="Search commands")


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


def parse_search_query(query: str) -> str:
    """
    Parse user-friendly search query to IMAP criteria.

    Supports:
    - from:domain.com
    - subject:keyword
    - has:attachment
    - unread / unseen
    - since:YYYY-MM-DD
    """
    query = query.strip()

    # Check for special patterns
    if query.lower().startswith("from:"):
        domain = query[5:].strip()
        return f'FROM "{domain}"'
    elif query.lower().startswith("subject:"):
        keyword = query[8:].strip()
        return f'SUBJECT "{keyword}"'
    elif query.lower() == "has:attachment":
        return "HAS attachment"
    elif query.lower() in ("unread", "unseen"):
        return "UNSEEN"
    elif query.lower().startswith("since:"):
        date = query[6:].strip()
        # Convert YYYY-MM-DD to DD-MMM-YYYY
        try:
            from datetime import datetime
            dt = datetime.strptime(date, "%Y-%m-%d")
            imap_date = dt.strftime("%d-%b-%Y")
            return f"SINCE {imap_date}"
        except ValueError:
            return f"SINCE {date}"
    else:
        # Default: search in body
        return f'BODY "{query}"'


@app.command()
def search(
    query: str = typer.Argument(..., help="Search query"),
    folder: str = typer.Option("INBOX", "--folder", "-f", help="Folder to search"),
    limit: int = typer.Option(50, "--limit", "-l", help="Max results"),
) -> None:
    """
    Search emails using IMAP criteria.

    Examples:
        gmail-manager search "FROM amazon"
        gmail-manager search "SUBJECT invoice"
        gmail-manager search "UNSEEN"
        gmail-manager search "has:attachment"
        gmail-manager search "from:amazon.com"
    """
    settings = get_settings()
    client = get_authenticated_client(settings)

    try:
        # Parse query
        imap_criteria = parse_search_query(query)
        console.print(f"[bold blue]Search[/bold blue]: {query}")
        console.print(f"[dim]IMAP criteria: {imap_criteria}[/dim]")
        console.print(f"[dim]Folder: {folder}[/dim]")
        console.print()

        # Select folder
        client.select_folder(folder)

        # Search
        message_ids = client.search(imap_criteria)
        total_found = len(message_ids)

        console.print(f"[green]Found: {total_found} messages[/green]")
        console.print()

        if not message_ids:
            return

        # Limit results
        display_ids = message_ids[-limit:] if len(message_ids) > limit else message_ids
        display_ids.reverse()  # Newest first

        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("ID", style="dim", width=5)
        table.add_column("Flags", width=8)
        table.add_column("From", style="cyan", width=30)
        table.add_column("Subject", style="white", width=50)
        table.add_column("Date", style="green", width=10)

        for msg_id in display_ids:
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

        if total_found > limit:
            console.print()
            print_info(f"Showing {len(display_ids)} of {total_found} results")

    except Exception as e:
        print_error(f"Search failed: {e}")
        raise typer.Exit(1)
    finally:
        client.disconnect()


@app.command()
def provider(
    domain: str = typer.Argument(..., help="Domain to search (e.g., amazon.com)"),
    folder: str = typer.Option("INBOX", "--folder", "-f", help="Folder to search"),
    limit: int = typer.Option(50, "--limit", "-l", help="Max results"),
) -> None:
    """Search emails by provider/domain."""
    settings = get_settings()
    client = get_authenticated_client(settings)

    try:
        console.print(f"[bold blue]Provider Search[/bold blue]: {domain}")
        console.print()

        client.select_folder(folder)

        # Search by domain
        message_ids = client.search(f'FROM "{domain}"')
        total_found = len(message_ids)

        console.print(f"[green]Found: {total_found:,} messages[/green]")
        console.print()

        if not message_ids:
            return

        # Show recent messages
        display_ids = message_ids[-limit:] if len(message_ids) > limit else message_ids
        display_ids.reverse()

        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("ID", style="dim", width=5)
        table.add_column("Flags", width=8)
        table.add_column("From", style="cyan", width=30)
        table.add_column("Subject", style="white", width=50)
        table.add_column("Date", style="green", width=10)

        for msg_id in display_ids:
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

        if total_found > limit:
            console.print()
            print_info(f"Showing {len(display_ids)} of {total_found:,} results")

    except Exception as e:
        print_error(f"Search failed: {e}")
        raise typer.Exit(1)
    finally:
        client.disconnect()
