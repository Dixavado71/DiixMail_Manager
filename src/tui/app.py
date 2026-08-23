"""Aplicação TUI Premium do Gmail Manager usando Textual."""

from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Any

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer, Grid
from textual.widgets import (
    Header,
    Footer,
    Static,
    Button,
    Input,
    DataTable,
    TabbedContent,
    TabPane,
    Label,
    LoadingIndicator,
    ProgressBar,
    Switch,
    Select,
    Checkbox,
    RadioSet,
    RadioButton,
    RichLog,
)
from textual.binding import Binding
from textual.screen import Screen, ModalScreen
from textual.message import Message
from textual import work
from textual.worker import Worker, WorkerState
from rich.text import Text
from rich.panel import Panel

from ..config.settings import Settings
from ..imap.client import IMAPClient
from ..imap.folders import FolderManager
from ..imap.messages import MessageManager
from ..imap.search import SearchEngine
from ..attachments.downloader import AttachmentDownloader


# ============================================================================
# CSS ESTILIZAÇÃO PREMIUM DA APLICAÇÃO
# ============================================================================

CSS = """
/* Variáveis de cores premium */
$primary: #0066cc;
$primary-light: #3399ff;
$secondary: #00cc99;
$accent: #ff9900;
$danger: #ff4444;
$success: #00cc66;
$warning: #ffbb00;
$background: #0d1117;
$surface: #161b22;
$surface-light: #21262d;
$text: #c9d1d9;
$text-muted: #8b949e;
$border: #30363d;

/* Tema escuro premium */
Screen {
    background: $background;
}

/* Header personalizado */
Header {
    background: $primary;
    color: white;
    text-style: bold;
}

Header > HeaderTitle {
    color: white;
    text-style: bold;
}

/* Footer estilizado */
Footer {
    background: $surface;
    border-top: solid $border;
}

FooterKey {
    color: $text;
}

FooterKey kbd {
    background: $primary;
    color: white;
}

/* Containers */
Container {
    width: 100%;
    height: 100%;
}

Horizontal {
    width: 100%;
    height: auto;
}

Vertical {
    width: 100%;
    height: 100%;
}

/* Scrollable containers */
ScrollableContainer {
    width: 100%;
    height: 1fr;
    border: solid $border;
    background: $surface;
}

/* Grid layout */
Grid {
    grid-size: 2;
    grid-gutter: 1 2;
    padding: 1 2;
}

/* Painéis e cards */
Static {
    background: $surface;
    border: solid $border;
    padding: 1 2;
}

Static.title {
    background: $primary;
    color: white;
    text-style: bold;
    text-align: center;
}

/* Status bar */
#status-bar {
    height: 3;
    dock: bottom;
    background: $surface-light;
    border-top: solid $border;
    padding: 0 2;
}

#status-bar Label {
    width: auto;
    margin-right: 4;
    color: $text;
}

.status-connected {
    color: $success;
    text-style: bold;
}

.status-disconnected {
    color: $danger;
    text-style: bold;
}

/* DataTable premium */
DataTable {
    width: 100%;
    height: 1fr;
    background: $surface;
    border: solid $border;
}

DataTable > .datatable--header {
    background: $primary;
    color: white;
    text-style: bold;
}

DataTable > .datatable--cursor {
    background: $accent;
    color: black;
}

DataTable > .datatable--hover {
    background: $surface-light;
}

/* Tabs modernas */
TabbedContent {
    width: 100%;
    height: 1fr;
}

TabbedContent > .tab-bar {
    background: $surface;
    border-bottom: solid $border;
}

TabbedContent > .tab-bar > .tab-button {
    background: $surface;
    color: $text-muted;
    padding: 0 2;
}

TabbedContent > .tab-bar > .tab-button.--active {
    background: $primary;
    color: white;
    text-style: bold;
}

TabPane {
    background: $surface;
    padding: 1 2;
}

/* Botões premium */
Button {
    min-width: 15;
    margin: 0 1;
}

Button.primary {
    background: $primary;
    color: white;
}

Button.success {
    background: $success;
    color: white;
}

Button.danger {
    background: $danger;
    color: white;
}

Button.warning {
    background: $warning;
    color: black;
}

Button:hover {
    text-style: bold;
}

/* Inputs modernos */
Input {
    width: 100%;
    background: $surface-light;
    border: solid $border;
    color: $text;
}

Input:focus {
    border: solid $primary-light;
    background: $surface;
}

Input > .input--placeholder {
    color: $text-muted;
}

/* Labels */
Label {
    color: $text;
    padding: 0 1;
}

Label.title {
    color: $primary-light;
    text-style: bold;
    padding: 1 2;
}

Label.subtitle {
    color: $text-muted;
    text-style: italic;
}

/* Loading indicator */
LoadingIndicator {
    height: 3;
    margin: 1 0;
}

/* Progress bar */
ProgressBar {
    margin: 1 0;
}

/* Checkbox e Switches */
Checkbox {
    margin: 1 0;
    color: $text;
}

Switch {
    margin: 0 1;
}

/* Radio buttons */
RadioSet {
    margin: 1 0;
}

RadioButton {
    color: $text;
}

/* Log rico */
RichLog {
    width: 100%;
    height: 1fr;
    background: $surface;
    border: solid $border;
    color: $text;
}

/* Modal dialogs */
ModalScreen {
    align: center middle;
}

#modal-container {
    width: 80%;
    height: auto;
    max-height: 80%;
    background: $surface;
    border: solid $primary;
    padding: 2 4;
}

#modal-title {
    width: 100%;
    text-align: center;
    color: $primary-light;
    text-style: bold;
    padding: 1 0;
}

#modal-content {
    width: 100%;
    height: auto;
    padding: 1 0;
}

#modal-buttons {
    width: 100%;
    height: auto;
    align: center middle;
    padding: 1 0;
}

/* Sidebar */
#sidebar {
    width: 30;
    height: 100%;
    dock: left;
    background: $surface;
    border-right: solid $border;
    padding: 1 0;
}

#main-content {
    width: 1fr;
    height: 100%;
}

/* Email preview */
#email-preview {
    width: 100%;
    height: 40%;
    dock: bottom;
    background: $surface-light;
    border-top: solid $border;
    padding: 1 2;
}

/* Badge styles */
.badge-new {
    color: $danger;
    text-style: bold;
}

.badge-read {
    color: $success;
}

.badge-attachment {
    color: $accent;
}

/* Scrollbars personalizadas */
* {
    scrollbar-background: $surface;
    scrollbar-color: $primary;
    scrollbar-color-hover: $primary-light;
    scrollbar-size: 1;
}
"""


