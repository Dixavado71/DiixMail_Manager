# Gmail CLI Manager

CLI/TUI application to manage Gmail using IMAP and SMTP protocols. No OAuth 2.0, no Google Cloud, no Gmail API required.

## Features

- **IMAP** for reading, searching, and managing messages
- **SMTP** for sending emails
- **App Password** authentication (no OAuth)
- **TUI Dashboard** with Textual
- **CLI commands** for automation
- **Bulk operations** with confirmation
- **Download** emails and attachments
- **Export** to CSV, JSON, EML
- **Organization rules**

## Installation

```bash
pip install -e .
```

## Configuration

Create a `.env` file:

```env
EMAIL=user@gmail.com
APP_PASSWORD=xxxx xxxx xxxx xxxx

IMAP_HOST=imap.gmail.com
IMAP_PORT=993

SMTP_HOST=smtp.gmail.com
SMTP_PORT=465

DOWNLOAD_DIR=./downloads
LOG_LEVEL=INFO
BATCH_SIZE=50
```

### Getting App Password

1. Go to Google Account settings
2. Enable 2-Factor Authentication
3. Generate an App Password at: https://myaccount.google.com/apppasswords
4. Use this password (not your regular password)

## Usage

### Login

```bash
gmail-manager login
```

Interactive login:
```bash
gmail-manager login --interactive
```

### Dashboard

```bash
gmail-manager
```

### Commands

```bash
gmail-manager status          # Check connection status
gmail-manager logout          # Clear credentials
gmail-manager inbox           # View inbox
gmail-manager folders         # List all folders
gmail-manager search "QUERY"  # Search emails
gmail-manager read ID         # Read specific email
gmail-manager move ID FOLDER  # Move email
gmail-manager delete ID       # Delete email
gmail-manager bulk --search "FROM amazon" --delete  # Bulk operations
gmail-manager organize        # Apply organization rules
gmail-manager download        # Download emails
gmail-manager export --format csv  # Export emails
gmail-manager config          # Show configuration
```

### Search Examples

```bash
gmail-manager search "FROM amazon"
gmail-manager search "SUBJECT invoice"
gmail-manager search "UNSEEN"
gmail-manager search "SINCE 01-Jan-2024"
gmail-manager search "has:attachment"
gmail-manager provider amazon.com  # Search by domain
```

### Bulk Operations

```bash
# Dry run (safe preview)
gmail-manager bulk --search "FROM amazon.com" --delete --dry-run

# With confirmation
gmail-manager bulk --search "FROM amazon.com" --move-to Archive
```

### Download

```bash
gmail-manager download --search "has:attachment" --dest ./downloads
```

## Architecture

```
src/gmail_manager/
├── cli/           # CLI commands
├── imap/          # IMAP operations
├── smtp/          # SMTP client
├── auth/          # Authentication
├── services/      # Business logic
├── tui/           # Textual dashboard
├── utils/         # Utilities
└── config.py      # Configuration
```

## Security

- Never stores regular password
- App Password stored securely
- No credentials in logs
- Confirmation required for destructive operations
- `--dry-run` available for all bulk operations

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Lint
ruff check .

# Type check
mypy src/
```

## License

MIT
