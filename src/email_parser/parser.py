"""Parser para mensagens de e-mail."""

import logging
from email.message import Message
from email.utils import parseaddr, parsedate_to_datetime
from datetime import datetime
from typing import Optional
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class Attachment:
    """Representa um anexo de e-mail."""
    filename: str
    content_type: str
    size: int
    payload: bytes = field(default_factory=bytes, repr=False)

    @property
    def size_formatted(self) -> str:
        """Retorna tamanho formatado."""
        if self.size < 1024:
            return f"{self.size} B"
        elif self.size < 1024 * 1024:
            return f"{self.size / 1024:.1f} KB"
        else:
            return f"{self.size / (1024 * 1024):.1f} MB"


@dataclass
class EmailMessage:
    """Representa uma mensagem de e-mail parseada."""
    id: int
    subject: str
    sender: str
    sender_email: str
    recipients: list[str]
    date: datetime
    body_text: str
    body_html: str
    attachments: list[Attachment]
    is_read: bool = False
    is_flagged: bool = False
    headers: dict = field(default_factory=dict)

    @property
    def date_formatted(self) -> str:
        """Retorna data formatada."""
        try:
            return self.date.strftime("%d/%m/%Y %H:%M")
        except Exception:
            return "Data inválida"

    @property
    def has_attachments(self) -> bool:
        """Verifica se tem anexos."""
        return len(self.attachments) > 0

    @property
    def attachment_count(self) -> int:
        """Retorna número de anexos."""
        return len(self.attachments)

    @property
    def status_display(self) -> str:
        """Retorna status para exibição."""
        return "LIDO" if self.is_read else "NOVO"


class EmailParser:
    """Parseia mensagens de e-mail IMAP."""

    def __init__(self):
        """Inicializa o parser."""
        pass

    def parse(self, msg: Message, message_id: int) -> EmailMessage:
        """
        Parseia uma mensagem MIME.

        Args:
            msg: Mensagem MIME.
            message_id: ID da mensagem.

        Returns:
            EmailMessage parseada.
        """
        # Extrai remetente
        sender_raw = msg.get("From", "")
        sender_name, sender_email = parseaddr(sender_raw)
        if not sender_name:
            sender_name = sender_email

        # Extrai destinatários
        recipients_raw = msg.get("To", "")
        recipients = []
        if recipients_raw:
            for addr in recipients_raw.split(","):
                name, email = parseaddr(addr.strip())
                if email:
                    recipients.append(email if not name else f"{name} <{email}>")

        # Extrai data
        date_raw = msg.get("Date", "")
        try:
            date = parsedate_to_datetime(date_raw) if date_raw else datetime.now()
        except Exception:
            date = datetime.now()

        # Extrai assunto
        subject = self._decode_header(msg.get("Subject", ""))

        # Extrai corpo
        body_text, body_html = self._extract_body(msg)

        # Extrai anexos
        attachments = self._extract_attachments(msg)

        # Verifica flags
        flags = msg.get("X-GM-FLAGS", "")
        is_read = "\\Seen" in str(flags) if flags else False
        is_flagged = "\\Flagged" in str(flags) if flags else False

        # Headers brutos para debug
        headers = {k: v for k, v in msg.items()}

        return EmailMessage(
            id=message_id,
            subject=subject,
            sender=sender_name,
            sender_email=sender_email,
            recipients=recipients,
            date=date,
            body_text=body_text,
            body_html=body_html,
            attachments=attachments,
            is_read=is_read,
            is_flagged=is_flagged,
            headers=headers,
        )

    def _decode_header(self, value: str) -> str:
        """Decodifica header com encoding."""
        if not value:
            return ""
        
        from email.header import decode_header
        
        decoded_parts = decode_header(value)
        result = []
        
        for part, encoding in decoded_parts:
            if isinstance(part, bytes):
                try:
                    enc = encoding or "utf-8"
                    result.append(part.decode(enc, errors="replace"))
                except Exception:
                    result.append(part.decode("utf-8", errors="replace"))
            else:
                result.append(part)
        
        return "".join(result)

    def _extract_body(self, msg: Message) -> tuple[str, str]:
        """
        Extrai corpo do e-mail.

        Returns:
            Tuple (texto_plano, html).
        """
        body_text = ""
        body_html = ""

        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get_content_disposition() or "")
                
                # Ignora anexos
                if "attachment" in content_disposition.lower():
                    continue

                try:
                    payload = part.get_payload(decode=True)
                    if payload is None:
                        continue
                    
                    charset = part.get_content_charset() or "utf-8"
                    
                    if content_type == "text/plain":
                        body_text += payload.decode(charset, errors="replace") + "\n"
                    elif content_type == "text/html":
                        body_html += payload.decode(charset, errors="replace")
                        
                except Exception as e:
                    logger.warning(f"Erro ao extrair parte: {e}")
        else:
            # Mensagem simples (não multipart)
            try:
                payload = msg.get_payload(decode=True)
                if payload:
                    charset = msg.get_content_charset() or "utf-8"
                    if msg.get_content_type() == "text/html":
                        body_html = payload.decode(charset, errors="replace")
                    else:
                        body_text = payload.decode(charset, errors="replace")
            except Exception as e:
                logger.warning(f"Erro ao extrair corpo: {e}")

        return body_text.strip(), body_html.strip()

    def _extract_attachments(self, msg: Message) -> list[Attachment]:
        """Extrai anexos da mensagem."""
        attachments = []

        if not msg.is_multipart():
            return attachments

        for part in msg.walk():
            content_disposition = str(part.get_content_disposition() or "")
            
            if "attachment" not in content_disposition.lower():
                continue

            filename = part.get_filename()
            if not filename:
                continue

            # Decodifica nome do arquivo
            filename = self._decode_header(filename)

            try:
                payload = part.get_payload(decode=True)
                if payload is None:
                    continue

                attachment = Attachment(
                    filename=filename,
                    content_type=part.get_content_type(),
                    size=len(payload),
                    payload=payload,
                )
                attachments.append(attachment)

            except Exception as e:
                logger.warning(f"Erro ao extrair anexo {filename}: {e}")

        return attachments
