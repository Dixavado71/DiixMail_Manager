"""Configurações do aplicativo carregadas do .env."""

import os
from pathlib import Path
from dotenv import load_dotenv


class Settings:
    """Classe para gerenciar configurações do aplicativo."""

    def __init__(self):
        """Inicializa as configurações carregando o arquivo .env."""
        # Carrega o arquivo .env do diretório raiz do projeto
        env_path = Path(__file__).parent.parent.parent / ".env"
        load_dotenv(env_path)

        self.gmail_email = os.getenv("GMAIL_EMAIL", "")
        self.gmail_app_password = os.getenv("GMAIL_APP_PASSWORD", "")
        self.download_dir = os.getenv("DOWNLOAD_DIR", "downloads")

        # Configurações IMAP do Gmail
        self.imap_server = "imap.gmail.com"
        self.imap_port = 993

    def validate(self) -> tuple[bool, str]:
        """
        Valida se as configurações necessárias estão presentes.

        Returns:
            Tuple[bool, str]: (é válido, mensagem de erro ou sucesso)
        """
        if not self.gmail_email:
            return False, "GMAIL_EMAIL não configurado no arquivo .env"

        if not self.gmail_app_password:
            return False, "GMAIL_APP_PASSWORD não configurado no arquivo .env"

        # Validação básica de formato de e-mail
        if "@" not in self.gmail_email or "." not in self.gmail_email:
            return False, "Formato de e-mail inválido em GMAIL_EMAIL"

        if len(self.gmail_app_password) < 8:
            return False, "Senha de app muito curta (deve ter pelo menos 16 caracteres)"

        return True, "Configurações válidas"

    def get_download_path(self) -> Path:
        """
        Obtém o caminho completo para o diretório de downloads.

        Returns:
            Path: Caminho absoluto para o diretório de downloads
        """
        base_path = Path(__file__).parent.parent.parent
        download_path = base_path / self.download_dir
        download_path.mkdir(parents=True, exist_ok=True)
        return download_path
