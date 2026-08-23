"""Motor de busca de e-mails IMAP."""

from typing import Optional
from datetime import datetime, timedelta
from .client import IMAPClient


class SearchEngine:
    """Classe para realizar buscas avançadas em e-mails via IMAP."""

    def __init__(self, imap_client: IMAPClient):
        """
        Inicializa o motor de busca.

        Args:
            imap_client: Instância do cliente IMAP
        """
        self.imap_client = imap_client

    def search_all(self) -> tuple[bool, list[str]]:
        """
        Busca todos os e-mails na pasta atual.

        Returns:
            Tuple[bool, List[str]]: (sucesso, lista de IDs)
        """
        return self.imap_client.search("ALL")

    def search_from(self, email_or_name: str) -> tuple[bool, list[str]]:
        """
        Busca e-mails por remetente.

        Args:
            email_or_name: E-mail ou nome do remetente

        Returns:
            Tuple[bool, List[str]]: (sucesso, lista de IDs)
        """
        # Tenta buscar por e-mail exato primeiro
        criteria = f'FROM "{email_or_name}"'
        success, results = self.imap_client.search(criteria)

        if success and results:
            return success, results

        # Se não encontrou, tenta buscar sem aspas para nomes parciais
        criteria = f"FROM {email_or_name}"
        return self.imap_client.search(criteria)

    def search_to(self, email_or_name: str) -> tuple[bool, list[str]]:
        """
        Busca e-mails por destinatário.

        Args:
            email_or_name: E-mail ou nome do destinatário

        Returns:
            Tuple[bool, List[str]]: (sucesso, lista de IDs)
        """
        criteria = f'TO "{email_or_name}"'
        return self.imap_client.search(criteria)

    def search_subject(self, subject: str) -> tuple[bool, list[str]]:
        """
        Busca e-mails por assunto.

        Args:
            subject: Texto do assunto

        Returns:
            Tuple[bool, List[str]]: (sucesso, lista de IDs)
        """
        criteria = f'SUBJECT "{subject}"'
        return self.imap_client.search(criteria)

    def search_body(self, text: str) -> tuple[bool, list[str]]:
        """
        Busca e-mails por texto no corpo da mensagem.

        Args:
            text: Texto a buscar

        Returns:
            Tuple[bool, List[str]]: (sucesso, lista de IDs)
        """
        criteria = f'BODY "{text}"'
        return self.imap_client.search(criteria)

    def search_text(self, text: str) -> tuple[bool, list[str]]:
        """
        Busca e-mails por texto em qualquer campo (assunto + corpo).

        Args:
            text: Texto a buscar

        Returns:
            Tuple[bool, List[str]]: (sucesso, lista de IDs)
        """
        criteria = f'TEXT "{text}"'
        return self.imap_client.search(criteria)

    def search_since(self, date: datetime) -> tuple[bool, list[str]]:
        """
        Busca e-mails enviados desde uma data.

        Args:
            date: Data inicial

        Returns:
            Tuple[bool, List[str]]: (sucesso, lista de IDs)
        """
        date_str = date.strftime("%d-%b-%Y")
        criteria = f'SINCE "{date_str}"'
        return self.imap_client.search(criteria)

    def search_before(self, date: datetime) -> tuple[bool, list[str]]:
        """
        Busca e-mails enviados antes de uma data.

        Args:
            date: Data limite

        Returns:
            Tuple[bool, List[str]]: (sucesso, lista de IDs)
        """
        date_str = date.strftime("%d-%b-%Y")
        criteria = f'BEFORE "{date_str}"'
        return self.imap_client.search(criteria)

    def search_between(self, start_date: datetime, end_date: datetime) -> tuple[bool, list[str]]:
        """
        Busca e-mails enviados entre duas datas.

        Args:
            start_date: Data inicial
            end_date: Data final

        Returns:
            Tuple[bool, List[str]]: (sucesso, lista de IDs)
        """
        start_str = start_date.strftime("%d-%b-%Y")
        end_str = end_date.strftime("%d-%b-%Y")
        criteria = f'SINCE "{start_str}" BEFORE "{end_str}"'
        return self.imap_client.search(criteria)

    def search_last_days(self, days: int) -> tuple[bool, list[str]]:
        """
        Busca e-mails dos últimos N dias.

        Args:
            days: Número de dias

        Returns:
            Tuple[bool, List[str]]: (sucesso, lista de IDs)
        """
        start_date = datetime.now() - timedelta(days=days)
        return self.search_since(start_date)

    def search_unseen(self) -> tuple[bool, list[str]]:
        """
        Busca e-mails não lidos.

        Returns:
            Tuple[bool, List[str]]: (sucesso, lista de IDs)
        """
        return self.imap_client.search("UNSEEN")

    def search_seen(self) -> tuple[bool, list[str]]:
        """
        Busca e-mails lidos.

        Returns:
            Tuple[bool, List[str]]: (sucesso, lista de IDs)
        """
        return self.imap_client.search("SEEN")

    def search_flagged(self) -> tuple[bool, list[str]]:
        """
        Busca e-mails marcados com estrela/flag.

        Returns:
            Tuple[bool, List[str]]: (sucesso, lista de IDs)
        """
        return self.imap_client.search("FLAGGED")

    def search_with_attachments(self) -> tuple[bool, list[str]]:
        """
        Busca e-mails que possuem anexos.

        Nota: IMAP não tem critério nativo para anexos,
        então usamos uma busca por HEADER Content-Disposition.

        Returns:
            Tuple[bool, List[str]]: (sucesso, lista de IDs)
        """
        # Gmail suporta busca por has:attachment
        return self.imap_client.search("has:attachment")

    def search_larger_than(self, size_kb: int) -> tuple[bool, list[str]]:
        """
        Busca e-mails maiores que um tamanho específico.

        Args:
            size_kb: Tamanho em KB

        Returns:
            Tuple[bool, List[str]]: (sucesso, lista de IDs)
        """
        # Gmail suporta larger:X
        criteria = f"larger:{size_kb}K"
        return self.imap_client.search(criteria)

    def search_smaller_than(self, size_kb: int) -> tuple[bool, list[str]]:
        """
        Busca e-mails menores que um tamanho específico.

        Args:
            size_kb: Tamanho em KB

        Returns:
            Tuple[bool, List[str]]: (sucesso, lista de IDs)
        """
        # Gmail suporta smaller:X
        criteria = f"smaller:{size_kb}K"
        return self.imap_client.search(criteria)

    def search_custom(self, criteria: str) -> tuple[bool, list[str]]:
        """
        Executa uma busca com critério personalizado.

        Args:
            criteria: Critério IMAP personalizado

        Returns:
            Tuple[bool, List[str]]: (sucesso, lista de IDs)
        """
        return self.imap_client.search(criteria)

    def parse_search_query(self, query: str) -> tuple[bool, list[str]]:
        """
        Analisa e executa uma query de busca no formato simplificado.

        Suporta formatos como:
        - from:email@exemplo.com
        - subject:texto
        - to:email@exemplo.com
        - since:2024-01-01
        - before:2024-01-01
        - has:attachment
        - is:unread
        - is:starred
        - texto livre (busca em TEXT)

        Args:
            query: String de busca

        Returns:
            Tuple[bool, List[str]]: (sucesso, lista de IDs)
        """
        query = query.strip()

        if not query:
            return self.search_all()

        # Parseia operadores
        if query.startswith("from:"):
            return self.search_from(query[5:].strip())

        elif query.startswith("to:"):
            return self.search_to(query[3:].strip())

        elif query.startswith("subject:"):
            return self.search_subject(query[8:].strip())

        elif query.startswith("since:"):
            try:
                date = datetime.strptime(query[6:].strip(), "%Y-%m-%d")
                return self.search_since(date)
            except ValueError:
                return False, []

        elif query.startswith("before:"):
            try:
                date = datetime.strptime(query[7:].strip(), "%Y-%m-%d")
                return self.search_before(date)
            except ValueError:
                return False, []

        elif query.startswith("last:"):
            try:
                days = int(query[5:].strip())
                return self.search_last_days(days)
            except ValueError:
                return False, []

        elif query == "has:attachment" or query == "has:anexo":
            return self.search_with_attachments()

        elif query == "is:unread" or query == "is:não_lido":
            return self.search_unseen()

        elif query == "is:read" or query == "is:lido":
            return self.search_seen()

        elif query == "is:starred" or query == "is:com_estrela":
            return self.search_flagged()

        else:
            # Busca textual genérica
            return self.search_text(query)
