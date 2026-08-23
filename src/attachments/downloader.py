"""Downloader de anexos de e-mail."""

import logging
from pathlib import Path
from typing import Optional
from src.email_parser.parser import Attachment, EmailMessage

logger = logging.getLogger(__name__)


class AttachmentDownloader:
    """Gerencia download de anexos."""

    def __init__(self, download_dir: Path):
        """
        Inicializa o downloader.

        Args:
            download_dir: Diretório base para downloads.
        """
        self.download_dir = download_dir
        self.download_dir.mkdir(parents=True, exist_ok=True)

    def download_attachment(
        self, attachment: Attachment, subfolder: Optional[str] = None
    ) -> Optional[Path]:
        """
        Baixa um anexo específico.

        Args:
            attachment: Anexo para baixar.
            subfolder: Subpasta opcional para organizar.

        Returns:
            Caminho do arquivo baixado ou None se falhar.
        """
        try:
            # Determina diretório de destino
            if subfolder:
                dest_dir = self.download_dir / subfolder
            else:
                dest_dir = self.download_dir
            
            dest_dir.mkdir(parents=True, exist_ok=True)

            # Gera nome único se arquivo já existir
            filename = self._safe_filename(attachment.filename, dest_dir)
            filepath = dest_dir / filename

            # Escreve arquivo
            with open(filepath, "wb") as f:
                f.write(attachment.payload)

            logger.info(f"Anexo baixado: {filepath} ({attachment.size_formatted})")
            return filepath

        except Exception as e:
            logger.error(f"Erro ao baixar anexo {attachment.filename}: {e}")
            return None

    def download_from_message(
        self, message: EmailMessage, subfolder: Optional[str] = None
    ) -> list[Path]:
        """
        Baixa todos os anexos de uma mensagem.

        Args:
            message: Mensagem com anexos.
            subfolder: Subpasta opcional.

        Returns:
            Lista de caminhos dos arquivos baixados.
        """
        if not message.attachments:
            return []

        # Usa assunto como subpasta se não especificado
        if subfolder is None and message.subject:
            safe_subject = self._safe_filename(message.subject, "")[:50]
            if safe_subject:
                subfolder = f"{message.sender_email}_{safe_subject}"

        downloaded = []
        for attachment in message.attachments:
            path = self.download_attachment(attachment, subfolder)
            if path:
                downloaded.append(path)

        return downloaded

    def download_multiple_messages(
        self, messages: list[EmailMessage], organize_by: str = "sender"
    ) -> tuple[int, int]:
        """
        Baixa anexos de múltiplas mensagens.

        Args:
            messages: Lista de mensagens.
            organize_by: Como organizar ("sender", "date", "none").

        Returns:
            Tuple (anexos_encontrados, anexos_baixados).
        """
        total_attachments = 0
        downloaded_count = 0

        for msg in messages:
            total_attachments += len(msg.attachments)
            
            if organize_by == "sender":
                subfolder = msg.sender_email.split("@")[0]
            elif organize_by == "date":
                subfolder = msg.date.strftime("%Y-%m-%d")
            else:
                subfolder = None

            downloaded = self.download_from_message(msg, subfolder)
            downloaded_count += len(downloaded)

        return total_attachments, downloaded_count

    def _safe_filename(self, filename: str, directory: Path | str) -> str:
        """
        Gera nome de arquivo seguro e único.

        Args:
            filename: Nome original.
            directory: Diretório de destino.

        Returns:
            Nome seguro e único.
        """
        from pathlib import Path
        
        # Remove caracteres inválidos
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, "_")
        
        filename = filename.strip()
        if not filename:
            filename = "sem_nome"

        # Verifica se existe e gera variante
        if isinstance(directory, str):
            directory = Path(directory)
            
        base_path = directory / filename
        counter = 1
        
        while base_path.exists():
            stem = base_path.stem
            suffix = base_path.suffix
            base_path = directory / f"{stem}_{counter}{suffix}"
            counter += 1

        return base_path.name
