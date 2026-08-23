"""Buscas IMAP avançadas."""

from datetime import datetime, timedelta
from typing import Optional


class SearchManager:
    """Gerencia buscas IMAP."""

    def __init__(self, client):
        """Inicializa o gerenciador de buscas.

        Args:
            client: Instância do IMAPClient.
        """
        self.client = client

    def search(self, criteria: str = "ALL") -> list[str]:
        """Executa busca com critério IMAP.

        Args:
            criteria: Critério de busca IMAP.

        Returns:
            Lista de IDs das mensagens encontradas.
        """
        return self.client.search(criteria)

    def from_sender(self, email_address: str) -> list[str]:
        """Busca e-mails de um remetente específico.

        Args:
            email_address: Endereço de e-mail do remetente.

        Returns:
            Lista de IDs das mensagens.
        """
        return self.search(f'(FROM "{email_address}")')

    def to_recipient(self, email_address: str) -> list[str]:
        """Busca e-mails para um destinatário específico.

        Args:
            email_address: Endereço de e-mail do destinatário.

        Returns:
            Lista de IDs das mensagens.
        """
        return self.search(f'(TO "{email_address}")')

    def by_subject(self, subject: str) -> list[str]:
        """Busca e-mails por assunto.

        Args:
            subject: Texto do assunto.

        Returns:
            Lista de IDs das mensagens.
        """
        return self.search(f'(SUBJECT "{subject}")')

    def by_body(self, text: str) -> list[str]:
        """Busca e-mails por texto no corpo.

        Args:
            text: Texto a buscar.

        Returns:
            Lista de IDs das mensagens.
        """
        return self.search(f'(BODY "{text}")')

    def since_date(self, date: datetime) -> list[str]:
        """Busca e-mails desde uma data.

        Args:
            date: Data inicial.

        Returns:
            Lista de IDs das mensagens.
        """
        date_str = date.strftime("%d-%b-%Y")
        return self.search(f'(SINCE "{date_str}")')

    def before_date(self, date: datetime) -> list[str]:
        """Busca e-mails anteriores a uma data.

        Args:
            date: Data limite.

        Returns:
            Lista de IDs das mensagens.
        """
        date_str = date.strftime("%d-%b-%Y")
        return self.search(f'(BEFORE "{date_str}")')

    def on_date(self, date: datetime) -> list[str]:
        """Busca e-mails de uma data específica.

        Args:
            date: Data da busca.

        Returns:
            Lista de IDs das mensagens.
        """
        date_str = date.strftime("%d-%b-%Y")
        return self.search(f'(ON "{date_str}")')

    def last_days(self, days: int) -> list[str]:
        """Busca e-mails dos últimos N dias.

        Args:
            days: Número de dias.

        Returns:
            Lista de IDs das mensagens.
        """
        date = datetime.now() - timedelta(days=days)
        return self.since_date(date)

    def unread(self) -> list[str]:
        """Busca e-mails não lidos.

        Returns:
            Lista de IDs das mensagens.
        """
        return self.search("UNSEEN")

    def read(self) -> list[str]:
        """Busca e-mails lidos.

        Returns:
            Lista de IDs das mensagens.
        """
        return self.search("SEEN")

    def flagged(self) -> list[str]:
        """Busca e-mails marcados com estrela/flag.

        Returns:
            Lista de IDs das mensagens.
        """
        return self.search("FLAGGED")

    def with_attachments(self) -> list[str]:
        """Busca e-mails com anexos.

        Returns:
            Lista de IDs das mensagens.
        """
        # Gmail tem critério especial para anexos
        return self.search('has:attachment')

    def larger_than(self, size_kb: int) -> list[str]:
        """Busca e-mails maiores que um tamanho.

        Args:
            size_kb: Tamanho em KB.

        Returns:
            Lista de IDs das mensagens.
        """
        return self.search(f"LARGER {size_kb * 1024}")

    def smaller_than(self, size_kb: int) -> list[str]:
        """Busca e-mails menores que um tamanho.

        Args:
            size_kb: Tamanho em KB.

        Returns:
            Lista de IDs das mensagens.
        """
        return self.search(f"SMALLER {size_kb * 1024}")

    def custom_query(self, query: str) -> list[str]:
        """Executa uma consulta personalizada.

        Args:
            query: Query no formato Gmail/IMAP.

        Returns:
            Lista de IDs das mensagens.
        """
        return self.search(query)

    def parse_search_query(self, query: str) -> str:
        """Converte uma query simples para formato IMAP.

        Args:
            query: Query do usuário (ex: from:email, subject:palavra).

        Returns:
            Critério IMAP formatado.
        """
        query = query.strip()

        if not query:
            return "ALL"

        # from:email@dominio.com
        if query.lower().startswith("from:"):
            email = query[5:].strip()
            return f'(FROM "{email}")'

        # to:email@dominio.com
        if query.lower().startswith("to:"):
            email = query[3:].strip()
            return f'(TO "{email}")'

        # subject:palavra
        if query.lower().startswith("subject:"):
            subject = query[8:].strip()
            return f'(SUBJECT "{subject}")'

        # since:YYYY-MM-DD
        if query.lower().startswith("since:"):
            try:
                date_str = query[6:].strip()
                date = datetime.strptime(date_str, "%Y-%m-%d")
                return self.since_date(date)
            except ValueError:
                pass

        # before:YYYY-MM-DD
        if query.lower().startswith("before:"):
            try:
                date_str = query[7:].strip()
                date = datetime.strptime(date_str, "%Y-%m-%d")
                return self.before_date(date)
            except ValueError:
                pass

        # Default: busca no corpo
        return f'(BODY "{query}")'