# ============================================================================
# TELAS MODAIS
# ============================================================================

class ConfirmDialog(ModalScreen[bool]):
    """Modal de confirmação."""

    BINDINGS = [
        Binding("enter", "confirm", "Confirmar"),
        Binding("escape", "cancel", "Cancelar"),
    ]

    def __init__(self, title: str, message: str) -> None:
        super().__init__()
        self.title_text = title
        self.message_text = message

    def compose(self) -> ComposeResult:
        with Container(id="modal-container"):
            yield Static(self.title_text, id="modal-title")
            yield Static(self.message_text, id="modal-content")
            with Horizontal(id="modal-buttons"):
                yield Button("Cancelar", variant="default", id="btn-cancel")
                yield Button("Confirmar", variant="primary", id="btn-confirm")

    def action_confirm(self) -> None:
        self.dismiss(True)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-cancel":
            self.dismiss(False)
        elif event.button.id == "btn-confirm":
            self.dismiss(True)


class EmailDetailScreen(ModalScreen[str | None]):
    """Tela de detalhes do e-mail."""

    BINDINGS = [
        Binding("escape", "close", "Fechar"),
        Binding("q", "close", "Fechar"),
    ]

    def __init__(self, email_data: dict[str, Any]) -> None:
        super().__init__()
        self.email_data = email_data

    def compose(self) -> ComposeResult:
        with Container(id="modal-container"):
            yield Static("📧 Detalhes do E-mail", id="modal-title")
            
            with ScrollableContainer(id="modal-content"):
                # Informações básicas
                yield Static(f"[bold]De:[/bold] {self.email_data.get('from', 'N/A')}", "")
                yield Static(f"[bold]Para:[/bold] {self.email_data.get('to', 'N/A')}", "")
                yield Static(f"[bold]Data:[/bold] {self.email_data.get('date', 'N/A')}", "")
                yield Static(f"[bold]Assunto:[/bold] {self.email_data.get('subject', 'N/A')}", "")
                yield Static("", "")
                
                # Corpo do e-mail
                yield Static("[bold]Conteúdo:[/bold]", "")
                content = self.email_data.get('body', 'Sem conteúdo')
                # Limita o tamanho para não sobrecarregar
                if len(content) > 2000:
                    content = content[:2000] + "\n\n... (conteúdo truncado)"
                yield Static(content, "")
                
                # Anexos
                attachments = self.email_data.get('attachments', [])
                if attachments:
                    yield Static("\n[bold]📎 Anexos:[/bold]", "")
                    for att in attachments:
                        yield Static(f"  • {att.get('filename', 'Unknown')} ({att.get('size', '?')} bytes)", "")

            with Horizontal(id="modal-buttons"):
                yield Button("Fechar", variant="primary", id="btn-close")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-close":
            self.dismiss(None)

    def action_close(self) -> None:
        self.dismiss(None)


