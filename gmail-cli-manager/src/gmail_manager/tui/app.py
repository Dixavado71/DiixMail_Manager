"""Textual TUI application for Gmail Manager."""

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Footer, Header, Label, ListView, ListItem, Static

from .config import Settings


class DashboardScreen(Screen):
    """Main dashboard screen."""

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("i", "focus('inbox_list')", "Inbox"),
        Binding("s", "push_screen('search')", "Search"),
        Binding("r", "refresh", "Refresh"),
    ]

    def __init__(self, settings: Settings) -> None:
        super().__init__()
        self.settings = settings

    def compose(self) -> ComposeResult:
        yield Header()

        with Container(id="main-container"):
            with Vertical(id="sidebar"):
                yield Static("📁 FOLDERS", id="sidebar-title")
                yield ListView(
                    ListItem(Label("📥 INBOX"), id="inbox-item"),
                    ListItem(Label("📤 SENT"), id="sent-item"),
                    ListItem(Label("📝 DRAFTS"), id="drafts-item"),
                    ListItem(Label("⚠️ SPAM"), id="spam-item"),
                    ListItem(Label("🗑️ TRASH"), id="trash-item"),
                    ListItem(Label("📂 ALL MAIL"), id="all-mail-item"),
                    id="folder-list",
                )

                yield Static("⚡ ACTIONS", id="sidebar-title")
                yield ListView(
                    ListItem(Label("🔍 Search"), id="search-item"),
                    ListItem(Label("📋 Organize"), id="organize-item"),
                    ListItem(Label("📦 Bulk Ops"), id="bulk-item"),
                    ListItem(Label("⬇️ Download"), id="download-item"),
                    ListItem(Label("⚙️ Config"), id="config-item"),
                    id="action-list",
                )

            with Vertical(id="main-content"):
                yield Static(f"👤 {self.settings.email}", id="user-info")

                with Horizontal(id="stats-row"):
                    yield Static("📊 Total: --", id="stat-total")
                    yield Static("📬 Unread: --", id="stat-unread")
                    yield Static("📁 Folders: --", id="stat-folders")

                yield Static("📧 Recent Messages", id="messages-title")
                yield Static("Loading...", id="messages-placeholder")

        yield Footer()

    def on_mount(self) -> None:
        """Load data when screen mounts."""
        self.call_later(self.load_data)

    async def load_data(self) -> None:
        """Load mailbox data asynchronously."""
        # This would connect to IMAP and load real data
        pass

    def action_refresh(self) -> None:
        """Refresh the dashboard."""
        self.load_data()


class GmailManagerApp(App):
    """Main Textual application."""

    CSS = """
    #main-container {
        height: 100%;
    }

    #sidebar {
        width: 25;
        height: 100%;
        background: $surface;
        padding: 1;
    }

    #sidebar-title {
        text-style: bold;
        padding: 1 0;
        color: $text-muted;
    }

    #main-content {
        width: 1fr;
        height: 100%;
        padding: 1 2;
    }

    #user-info {
        text-style: bold;
        padding: 1 0;
        margin-bottom: 1;
    }

    #stats-row {
        height: auto;
        margin-bottom: 1;
    }

    #stat-total, #stat-unread, #stat-folders {
        width: 1fr;
        padding: 1;
        background: $surface;
    }

    #messages-title {
        text-style: bold;
        padding: 1 0;
    }

    #messages-placeholder {
        color: $text-muted;
        padding: 1 0;
    }

    ListView {
        height: auto;
    }

    ListItem {
        padding: 0 1;
    }

    ListItem:hover {
        background: $accent;
    }

    ListItem--selected {
        background: $primary;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("d", "toggle_dark", "Toggle Dark Mode"),
    ]

    SCREENS = {
        "dashboard": DashboardScreen,
    }

    def __init__(self, settings: Settings) -> None:
        super().__init__()
        self.settings = settings
        self.title = "Gmail Manager"
        self.sub_title = settings.email if settings.email else "Not logged in"

    def on_mount(self) -> None:
        """Initialize the app."""
        self.push_screen("dashboard")

    def action_toggle_dark(self) -> None:
        """Toggle dark mode."""
        self.dark = not self.dark
