#!/usr/bin/env python3
"""Gmail Manager CLI - Ponto de entrada da aplicação."""

import sys
from rich.console import Console
from rich.panel import Panel

from src.config.settings import get_settings, Settings
from src.imap.client import IMAPClient
from src.cli.menu import CLIMenu


console = Console()


def print_banner() -> None:
    """Imprime banner inicial."""
    console.print()
    console.print(Panel.fit(
        "[bold blue]GMAIL MANAGER CLI[/bold blue]\n"
        "[dim]Gerenciador Premium de E-mails via IMAP[/dim]",
        border_style="blue",
    ))
    console.print()


def main() -> int:
    """Função principal.

    Returns:
        Código de saída (0 para sucesso).
    """
    print_banner()

    # Carrega configurações
    console.print("[bold yellow]⚡ Carregando configurações...[/bold yellow]")
    try:
        settings = get_settings()
        console.print("[green]✓ Configurações carregadas com sucesso[/green]")
        console.print(f"[dim]Conta: {settings.gmail_email}[/dim]")
    except ValueError as e:
        console.print(f"[bold red]✗ Erro: {e}[/bold red]")
        console.print()
        console.print("[dim]Para configurar:[/dim]")
        console.print("  1. Edite o arquivo [cyan].env[/cyan]")
        console.print("  2. Adicione suas credenciais do Gmail")
        console.print("  3. Use uma [cyan]Senha de App[/cyan] (não sua senha normal)")
        console.print()
        console.print("[dim]Como gerar Senha de App:[/dim]")
        console.print("  1. Acesse https://myaccount.google.com/apppasswords")
        console.print("  2. Selecione 'Mail' e seu dispositivo")
        console.print("  3. Copie a senha de 16 caracteres")
        console.print("  4. Cole no arquivo .env como GMAIL_APP_PASSWORD")
        return 1

    # Conecta ao Gmail
    console.print("\n[bold yellow]⚡ Conectando ao Gmail...[/bold yellow]")
    client = IMAPClient(settings)

    try:
        console.print("[dim]⠋ Autenticando...[/dim]", end="\r")
        if not client.connect():
            console.print("[bold red]✗ Falha na conexão[/bold red]")
            return 1
        
        console.print("[green]✓ Conectado com sucesso ao Gmail[/green]")

        # Testa acesso à INBOX
        console.print("[dim]⠋ Acessando caixa de entrada...[/dim]", end="\r")
        total = client.select_folder("INBOX")
        console.print(f"[green]✓ Caixa de entrada selecionada ({total} mensagens)[/green]")

    except ConnectionError as e:
        console.print(f"[bold red]✗ {e}[/bold red]")
        console.print()
        console.print("[dim]Verifique:[/dim]")
        console.print("  • Seu e-mail está correto no .env")
        console.print("  • Você está usando Senha de App (não senha normal)")
        console.print("  • IMAP está habilitado na conta Gmail")
        console.print("  • Verificação em duas etapas está ativa")
        return 1
    except Exception as e:
        console.print(f"[bold red]✗ Erro inesperado: {e}[/bold red]")
        return 1

    # Inicia menu CLI
    console.print()
    menu = CLIMenu(client, settings)
    
    try:
        menu.run()
    except KeyboardInterrupt:
        console.print("\n\n[dim]Interrupto pelo usuário.[/dim]")
    finally:
        client.disconnect()

    return 0


if __name__ == "__main__":
    sys.exit(main())
