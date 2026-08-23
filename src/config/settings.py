"""Configurações da aplicação."""

import os
from pathlib import Path
from dotenv import load_dotenv


class Settings:
    """Configurações do Gmail Manager."""

    def __init__(self):
        """Inicializa as configurações."""
        # Carrega variáveis de ambiente do arquivo .env
        load_dotenv()

        self.gmail_email = os.getenv("GMAIL_EMAIL", "")
        self.gmail_app_password = os.getenv("GMAIL_APP_PASSWORD", "")
        self.download_dir = os.getenv("DOWNLOAD_DIR", "downloads")

        # Configurações IMAP
        self.imap_server = "imap.gmail.com"
        self.imap_port = 993

        # Valida configurações
        self._validate()

    def _validate(self) -> None:
        """Valida as configurações obrigatórias."""
        if not self.gmail_email or "@" not in self.gmail_email:
            raise ValueError(
                "GMAIL_EMAIL inválido. Configure no arquivo .env"
            )
        if not self.gmail_app_password:
            raise ValueError(
                "GMAIL_APP_PASSWORD não configurada. Configure no arquivo .env"
            )

    @property
    def download_path(self) -> Path:
        """Retorna o caminho absoluto para a pasta de downloads."""
        base_dir = Path(__file__).parent.parent.parent
        path = base_dir / self.download_dir
        path.mkdir(parents=True, exist_ok=True)
        return path


# Singleton
_settings: Settings | None = None


def get_settings() -> Settings:
    """Retorna a instância única de configurações."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
