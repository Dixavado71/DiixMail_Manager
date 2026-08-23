"""SMTP client implementation using smtplib."""

import logging
import smtplib
import socket
import ssl
from email.message import Message
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Any

from tenacity import retry, stop_after_attempt, wait_exponential

from ..config import Settings
from ..exceptions import AuthenticationError, ConnectionError, SMTPError
from ..protocols.imap_client import SMTPClientProtocol

logger = logging.getLogger(__name__)


class GmailSMTPClient(SMTPClientProtocol):
    """SMTP client for Gmail operations."""

    def __init__(self, settings: Settings) -> None:
        """Initialize SMTP client with settings."""
        self.settings = settings
        self._client: smtplib.SMTP | smtplib.SMTP_SSL | None = None
        self._last_error: str | None = None

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
    def connect(self) -> bool:
        """Connect to SMTP server with retry logic."""
        try:
            logger.info(f"Connecting to {self.settings.smtp_host}:{self.settings.smtp_port}")

            if self.settings.smtp_ssl or self.settings.smtp_port == 465:
                # SSL connection (port 465)
                self._client = smtplib.SMTP_SSL(
                    host=self.settings.smtp_host,
                    port=self.settings.smtp_port,
                    timeout=30,
                )
            else:
                # Plain connection with STARTTLS (port 587)
                self._client = smtplib.SMTP(
                    host=self.settings.smtp_host,
                    port=self.settings.smtp_port,
                    timeout=30,
                )
                if self.settings.smtp_starttls or self.settings.smtp_port == 587:
                    self._client.starttls()

            logger.info("Connected to SMTP server")
            return True
        except (socket.error, ssl.SSLError, OSError) as e:
            logger.error(f"Connection failed: {e}")
            raise ConnectionError(f"Failed to connect to SMTP server: {e}") from e

    def disconnect(self) -> None:
        """Disconnect from SMTP server."""
        if self._client:
            try:
                self._client.quit()
                logger.info("Disconnected from SMTP server")
            except Exception as e:
                logger.warning(f"Error during disconnect: {e}")
            finally:
                self._client = None

    def login(self, email: str, password: str) -> bool:
        """Authenticate with SMTP server."""
        if not self._client:
            raise ConnectionError("Not connected to server")

        try:
            logger.info(f"Authenticating as {email}")
            self._client.login(email, password)
            logger.info("Authentication successful")
            return True
        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"Authentication failed: {e}")
            raise AuthenticationError("Invalid email or app password") from e
        except Exception as e:
            logger.error(f"Login error: {e}")
            raise AuthenticationError(f"Login failed: {e}") from e

    def is_connected(self) -> bool:
        """Check if connected to server."""
        if not self._client:
            return False
        try:
            # Verify connection with NOOP
            self._client.noop()
            return True
        except Exception:
            return False

    def _ensure_connected(self) -> None:
        """Ensure client is connected."""
        if not self.is_connected():
            raise ConnectionError("Not connected to SMTP server")

    def send_message(self, message: Message) -> bool:
        """Send an email message."""
        self._ensure_connected()

        try:
            from_addr = message.get("From", "")
            to_addrs = message.get_all("To", [])

            # Parse To addresses
            if isinstance(to_addrs, str):
                to_addrs = [addr.strip() for addr in to_addrs.split(",")]

            self._client.send_message(message, from_addr=from_addr, to_addrs=to_addrs)
            logger.info(f"Message sent to {to_addrs}")
            return True
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            raise SMTPError(f"Failed to send message: {e}") from e

    def send_simple(
        self,
        subject: str,
        body: str,
        to_addresses: list[str],
        from_address: str | None = None,
        html: bool = False,
        attachments: list[str] | None = None,
    ) -> bool:
        """Send a simple email."""
        self._ensure_connected()

        try:
            if not from_address:
                from_address = self.settings.email

            if not from_address:
                raise SMTPError("No from address specified")

            # Create message
            if attachments:
                msg = MIMEMultipart()
                msg.attach(MIMEText(body, "html" if html else "plain"))

                # Add attachments
                for attachment_path in attachments:
                    path = Path(attachment_path)
                    if not path.exists():
                        logger.warning(f"Attachment not found: {attachment_path}")
                        continue

                    with open(path, "rb") as f:
                        content = f.read()

                    part = MIMEApplication(content)
                    part.add_header(
                        "Content-Disposition",
                        "attachment",
                        filename=path.name,
                    )
                    msg.attach(part)
            else:
                msg = MIMEText(body, "html" if html else "plain")

            msg["Subject"] = subject
            msg["From"] = from_address
            msg["To"] = ", ".join(to_addresses)

            return self.send_message(msg)
        except Exception as e:
            logger.error(f"Error sending simple message: {e}")
            raise SMTPError(f"Failed to send message: {e}") from e

    def get_last_error(self) -> str | None:
        """Get the last error message."""
        return self._last_error
