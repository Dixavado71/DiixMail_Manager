#!/usr/bin/env python3
"""
Gmail Manager CLI - Gerenciador de e-mail Gmail via IMAP

Aplicação CLI para gerenciar e-mails do Gmail usando IMAP.
Permite ler, pesquisar, baixar anexos e organizar e-mails.

Uso:
    python app.py

Requisitos:
    - Python 3.11+
    - Arquivo .env configurado com credenciais do Gmail
    - Acesso IMAP habilitado na conta Gmail
    - Senha de app do Google (não a senha normal)
"""

import sys
from pathlib import Path

# Adiciona o diretório raiz ao path para imports
sys.path.insert(0, str(Path(__file__).parent))

from rich.console import Console
from rich.panel import Panel

from src.config.settings import Settings
from src.cli.menu import Menu


def main():
    """Função principal da aplicação."""
    console = Console()

    # Exibe cabeçalho inicial
    console.print(Panel.fit(
        "[bold blue]GMAIL MANAGER CLI[/bold blue]\n"
        "Gerenciador de e-mail Gmail via IMAP",
        border_style="blue"
    ))

    # Carrega configurações
    console.print("\n[cyan]Carregando configurações...[/cyan]")
    settings = Settings()

    # Valida configurações
    valid, message = settings.validate()

    if not valid:
        console.print(f"[red]✗ Erro de configuração: {message}[/red]")
        console.print("\n[yellow]Instruções:[/yellow]")
        console.print("  1. Copie .env.example para .env")
        console.print("  2. Edite .env com suas credenciais do Gmail")
        console.print("  3. Use uma Senha de App do Google (não sua senha normal)")
        console.print("\nPara criar uma Senha de App:")
        console.print("  1. Acesse https://myaccount.google.com/apppasswords")
        console.print("  2. Selecione 'Mail' e seu dispositivo")
        console.print("  3. Copie a senha gerada para o arquivo .env")
        sys.exit(1)

    console.print("[green]✓ Configurações carregadas com sucesso[/green]")

    # Inicia menu principal
    console.print("\n[cyan]Iniciando aplicação...[/cyan]\n")

    try:
        menu = Menu(settings)
        menu.start()
    except KeyboardInterrupt:
        console.print("\n\n[yellow]Aplicação encerrada pelo usuário.[/yellow]")
        sys.exit(0)
    except Exception as e:
        console.print(f"\n[red]Erro crítico: {e}[/red]")
        console.print("\n[yellow]Verifique o arquivo .env e tente novamente.[/yellow]")
        sys.exit(1)


if __name__ == "__main__":
    main()
