"""Confirmation utilities for dangerous operations."""

from rich.console import Console
from rich.prompt import Confirm, Prompt

console = Console()


def confirm_action(
    action: str,
    target: str = "",
    count: int = 1,
    required_text: str | None = None,
) -> bool:
    """
    Ask for confirmation before a dangerous operation.

    Args:
        action: Action being performed (e.g., "DELETE", "MOVE")
        target: Target of the action (e.g., folder name)
        count: Number of items affected
        required_text: If provided, user must type this exact text

    Returns:
        True if confirmed, False otherwise
    """
    console.print()
    console.print("[bold red]⚠️  CONFIRMATION REQUIRED[/bold red]")
    console.print()

    if count > 1:
        console.print(f"[yellow]{count} items will be affected[/yellow]")
    elif target:
        console.print(f"[yellow]Target: {target}[/yellow]")

    console.print(f"[bold red]Action: {action}[/bold red]")
    console.print()

    # If specific text required
    if required_text:
        console.print(f"Type exactly: [bold]{required_text}[/bold]")
        console.print()

        user_input = Prompt.ask("Confirmation")
        return user_input == required_text

    # Simple yes/no confirmation
    return Confirm.ask("[red]Are you sure?[/red]", default=False)


def confirm_bulk_operation(
    action: str,
    message_count: int,
    search_criteria: str = "",
) -> bool:
    """
    Ask for confirmation for bulk operations.

    Args:
        action: Action being performed
        message_count: Number of messages affected
        search_criteria: Search criteria used

    Returns:
        True if confirmed, False otherwise
    """
    console.print()
    console.print("[bold red]╔════════════════════════════════════════╗[/bold red]")
    console.print("[bold red]║     BULK OPERATION CONFIRMATION        ║[/bold red]")
    console.print("[bold red]╚════════════════════════════════════════╝[/bold red]")
    console.print()

    console.print(f"[yellow]Messages affected: {message_count:,}[/yellow]")

    if search_criteria:
        console.print(f"[dim]Search: {search_criteria}[/dim]")

    console.print()
    console.print(f"[bold red]ACTION: {action}[/bold red]")
    console.print()

    required_text = f"CONFIRM {action}"
    console.print(f"Type exactly: [bold green]{required_text}[/bold green]")
    console.print()

    user_input = Prompt.ask("Confirmation", password=False)
    return user_input == required_text


def confirm_exit() -> bool:
    """Ask for confirmation to exit."""
    return Confirm.ask("[yellow]Exit application?[/yellow]", default=True)


def prompt_required(message: str, required_value: str, hide_input: bool = False) -> bool:
    """
    Prompt user to enter a required value.

    Args:
        message: Prompt message
        required_value: Value that must be entered
        hide_input: Whether to hide input (for passwords)

    Returns:
        True if correct value entered
    """
    console.print()
    console.print(f"[dim]{message}[/dim]")
    console.print(f"Required: [bold]{required_value}[/bold]")
    console.print()

    user_input = Prompt.ask("Enter value", password=hide_input)
    return user_input == required_value
