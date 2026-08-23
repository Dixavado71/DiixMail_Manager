#!/usr/bin/env python3
"""
Gmail Manager TUI - Gerenciador de e-mail Gmail via IMAP com Interface Textual Premium

Aplicação TUI moderna para gerenciar e-mails do Gmail usando IMAP.
Interface premium com widgets reais, suporte a mouse, layouts dinâmicos e concorrência nativa.

Uso:
    python app.py              # Inicia interface TUI completa
    python app.py --cli        # Inicia interface CLI clássica

Recursos Premium:
    - Widgets reais: botões, inputs, scrollbars, abas
    - Estilo com CSS no terminal
    - Suporte a mouse e layouts dinâmicos
    - Concorrência nativa com workers assíncronos
    - Temas personalizáveis (dark/light mode)
    - Navegação por teclado e mouse
    - Preview de e-mails em tempo real
    - Downloads gerenciados em background

Requisitos:
    - Python 3.11+
    - Arquivo .env configurado com credenciais do Gmail
    - Acesso IMAP habilitado na conta Gmail
    - Senha de app do Google (não a senha normal)
"""

import sys
from pathlib import Path
import argparse

# Adiciona o diretório raiz ao path para imports
sys.path.insert(0, str(Path(__file__).parent))

from rich.console import Console
from rich.panel import Panel

from src.config.settings import Settings


def main():
    """Função principal da aplicação."""
    parser = argparse.ArgumentParser(
        description="Gmail Manager - Gerenciador Premium de E-mails",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos de uso:
  python app.py           # Inicia interface TUI completa (recomendado)
  python app.py --cli     # Inicia interface CLI clássica

Atalhos TUI:
  [q]       - Sair
  [r]       - Atualizar e-mails
  [1-3]     - Navegar entre abas
  [t]       - Toggle preview
  [?]       - Ajuda
  Mouse     - Clique e scroll suportados
        """
    )
    
    parser.add_argument(
        "--cli",
        action="store_true",
        help="Usar interface CLI clássica em vez da TUI moderna"
    )
    
    args = parser.parse_args()

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

    # Decide qual interface usar
    if args.cli:
        console.print("\n[cyan]Iniciando interface CLI clássica...[/cyan]\n")
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
    else:
        # Interface TUI moderna com Textual
        console.print("\n[green bold]🚀 Iniciando interface TUI Premium...[/green bold]")
        console.print("[dim]Use --cli para usar a interface clássica[/dim]\n")
        
        from src.tui.app import run_app
        
        try:
            run_app(settings)
        except KeyboardInterrupt:
            console.print("\n\n[yellow]Aplicação encerrada pelo usuário.[/yellow]")
            sys.exit(0)
        except Exception as e:
            console.print(f"\n[red]Erro crítico: {e}[/red]")
            console.print("\n[yellow]Dicas:[/yellow]")
            console.print("  • Verifique se o terminal suporta TUI (use terminais modernos)")
            console.print("  • Tente redimensionar a janela do terminal")
            console.print("  • Use --cli para fallback para interface clássica")
            sys.exit(1)


if __name__ == "__main__":
    main()