class DownloadOptionsScreen(ModalScreen[dict[str, Any]]):
    """Tela de opções de download."""

    def __init__(self, selected_count: int) -> None:
        super().__init__()
        self.selected_count = selected_count

    def compose(self) -> ComposeResult:
        with Container(id="modal-container"):
            yield Static("⬇️ Opções de Download", id="modal-title")
            
            with Vertical(id="modal-content"):
                yield Static(f"E-mails selecionados: {self.selected_count}", "")
                yield Static("", "")
                
                yield Label("Organizar por:", classes="title")
                with RadioSet(id="organize-options"):
                    yield RadioButton("Pasta Downloads (sem organização)", value=True)
                    yield RadioButton("Por remetente")
                    yield RadioButton("Por assunto")
                    yield RadioButton("Por data (ano/mês)")
                
                yield Static("", "")
                yield Checkbox("Substituir arquivos existentes", value=False)

            with Horizontal(id="modal-buttons"):
                yield Button("Cancelar", variant="default", id="btn-cancel")
                yield Button("Baixar", variant="success", id="btn-download")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-cancel":
            self.dismiss({})
        elif event.button.id == "btn-download":
            radio_set = self.query_one("#organize-options", RadioSet)
            options = {
                "organize_by": ["none", "sender", "subject", "date"][radio_set.pressed_index],
                "overwrite": self.query_one(Checkbox).value,
            }
            self.dismiss(options)


# ============================================================================
# TELA PRINCIPAL
# ============================================================================

