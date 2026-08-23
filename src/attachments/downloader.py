"""Downloader de anexos."""

from pathlib import Path
from datetime import datetime

from src.email_parser.parser import EmailParser
from src.imap.client import IMAPClient


class AttachmentDownloader:
    """Gerencia download de anexos."""

    def __init__(self, client: IMAPClient, download_dir: Path):
        """Inicializa o downloader.

        Args:
            client: Cliente IMAP.
            download_dir: Diretório para salvar downloads.
        """
        self.client = client
        self.download_dir = download_dir
        self.parser = EmailParser()

    def download_single(self, message_id: str, attachment_index: int,
                       filename: str | None = None) -> tuple[bool, str]:
        """Baixa um único anexo.

        Args:
            message_id: ID da mensagem.
            attachment_index: Índice do anexo.
            filename: Nome opcional para o arquivo.

        Returns:
            Tupla (sucesso, caminho ou mensagem de erro).
        """
        # Gera nome seguro
        if filename:
            safe_name = self.parser.sanitize_filename(filename)
        else:
            safe_name = f"anexo_{message_id}_{attachment_index}"

        # Cria path único se já existir
        save_path = self.download_dir / safe_name
        counter = 1
        
        while save_path.exists():
            name_parts = safe_name.rsplit(".", 1)
            if len(name_parts) == 2:
                new_name = f"{name_parts[0]}_{counter}.{name_parts[1]}"
            else:
                new_name = f"{safe_name}_{counter}"
            save_path = self.download_dir / new_name
            counter += 1

        # Baixa arquivo
        success = self.client.download_attachment(
            message_id, attachment_index, str(save_path)
        )

        if success:
            return True, str(save_path)
        else:
            return False, "Falha ao baixar anexo"

    def download_from_messages(self, message_ids: list[str], 
                               progress_callback=None) -> dict:
        """Baixa anexos de múltiplas mensagens.

        Args:
            message_ids: Lista de IDs das mensagens.
            progress_callback: Callback para progresso.

        Returns:
            Dicionário com estatísticas do download.
        """
        stats = {
            "messages_processed": 0,
            "attachments_found": 0,
            "attachments_downloaded": 0,
            "errors": [],
        }

        for msg_id in message_ids:
            if progress_callback:
                progress_callback(stats["messages_processed"], len(message_ids))

            # Busca mensagem completa
            msg_data = self.client.fetch_message(msg_id)
            
            if not msg_data or not msg_data.get("attachments"):
                stats["messages_processed"] += 1
                continue

            attachments = msg_data["attachments"]
            stats["attachments_found"] += len(attachments)

            # Baixa cada anexo
            for idx, attachment in enumerate(attachments):
                filename = attachment.get("filename", f"anexo_{msg_id}_{idx}")
                success, result = self.download_single(msg_id, idx, filename)

                if success:
                    stats["attachments_downloaded"] += 1
                else:
                    stats["errors"].append(f"{filename}: {result}")

            stats["messages_processed"] += 1

        return stats
