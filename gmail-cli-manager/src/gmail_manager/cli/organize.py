"""Organization rules CLI commands."""

import typer
from rich.console import Console
from rich.table import Table

from ..auth.credentials import CredentialManager
from ..config import Settings, get_settings
from ..imap.client import GmailIMAPClient
from ..utils.logging import print_error, print_info, print_success, print_warning

console = Console()

app = typer.Typer(help="Organization rules commands")


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


# Default organization rules
DEFAULT_RULES = [
    {
        "name": "Amazon Orders",
        "condition": {"from_contains": "amazon.com"},
        "action": {"move_to": "Shopping"},
    },
    {
        "name": "Invoices",
        "condition": {"subject_contains": ["invoice", "fatura", "receipt"]},
        "action": {"move_to": "Finance"},
    },
    {
        "name": "Newsletters",
        "condition": {"subject_contains": ["newsletter", "unsubscribe"]},
        "action": {"move_to": "Newsletters"},
    },
    {
        "name": "Social Media",
        "condition": {"from_contains": ["facebook.com", "twitter.com", "linkedin.com", "instagram.com"]},
        "action": {"move_to": "Social"},
    },
]


@app.command()
def organize(
    folder: str = typer.Option("INBOX", "--folder", "-f", help="Folder to organize"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Preview without executing"),
    rule_index: int | None = typer.Option(None, "--rule", "-r", help="Apply specific rule by index"),
) -> None:
    """
    Apply organization rules to messages.

    Rules are applied in order. Each message is processed only once.

    Examples:
        gmail-manager organize --dry-run
        gmail-manager organize --rule 0
        gmail-manager organize --folder INBOX
    """
    settings = get_settings()
    client = get_authenticated_client(settings)

    try:
        console.print("[bold blue]Organization Rules[/bold blue]")
        console.print()

        # Show rules
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("#", style="dim", width=3)
        table.add_column("Name", style="cyan")
        table.add_column("Condition", style="yellow")
        table.add_column("Action", style="green")

        for i, rule in enumerate(DEFAULT_RULES):
            condition = list(rule["condition"].items())[0]
            action = list(rule["action"].items())[0]
            table.add_row(
                str(i),
                rule["name"],
                f"{condition[0]}: {condition[1]}",
                f"{action[0]}: {action[1]}",
            )

        console.print(table)
        console.print()

        # Select folder
        count = client.select_folder(folder)
        console.print(f"[dim]Organizing folder: {folder} ({count} messages)[/dim]")
        console.print()

        # Get all message IDs
        message_ids = client.search("ALL")

        if not message_ids:
            print_warning("No messages to organize")
            return

        # Determine which rules to apply
        rules_to_apply = DEFAULT_RULES
        if rule_index is not None:
            if rule_index < 0 or rule_index >= len(DEFAULT_RULES):
                print_error(f"Invalid rule index: {rule_index}")
                raise typer.Exit(1)
            rules_to_apply = [DEFAULT_RULES[rule_index]]

        total_processed = 0
        total_moved = 0

        for rule in rules_to_apply:
            console.print(f"[bold]Applying rule: {rule['name']}[/bold]")

            # Build search criteria based on condition
            condition_key, condition_value = list(rule["condition"].items())[0]
            search_criteria = build_search_criteria(condition_key, condition_value)

            if not search_criteria:
                console.print(f"[dim]Skipping - unsupported condition[/dim]")
                continue

            # Search for matching messages
            matching_ids = client.search(search_criteria)

            if not matching_ids:
                console.print(f"[dim]No matches found[/dim]")
                continue

            console.print(f"[dim]Found {len(matching_ids)} matching messages[/dim]")

            if dry_run:
                console.print(f"[yellow]Would move {len(matching_ids)} messages to {rule['action'].get('move_to', 'N/A')}[/yellow]")
                total_processed += len(matching_ids)
            else:
                # Move messages
                dest_folder = rule["action"].get("move_to")
                if dest_folder:
                    success = 0
                    for msg_id in matching_ids[:100]:  # Limit per rule for safety
                        try:
                            client.move_message(msg_id, dest_folder)
                            success += 1
                        except Exception:
                            pass
                    console.print(f"[green]Moved {success} messages to {dest_folder}[/green]")
                    total_moved += success
                    total_processed += len(matching_ids)

            console.print()

        if dry_run:
            console.print(f"[bold yellow]DRY RUN: Would process {total_processed} messages[/bold yellow]")
        else:
            print_success(f"Processed {total_processed} messages, moved {total_moved}")

    except Exception as e:
        print_error(f"Organization failed: {e}")
        raise typer.Exit(1)
    finally:
        client.disconnect()


def build_search_criteria(key: str, value: str | list[str]) -> str | None:
    """Build IMAP search criteria from rule condition."""
    if key == "from_contains":
        domains = [value] if isinstance(value, str) else value
        # Use OR for multiple domains
        if len(domains) == 1:
            return f'FROM "{domains[0]}"'
        return None  # Complex OR not easily supported
    elif key == "subject_contains":
        keywords = [value] if isinstance(value, str) else value
        if len(keywords) == 1:
            return f'SUBJECT "{keywords[0]}"'
        return None
    elif key == "has_attachment":
        return "HAS attachment"
    return None


@app.command()
def rules() -> None:
    """List available organization rules."""
    console.print("[bold blue]Available Organization Rules[/bold blue]")
    console.print()

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("#", style="dim", width=3)
    table.add_column("Name", style="cyan")
    table.add_column("Condition", style="yellow")
    table.add_column("Action", style="green")

    for i, rule in enumerate(DEFAULT_RULES):
        condition = list(rule["condition"].items())[0]
        action = list(rule["action"].items())[0]
        table.add_row(
            str(i),
            rule["name"],
            f"{condition[0]}: {condition[1]}",
            f"{action[0]}: {action[1]}",
        )

    console.print(table)
