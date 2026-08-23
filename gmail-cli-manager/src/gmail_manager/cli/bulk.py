"""Bulk operations CLI commands."""

import typer
from rich.console import Console

from ..auth.credentials import CredentialManager
from ..config import Settings, get_settings
from ..imap.client import GmailIMAPClient
from ..utils.confirmations import confirm_bulk_operation
from ..utils.logging import print_error, print_info, print_success, print_warning

console = Console()

app = typer.Typer(help="Bulk operation commands")


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
def bulk(
    search: str = typer.Option(..., "--search", "-s", help="Search criteria"),
    delete: bool = typer.Option(False, "--delete", help="Delete matching messages"),
    move_to: str | None = typer.Option(None, "--move-to", help="Move to folder"),
    copy_to: str | None = typer.Option(None, "--copy-to", help="Copy to folder"),
    mark_read: bool = typer.Option(False, "--mark-read", help="Mark as read"),
    mark_unread: bool = typer.Option(False, "--mark-unread", help="Mark as unread"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Preview without executing"),
    folder: str = typer.Option("INBOX", "--folder", "-f", help="Folder to search"),
    no_confirm: bool = typer.Option(False, "--no-confirm", help="Skip confirmation"),
) -> None:
    """
    Perform bulk operations on messages matching search criteria.

    Examples:
        gmail-manager bulk --search "FROM amazon.com" --delete --dry-run
        gmail-manager bulk --search "UNSEEN" --mark-read
        gmail-manager bulk --search "SUBJECT invoice" --move-to Finance
    """
    settings = get_settings()
    client = get_authenticated_client(settings)

    # Validate operation
    operations = sum([bool(delete), bool(move_to), bool(copy_to), bool(mark_read), bool(mark_unread)])
    if operations == 0:
        print_error("Specify at least one operation: --delete, --move-to, --copy-to, --mark-read, --mark-unread")
        raise typer.Exit(1)
    if operations > 1:
        print_error("Only one operation can be performed at a time")
        raise typer.Exit(1)

    try:
        # Select folder and search
        client.select_folder(folder)
        message_ids = client.search(search)
        total_count = len(message_ids)

        console.print()
        console.print("[bold blue]Bulk Operation Preview[/bold blue]")
        console.print(f"[dim]Search: {search}[/dim]")
        console.print(f"[dim]Folder: {folder}[/dim]")
        console.print()

        if total_count == 0:
            print_warning("No messages found matching criteria")
            return

        console.print(f"[yellow]Messages affected: {total_count:,}[/yellow]")
        console.print()

        # Determine action description
        if delete:
            action = "DELETE"
        elif move_to:
            action = f"MOVE to {move_to}"
        elif copy_to:
            action = f"COPY to {copy_to}"
        elif mark_read:
            action = "MARK AS READ"
        elif mark_unread:
            action = "MARK AS UNREAD"
        else:
            action = "UNKNOWN"

        # Dry run mode
        if dry_run:
            console.print("[bold yellow]🔍 DRY RUN MODE - No changes will be made[/bold yellow]")
            console.print()
            console.print(f"Would {action.lower()} {total_count:,} messages")

            # Show sample of affected messages
            sample_ids = message_ids[-5:] if len(message_ids) > 5 else message_ids
            console.print()
            console.print("[dim]Sample messages:[/dim]")
            for msg_id in sample_ids:
                summary = client.fetch_summary(msg_id)
                if summary:
                    console.print(f"  ID {msg_id}: {summary.subject[:60]}")

            return

        # Confirmation
        if not no_confirm and total_count > 1:
            if not confirm_bulk_operation(action, total_count, search):
                console.print()
                print_warning("Operation cancelled")
                return

        # Execute operation
        console.print()
        console.print(f"[dim]Executing {action}...[/dim]")

        success_count = 0
        error_count = 0

        for msg_id in message_ids:
            try:
                if delete:
                    client.delete_message(msg_id)
                elif move_to:
                    client.move_message(msg_id, move_to)
                elif copy_to:
                    client.copy_message(msg_id, copy_to)
                elif mark_read:
                    client.mark_as_read(msg_id)
                elif mark_unread:
                    client.mark_as_unread(msg_id)

                success_count += 1
            except Exception as e:
                error_count += 1
                if error_count <= 5:
                    console.print(f"[dim]Error processing message {msg_id}: {e}[/dim]")

        # Expunge if deletions were made
        if delete and success_count > 0:
            deleted = client.expunge()
            console.print(f"[dim]Expunged {deleted} messages[/dim]")

        console.print()
        print_success(f"Completed: {success_count:,} messages processed")

        if error_count > 0:
            print_warning(f"Errors: {error_count:,} messages failed")

    except Exception as e:
        print_error(f"Bulk operation failed: {e}")
        raise typer.Exit(1)
    finally:
        client.disconnect()
