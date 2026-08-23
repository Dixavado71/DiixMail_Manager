"""Motor de busca para e-mails do Gmail."""

import logging
from typing import Optional
from .client import IMAPClient

logger = logging.getLogger(__name__)


class SearchEngine:
    """Motor de busca para mensagens IMAP."""

    def __init__(self, client: IMAPClient):
        """
        Inicializa o motor de busca.

        Args:
            client: Instância do IMAPClient.
        """
        self.client = client

    def search_by_sender(self, sender: str) -> list[int]:
        """
        Busca e-mails por remetente.

        Args:
            sender: Endereço ou nome do remetente.

        Returns:
            Lista de IDs das mensagens.
        """
        # Tenta buscar por endereço exato primeiro
        criteria = f'FROM "{sender}"'
        ids = self.client.search(criteria)
        
        if not ids and "@" in sender:
            # Tenta buscar apenas pelo domínio
            domain = sender.split("@")[1] if "@" in sender else sender
            criteria = f'FROM "{domain}"'
            ids = self.client.search(criteria)
        
        return ids

    def search_by_subject(self, subject: str) -> list[int]:
        """
        Busca e-mails por assunto.

        Args:
            subject: Texto do assunto.

        Returns:
            Lista de IDs das mensagens.
        """
        criteria = f'SUBJECT "{subject}"'
        return self.client.search(criteria)

    def search_by_recipient(self, recipient: str) -> list[int]:
        """
        Busca e-mails por destinatário.

        Args:
            recipient: Endereço do destinatário.

        Returns:
            Lista de IDs das mensagens.
        """
        criteria = f'TO "{recipient}"'
        return self.client.search(criteria)

    def search_unseen(self) -> list[int]:
        """Busca e-mails não lidos."""
        return self.client.search("UNSEEN")

    def search_seen(self) -> list[int]:
        """Busca e-mails lidos."""
        return self.client.search("SEEN")

    def search_flagged(self) -> list[int]:
        """Busca e-mails marcados com estrela."""
        return self.client.search("FLAGGED")

    def search_with_attachments(self) -> list[int]:
        """
        Busca e-mails com anexos.
        Nota: IMAP não tem critério direto para anexos,
        então buscamos todos e filtramos depois.
        """
        return self.client.search("ALL")

    def search_by_date(self, days: int = 7) -> list[int]:
        """
        Busca e-mails dos últimos dias.

        Args:
            days: Número de dias.

        Returns:
            Lista de IDs das mensagens.
        """
        # IMAP usa formato date-string específico
        # Para simplicidade, retornamos todos e filtramos no parser
        return self.client.search("ALL")

    def search_custom(self, query: str) -> list[int]:
        """
        Busca personalizada usando sintaxe IMAP.

        Args:
            query: Query no formato IMAP.

        Returns:
            Lista de IDs das mensagens.
        """
        return self.client.search(query)

    def parse_search_query(self, query: str) -> tuple[str, str]:
        """
        Parseia uma query simples do usuário.

        Args:
            query: Query do usuário (ex: "from:email@com", "subject:teste").

        Returns:
            Tuple (tipo_busca, termo).
        """
        query = query.strip().lower()
        
        if query.startswith("from:"):
            return ("sender", query[5:].strip())
        elif query.startswith("to:"):
            return ("recipient", query[3:].strip())
        elif query.startswith("subject:"):
            return ("subject", query[8:].strip())
        elif query.startswith("has:attachment"):
            return ("attachments", "")
        elif query.startswith("is:unread"):
            return ("unseen", "")
        elif query.startswith("is:read"):
            return ("seen", "")
        elif query.startswith("is:starred"):
            return ("flagged", "")
        else:
            # Busca genérica no assunto
            return ("subject", query)

    def execute_user_query(self, query: str) -> list[int]:
        """
        Executa uma query do usuário.

        Args:
            query: Query do usuário.

        Returns:
            Lista de IDs das mensagens.
        """
        search_type, term = self.parse_search_query(query)
        
        if search_type == "sender":
            return self.search_by_sender(term)
        elif search_type == "recipient":
            return self.search_by_recipient(term)
        elif search_type == "subject":
            return self.search_by_subject(term)
        elif search_type == "unseen":
            return self.search_unseen()
        elif search_type == "seen":
            return self.search_seen()
        elif search_type == "flagged":
            return self.search_flagged()
        else:
            # Busca genérica
            return self.search_by_subject(term) if term else self.client.search("ALL")
