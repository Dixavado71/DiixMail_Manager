"""Menu e interface CLI."""

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, Confirm

from src.imap.client import IMAPClient
from src.attachments.downloader import AttachmentDownloader
from src.email_parser.parser import EmailParser
from src.config.settings import Settings


console = Console()


def display_dashboard(email: str, folder: str, selected_count: int) -> None:
    """Exibe o dashboard principal."""
    panel = Panel(
        f"[bold]📧 Conta:[/bold] {email}\n"
        f"[bold]Status:[/bold] 🟢 Conectado\n"
        f"[bold]📁 Pasta atual:[/bold] {folder}\n"
        f"[bold]📌 Selecionados:[/bold] {selected_count} e-mail(s)",
        title="🚀 GMAIL MANAGER PREMIUM",
        border_style="blue",
    )
    console.print(panel)


class CLIMenu:
    """Gerencia o menu CLI."""

    def __init__(self, client: IMAPClient, settings: Settings):
        self.client = client
        self.settings = settings
        self.parser = EmailParser()
        self.downloader = AttachmentDownloader(client, settings.download_path)
        self.selected_emails: list[str] = []
        self.current_folder = "INBOX"
        self.message_ids: list[str] = []

    def show_main_menu(self) -> str:
        """Exibe menu principal."""
        console.print()
        console.print("[bold cyan]   1.[/bold cyan] Caixa de entrada".ljust(60) + "📥")
        console.print("[bold cyan]   2.[/bold cyan] Pastas / Marcadores".ljust(60) + "📁")
        console.print("[bold cyan]   3.[/bold cyan] Pesquisar e-mails".ljust(60) + "🔍")
        console.print("[bold cyan]   4.[/bold cyan] Abrir e-mail".ljust(60) + "📖")
        console.print("[bold cyan]   5.[/bold cyan] Selecionar e-mails".ljust(60) + "✓")
        console.print("[bold cyan]   6.[/bold cyan] Baixar anexos".ljust(60) + "⬇️")
        console.print("[bold cyan]   7.[/bold cyan] Gerenciar e-mails".ljust(60) + "⚙️")
        console.print("[bold cyan]   8.[/bold cyan] Atualizar".ljust(60) + "🔄")
        console.print("[bold red]   0.[/bold red] Sair".ljust(60) + "🚪")
        console.print()
        
        return Prompt.ask("Escolha uma opção", choices=["0","1","2","3","4","5","6","7","8"], default="0")

    def load_inbox(self) -> None:
        """Carrega caixa de entrada."""
        console.print("\n[bold yellow]⚡ Carregando caixa de entrada...[/bold yellow]")
        try:
            total = self.client.select_folder("INBOX")
            self.current_folder = "INBOX"
            console.print(f"[green]✓ Pasta INBOX selecionada ({total} mensagens)[/green]")
            
            console.print("[dim]⠋ Buscando mensagens...[/dim]", end="\r")
            self.message_ids = self.client.search("ALL")
            console.print(f"[dim]✓ Busca retornou {len(self.message_ids)} mensagens[/dim]")
            
            if not self.message_ids:
                console.print("[yellow]Nenhum e-mail encontrado.[/yellow]")
                return
            
            messages = self.client.fetch_headers(self.message_ids, count=20)
            if not messages:
                console.print("[yellow]Nenhum e-mail encontrado.[/yellow]")
                return
            
            table = Table(title=f"📥 Caixa de Entrada ({len(self.message_ids)} totais)")
            table.add_column("ID", style="cyan", width=6)
            table.add_column("Data", style="white", width=16)
            table.add_column("Remetente", style="green", width=30)
            table.add_column("Assunto", style="yellow", width=50)
            table.add_column("Status", style="magenta", width=8)
            table.add_column("Anexos", style="blue", width=8)
            
            for msg in messages:
                status = "✓ LIDO" if msg["is_read"] else "[bold red]🆕 NOVO[/bold red]"
                anexos = f"📎 {msg['has_attachments']}" if msg["has_attachments"] else "-"
                table.add_row(
                    str(msg["id"]), msg["date"],
                    msg["from"][:28]+".." if len(msg["from"])>30 else msg["from"],
                    msg["subject"][:48]+".." if len(msg["subject"])>50 else msg["subject"],
                    status, anexos,
                )
            console.print(table)
        except Exception as e:
            console.print(f"\n[bold red]Erro: {e}[/bold red]")

    def list_folders(self) -> None:
        """Lista pastas."""
        console.print("\n[bold yellow]⚡ Buscando pastas...[/bold yellow]")
        folders = self.client.get_folders()
        if not folders:
            console.print("[yellow]Nenhuma pasta encontrada.[/yellow]")
            return
        
        table = Table(title="📁 Pastas Disponíveis")
        table.add_column("Pasta", style="green")
        for folder in sorted(folders):
            table.add_row(folder)
        console.print(table)

    def search_emails(self) -> None:
        """Pesquisa e-mails."""
        console.print("\n[bold yellow]🔍 Pesquisar e-mails[/bold yellow]")
        query = Prompt.ask("Digite sua pesquisa (ex: from:email ou subject:palavra)")
        if not query:
            return
        
        if query.startswith("from:"):
            criteria = f'(FROM "{query[5:]}")'
        elif query.startswith("subject:"):
            criteria = f'(SUBJECT "{query[8:]}")'
        else:
            criteria = f'(BODY "{query}")'
        
        results = self.client.search(criteria)
        if not results:
            console.print("[yellow]Nenhum resultado encontrado.[/yellow]")
            return
        
        console.print(f"[green]✓ Encontrados {len(results)} e-mail(s)[/green]")
        messages = self.client.fetch_headers(results, count=20)
        if messages:
            table = Table(title=f"🔍 Resultados ({len(results)} encontrados)")
            table.add_column("ID", style="cyan", width=6)
            table.add_column("Data", style="white", width=16)
            table.add_column("Remetente", style="green", width=30)
            table.add_column("Assunto", style="yellow", width=50)
            for msg in messages:
                table.add_row(str(msg["id"]), msg["date"], msg["from"][:28], msg["subject"][:48])
            console.print(table)

    def open_email(self) -> None:
        """Abre e-mail."""
        if not self.message_ids:
            console.print("[yellow]Carregue a caixa de entrada primeiro.[/yellow]")
            return
        
        msg_id = Prompt.ask("ID do e-mail")
        if msg_id not in self.message_ids:
            console.print("[red]ID inválido.[/red]")
            return
        
        msg_data = self.client.fetch_message(msg_id)
        if not msg_data:
            console.print("[red]E-mail não encontrado.[/red]")
            return
        
        console.print(Panel(
            f"[bold]De:[/bold] {msg_data['from']}\n"
            f"[bold]Para:[/bold] {msg_data['to']}\n"
            f"[bold]Data:[/bold] {msg_data['date']}\n"
            f"[bold]Assunto:[/bold] {msg_data['subject']}",
            title="📧 Cabeçalho"
        ))
        
        body = msg_data.get("body_plain") or self.parser.html_to_text(msg_data.get("body_html", ""))
        if body:
            console.print("\n[bold]CONTEÚDO:[/bold]")
            console.print("-" * 60)
            for line in body.split("\n")[:50]:
                console.print(line)
        
        attachments = msg_data.get("attachments", [])
        if attachments:
            console.print("\n[bold]📎 Anexos:[/bold]")
            for idx, att in enumerate(attachments):
                size = self.parser.format_size(att["size"])
                console.print(f"  [cyan]{idx+1}.[/cyan] {att['filename']} ({size})")

    def select_emails(self) -> None:
        """Seleciona e-mails."""
        if not self.message_ids:
            console.print("[yellow]Carregue a caixa de entrada primeiro.[/yellow]")
            return
        
        input_ids = Prompt.ask(f"IDs disponíveis: {len(self.message_ids)}. Digite IDs (vírgula) ou 'all'")
        if input_ids.lower() == "all":
            self.selected_emails = self.message_ids.copy()
        else:
            ids = [x.strip() for x in input_ids.split(",")]
            self.selected_emails = [x for x in ids if x in self.message_ids]
        console.print(f"[green]✓ {len(self.selected_emails)} e-mail(s) selecionado(s)[/green]")

    def download_attachments(self) -> None:
        """Baixa anexos."""
        emails = self.selected_emails if self.selected_emails else self.message_ids
        if not emails:
            console.print("[yellow]Nenhum e-mail disponível.[/yellow]")
            return
        
        stats = self.downloader.download_from_messages(emails)
        console.print(f"\n[green]✓ Download concluído![/green]")
        console.print(f"  Anexos encontrados: {stats['attachments_found']}")
        console.print(f"  Downloads realizados: {stats['attachments_downloaded']}")

    def manage_emails(self) -> None:
        """Gerencia e-mails."""
        if not self.selected_emails:
            console.print("[yellow]Selecione e-mails primeiro.[/yellow]")
            return
        
        console.print(f"[bold]{len(self.selected_emails)} e-mail(s) selecionado(s)[/bold]")
        console.print("  1. Marcar como lido\n  2. Marcar como não lido\n  3. Excluir\n  4. Mover\n  0. Cancelar")
        choice = Prompt.ask("Escolha", choices=["0","1","2","3","4"], default="0")
        
        if choice == "1":
            self.client.mark_as_read(self.selected_emails)
            console.print("[green]✓ Marcados como lidos[/green]")
        elif choice == "2":
            self.client.mark_as_unread(self.selected_emails)
            console.print("[green]✓ Marcados como não lidos[/green]")
        elif choice == "3" and Confirm.ask("Confirmar exclusão?"):
            self.client.delete_messages(self.selected_emails)
            console.print("[green]✓ Excluídos[/green]")
            self.selected_emails = []
        elif choice == "4":
            folders = self.client.get_folders()
            for i, f in enumerate(folders, 1):
                console.print(f"  {i}. {f}")
            idx = Prompt.ask("Número da pasta")
            try:
                dest = folders[int(idx)-1]
                self.client.move_messages(self.selected_emails, dest)
                console.print(f"[green]✓ Movidos para {dest}[/green]")
            except:
                console.print("[red]Erro[/red]")

    def run(self) -> None:
        """Loop principal."""
        while True:
            display_dashboard(self.settings.gmail_email, self.current_folder, len(self.selected_emails))
            choice = self.show_main_menu()
            
            if choice == "0":
                console.print("\n[bold green]Até logo! 👋[/bold green]")
                break
            elif choice == "1":
                self.load_inbox()
            elif choice == "2":
                self.list_folders()
            elif choice == "3":
                self.search_emails()
            elif choice == "4":
                self.open_email()
            elif choice == "5":
                self.select_emails()
            elif choice == "6":
                self.download_attachments()
            elif choice == "7":
                self.manage_emails()
            elif choice == "8":
                self.message_ids = self.client.search("ALL")
                console.print(f"[green]✓ Atualizado ({len(self.message_ids)} e-mails)[/green]")
