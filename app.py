#!/usr/bin/env python3
"""
Gmail Manager CLI - Gerenciador de e-mail Gmail via IMAP.

Este é o ponto de entrada da aplicação.
"""

import sys
import logging
from pathlib import Path

# Configura logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("gmail_manager.log", encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)

logger = logging.getLogger(__name__)


def main():
    """Função principal da aplicação."""
    # Adiciona src ao path
    src_path = Path(__file__).parent / "src"
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))
    
    from rich.console import Console
    from rich.panel import Panel
    
    console = Console()
    
    # Banner inicial
    console.print(Panel.fit(
        "[bold blue]GMAIL MANAGER CLI[/bold blue]\n"
        "[cyan]Gerenciador Premium de E-mails[/cyan]",
        border_style="blue",
    ))
    
    # Carrega configurações
    console.print("\n[bold]⚡ Carregando configurações...[/bold]")
    
    try:
        from src.config.settings import load_settings, Settings
        
        settings = load_settings()
        
        if not settings.is_valid():
            console.print("\n[red]✗ Erro: Credenciais inválidas no arquivo .env[/red]")
            console.print("\n[cyan]Certifique-se de que o arquivo .env contém:[/cyan]")
            console.print("  GMAIL_EMAIL=seuemail@gmail.com")
            console.print("  GMAIL_APP_PASSWORD=sua_senha_de_app")
            console.print("\n[cyan]Para obter a Senha de App:[/cyan]")
            console.print("  1. Acesse https://myaccount.google.com/apppasswords")
            console.print("  2. Selecione 'Mail' e seu dispositivo")
            console.print("  3. Copie a senha gerada (16 caracteres)")
            console.print("  4. Cole no arquivo .env como GMAIL_APP_PASSWORD")
            sys.exit(1)
        
        console.print("[green]✓ Configurações carregadas com sucesso[/green]")
        console.print(f"[cyan]Conta: {settings.gmail_email}[/cyan]")
        
    except Exception as e:
        logger.exception("Erro ao carregar configurações")
        console.print(f"[red]✗ Erro: {e}[/red]")
        sys.exit(1)
    
    # Inicia CLI
    try:
        from src.cli.menu import GmailCLI
        
        cli = GmailCLI(settings)
        cli.run()
        
    except KeyboardInterrupt:
        console.print("\n\n[yellow]⚠ Aplicação encerrada pelo usuário[/yellow]")
        sys.exit(0)
    except Exception as e:
        logger.exception("Erro fatal na aplicação")
        console.print(f"\n[red]✗ Erro fatal: {e}[/red]")
        console.print("[yellow]Verifique o arquivo gmail_manager.log para detalhes[/yellow]")
        sys.exit(1)


if __name__ == "__main__":
    main()
