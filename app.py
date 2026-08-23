#!/usr/bin/env python3
"""
Gmail Manager CLI - Gerenciador de e-mail Gmail via IMAP com Interface CLI Premium

Aplicação CLI moderna para gerenciar e-mails do Gmail usando IMAP.
Interface premium com Rich, suporte a threads, cache e operações assíncronas.

Uso:
    python app.py              # Inicia interface CLI completa

Recursos Premium:
    - Interface moderna com Rich
    - Threads para operações assíncronas
    - Cache inteligente de mensagens
    - Download de anexos em paralelo
    - Busca avançada de e-mails
    - Gerenciamento de pastas/marcadores
    - Status em tempo real

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


def main():
    """Função principal da aplicação."""
    console = Console()

    # Carrega configurações
    console.print("\n[cyan bold]⚡ Carregando configurações...[/cyan bold]")
    settings = Settings()

    # Valida configurações
    valid, message = settings.validate()

    if not valid:
        console.print(f"\n[red bold]✗ Erro de configuração: {message}[/red bold]")
        console.print("\n[yellow]📋 Instruções de configuração:[/yellow]")
        console.print("  1. Copie .env.example para .env")
        console.print("  2. Edite .env com suas credenciais do Gmail")
        console.print("  3. Use uma Senha de App do Google (não sua senha normal)")
        console.print("\n[blue]🔐 Para criar uma Senha de App:[/blue]")
        console.print("  1. Acesse https://myaccount.google.com/apppasswords")
        console.print("  2. Selecione 'Mail' e seu dispositivo")
        console.print("  3. Copie a senha gerada para o arquivo .env")
        sys.exit(1)

    console.print("[green bold]✓ Configurações carregadas com sucesso[/green bold]")
    console.print(f"[dim]Conta: {settings.gmail_email}[/dim]")

    console.print("\n[cyan]Iniciando interface CLI Premium...[/cyan]\n")
    
    from src.cli.menu import Menu
    
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
