"""Menu e interface CLI do Gmail Manager."""

import sys
from typing import Optional, List

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, Confirm
from rich.text import Text

from ..config.settings import Settings
from ..imap.client import IMAPClient
from ..imap.folders import FolderManager
from ..imap.messages import MessageManager
from ..imap.search import SearchEngine
from ..attachments.downloader import AttachmentDownloader


class Menu:
    """Classe principal para a interface CLI do aplicativo."""

    def __init__(self, settings: Settings):
        """
        Inicializa o menu CLI.

        Args:
            settings: Configurações do aplicativo
        """
        self.settings = settings
        self.console = Console()

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
        """Exibe o cabeçalho da aplicação."""
        header = Panel(
            Text("GMAIL MANAGER CLI", style="bold white", justify="center"),
            title="[bold blue]╔════════════════════════════════════════════╗[/bold blue]",
            subtitle="[bold blue]╚════════════════════════════════════════════╝[/bold blue]",
            border_style="blue",
        )
        self.console.print(header)

    def _connect(self) -> bool:
        """
        Realiza conexão com o Gmail.

        Returns:
            bool: True se conectado com sucesso
        """
        self.console.print("\n[cyan]Conectando ao Gmail...[/cyan]")

        success, message = self.imap_client.connect(
            self.settings.gmail_email,
            self.settings.gmail_app_password,
        )

        if success:
            self.is_connected = True
            self.console.print(f"[green]✓ {message}[/green]")

            # Seleciona INBOX por padrão
            success, _, count = self.imap_client.select_folder("INBOX")
            if success:
                self.current_folder = "INBOX"
                self.console.print(f"[green]✓ Caixa de entrada selecionada ({count} mensagens)[/green]")
        else:
            self.console.print(f"[red]✗ Erro: {message}[/red]")
            self.console.print("\n[yellow]Verifique:[/yellow]")
            self.console.print("  1. Suas credenciais no arquivo .env")
            self.console.print("  2. Se o acesso IMAP está habilitado no Gmail")
            self.console.print("  3. Se você está usando uma Senha de App (não a senha normal)")
            return False

        return True

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
        """Exibe o dashboard principal."""
        dashboard = Panel(
            f"[bold]Conta:[/bold] {self.settings.gmail_email}\n"
            f"[bold]Status:[/bold] {'● Conectado' if self.is_connected else '○ Desconectado'}\n"
            f"[bold]Pasta atual:[/bold] {self.current_folder}\n"
            f"[bold]Selecionados:[/bold] {len(self.selected_messages)} e-mail(s)",
            title="[bold green]GMAIL MANAGER[/bold green]",
            border_style="green",
        )
        self.console.print("\n")
        self.console.print(dashboard)

        menu_table = Table(show_header=False, box=None, padding=(0, 2))
        menu_table.add_column("Opção", style="cyan")
        menu_table.add_column("Descrição", style="white")

        menu_items = [
            ("1", "Caixa de entrada"),
            ("2", "Pastas / Marcadores"),
            ("3", "Pesquisar e-mails"),
            ("4", "Abrir e-mail"),
            ("5", "Selecionar e-mails"),
            ("6", "Baixar anexos"),
            ("7", "Gerenciar e-mails"),
            ("8", "Atualizar"),
            ("0", "Sair"),
        ]

        for option, description in menu_items:
            menu_table.add_row(f"[bold cyan]{option}.[/bold cyan]", description)

        self.console.print(menu_table)

    def _get_main_choice(self) -> str:
        """
        Obtém a escolha do usuário no menu principal.

        Returns:
            str: Opção escolhida
        """
        return Prompt.ask("\n[bold]Escolha uma opção[/bold]", choices=[str(i) for i in range(9)])

    def _show_inbox(self) -> None:
        """Exibe a caixa de entrada."""
        self.console.print("\n[cyan]Carregando caixa de entrada...[/cyan]")

        # Seleciona INBOX
        success, _, count = self.imap_client.select_folder("INBOX")
        if not success:
            self.console.print("[red]Falha ao acessar caixa de entrada[/red]")
            return

        self.current_folder = "INBOX"

        # Busca todas as mensagens
        success, message_ids = self.search_engine.search_all()

        if not success or not message_ids:
            self.console.print("[yellow]Nenhum e-mail encontrado.[/yellow]")
            Prompt.ask("\nPressione Enter para continuar")
            return

        self.current_messages = message_ids

        # Obtém resumo das últimas 50 mensagens
        summaries = self.message_manager.get_messages_summary(message_ids, limit=50)

        if not summaries:
            self.console.print("[yellow]Nenhum e-mail encontrado.[/yellow]")
            Prompt.ask("\nPressione Enter para continuar")
            return

        # Cria tabela
        table = Table(title=f"Caixa de Entrada ({len(message_ids)} e-mails total)")
        table.add_column("ID", style="cyan", width=6)
        table.add_column("Data", style="white", width=16)
        table.add_column("Remetente", style="green", width=30)
        table.add_column("Assunto", style="yellow", width=50)
        table.add_column("Status", style="magenta", width=8)
        table.add_column("Anexos", style="blue", width=8)

        for msg in summaries:
            status = "[red]NOVO[/red]" if not msg["is_read"] else "[green]LIDO[/green]"
            anexos = f"{msg['attachment_count']} 📎" if msg["attachment_count"] > 0 else "-"

            table.add_row(
                msg["id"],
                msg["date_str"],
                msg["from_name"][:28] + ".." if len(msg["from_name"]) > 30 else msg["from_name"],
                msg["subject"][:47] + "..." if len(msg["subject"]) > 50 else msg["subject"],
                status,
                anexos,
            )

        self.console.print(table)
        Prompt.ask("\nPressione Enter para continuar")

    def _show_folders(self) -> None:
        """Exibe lista de pastas/marcadores."""
        self.console.print("\n[cyan]Carregando pastas...[/cyan]")

        success, folders = self.folder_manager.list_folders()

        if not success or not folders:
            self.console.print("[red]Falha ao carregar pastas[/red]")
            Prompt.ask("\nPressione Enter para continuar")
            return

        table = Table(title="Pastas / Marcadores Disponíveis")
        table.add_column("Nome", style="cyan")
        table.add_column("Exibição", style="green")
        table.add_column("Tipo", style="yellow")

        for folder in folders:
            folder_type = "📁" if folder["has_children"] else "📄"
            table.add_row(
                folder["name"],
                folder["display_name"],
                folder_type,
            )

        self.console.print(table)

        # Pergunta se deseja mudar de pasta
        if Confirm.ask("\nDeseja mudar para outra pasta?"):
            folder_name = Prompt.ask("Digite o nome exato da pasta")
            success, _, count = self.imap_client.select_folder(folder_name)

            if success:
                self.current_folder = folder_name
                self.console.print(f"[green]✓ Pasta '{folder_name}' selecionada ({count} mensagens)[/green]")
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
        """Baixa anexos dos e-mails selecionados."""
        if not self.selected_messages:
            self.console.print("[yellow]Nenhum e-mail selecionado. Use a opção 5 primeiro.[/yellow]")
            return

        if not Confirm.ask(f"Deseja baixar anexos de {len(self.selected_messages)} e-mail(s)?"):
            return

        organize = Prompt.ask(
            "Organizar por",
            choices=["none", "sender", "subject", "date"],
            default="none",
        )

        organize_by = None if organize == "none" else organize

        # Carrega mensagens completas
        messages = []
        self.console.print("\n[cyan]Carregando mensagens...[/cyan]")

        for msg_id in self.selected_messages:
            msg = self.message_manager.get_full_message(msg_id)
            if msg:
                messages.append(msg)

        if not messages:
            self.console.print("[red]Falha ao carregar mensagens.[/red]")
            return

        stats = self.downloader.download_attachments_from_messages(
            messages,
            organize_by=organize_by,
        )

        self._show_download_stats(stats)

    def _show_download_stats(self, stats: dict) -> None:
        """Exibe estatísticas de download."""
        self.console.print("\n[bold green]✓ Download concluído![/bold green]")
        self.console.print(f"  Mensagens processadas: {stats['messages_processed']}")
        self.console.print(f"  Anexos encontrados: {stats['attachments_found']}")
        self.console.print(f"  Downloads realizados: {stats['downloads_success']}")

        if stats["downloads_failed"] > 0:
            self.console.print(f"  Falhas: {stats['downloads_failed']}")

        if stats["errors"]:
            self.console.print("\n[yellow]Erros:[/yellow]")
            for error in stats["errors"][:5]:
                self.console.print(f"  • {error}")

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
        """Encerra a aplicação."""
        self.console.print("\n[yellow]Desconectando...[/yellow]")
        self.imap_client.disconnect()
        self.console.print("[green]✓ Aplicação encerrada. Até logo![/green]")

    @staticmethod
    def _format_size(size_bytes: int) -> str:
        """Formata tamanho em bytes."""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        else:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
