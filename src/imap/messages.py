"""Operações com mensagens IMAP."""

from typing import Optional


class MessageManager:
    """Gerencia operações com mensagens IMAP."""

    def __init__(self, client):
        """Inicializa o gerenciador de mensagens.

        Args:
            client: Instância do IMAPClient.
        """
        self.client = client

    def mark_as_read(self, message_ids: list[str]) -> bool:
        """Marca mensagens como lidas.

        Args:
            message_ids: Lista de IDs das mensagens.

        Returns:
            True se todas foram marcadas.
        """
        return self.client.mark_as_read(message_ids)

    def mark_as_unread(self, message_ids: list[str]) -> bool:
        """Marca mensagens como não lidas.

        Args:
            message_ids: Lista de IDs das mensagens.

        Returns:
            True se todas foram marcadas.
        """
        return self.client.mark_as_unread(message_ids)

    def delete(self, message_ids: list[str]) -> bool:
        """Marca mensagens para exclusão.

        Args:
            message_ids: Lista de IDs das mensagens.

        Returns:
            True se todas foram marcadas.
        """
        return self.client.delete_messages(message_ids)

    def move(self, message_ids: list[str], destination: str) -> bool:
        """Move mensagens para outra pasta.

        Args:
            message_ids: Lista de IDs das mensagens.
            destination: Pasta de destino.

        Returns:
            True se movidas com sucesso.
        """
        return self.client.move_messages(message_ids, destination)

    def get_flags(self, message_id: str) -> list[str]:
        """Obtém flags de uma mensagem.

        Args:
            message_id: ID da mensagem.

        Returns:
            Lista de flags ou lista vazia.
        """
        if not self.client.connection:
            return []

        try:
            status, data = self.client.connection.fetch(message_id, "(FLAGS)")
            if status == "OK" and data:
                flags_str = data[0][1].decode()
                # Extrai flags entre parênteses
                start = flags_str.find("(")
                end = flags_str.find(")")
                if start != -1 and end != -1:
                    return flags_str[start + 1:end].split()
        except Exception:
            pass

        return []

    def add_flag(self, message_ids: list[str], flag: str) -> bool:
        """Adiciona uma flag a mensagens.

        Args:
            message_ids: Lista de IDs das mensagens.
            flag: Flag a adicionar.

        Returns:
            True se adicionada com sucesso.
        """
        if not self.client.connection:
            return False

        try:
            ids_str = ",".join(message_ids)
            self.client.connection.store(ids_str, "+FLAGS", flag)
            return True
        except Exception:
            return False

    def remove_flag(self, message_ids: list[str], flag: str) -> bool:
        """Remove uma flag de mensagens.

        Args:
            message_ids: Lista de IDs das mensagens.
            flag: Flag a remover.

        Returns:
            True se removida com sucesso.
        """
        if not self.client.connection:
            return False

        try:
            ids_str = ",".join(message_ids)
            self.client.connection.store(ids_str, "-FLAGS", flag)
            return True
        except Exception:
            return False

    def copy(self, message_ids: list[str], destination: str) -> bool:
        """Copia mensagens para outra pasta.

        Args:
            message_ids: Lista de IDs das mensagens.
            destination: Pasta de destino.

        Returns:
            True se copiadas com sucesso.
        """
        if not self.client.connection:
            return False

        try:
            ids_str = ",".join(message_ids)
            self.client.connection.copy(ids_str, destination)
            return True
        except Exception:
            return False

    def expunge(self) -> bool:
        """Remove permanentemente mensagens marcadas como Deleted.

        Returns:
            True se executado com sucesso.
        """
        if not self.client.connection:
            return False

        try:
            self.client.connection.expunge()
            return True
        except Exception:
            return False