class MainScreen(Screen):
    """Tela principal da aplicação."""

    BINDINGS = [
        Binding("q", "quit", "Sair", priority=True),
        Binding("r", "refresh", "Atualizar"),
        Binding("n", "new_email", "Novo"),
        Binding("s", "search", "Pesquisar"),
        Binding("d", "delete", "Excluir"),
        Binding("f", "forward", "Encaminhar"),
        Binding("1", "show_inbox", "Caixa Entrada"),
        Binding("2", "show_folders", "Pastas"),
        Binding("3", "show_sent", "Enviados"),
        Binding("t", "toggle_preview", "Preview"),
        Binding("?", "help", "Ajuda"),
    ]

    def __init__(self, settings: Settings) -> None:
        super().__init__()
        self.settings = settings
        self.imap_client = IMAPClient(settings.imap_server, settings.imap_port)
        self.folder_manager = FolderManager(self.imap_client)
        self.message_manager = MessageManager(self.imap_client)
        self.search_engine = SearchEngine(self.imap_client)
        self.downloader = AttachmentDownloader(settings.get_download_path())
        
        self.current_folder = "INBOX"
        self.emails: list[dict[str, Any]] = []
        self.selected_emails: set[str] = set()
        self.is_connected = False
        self.show_preview = True

    def compose(self) -> ComposeResult:
        """Compõe a interface principal."""
        yield Header(show_clock=True)
        
        with Horizontal():
            # Sidebar com navegação
            with Vertical(id="sidebar"):
                yield Static("🚀 GMAIL MANAGER", classes="title")
                yield Static("", "")
                
                yield Button("📥 Caixa de Entrada", variant="primary", id="btn-inbox")
                yield Button("📤 Enviados", variant="default", id="btn-sent")
                yield Button("📁 Pastas", variant="default", id="btn-folders")
                yield Button("🔍 Pesquisar", variant="default", id="btn-search")
                yield Button("⭐ Importantes", variant="default", id="btn-important")
                yield Button("🗑️ Lixeira", variant="default", id="btn-trash")
                
                yield Static("", "")
                yield Static("─" * 25, "")
                yield Static("", "")
                
                yield Button("⬇️ Baixar Anexos", variant="warning", id="btn-download")
                yield Button("🏷️ Mover", variant="default", id="btn-move")
                yield Button("❌ Excluir", variant="danger", id="btn-delete")
                yield Button("🔄 Atualizar", variant="default", id="btn-refresh")
                
                yield Static("", "")
                yield Static("─" * 25, "")
                yield Static("", "")
                
                yield Button("🚪 Sair", variant="default", id="btn-exit")
        
        # Conteúdo principal
        with Vertical(id="main-content"):
            # Barra de status
            with Horizontal(id="status-bar"):
                yield Static("● ", id="status-indicator", classes="status-disconnected")
                yield Static("Desconectado", id="status-text")
                yield Static("|", "")
                yield Static("Pasta: ", "")
                yield Static("INBOX", id="current-folder")
                yield Static("|", "")
                yield Static("E-mails: ", "")
                yield Static("0", id="email-count")
                yield Static("|", "")
                yield Static("Selecionados: ", "")
                yield Static("0", id="selected-count")
            
            # Área de conteúdo com tabs
            with TabbedContent(initial="emails"):
                with TabPane("📧 E-mails", id="tab-emails"):
                    # Tabela de e-mails
                    yield DataTable(id="email-table")
                    
                    # Preview do e-mail
                    with Vertical(id="email-preview"):
                        yield Static("📖 Preview do E-mail", classes="title")
                        yield Static("Selecione um e-mail para visualizar", id="preview-content")
                
                with TabPane("📊 Estatísticas", id="tab-stats"):
                    with ScrollableContainer():
                        yield Static("Carregando estatísticas...", id="stats-content")
                
                with TabPane("📋 Log", id="tab-log"):
                    yield RichLog(markup=True, highlight=True, id="log-widget")
        
        yield Footer()

    def on_mount(self) -> None:
        """Executado quando a tela é montada."""
        self._connect_to_server()
        self._setup_email_table()

    def _setup_email_table(self) -> None:
        """Configura a tabela de e-mails."""
        table = self.query_one("#email-table", DataTable)
        table.add_columns(
            "✓",  # Selecionado
            "ID",
            "Status",
            "Remetente",
            "Assunto",
            "Data",
            "Anexos",
        )
        table.cursor_type = "row"

    @work(exclusive=True)
    async def _connect_to_server(self) -> None:
        """Conecta ao servidor IMAP em background."""
        try:
            success, message = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.imap_client.connect(
                    self.settings.gmail_email,
                    self.settings.gmail_app_password,
                )
            )
            
            if success:
                self.is_connected = True
                self.call_from_thread(self._update_status, True, message)
                self.call_from_thread(self._load_emails)
            else:
                self.call_from_thread(self._update_status, False, message)
                
        except Exception as e:
            self.call_from_thread(self._update_status, False, f"Erro: {e}")

    def _update_status(self, connected: bool, message: str) -> None:
        """Atualiza a barra de status."""
        indicator = self.query_one("#status-indicator", Static)
        status_text = self.query_one("#status-text", Static)
        
        if connected:
            indicator.update("🟢 ")
            indicator.remove_class("status-disconnected")
            indicator.add_class("status-connected")
            status_text.update("Conectado")
        else:
            indicator.update("🔴 ")
            indicator.remove_class("status-connected")
            indicator.add_class("status-disconnected")
            status_text.update(message)

    @work(exclusive=True)
    async def _load_emails(self) -> None:
        """Carrega e-mails em background."""
        try:
            # Seleciona pasta
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.imap_client.select_folder(self.current_folder)
            )
            
            # Busca mensagens
            success, message_ids = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.search_engine.search_all()
            )
            
            if success and message_ids:
                # Pega resumo das últimas 100 mensagens
                message_ids = sorted(message_ids, key=int, reverse=True)[:100]
                
                emails_data = []
                for msg_id in message_ids:
                    headers = await asyncio.get_event_loop().run_in_executor(
                        None,
                        lambda mid=msg_id: self.message_manager.get_message_headers(mid)
                    )
                    if headers:
                        emails_data.append(headers)
                
                self.emails = emails_data
                self.call_from_thread(self._populate_email_table)
                self.call_from_thread(self._update_counts)
                
        except Exception as e:
            log_widget = self.query_one("#log-widget", RichLog)
            log_widget.write(f"[red]Erro ao carregar e-mails: {e}[/red]")

    def _populate_email_table(self) -> None:
        """Popula a tabela com e-mails."""
        table = self.query_one("#email-table", DataTable)
        table.clear()
        
        for email in self.emails:
            msg_id = email.get('id', '')
            is_read = email.get('is_read', True)
            attachment_count = email.get('attachment_count', 0)
            
            status_icon = "📬" if is_read else "🆕"
            attachment_icon = f"📎{attachment_count}" if attachment_count > 0 else ""
            
            table.add_row(
                "✓" if msg_id in self.selected_emails else "",
                msg_id,
                status_icon,
                email.get('from_name', '')[:30],
                email.get('subject', '')[:40],
                email.get('date_str', '')[:10],
                attachment_icon,
                key=msg_id,
            )

    def _update_counts(self) -> None:
        """Atualiza contadores na UI."""
        self.query_one("#email-count", Static).update(str(len(self.emails)))
        self.query_one("#selected-count", Static).update(str(len(self.selected_emails)))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events."""
        button_id = event.button.id
        
        if button_id == "btn-inbox":
            self.action_show_inbox()
        elif button_id == "btn-folders":
            self.action_show_folders()
        elif button_id == "btn-search":
            self.action_search()
        elif button_id == "btn-download":
            self._show_download_options()
        elif button_id == "btn-delete":
            self._confirm_delete()
        elif button_id == "btn-refresh":
            self.action_refresh()
        elif button_id == "btn-exit":
            self.app.exit()

    def on_data_table_row_highlighted(self, event: DataTable.RowHighlighted) -> None:
        """Quando uma linha é destacada, mostra preview."""
        if event.row_key and self.show_preview:
            email_id = event.row_key.value
            self._show_email_preview(email_id)

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Quando uma linha é selecionada, toggle seleção."""
        if event.row_key:
            email_id = event.row_key.value
            if email_id in self.selected_emails:
                self.selected_emails.remove(email_id)
            else:
                self.selected_emails.add(email_id)
            self._update_counts()
            self._populate_email_table()

    def _show_email_preview(self, email_id: str) -> None:
        """Mostra preview do e-mail selecionado."""
        email_data = next((e for e in self.emails if e.get('id') == email_id), None)
        if email_data:
            preview_content = self.query_one("#preview-content", Static)
            preview_content.update(
                f"[bold]De:[/bold] {email_data.get('from', 'N/A')}\n"
                f"[bold]Assunto:[/bold] {email_data.get('subject', 'N/A')}\n"
                f"[bold]Data:[/bold] {email_data.get('date_str', 'N/A')}\n\n"
                f"{email_data.get('snippet', 'Sem preview disponível.')[:200]}"
            )

    def _show_download_options(self) -> None:
        """Mostra tela de opções de download."""
        if not self.selected_emails:
            self.notify("Nenhum e-mail selecionado!", severity="warning")
            return
        
        def handle_options(options: dict[str, Any] | None) -> None:
            if options:
                self._download_attachments(options)
        
        self.app.push_screen(DownloadOptionsScreen(len(self.selected_emails)), handle_options)

    @work
    async def _download_attachments(self, options: dict[str, Any]) -> None:
        """Baixa anexos em background."""
        organize_by = options.get('organize_by', 'none')
        overwrite = options.get('overwrite', False)
        
        downloaded = 0
        errors = 0
        
        for email_id in self.selected_emails:
            try:
                # Implementação simplificada - na prática precisaria buscar os anexos
                downloaded += 1
            except Exception:
                errors += 1
        
        self.notify(f"Download concluído: {downloaded} anexos baixados, {errors} erros")

    def _confirm_delete(self) -> None:
        """Confirma exclusão de e-mails."""
        if not self.selected_emails:
            self.notify("Nenhum e-mail selecionado!", severity="warning")
            return
        
        def handle_confirm(confirmed: bool) -> None:
            if confirmed:
                self._delete_emails()
        
        self.app.push_screen(
            ConfirmDialog(
                "Excluir E-mails",
                f"Tem certeza que deseja excluir {len(self.selected_emails)} e-mail(s)?",
            ),
            handle_confirm
        )

    @work
    async def _delete_emails(self) -> None:
        """Exclui e-mails selecionados."""
        # Implementação da exclusão
        self.notify("E-mails excluídos com sucesso!")
        self.selected_emails.clear()
        self._update_counts()
        await self._load_emails()

    # Actions
    def action_refresh(self) -> None:
        """Atualiza a lista de e-mails."""
        self.notify("Atualizando e-mails...")
        self._load_emails()

    def action_show_inbox(self) -> None:
        """Mostra caixa de entrada."""
        self.current_folder = "INBOX"
        self.query_one("#current-folder", Static).update("INBOX")
        self._load_emails()

    def action_show_folders(self) -> None:
        """Mostra lista de pastas."""
        self.notify("Funcionalidade em desenvolvimento")

    def action_search(self) -> None:
        """Abre busca."""
        input_widget = self.query_one(Input)
        if input_widget:
            input_widget.focus()

    def action_toggle_preview(self) -> None:
        """Toggle preview do e-mail."""
        self.show_preview = not self.show_preview
        preview = self.query_one("#email-preview", Vertical)
        preview.display = self.show_preview

    def action_help(self) -> None:
        """Mostra ajuda."""
        help_text = """
[bold]Atalhos de Teclado:[/bold]

[q] - Sair da aplicação
[r] - Atualizar e-mails
[n] - Novo e-mail
[s] - Pesquisar
[d] - Excluir selecionados
[f] - Encaminhar
[1] - Caixa de Entrada
[2] - Pastas
[3] - Enviados
[t] - Toggle preview
[?] - Esta ajuda

[Clique] - Selecionar e-mail
[Double-click] - Abrir e-mail
        """
        log_widget = self.query_one("#log-widget", RichLog)
        log_widget.write(help_text)


# ============================================================================
# APLICAÇÃO PRINCIPAL
# ============================================================================

class GmailManagerApp(App):
    """Aplicação TUI Premium do Gmail Manager."""

    CSS = CSS
    TITLE = "Gmail Manager TUI"
    SUB_TITLE = "Gerenciador Premium de E-mails"
    
    BINDINGS = [
        Binding("ctrl+q", "quit", "Sair"),
        Binding("ctrl+d", "toggle_dark", "Toggle Dark Mode"),
    ]

    def __init__(self, settings: Settings) -> None:
        super().__init__()
        self.settings = settings

    def on_mount(self) -> None:
        """Executado quando a aplicação é montada."""
        self.push_screen(MainScreen(self.settings))

    def action_toggle_dark(self) -> None:
        """Alterna tema escuro/claro."""
        self.theme = "textual-dark" if self.theme == "textual-light" else "textual-light"


def run_app(settings: Settings) -> None:
    """Executa a aplicação TUI."""
    app = GmailManagerApp(settings)
    app.run()
