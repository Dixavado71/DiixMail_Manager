"""Menu e interface CLI do Gmail Manager - Versão Premium."""

import sys
from typing import Optional, List
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
import time

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, Confirm
from rich.text import Text
from rich.live import Live
from rich.spinner import Spinner
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.layout import Layout
from rich.align import Align
from rich.style import Style

from ..config.settings import Settings
from ..imap.client import IMAPClient
from ..imap.folders import FolderManager
from ..imap.messages import MessageManager
from ..imap.search import SearchEngine
from ..attachments.downloader import AttachmentDownloader


class Menu:
    """Classe principal para a interface CLI premium do aplicativo."""

    def __init__(self, settings: Settings):
        """
        Inicializa o menu CLI premium.

        Args:
            settings: Configurações do aplicativo
        """
        self.settings = settings
        self.console = Console(force_terminal=True)
        
        # Thread pool para operações assíncronas
        self.executor = ThreadPoolExecutor(max_workers=5, thread_name_prefix="gmail_worker")
        self.lock = Lock()

        # Inicializa componentes
        self.imap_client = IMAPClient(settings.imap_server, settings.imap_port)
        self.folder_manager = FolderManager(self.imap_client)
        self.message_manager = MessageManager(self.imap_client)
        self.search_engine = SearchEngine(self.imap_client)
        self.downloader = AttachmentDownloader(settings.get_download_path())

        # Estado da aplicação
        self.current_folder = "INBOX"
        self.current_messages: List[str] = []
        self.selected_messages: List[str] = []
        self.is_connected = False
        self.cache_enabled = True
        self.message_cache = {}

    def start(self) -> None:
        """Inicia a aplicação e o loop principal do menu."""
        self._show_header()

        # Conecta ao Gmail
        if not self._connect():
            return

        # Loop principal
        while True:
            try:
                self._show_dashboard()
                choice = self._get_main_choice()

                if choice == "1":
                    self._show_inbox()
                elif choice == "2":
                    self._show_folders()
                elif choice == "3":
                    self._search_emails()
                elif choice == "4":
                    self._open_email()
                elif choice == "5":
                    self._select_emails()
                elif choice == "6":
                    self._download_attachments_menu()
                elif choice == "7":
                    self._manage_emails_menu()
                elif choice == "8":
                    self._refresh()
                elif choice == "0":
                    self._exit()
                    break
                else:
                    self.console.print("\n[red]Opção inválida! Tente novamente.[/red]")
                    Prompt.ask("\nPressione Enter para continuar")

            except KeyboardInterrupt:
                self.console.print("\n\n[yellow]Aplicação interrompida pelo usuário.[/yellow]")
                break
            except Exception as e:
                self.console.print(f"\n[red]Erro inesperado: {e}[/red]")
                self.console.print("\n[yellow]Tentando reconectar...[/yellow]")
                self._reconnect()

    def _show_header(self) -> None:
        """Exibe o cabeçalho premium da aplicação."""
        header_text = Text.assemble(
            ("╔══════════════════════════════════════════════╗\n", "bold blue"),
            ("║         ", "blue"),
            ("GMAIL MANAGER CLI", "bold white"),
            ("          ║\n", "blue"),
            ("║      Gerenciador Premium de E-mails      ║\n", "cyan"),
            ("╚══════════════════════════════════════════════╝", "bold blue"),
        )
        self.console.print(header_text)

    def _connect(self) -> bool:
        """
        Realiza conexão com o Gmail usando thread pool.

        Returns:
            bool: True se conectado com sucesso
        """
        self.console.print("\n[cyan bold]⚡ Conectando ao Gmail...[/cyan bold]")

        # Verifica credenciais primeiro
        if not self.settings.gmail_email or not self.settings.gmail_app_password:
            self.console.print("[red]✗ Erro: Credenciais não configuradas no arquivo .env[/red]")
            self._show_setup_instructions()
            return False

        # Detecta credenciais de teste
        is_test_credentials = (
            "teste@gmail.com" in self.settings.gmail_email.lower() or
            "testpassword" in self.settings.gmail_app_password.lower() or
            self.settings.gmail_app_password == "testpassword123"
        )

        if is_test_credentials:
            self.console.print("[yellow]⚠ Credenciais de teste detectadas![/yellow]")
            self.console.print("[yellow]Iniciando modo de demonstração com dados mockados...[/yellow]\n")
            self._start_demo_mode()
            return True

        # Usa thread para não bloquear a UI
        future = self.executor.submit(
            self.imap_client.connect,
            self.settings.gmail_email,
            self.settings.gmail_app_password,
        )
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console,
        ) as progress:
            task = progress.add_task("Autenticando...", total=None)
            
            try:
                success, message = future.result(timeout=30)
                progress.update(task, completed=True)
            except Exception as e:
                self.console.print(f"\n[red]✗ Erro na conexão: {e}[/red]")
                return False

        if success:
            self.is_connected = True
            self.console.print(f"[green bold]✓ {message}[/green bold]")

            # Seleciona INBOX por padrão
            success, _, count = self.imap_client.select_folder("INBOX")
            if success:
                self.current_folder = "INBOX"
                self.console.print(f"[green]✓ Caixa de entrada selecionada ([bold]{count}[/bold] mensagens)[/green]")
                
                # Carrega mensagens iniciais
                self._load_current_messages()
        else:
            self.console.print(f"\n[red]✗ Erro: {message}[/red]")
            self._show_setup_instructions()
            return False

        return True

    def _show_setup_instructions(self) -> None:
        """Mostra instruções para configurar credenciais reais."""
        self.console.print("\n[yellow]╔══════════════════════════════════════════════════╗[/yellow]")
        self.console.print("[yellow]║     COMO CONFIGURAR CREDENCIAIS REAIS           ║[/yellow]")
        self.console.print("[yellow]╚══════════════════════════════════════════════════╝[/yellow]")
        self.console.print("\n[bold]1. Edite o arquivo .env:[/bold]")
        self.console.print("   [cyan]GMAIL_EMAIL=seu_email@gmail.com[/cyan]")
        self.console.print("   [cyan]GMAIL_APP_PASSWORD=sua_senha_de_app_16_caracteres[/cyan]")
        self.console.print("\n[bold]2. Gere uma Senha de App no Gmail:[/bold]")
        self.console.print("   • Acesse sua conta Google")
        self.console.print("   • Vá em [cyan]Segurança → Verificação em duas etapas[/cyan]")
        self.console.print("   • Em [cyan]Senhas de app[/cyan], gere uma nova senha")
        self.console.print("   • Use essa senha (16 caracteres) no arquivo .env")
        self.console.print("\n[bold]3. Habilite acesso IMAP no Gmail:[/bold]")
        self.console.print("   • Acesse Gmail no navegador")
        self.console.print("   • Configurações → Encaminhamento e POP/IMAP")
        self.console.print("   • Ative [cyan]Acesso IMAP[/cyan]")
        self.console.print("\n[yellow]Após configurar, execute: python app.py[/yellow]\n")

    def _start_demo_mode(self) -> None:
        """Inicia modo de demonstração com dados mockados."""
        self.is_connected = True
        self.current_folder = "INBOX"
        self._demo_mode = True  # Flag para identificar modo demo
        
        # Dados mockados para demonstração
        demo_messages = [
            {"id": "1", "from_name": "Google", "from_email": "no-reply@google.com", "subject": "Confirmação de segurança", "date_str": "01/01/2025 10:00", "is_read": True, "attachment_count": 0},
            {"id": "2", "from_name": "Amazon", "from_email": "pedidos@amazon.com.br", "subject": "Seu pedido foi enviado", "date_str": "01/01/2025 09:30", "is_read": False, "attachment_count": 0},
            {"id": "3", "from_name": "LinkedIn", "from_email": "notifications@linkedin.com", "subject": "Você tem novas conexões", "date_str": "31/12/2024 18:45", "is_read": True, "attachment_count": 0},
            {"id": "4", "from_name": "GitHub", "from_email": "noreply@github.com", "subject": "[GitHub] Security alert", "date_str": "31/12/2024 14:20", "is_read": False, "attachment_count": 1},
            {"id": "5", "from_name": "Netflix", "from_email": "info@netflix.com", "subject": "Novidades este mês", "date_str": "30/12/2024 08:00", "is_read": True, "attachment_count": 0},
            {"id": "6", "from_name": "Banco Inter", "from_email": "notif@inter.co", "subject": "Fatura disponível", "date_str": "29/12/2024 16:30", "is_read": False, "attachment_count": 1},
            {"id": "7", "from_name": "Microsoft", "from_email": "account-security-noreply@accountprotection.microsoft.com", "subject": "Entrada recente detectada", "date_str": "28/12/2024 11:15", "is_read": True, "attachment_count": 0},
            {"id": "8", "from_name": "Spotify", "from_email": "no-reply@spotify.com", "subject": "Sua playlist semanal está pronta", "date_str": "27/12/2024 07:00", "is_read": True, "attachment_count": 0},
        ]
        
        self.current_messages = [m["id"] for m in demo_messages]
        self.message_cache = {m["id"]: m for m in demo_messages}
        
        self.console.print("[green bold]✓ Modo de demonstração ativado![/green bold]")
        self.console.print("[dim]Dados fictícios carregados para demonstração da interface.[/dim]\n")

    def _load_current_messages(self) -> None:
        """Carrega a lista atual de mensagens da pasta selecionada."""
        if not self.is_connected:
            return
            
        success, message_ids = self.search_engine.search_all()
        if success and message_ids:
            self.current_messages = message_ids

    def _reconnect(self) -> bool:
        """
        Tenta reconectar ao servidor.

        Returns:
            bool: True se reconectado com sucesso
        """
        self.imap_client.disconnect()
        self.is_connected = False

        return self._connect()

    def _show_dashboard(self) -> None:
        """Exibe o dashboard premium com layout moderno."""
        # Status colorido baseado no estado da conexão
        status_icon = "🟢" if self.is_connected else "🔴"
        status_text = "Conectado" if self.is_connected else "Desconectado"
        status_style = "green bold" if self.is_connected else "red"
        
        # Painel de status
        dashboard = Panel(
            f"[bold]📧 Conta:[/bold] {self.settings.gmail_email}\n"
            f"[bold]Status:[/bold] [{status_style}]{status_icon} {status_text}[/{status_style}]\n"
            f"[bold]📁 Pasta atual:[/bold] [cyan]{self.current_folder}[/cyan]\n"
            f"[bold]📌 Selecionados:[/bold] [yellow]{len(self.selected_messages)}[/yellow] e-mail(s)",
            title="[bold green]🚀 GMAIL MANAGER PREMIUM[/bold green]",
            border_style="green",
            padding=(1, 2),
        )
        self.console.print("\n")
        self.console.print(dashboard)

        # Menu estilizado
        menu_table = Table(
            show_header=False, 
            box=None, 
            padding=(0, 3),
            expand=True,
        )
        menu_table.add_column("Opção", style="cyan bold", width=4)
        menu_table.add_column("Descrição", style="white", ratio=1)
        menu_table.add_column("Ícone", style="dim", justify="right")

        menu_items = [
            ("1", "Caixa de entrada", "📥"),
            ("2", "Pastas / Marcadores", "📁"),
            ("3", "Pesquisar e-mails", "🔍"),
            ("4", "Abrir e-mail", "📖"),
            ("5", "Selecionar e-mails", "✓"),
            ("6", "Baixar anexos", "⬇️"),
            ("7", "Gerenciar e-mails", "⚙️"),
            ("8", "Atualizar", "🔄"),
            ("0", "Sair", "🚪"),
        ]

        for option, description, icon in menu_items:
            menu_table.add_row(
                f"[bold cyan]{option}.[/bold cyan]", 
                description,
                icon
            )

        self.console.print(menu_table)

    def _get_main_choice(self) -> str:
        """
        Obtém a escolha do usuário no menu principal.

        Returns:
            str: Opção escolhida
        """
        return Prompt.ask("\n[bold]Escolha uma opção[/bold]", choices=[str(i) for i in range(9)])

    def _show_inbox(self) -> None:
        """Exibe a caixa de entrada com carregamento assíncrono."""
        self.console.print("\n[cyan bold]⚡ Carregando caixa de entrada...[/cyan bold]")

        # Verifica se está em modo de demonstração
        if self.message_cache and len(self.message_cache) > 0 and hasattr(self, '_demo_mode'):
            # Modo de demonstração - usa dados mockados
            summaries = list(self.message_cache.values())[:50]
            self.console.print("[green]✓ Dados de demonstração carregados[/green]")
            self._display_email_table(summaries)
            return

        # Modo real - seleciona INBOX
        success, msg_count = self.imap_client.select_folder("INBOX")
        if not success:
            self.console.print("[red]Falha ao acessar caixa de entrada[/red]")
            return

        self.current_folder = "INBOX"
        self.console.print(f"[dim]Pasta INBOX selecionada ({msg_count} mensagens no total)[/dim]")

        # Busca todas as mensagens usando thread
        future = self.executor.submit(self.search_engine.search_all)
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console,
        ) as progress:
            task = progress.add_task("Buscando mensagens...", total=None)
            try:
                success, message_ids = future.result(timeout=60)
                progress.update(task, completed=True)
            except Exception as e:
                self.console.print(f"[red]Erro na busca: {e}[/red]")
                return

        self.console.print(f"[dim]Busca retornou {len(message_ids) if message_ids else 0} mensagens[/dim]")
        
        if not success or not message_ids:
            self.console.print("[yellow]Nenhum e-mail encontrado ou erro na busca.[/yellow]")
            self.console.print("[dim]Dica: Verifique se há e-mails na conta Gmail ou se o acesso IMAP está habilitado.[/dim]")
            Prompt.ask("\nPressione Enter para continuar")
            return

        self.current_messages = message_ids
        self.console.print(f"[dim]Processando últimos 50 e-mails...[/dim]")

        # Obtém resumo das últimas 50 mensagens DIRETAMENTE (sem cache para evitar problemas)
        summaries = self.message_manager.get_messages_summary(message_ids, limit=50)

        if not summaries:
            self.console.print("[yellow]Nenhum e-mail pôde ser carregado.[/yellow]")
            self.console.print("[dim]Isso pode indicar um problema de conexão ou formato dos e-mails.[/dim]")
            Prompt.ask("\nPressione Enter para continuar")
            return

        self.console.print(f"[green]✓ {len(summaries)} e-mail(s) carregado(s) com sucesso![/green]")
        self._display_email_table(summaries)

    def _display_email_table(self, summaries: list) -> None:
        """Exibe a tabela de e-mails formatada."""
        if not summaries:
            self.console.print("[yellow]Nenhum e-mail para exibir.[/yellow]")
            Prompt.ask("\nPressione Enter para continuar")
            return

        # Cria tabela premium
        table = Table(
            title=f"📥 Caixa de Entrada ([bold cyan]{len(summaries)}[/bold cyan] e-mails exibidos)",
            show_header=True,
            header_style="bold cyan",
            border_style="blue",
            expand=True,
        )
        table.add_column("ID", style="cyan", width=6, justify="right")
        table.add_column("Data", style="white", width=16)
        table.add_column("Remetente", style="green", width=35)
        table.add_column("Assunto", style="yellow", width=50)
        table.add_column("Status", style="magenta", width=12)
        table.add_column("Anexos", style="blue", width=8, justify="center")

        for msg in summaries:
            status = "[red bold]🆕 NOVO[/red bold]" if not msg.get("is_read", True) else "[green]✓ LIDO[/green]"
            anexos = f"[blue]{msg.get('attachment_count', 0)} 📎[/blue]" if msg.get("attachment_count", 0) > 0 else "—"

            table.add_row(
                f"[bold]{msg.get('id', '?')}[/bold]",
                msg.get("date_str", "?"),
                msg.get("from_name", "?")[:33] + "..." if len(msg.get("from_name", "")) > 35 else msg.get("from_name", "?"),
                msg.get("subject", "?")[:47] + "..." if len(msg.get("subject", "")) > 50 else msg.get("subject", "?"),
                status,
                anexos,
            )

        self.console.print(table)
        Prompt.ask("\nPressione Enter para continuar")

    def _get_messages_summary_cached(self, message_ids: list[str], limit: int = 50) -> list[dict]:
        """
        Obtém resumo de mensagens com cache e threads.

        Args:
            message_ids: Lista de IDs das mensagens
            limit: Limite máximo de mensagens

        Returns:
            list[dict]: Lista de resumos
        """
        if not self.cache_enabled:
            return self.message_manager.get_messages_summary(message_ids, limit)

        summaries = []
        sorted_ids = sorted(message_ids, key=int, reverse=True)[:limit]

        # Usa threads para buscar múltiplas mensagens em paralelo
        futures = {}
        for msg_id in sorted_ids:
            if msg_id in self.message_cache:
                summaries.append(self.message_cache[msg_id])
            else:
                future = self.executor.submit(self.message_manager.get_message_headers, msg_id)
                futures[future] = msg_id

        # Coleta resultados
        for future in as_completed(futures):
            msg_id = futures[future]
            try:
                result = future.result(timeout=10)
                if result:
                    with self.lock:
                        self.message_cache[msg_id] = result
                    summaries.append(result)
            except Exception:
                continue

        return summaries

    def _show_folders(self) -> None:
        """Exibe lista de pastas/marcadores com carregamento assíncrono."""
        self.console.print("\n[cyan bold]📁 Carregando pastas...[/cyan bold]")

        # Busca pastas usando thread
        future = self.executor.submit(self.folder_manager.list_folders)
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console,
        ) as progress:
            task = progress.add_task("Listando pastas...", total=None)
            try:
                success, folders = future.result(timeout=30)
                progress.update(task, completed=True)
            except Exception as e:
                self.console.print(f"[red]Erro ao carregar pastas: {e}[/red]")
                return

        if not success or not folders:
            self.console.print("[red]Falha ao carregar pastas[/red]")
            Prompt.ask("\nPressione Enter para continuar")
            return

        # Cria tabela premium de pastas
        table = Table(
            title="📂 Pastas / Marcadores Disponíveis",
            show_header=True,
            header_style="bold cyan",
            border_style="blue",
        )
        table.add_column("Nome", style="cyan", width=40)
        table.add_column("Exibição", style="green", width=30)
        table.add_column("Tipo", style="yellow", width=10, justify="center")

        for folder in folders:
            folder_type = "📁" if folder["has_children"] else "📄"
            table.add_row(
                f"[bold]{folder['name']}[/bold]",
                folder["display_name"],
                folder_type,
            )

        self.console.print(table)

        # Pergunta se deseja mudar de pasta
        if Confirm.ask("\n[bold]Deseja mudar para outra pasta?[/bold]"):
            folder_name = Prompt.ask("[cyan]Digite o nome exato da pasta[/cyan]")
            success, _, count = self.imap_client.select_folder(folder_name)

            if success:
                self.current_folder = folder_name
                self.console.print(f"[green bold]✓ Pasta '[bold]{folder_name}[/bold]' selecionada ([bold cyan]{count}[/bold cyan] mensagens)[/green bold]")
                
                # Atualiza cache quando muda de pasta
                self.message_cache.clear()
            else:
                self.console.print(f"[red]✗ Falha ao selecionar pasta '{folder_name}'[/red]")

        Prompt.ask("\nPressione Enter para continuar")

    def _search_emails(self) -> None:
        """Realiza busca de e-mails."""
        self.console.print("\n[bold]Tipos de busca disponíveis:[/bold]")
        self.console.print("  • from:email@exemplo.com")
        self.console.print("  • subject:texto do assunto")
        self.console.print("  • to:email@destinatario.com")
        self.console.print("  • since:2024-01-01")
        self.console.print("  • last:30 (últimos 30 dias)")
        self.console.print("  • has:attachment (com anexos)")
        self.console.print("  • is:unread (não lidos)")
        self.console.print("  • texto livre (busca em tudo)")

        query = Prompt.ask("\nDigite sua busca")

        success, message_ids = self.search_engine.parse_search_query(query)

        if not success or not message_ids:
            self.console.print("[yellow]Nenhum resultado encontrado.[/yellow]")
            Prompt.ask("\nPressione Enter para continuar")
            return

        self.current_messages = message_ids
        self.console.print(f"[green]✓ {len(message_ids)} e-mail(s) encontrado(s)[/green]")

        # Mostra resultados
        summaries = self.message_manager.get_messages_summary(message_ids, limit=50)

        if summaries:
            table = Table(title=f"Resultados da Busca ({len(message_ids)} total)")
            table.add_column("ID", style="cyan", width=6)
            table.add_column("Data", style="white", width=16)
            table.add_column("Remetente", style="green", width=30)
            table.add_column("Assunto", style="yellow", width=50)

            for msg in summaries:
                table.add_row(
                    msg["id"],
                    msg["date_str"],
                    msg["from_name"][:28] + ".." if len(msg["from_name"]) > 30 else msg["from_name"],
                    msg["subject"][:47] + "..." if len(msg["subject"]) > 50 else msg["subject"],
                )

            self.console.print(table)

        Prompt.ask("\nPressione Enter para continuar")

    def _open_email(self) -> None:
        """Abre e exibe um e-mail específico."""
        if not self.current_messages:
            self.console.print("[yellow]Nenhum e-mail carregado. Vá para Caixa de Entrada primeiro.[/yellow]")
            Prompt.ask("\nPressione Enter para continuar")
            return

        msg_id = Prompt.ask("Digite o ID do e-mail para abrir")

        if msg_id not in self.current_messages:
            self.console.print("[red]ID inválido ou e-mail não está na lista atual.[/red]")
            Prompt.ask("\nPressione Enter para continuar")
            return

        # Carrega mensagem completa
        msg = self.message_manager.get_full_message(msg_id)

        if not msg:
            self.console.print("[red]Falha ao carregar e-mail.[/red]")
            Prompt.ask("\nPressione Enter para continuar")
            return

        # Exibe cabeçalhos
        self.console.print("\n" + "=" * 60)
        self.console.print(f"[bold]De:[/bold]     {msg['from_name']} <{msg['from_email']}>")
        self.console.print(f"[bold]Para:[/bold]   {msg['to_name']} <{msg['to_email']}>")
        self.console.print(f"[bold]Data:[/bold]   {msg['date_str']}")
        self.console.print(f"[bold]Assunto:[/bold] {msg['subject']}")
        self.console.print("=" * 60)

        # Exibe conteúdo
        content = msg.get("body_plain") or msg.get("body_html", "")

        if not content:
            self.console.print("\n[yellow]Conteúdo vazio ou indisponível.[/yellow]")
        else:
            self.console.print("\n[bold]CONTEÚDO:[/bold]")
            self.console.print("-" * 60)
            # Trunca se muito longo
            if len(content) > 2000:
                content = content[:2000] + "\n\n... (conteúdo truncado)"
            self.console.print(content)

        # Exibe anexos
        attachments = msg.get("attachments", [])
        if attachments:
            self.console.print("\n" + "-" * 60)
            self.console.print(f"[bold]ANEXOS ({len(attachments)}):[/bold]")

            for att in attachments:
                size_str = self._format_size(att.get("size", 0))
                self.console.print(f"  • {att['filename']} ({size_str})")

        Prompt.ask("\nPressione Enter para continuar")

    def _select_emails(self) -> None:
        """Permite selecionar múltiplos e-mails."""
        if not self.current_messages:
            self.console.print("[yellow]Nenhum e-mail carregado.[/yellow]")
            Prompt.ask("\nPressione Enter para continuar")
            return

        self.console.print(f"\nE-mails disponíveis: {len(self.current_messages)}")
        self.console.print("\nFormatos aceitos:")
        self.console.print("  • IDs individuais: 1,3,5")
        self.console.print("  • Intervalo: 1-10")
        self.console.print("  • Todos: all")

        selection = Prompt.ask("Digite os IDs para selecionar")

        selected = []

        if selection.lower() == "all":
            selected = self.current_messages.copy()
        else:
            # Parseia entrada
            parts = selection.replace(" ", "").split(",")

            for part in parts:
                if "-" in part:
                    # Intervalo
                    try:
                        start, end = part.split("-")
                        start_id = int(start)
                        end_id = int(end)
                        for mid in range(start_id, end_id + 1):
                            if str(mid) in self.current_messages:
                                selected.append(str(mid))
                    except ValueError:
                        pass
                else:
                    # ID individual
                    if part in self.current_messages:
                        selected.append(part)

        self.selected_messages = list(set(selected))
        self.console.print(f"[green]✓ {len(self.selected_messages)} e-mail(s) selecionado(s)[/green]")

        Prompt.ask("\nPressione Enter para continuar")

    def _download_attachments_menu(self) -> None:
        """Menu para download de anexos."""
        self.console.print("\n[bold]Opções de download:[/bold]")
        self.console.print("  1. Baixar de e-mail específico")
        self.console.print("  2. Baixar dos e-mails selecionados")
        self.console.print("  3. Voltar")

        choice = Prompt.ask("Escolha", choices=["1", "2", "3"])

        if choice == "1":
            self._download_from_single_email()
        elif choice == "2":
            self._download_from_selected()
        # 3 = voltar

    def _download_from_single_email(self) -> None:
        """Baixa anexos de um único e-mail."""
        if not self.current_messages:
            self.console.print("[yellow]Nenhum e-mail carregado.[/yellow]")
            return

        msg_id = Prompt.ask("Digite o ID do e-mail")

        if msg_id not in self.current_messages:
            self.console.print("[red]ID inválido.[/red]")
            return

        msg = self.message_manager.get_full_message(msg_id)

        if not msg or not msg.get("attachments"):
            self.console.print("[yellow]Este e-mail não tem anexos.[/yellow]")
            return

        self.console.print(f"\nAnexos encontrados: {len(msg['attachments'])}")

        organize = Prompt.ask(
            "Organizar por",
            choices=["none", "sender", "subject", "date"],
            default="none",
        )

        organize_by = None if organize == "none" else organize

        stats = self.downloader.download_attachments_from_messages(
            [msg],
            organize_by=organize_by,
        )

        self._show_download_stats(stats)

    def _download_from_selected(self) -> None:
        """Baixa anexos dos e-mails selecionados com barra de progresso."""
        if not self.selected_messages:
            self.console.print("[yellow]Nenhum e-mail selecionado. Use a opção 5 primeiro.[/yellow]")
            return

        if not Confirm.ask(f"[bold]Deseja baixar anexos de {len(self.selected_messages)} e-mail(s)?[/bold]"):
            return

        organize = Prompt.ask(
            "[cyan]Organizar por[/cyan]",
            choices=["none", "sender", "subject", "date"],
            default="none",
        )

        organize_by = None if organize == "none" else organize

        # Carrega mensagens completas usando threads
        messages = []
        self.console.print("\n[cyan bold]⚡ Carregando mensagens...[/cyan bold]")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=self.console,
        ) as progress:
            task = progress.add_task("Carregando...", total=len(self.selected_messages))
            
            futures = {}
            for msg_id in self.selected_messages:
                future = self.executor.submit(self.message_manager.get_full_message, msg_id)
                futures[future] = msg_id
            
            for future in as_completed(futures):
                try:
                    msg = future.result(timeout=30)
                    if msg:
                        messages.append(msg)
                except Exception:
                    pass
                progress.update(task, advance=1)

        if not messages:
            self.console.print("[red]Falha ao carregar mensagens.[/red]")
            return

        # Baixa anexos com barra de progresso
        stats = self.downloader.download_attachments_from_messages(
            messages,
            organize_by=organize_by,
            progress_callback=lambda s: None,  # Callback opcional
        )

        self._show_download_stats(stats)

    def _show_download_stats(self, stats: dict) -> None:
        """Exibe estatísticas de download com painel premium."""
        panel = Panel(
            f"[bold green]✓ Download concluído![/bold green]\n\n"
            f"📧 Mensagens processadas: [bold cyan]{stats['messages_processed']}[/bold cyan]\n"
            f"📎 Anexos encontrados:  [bold yellow]{stats['attachments_found']}[/bold yellow]\n"
            f"⬇️ Downloads realizados: [bold green]{stats['downloads_success']}[/bold green]\n"
            + (f"❌ Falhas: [red]{stats['downloads_failed']}[/red]\n" if stats["downloads_failed"] > 0 else "")
            + (f"📁 Pasta: [cyan]{self.settings.get_download_path()}[/cyan]" if stats['downloads_success'] > 0 else ""),
            title="[bold]📊 Estatísticas de Download[/bold]",
            border_style="green",
            padding=(1, 2),
        )
        self.console.print("\n")
        self.console.print(panel)

        if stats["errors"]:
            self.console.print("\n[yellow bold]⚠️ Erros:[/yellow bold]")
            for error in stats["errors"][:5]:
                self.console.print(f"  • [dim]{error}[/dim]")

    def _manage_emails_menu(self) -> None:
        """Menu para gerenciar e-mails."""
        self.console.print("\n[bold]Gerenciar e-mails:[/bold]")
        self.console.print("  1. Marcar como lido")
        self.console.print("  2. Marcar como não lido")
        self.console.print("  3. Excluir e-mail(s)")
        self.console.print("  4. Mover para pasta")
        self.console.print("  5. Voltar")

        choice = Prompt.ask("Escolha", choices=["1", "2", "3", "4", "5"])

        if choice == "1":
            self._mark_as_read()
        elif choice == "2":
            self._mark_as_unread()
        elif choice == "3":
            self._delete_emails()
        elif choice == "4":
            self._move_emails()
        # 5 = voltar

    def _mark_as_read(self) -> None:
        """Marca e-mails como lidos."""
        if not self._ensure_selection():
            return

        if Confirm.ask(f"Marcar {len(self.selected_messages)} e-mail(s) como lido(s)?"):
            success, msg = self.message_manager.mark_messages_read(self.selected_messages)
            self.console.print(f"[green]✓ {msg}[/green]" if success else f"[red]✗ {msg}[/red]")

        Prompt.ask("\nPressione Enter para continuar")

    def _mark_as_unread(self) -> None:
        """Marca e-mails como não lidos."""
        if not self._ensure_selection():
            return

        if Confirm.ask(f"Marcar {len(self.selected_messages)} e-mail(s) como não lido(s)?"):
            success, msg = self.message_manager.mark_messages_unread(self.selected_messages)
            self.console.print(f"[green]✓ {msg}[/green]" if success else f"[red]✗ {msg}[/red]")

        Prompt.ask("\nPressione Enter para continuar")

    def _delete_emails(self) -> None:
        """Exclui e-mails selecionados."""
        if not self._ensure_selection():
            return

        self.console.print(f"\n[yellow bold]ATENÇÃO:[/yellow bold] Esta ação irá excluir permanentemente {len(self.selected_messages)} e-mail(s).")

        if not Confirm.ask("Tem certeza que deseja continuar?", default=False):
            self.console.print("[yellow]Operação cancelada.[/yellow]")
            return

        success, deleted, errors = self.message_manager.delete_messages(self.selected_messages)

        if success:
            self.console.print(f"[green]✓ {deleted} e-mail(s) excluído(s) com sucesso.[/green]")
            self.selected_messages = []
            self.current_messages = []
        else:
            self.console.print(f"[yellow]⚠ {deleted} excluídos, {len(errors)} falharam.[/yellow]")

        Prompt.ask("\nPressione Enter para continuar")

    def _move_emails(self) -> None:
        """Move e-mails para outra pasta."""
        if not self._ensure_selection():
            return

        # Lista pastas disponíveis
        success, folders = self.folder_manager.list_folders()

        if not success:
            self.console.print("[red]Falha ao carregar pastas.[/red]")
            return

        self.console.print("\nPastas disponíveis:")
        for folder in folders:
            self.console.print(f"  • {folder['display_name']} ({folder['name']})")

        dest_folder = Prompt.ask("\nDigite o nome exato da pasta de destino")

        if not Confirm.ask(f"Mover {len(self.selected_messages)} e-mail(s) para '{dest_folder}'?"):
            return

        success, moved, errors = self.message_manager.move_messages(self.selected_messages, dest_folder)

        if success:
            self.console.print(f"[green]✓ {moved} e-mail(s) movido(s) com sucesso.[/green]")
            self.selected_messages = []
        else:
            self.console.print(f"[yellow]⚠ {moved} movidos, {len(errors)} falharam.[/yellow]")

        Prompt.ask("\nPressione Enter para continuar")

    def _ensure_selection(self) -> bool:
        """
        Verifica se há e-mails selecionados.

        Returns:
            bool: True se há seleção
        """
        if not self.selected_messages:
            self.console.print("[yellow]Nenhum e-mail selecionado. Use a opção 5 primeiro.[/yellow]")
            return False
        return True

    def _refresh(self) -> None:
        """Atualiza a conexão e recarrega dados."""
        self.console.print("\n[cyan]Atualizando...[/cyan]")

        # Reconecta se necessário
        if not self.is_connected:
            self._reconnect()

        # Recarrega pasta atual
        success, _, count = self.imap_client.select_folder(self.current_folder)

        if success:
            self.console.print(f"[green]✓ Pasta '{self.current_folder}' recarregada ({count} mensagens)[/green]")

            # Atualiza lista de mensagens
            success, message_ids = self.search_engine.search_all()
            if success:
                self.current_messages = message_ids
        else:
            self.console.print("[red]Falha ao atualizar.[/red]")

        Prompt.ask("\nPressione Enter para continuar")

    def _exit(self) -> None:
        """Encerra a aplicação limpando recursos."""
        self.console.print("\n[yellow]🔄 Desconectando...[/yellow]")
        
        # Limpa cache
        self.message_cache.clear()
        
        # Desconecta IMAP
        self.imap_client.disconnect()
        
        # Shutdown thread pool
        self.executor.shutdown(wait=False)
        
        self.console.print("[green bold]✓ Aplicação encerrada. Até logo! 👋[/green bold]")

    @staticmethod
    def _format_size(size_bytes: int) -> str:
        """Formata tamanho em bytes."""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        else:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
