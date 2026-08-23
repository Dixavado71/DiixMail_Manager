"""Authentication CLI commands."""

import getpass
from pathlib import Path

import typer
from rich.console import Console

from ..auth.credentials import CredentialManager
from ..config import get_settings
from ..imap.client import GmailIMAPClient
from ..utils.logging import print_error, print_info, print_success, print_warning

console = Console()

app = typer.Typer(help="Authentication commands")


@app.command()
def login(
    interactive: bool = typer.Option(False, "--interactive", "-i", help="Interactive login"),
    email: str | None = typer.Option(None, "--email", "-e", help="Email address"),
) -> None:
    """
    Login to Gmail using App Password.

    If no credentials provided, prompts interactively.
    Credentials are stored securely in ~/.gmail-manager/credentials.json
    """
    settings = get_settings()
    cred_manager = CredentialManager(settings)

    console.print("[bold blue]Gmail Manager Login[/bold blue]")
    console.print()

    # Get email
    if email:
        user_email = email
    elif settings.email:
        user_email = settings.email
        console.print(f"Using email from config: {user_email}")
    else:
        user_email = input("E-mail: ").strip()

    if not user_email:
        print_error("Email is required")
        raise typer.Exit(1)

    # Get app password
    if settings.app_password and not interactive:
        app_password = settings.app_password
        console.print("Using password from config")
    else:
        app_password = getpass.getpass("Senha de aplicativo: ")

    if not app_password:
        print_error("App password is required")
        raise typer.Exit(1)

    # Test connection
    console.print()
    print_info("Testing connection...")

    client = GmailIMAPClient(settings)

    try:
        # Connect
        console.print("[dim]Connecting to IMAP server...[/dim]")
        client.connect()

        # Login
        console.print("[dim]Authenticating...[/dim]")
        client.login(user_email, app_password)

        # Success
        print_success("Conectado")
        print_success(f"Conta: {user_email}")
        print_success(f"Servidor: {settings.imap_host}")
        print_success("Autenticação funcionando")

        # Save credentials
        console.print()
        console.print("[dim]Saving credentials...[/dim]")
        cred_manager.save_credentials(
            email=user_email,
            app_password=app_password,
            imap_host=settings.imap_host,
            imap_port=settings.imap_port,
            smtp_host=settings.smtp_host,
            smtp_port=settings.smtp_port,
        )

        print_success("Credentials saved securely")

    except Exception as e:
        print_error(f"Login failed: {e}")
        raise typer.Exit(1)
    finally:
        client.disconnect()


@app.command()
def logout() -> None:
    """Logout and remove stored credentials."""
    settings = get_settings()
    cred_manager = CredentialManager(settings)

    if cred_manager.delete_credentials():
        print_success("Logged out successfully")
        print_info("Credentials removed")
    else:
        print_warning("No stored credentials found")


@app.command()
def status() -> None:
    """Check authentication status and connection."""
    settings = get_settings()
    cred_manager = CredentialManager(settings)

    console.print("[bold blue]Gmail Manager Status[/bold blue]")
    console.print()

    # Check credentials
    if cred_manager.has_credentials():
        print_success("Credentials stored")
        email = cred_manager.get_email()
        if email:
            console.print(f"  Email: [green]{email}[/green]")
    else:
        print_warning("No credentials stored")
        console.print("  Run 'gmail-manager login' to authenticate")
        raise typer.Exit(1)

    console.print()

    # Test connection
    console.print("[dim]Testing connection...[/dim]")
    client = GmailIMAPClient(settings)

    try:
        client.connect()
        print_success(f"IMAP: {settings.imap_host}:{settings.imap_port}")

        # Try to get quota
        quota = client.get_quota()
        if quota:
            used_gb = quota["used"] / 1024 / 1024
            limit_gb = quota["limit"] / 1024 / 1024
            percent = quota["percent_used"]
            console.print(f"  Storage: {used_gb:.1f} GB / {limit_gb:.1f} GB ({percent:.1f}%)")

    except Exception as e:
        print_error(f"Connection test failed: {e}")
        raise typer.Exit(1)
    finally:
        client.disconnect()

    console.print()
    print_success("All systems operational")
