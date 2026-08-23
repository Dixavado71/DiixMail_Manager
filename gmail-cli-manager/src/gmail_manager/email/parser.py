"""Email parser for MIME messages."""

import email
import logging
from dataclasses import dataclass, field
from email.message import Message
from email.utils import parseaddr
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class EmailContent:
    """Parsed email content."""

    subject: str = ""
    from_address: str = ""
    from_name: str = ""
    to_addresses: list[str] = field(default_factory=list)
    cc_addresses: list[str] = field(default_factory=list)
    bcc_addresses: list[str] = field(default_factory=list)
    date: str = ""
    text_body: str = ""
    html_body: str = ""
    headers: dict[str, str] = field(default_factory=dict)
    attachments: list[dict[str, Any]] = field(default_factory=list)
    is_multipart: bool = False
    message_id: str = ""
    in_reply_to: str | None = None
    references: list[str] = field(default_factory=list)


class EmailParser:
    """Parser for email MIME messages."""

    @staticmethod
    def parse(message: Message) -> EmailContent:
        """
        Parse an email message into structured content.

        Args:
            message: Email message object

        Returns:
            EmailContent with parsed data
        """
        content = EmailContent()

        # Basic headers
        content.subject = message.get("Subject", "")
        content.date = message.get("Date", "")
        content.message_id = message.get("Message-ID", "")
        content.in_reply_to = message.get("In-Reply-To")
        content.references = message.get_all("References", [])

        # From address
        from_full = message.get("From", "")
        content.from_address = from_full
        name, addr = parseaddr(from_full)
        content.from_name = name
        if not content.from_address and addr:
            content.from_address = addr

        # To addresses
        to_header = message.get("To", "")
        if to_header:
            content.to_addresses = [parseaddr(addr)[1] for addr in to_header.split(",") if parseaddr(addr)[1]]

        # CC addresses
        cc_header = message.get("Cc", "")
        if cc_header:
            content.cc_addresses = [parseaddr(addr)[1] for addr in cc_header.split(",") if parseaddr(addr)[1]]

        # Store all headers
        for key, value in message.items():
            content.headers[key] = value

        # Check if multipart
        content.is_multipart = message.is_multipart()

        if content.is_multipart:
            EmailParser._parse_multipart(message, content)
        else:
            EmailParser._parse_singlepart(message, content)

        return content

    @staticmethod
    def _parse_multipart(message: Message, content: EmailContent) -> None:
        """Parse multipart message."""
        for part in message.walk():
            content_type = part.get_content_type()
            content_disposition = part.get_content_disposition()

            # Skip the container itself
            if content_type.startswith("multipart/"):
                continue

            # Handle attachments
            if content_disposition == "attachment" or part.get_filename():
                filename = part.get_filename()
                if filename:
                    content.attachments.append(
                        {
                            "filename": filename,
                            "content_type": content_type,
                            "payload": part.get_payload(decode=True),
                            "size": len(part.get_payload(decode=True) or b""),
                        }
                    )
                continue

            # Handle body parts
            if content_type == "text/plain" and not content.text_body:
                payload = part.get_payload(decode=True)
                if payload:
                    try:
                        content.text_body = payload.decode(part.get_content_charset() or "utf-8", errors="replace")
                    except Exception as e:
                        logger.warning(f"Failed to decode text part: {e}")
                        content.text_body = str(payload)

            elif content_type == "text/html" and not content.html_body:
                payload = part.get_payload(decode=True)
                if payload:
                    try:
                        content.html_body = payload.decode(part.get_content_charset() or "utf-8", errors="replace")
                    except Exception as e:
                        logger.warning(f"Failed to decode HTML part: {e}")
                        content.html_body = str(payload)

    @staticmethod
    def _parse_singlepart(message: Message, content: EmailContent) -> None:
        """Parse single-part message."""
        content_type = message.get_content_type()
        payload = message.get_payload(decode=True)

        if payload:
            try:
                decoded = payload.decode(message.get_content_charset() or "utf-8", errors="replace")
                if content_type == "text/html":
                    content.html_body = decoded
                else:
                    content.text_body = decoded
            except Exception as e:
                logger.warning(f"Failed to decode message body: {e}")
                content.text_body = str(payload)

    @staticmethod
    def get_attachment_names(message: Message) -> list[str]:
        """Get list of attachment filenames."""
        attachments = []
        for part in message.walk():
            filename = part.get_filename()
            if filename:
                attachments.append(filename)
        return attachments

    @staticmethod
    def has_attachments(message: Message) -> bool:
        """Check if message has attachments."""
        for part in message.walk():
            if part.get_content_disposition() == "attachment":
                return True
        return False
