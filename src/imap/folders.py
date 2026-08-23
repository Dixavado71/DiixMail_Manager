"""Gerenciamento de pastas e marcadores IMAP."""

from typing import Optional
from .client import IMAPClient


class FolderManager:
    """Classe para gerenciar pastas e marcadores do Gmail."""

    def __init__(self, imap_client: IMAPClient):
        """
        Inicializa o gerenciador de pastas.

        Args:
            imap_client: Instância do cliente IMAP
        """
        self.imap_client = imap_client

    def list_folders(self) -> tuple[bool, list[dict]]:
        """
        Lista todas as pastas/marcadores disponíveis.

        Returns:
            Tuple[bool, List[dict]]: (sucesso, lista de pastas com informações)
        """
        connection = self.imap_client.get_connection()

        if not connection or not self.imap_client.is_connected:
            return False, []

        try:
            status, data = connection.list()

            if status != "OK":
                return False, []

            folders = []
            for folder_data in data:
                if folder_data is None:
                    continue

                # Decodifica os dados da pasta
                if isinstance(folder_data, bytes):
                    folder_str = folder_data.decode("utf-8", errors="ignore")
                else:
                    folder_str = str(folder_data)

                # Parseia a resposta IMAP LIST
                # Formato típico: (\\HasNoChildren) "/" "INBOX"
                parts = folder_str.split(' "')
                if len(parts) >= 2:
                    # Extrai flags
                    flags_part = parts[0].strip("() ")
                    flags = [f.strip("\\") for f in flags_part.split()]

                    # Extrai separador e nome da pasta
                    remaining = ' "'.join(parts[1:])
                    sub_parts = remaining.split('" ')

                    if len(sub_parts) >= 2:
                        separator = sub_parts[0].strip('" ')
                        folder_name = sub_parts[1].strip('"')

                        # Traduz nomes comuns do Gmail
                        display_name = self._translate_folder_name(folder_name)

                        folders.append({
                            "name": folder_name,
                            "display_name": display_name,
                            "separator": separator,
                            "flags": flags,
                            "has_children": "\\HasChildren" in flags,
                        })

            return True, folders

        except Exception:
            return False, []

    def _translate_folder_name(self, name: str) -> str:
        """
        Traduz nomes de pastas do Gmail para português.

        Args:
            name: Nome original da pasta

        Returns:
            str: Nome traduzido ou original
        """
        translations = {
            "INBOX": "Caixa de Entrada",
            "[Gmail]/All Mail": "Todos os E-mails",
            "[Gmail]/Drafts": "Rascunhos",
            "[Gmail]/Sent Mail": "Enviados",
            "[Gmail]/Spam": "Spam",
            "[Gmail]/Starred": "Com Estrela",
            "[Gmail]/Trash": "Lixeira",
            "[Gmail]/Important": "Importantes",
            "INBOX.Sent": "Enviados",
            "INBOX.Drafts": "Rascunhos",
            "INBOX.Spam": "Spam",
            "INBOX.Trash": "Lixeira",
        }

        return translations.get(name, name)

    def get_folder_info(self, folder_name: str) -> Optional[dict]:
        """
        Obtém informações detalhadas sobre uma pasta específica.

        Args:
            folder_name: Nome da pasta

        Returns:
            dict ou None: Informações da pasta ou None se não encontrada
        """
        success, folders = self.list_folders()

        if not success:
            return None

        for folder in folders:
            if folder["name"] == folder_name:
                return folder

        return None

    def folder_exists(self, folder_name: str) -> bool:
        """
        Verifica se uma pasta existe.

        Args:
            folder_name: Nome da pasta

        Returns:
            bool: True se a pasta existe
        """
        info = self.get_folder_info(folder_name)
        return info is not None

    def create_folder(self, folder_name: str) -> tuple[bool, str]:
        """
        Cria uma nova pasta no servidor IMAP.

        Args:
            folder_name: Nome da pasta a criar

        Returns:
            Tuple[bool, str]: (sucesso, mensagem)
        """
        connection = self.imap_client.get_connection()

        if not connection or not self.imap_client.is_connected:
            return False, "Não conectado ao servidor"

        try:
            encoded_name = folder_name.encode("utf-7").decode("utf-7")
            status, data = connection.create(encoded_name)

            if status == "OK":
                return True, f"Pasta '{folder_name}' criada com sucesso"
            else:
                return False, f"Falha ao criar pasta: {data}"

        except Exception as e:
            return False, f"Erro ao criar pasta: {e}"

    def delete_folder(self, folder_name: str) -> tuple[bool, str]:
        """
        Exclui uma pasta do servidor IMAP.

        Args:
            folder_name: Nome da pasta a excluir

        Returns:
            Tuple[bool, str]: (sucesso, mensagem)
        """
        connection = self.imap_client.get_connection()

        if not connection or not self.imap_client.is_connected:
            return False, "Não conectado ao servidor"

        try:
            encoded_name = folder_name.encode("utf-7").decode("utf-7")
            status, data = connection.delete(encoded_name)

            if status == "OK":
                return True, f"Pasta '{folder_name}' excluída com sucesso"
            else:
                return False, f"Falha ao excluir pasta: {data}"

        except Exception as e:
            return False, f"Erro ao excluir pasta: {e}"

    def rename_folder(self, old_name: str, new_name: str) -> tuple[bool, str]:
        """
        Renomeia uma pasta no servidor IMAP.

        Args:
            old_name: Nome atual da pasta
            new_name: Novo nome da pasta

        Returns:
            Tuple[bool, str]: (sucesso, mensagem)
        """
        connection = self.imap_client.get_connection()

        if not connection or not self.imap_client.is_connected:
            return False, "Não conectado ao servidor"

        try:
            encoded_old = old_name.encode("utf-7").decode("utf-7")
            encoded_new = new_name.encode("utf-7").decode("utf-7")
            status, data = connection.rename(encoded_old, encoded_new)

            if status == "OK":
                return True, f"Pasta renomeada de '{old_name}' para '{new_name}'"
            else:
                return False, f"Falha ao renomear pasta: {data}"

        except Exception as e:
            return False, f"Erro ao renomear pasta: {e}"
