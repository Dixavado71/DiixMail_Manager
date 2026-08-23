"""Gerenciamento de pastas e marcadores do Gmail."""

import logging
from typing import Optional
from .client import IMAPClient

logger = logging.getLogger(__name__)


class FolderManager:
    """Gerencia pastas e marcadores IMAP."""

    def __init__(self, client: IMAPClient):
        """
        Inicializa o gerenciador de pastas.

        Args:
            client: Instância do IMAPClient.
        """
        self.client = client

    def list_folders(self) -> list[dict]:
        """
        Lista todas as pastas disponíveis.

        Returns:
            Lista de dicionários com informações das pastas.
        """
        if not self.client.is_connected():
            return []

        try:
            status, data = self.client.connection.list()
            
            if status != "OK":
                logger.warning(f"Erro ao listar pastas: {data}")
                return []

            folders = []
            for item in data:
                if isinstance(item, bytes):
                    item = item.decode("utf-8", errors="ignore")
                
                # Parse da resposta IMAP
                parts = item.split(' "')
                if len(parts) >= 3:
                    flags_str = parts[0].replace("(", "").replace(")", "")
                    delimiter = parts[1].strip('" ')
                    name = parts[2].strip('"')
                    
                    # Remove prefixo INBOX. se existir para exibição
                    display_name = name.replace("INBOX.", "📥 ") if name.startswith("INBOX.") else name
                    display_name = display_name.replace("[Gmail]/", "⭐ ")
                    
                    folders.append({
                        "name": name,
                        "display_name": display_name,
                        "delimiter": delimiter if delimiter != "NIL" else None,
                        "flags": flags_str.split(),
                        "is_inbox": name == "INBOX" or name.upper() == "INBOX",
                    })

            # Ordena: INBOX primeiro, depois alfabético
            folders.sort(key=lambda x: (not x["is_inbox"], x["name"].lower()))
            logger.info(f"{len(folders)} pastas encontradas")
            return folders

        except Exception as e:
            logger.error(f"Erro ao listar pastas: {e}")
            return []

    def get_folder_display(self, folder: dict) -> str:
        """
        Retorna nome formatado para exibição.

        Args:
            folder: Dicionário com informações da pasta.

        Returns:
            Nome formatado para exibição.
        """
        return folder.get("display_name", folder.get("name", "Unknown"))

    def select_folder_by_name(self, folder_name: str) -> tuple[bool, int]:
        """
        Seleciona uma pasta pelo nome.

        Args:
            folder_name: Nome da pasta.

        Returns:
            Tuple (sucesso, número_de_mensagens).
        """
        return self.client.select_folder(folder_name)
