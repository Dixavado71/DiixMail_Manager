"""Downloader de anexos de e-mail."""

import os
from pathlib import Path
from typing import Optional
from datetime import datetime

from ..email.parser import EmailParser


class AttachmentDownloader:
    """Classe para gerenciar download de anexos de e-mails."""

    def __init__(self, base_download_dir: Path):
        """
        Inicializa o downloader de anexos.

        Args:
            base_download_dir: Diretório base para downloads
        """
        self.base_dir = base_download_dir
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def download_attachment(
        self,
        attachment: dict,
        sender_email: str = "",
        subject: str = "",
        date: Optional[datetime] = None,
        organize_by: Optional[str] = None,
    ) -> tuple[bool, str]:
        """
        Baixa um anexo individual.

        Args:
            attachment: Dicionário com informações do anexo (filename, payload, etc.)
            sender_email: E-mail do remetente (para organização opcional)
            subject: Assunto do e-mail (para organização opcional)
            date: Data do e-mail (para organização opcional)
            organize_by: Critério de organização ('sender', 'subject', 'date', None)

        Returns:
            Tuple[bool, str]: (sucesso, caminho do arquivo ou mensagem de erro)
        """
        filename = attachment.get("filename", "anexo_sem_nome")
        payload = attachment.get("payload")

        if not payload:
            return False, "Anexo sem conteúdo"

        # Sanitiza o nome do arquivo
        filename = EmailParser.sanitize_filename(filename)

        # Determina o diretório de destino
        dest_dir = self.base_dir

        if organize_by:
            if organize_by == "sender" and sender_email:
                # Usa apenas a parte antes do @
                sender_name = sender_email.split("@")[0]
                dest_dir = self.base_dir / f"remetentes/{sender_name}"

            elif organize_by == "subject" and subject:
                # Limpa e usa o assunto como nome da pasta
                clean_subject = EmailParser.clean_subject(subject)
                # Usa apenas as primeiras 50 chars e remove caracteres inválidos
                folder_name = EmailParser.sanitize_filename(clean_subject[:50])
                dest_dir = self.base_dir / f"assuntos/{folder_name}"

            elif organize_by == "date" and date:
                # Organiza por ano/mês
                year_month = date.strftime("%Y-%m")
                dest_dir = self.base_dir / f"data/{year_month}"

        # Cria o diretório se necessário
        dest_dir.mkdir(parents=True, exist_ok=True)

        # Gera caminho completo
        file_path = dest_dir / filename

        # Evita sobrescrever arquivos existentes
        if file_path.exists():
            file_path = self._get_unique_path(file_path)

        try:
            # Escreve o arquivo
            with open(file_path, "wb") as f:
                f.write(payload)

            return True, str(file_path)

        except Exception as e:
            return False, f"Erro ao salvar arquivo: {e}"

    def download_attachments_from_messages(
        self,
        messages: list[dict],
        organize_by: Optional[str] = None,
        progress_callback=None,
    ) -> dict:
        """
        Baixa anexos de múltiplas mensagens.

        Args:
            messages: Lista de dicionários de mensagens completas
            organize_by: Critério de organização ('sender', 'subject', 'date', None)
            progress_callback: Função opcional para reportar progresso

        Returns:
            dict: Estatísticas do download
        """
        stats = {
            "messages_processed": 0,
            "attachments_found": 0,
            "downloads_success": 0,
            "downloads_failed": 0,
            "files_saved": [],
            "errors": [],
        }

        for msg in messages:
            stats["messages_processed"] += 1

            attachments = msg.get("attachments", [])
            if not attachments:
                continue

            sender_email = msg.get("from_email", "")
            subject = msg.get("subject", "")
            date = msg.get("date_obj")

            for attachment in attachments:
                stats["attachments_found"] += 1

                success, result = self.download_attachment(
                    attachment=attachment,
                    sender_email=sender_email,
                    subject=subject,
                    date=date,
                    organize_by=organize_by,
                )

                if success:
                    stats["downloads_success"] += 1
                    stats["files_saved"].append(result)
                else:
                    stats["downloads_failed"] += 1
                    stats["errors"].append(f"{attachment.get('filename', 'unknown')}: {result}")

                # Reporta progresso se callback fornecido
                if progress_callback:
                    progress_callback(stats)

        return stats

    def _get_unique_path(self, file_path: Path) -> Path:
        """
        Gera um caminho único para um arquivo que já existe.

        Args:
            file_path: Caminho original do arquivo

        Returns:
            Path: Novo caminho com sufixo numérico
        """
        if not file_path.exists():
            return file_path

        stem = file_path.stem
        suffix = file_path.suffix
        parent = file_path.parent

        counter = 1
        while True:
            new_path = parent / f"{stem}_{counter}{suffix}"
            if not new_path.exists():
                return new_path
            counter += 1

            # Segurança: limite de 999 iterações
            if counter > 999:
                # Gera nome com timestamp
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                return parent / f"{stem}_{timestamp}{suffix}"

    def get_download_stats(self) -> dict:
        """
        Obtém estatísticas sobre os arquivos na pasta de downloads.

        Returns:
            dict: Estatísticas dos downloads
        """
        stats = {
            "total_files": 0,
            "total_size": 0,
            "by_extension": {},
            "by_folder": {},
        }

        if not self.base_dir.exists():
            return stats

        # Conta arquivos no diretório base e subdiretórios
        for file_path in self.base_dir.rglob("*"):
            if file_path.is_file():
                stats["total_files"] += 1
                stats["total_size"] += file_path.stat().st_size

                # Conta por extensão
                ext = file_path.suffix.lower() or ".sem_extensao"
                stats["by_extension"][ext] = stats["by_extension"].get(ext, 0) + 1

                # Conta por pasta imediata
                try:
                    relative = file_path.relative_to(self.base_dir)
                    if len(relative.parts) > 1:
                        folder = relative.parts[0]
                    else:
                        folder = "(raiz)"
                    stats["by_folder"][folder] = stats["by_folder"].get(folder, 0) + 1
                except ValueError:
                    pass

        return stats

    def clear_downloads(self, keep_folders: bool = False) -> int:
        """
        Limpa todos os arquivos baixados.

        Args:
            keep_folders: Se True, mantém a estrutura de pastas

        Returns:
            int: Número de arquivos removidos
        """
        removed_count = 0

        if not self.base_dir.exists():
            return 0

        if keep_folders:
            # Remove apenas arquivos, mantém pastas
            for file_path in self.base_dir.rglob("*"):
                if file_path.is_file():
                    try:
                        file_path.unlink()
                        removed_count += 1
                    except Exception:
                        pass
        else:
            # Remove tudo
            try:
                import shutil
                shutil.rmtree(self.base_dir)
                removed_count = -1  # Indica remoção completa
            except Exception:
                pass

            # Recria o diretório base vazio
            self.base_dir.mkdir(parents=True, exist_ok=True)

        return removed_count
