"""Gerenciamento de pastas IMAP."""

from typing import Optional


class FolderManager:
    """Gerencia operações com pastas IMAP."""

    def __init__(self, client):
        """Inicializa o gerenciador de pastas.

        Args:
            client: Instância do IMAPClient.
        """
        self.client = client

    def list_folders(self) -> list[str]:
        """Lista todas as pastas disponíveis.

        Returns:
            Lista de nomes de pastas.
        """
        return self.client.get_folders()

    def select_folder(self, folder_name: str) -> int:
        """Seleciona uma pasta.

        Args:
            folder_name: Nome da pasta.

        Returns:
            Número de mensagens na pasta.
        """
        return self.client.select_folder(folder_name)

    def create_folder(self, folder_name: str) -> bool:
        """Cria uma nova pasta.

        Args:
            folder_name: Nome da pasta a criar.

        Returns:
            True se criada com sucesso.
        """
        if not self.client.connection:
            return False

        try:
            self.client.connection.create(folder_name)
            return True
        except Exception:
            return False

    def delete_folder(self, folder_name: str) -> bool:
        """Exclui uma pasta.

        Args:
            folder_name: Nome da pasta a excluir.

        Returns:
            True se excluída com sucesso.
        """
        if not self.client.connection:
            return False

        try:
            self.client.connection.delete(folder_name)
            return True
        except Exception:
            return False

    def rename_folder(self, old_name: str, new_name: str) -> bool:
        """Renomeia uma pasta.

        Args:
            old_name: Nome atual da pasta.
            new_name: Novo nome da pasta.

        Returns:
            True se renomeada com sucesso.
        """
        if not self.client.connection:
            return False

        try:
            self.client.connection.rename(old_name, new_name)
            return True
        except Exception:
            return False

    def get_folder_info(self, folder_name: str) -> Optional[dict]:
        """Obtém informações sobre uma pasta.

        Args:
            folder_name: Nome da pasta.

        Returns:
            Dicionário com informações ou None.
        """
        if not self.client.connection:
            return None

        try:
            status, data = self.client.connection.status(
                folder_name, ["MESSAGES", "RECENT", "UNSEEN"]
            )

            if status != "OK":
                return None

            info = {"name": folder_name}

            for item in data:
                if isinstance(item, bytes):
                    item_str = item.decode()
                    if "MESSAGES" in item_str:
                        parts = item_str.split()
                        for i, p in enumerate(parts):
                            if p == "MESSAGES":
                                info["messages"] = int(parts[i + 1])
                            elif p == "RECENT":
                                info["recent"] = int(parts[i + 1])
                            elif p == "UNSEEN":
                                info["unseen"] = int(parts[i + 1])

            return info

        except Exception:
            return None
