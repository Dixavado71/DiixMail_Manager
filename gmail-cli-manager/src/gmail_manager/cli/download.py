"""Download CLI commands."""

from datetime import datetime
from pathlib import Path

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from ..auth.credentials import CredentialManager
from ..config import Settings, get_settings
from ..email.parser import EmailParser
from ..imap.client import GmailIMAPClient
from ..utils.filesystem import ensure_directory, sanitize_filename, write_json_safe
from ..utils.logging import print_error, print_info, print_success, print_warning

console = Console()

app = typer.Typer(help="Download commands")


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
def download(
    search: str = typer.Option("ALL", "--search", "-s", help="Search criteria"),
    dest: Path = typer.Option(None, "--dest", "-d", help="Destination directory"),
    folder: str = typer.Option("INBOX", "--folder", "-f", help="Folder to search"),
    limit: int = typer.Option(100, "--limit", "-l", help="Max messages to download"),
    include_attachments: bool = typer.Option(True, "--attachments/--no-attachments", help="Include attachments"),
    format_type: str = typer.Option("eml", "--format", help="Format: eml, html, txt, json"),
) -> None:
    """
    Download emails and attachments.

    Examples:
        gmail-manager download --search "has:attachment"
        gmail-manager download --dest ./backup --limit 50
        gmail-manager download --format html --include-body
    """
    settings = get_settings()
    client = get_authenticated_client(settings)

    # Determine destination
    download_dir = dest or settings.download_dir
    today = datetime.now().strftime("%Y-%m-%d")
    download_path = download_dir / today

    try:
        console.print("[bold blue]Download Emails[/bold blue]")
        console.print(f"[dim]Destination: {download_path}[/dim]")
        console.print(f"[dim]Search: {search}[/dim]")
        console.print()

        # Select folder and search
        client.select_folder(folder)
        message_ids = client.search(search)

        if not message_ids:
            print_warning("No messages found")
            return

        # Limit results
        message_ids = message_ids[-limit:] if len(message_ids) > limit else message_ids
        total_count = len(message_ids)

        console.print(f"[green]Found {total_count} messages to download[/green]")
        console.print()

        downloaded = 0
        errors = 0

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Downloading...", total=total_count)

            for msg_id in message_ids:
                try:
                    message = client.fetch_message(msg_id)
                    if not message:
                        errors += 1
                        progress.advance(task)
                        continue

                    # Parse message
                    content = EmailParser.parse(message)

                    # Create download subdirectory by sender domain
                    from_domain = content.from_address.split("@")[-1] if "@" in content.from_address else "unknown"
                    msg_dir = download_path / sanitize_filename(from_domain)
                    ensure_directory(msg_dir)

                    # Generate filename
                    safe_subject = sanitize_filename(content.subject or "no-subject", 50)
                    base_name = f"email-{msg_id:06d}-{safe_subject}"

                    # Save based on format
                    if format_type == "eml":
                        # Save raw EML
                        eml_path = msg_dir / f"{base_name}.eml"
                        eml_path = get_unique_path(eml_path)
                        eml_path.write_bytes(message.as_bytes())
                        downloaded += 1

                    elif format_type == "html" and content.html_body:
                        html_path = msg_dir / f"{base_name}.html"
                        html_path = get_unique_path(html_path)
                        html_path.write_text(content.html_body, encoding="utf-8")
                        downloaded += 1

                    elif format_type == "txt" and content.text_body:
                        txt_path = msg_dir / f"{base_name}.txt"
                        txt_path = get_unique_path(txt_path)
                        txt_path.write_text(content.text_body, encoding="utf-8")
                        downloaded += 1

                    elif format_type == "json":
                        # Save metadata as JSON
                        json_path = msg_dir / f"{base_name}.json"
                        json_path = get_unique_path(json_path)
                        write_json_safe(
                            json_path,
                            {
                                "id": msg_id,
                                "subject": content.subject,
                                "from": content.from_address,
                                "to": content.to_addresses,
                                "date": content.date,
                                "text_body": content.text_body,
                                "html_body": content.html_body,
                                "attachments": [a["filename"] for a in content.attachments],
                            },
                        )
                        downloaded += 1

                    # Save attachments if requested
                    if include_attachments and content.attachments:
                        attachments_dir = msg_dir / f"{base_name}_attachments"
                        ensure_directory(attachments_dir)

                        for attachment in content.attachments:
                            att_path = attachments_dir / sanitize_filename(attachment["filename"])
                            att_path = get_unique_path(att_path)
                            if attachment.get("payload"):
                                att_path.write_bytes(attachment["payload"])

                    progress.advance(task)

                except Exception as e:
                    errors += 1
                    if errors <= 5:
                        console.print(f"[dim]Error downloading message {msg_id}: {e}[/dim]")
                    progress.advance(task)

        console.print()
        print_success(f"Downloaded {downloaded} messages to {download_path}")

        if errors > 0:
            print_warning(f"Errors: {errors} messages failed")

    except Exception as e:
        print_error(f"Download failed: {e}")
        raise typer.Exit(1)
    finally:
        client.disconnect()


def get_unique_path(path: Path) -> Path:
    """Get unique path by appending number if exists."""
    if not path.exists():
        return path

    counter = 1
    stem = path.stem
    suffix = path.suffix
    parent = path.parent

    while True:
        new_path = parent / f"{stem}_{counter}{suffix}"
        if not new_path.exists():
            return new_path
        counter += 1
