"""Gerenciamento de mensagens do Gmail."""

import logging
from email import message_from_bytes
from typing import Optional
from .client import IMAPClient
from src.email_parser.parser import EmailParser, EmailMessage

logger = logging.getLogger(__name__)


class MessageManager:
    """Gerencia operações com mensagens de e-mail."""

    def __init__(self, client: IMAPClient):
        """
        Inicializa o gerenciador de mensagens.

        Args:
            client: Instância do IMAPClient.
        """
        self.client = client
        self.parser = EmailParser()

    def get_message_ids(self, criteria: str = "ALL") -> list[int]:
        """
        Obtém IDs das mensagens baseado em critérios.

        Args:
            criteria: Critério de busca IMAP.

        Returns:
            Lista de IDs das mensagens.
        """
        return self.client.search(criteria)

    def fetch_message(self, message_id: int, full: bool = False) -> Optional[EmailMessage]:
        """
        Busca uma mensagem específica.

        Args:
            message_id: ID da mensagem.
            full: Se True, busca a mensagem completa.

        Returns:
            EmailMessage ou None se falhar.
        """
        if full:
            data = self.client.fetch_full(message_id)
        else:
            data = self.client.fetch(message_id)

        if data is None:
            return None

        try:
            msg = message_from_bytes(data)
            return self.parser.parse(msg, message_id)
        except Exception as e:
            logger.error(f"Erro ao parsear mensagem {message_id}: {e}")
            return None

    def fetch_messages_batch(
        self, message_ids: list[int], limit: int = 50
    ) -> list[EmailMessage]:
        """
        Busca um lote de mensagens.

        Args:
            message_ids: Lista de IDs.
            limit: Número máximo de mensagens para buscar.

        Returns:
            Lista de EmailMessage.
        """
        messages = []
        for mid in message_ids[:limit]:
            msg = self.fetch_message(mid)
            if msg:
                messages.append(msg)
        return messages

    def mark_as_read(self, message_ids: list[int]) -> bool:
        """Marca mensagens como lidas."""
        return self.client.mark_as_read(message_ids)

    def mark_as_unread(self, message_ids: list[int]) -> bool:
        """Marca mensagens como não lidas."""
        return self.client.mark_as_unread(message_ids)

    def delete_messages(self, message_ids: list[int], confirm: bool = True) -> bool:
        """
        Exclui mensagens permanentemente.

        Args:
            message_ids: Lista de IDs.
            confirm: Se True, requer confirmação (expunge).

        Returns:
            True se excluído com sucesso.
        """
        if not self.client.delete(message_ids):
            return False
        
        if confirm:
            return self.client.expunge()
        return True

    def move_messages(self, message_ids: list[int], folder: str) -> bool:
        """Move mensagens para outra pasta."""
        return self.client.move_to_folder(message_ids, folder)
