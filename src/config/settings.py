"""Configurações da aplicação carregadas do arquivo .env."""

import os
from pathlib import Path
from dotenv import load_dotenv


class Settings:
    """Configurações da aplicação."""

    def __init__(self):
        """Inicializa as configurações."""
        self.gmail_email: str = ""
        self.gmail_app_password: str = ""
        self.download_dir: Path = Path("downloads")
        self.imap_server: str = "imap.gmail.com"
        self.imap_port: int = 993
        self._loaded: bool = False

    def load(self, env_path: Path | None = None) -> bool:
        """
        Carrega as configurações do arquivo .env.

        Args:
            env_path: Caminho para o arquivo .env. Se None, usa o padrão.

        Returns:
            True se carregado com sucesso, False caso contrário.
        """
        if self._loaded:
            return True

        if env_path is None:
            env_path = Path(".") / ".env"

        if env_path.exists():
            load_dotenv(env_path)
        else:
            load_dotenv()

        self.gmail_email = os.getenv("GMAIL_EMAIL", "").strip()
        self.gmail_app_password = os.getenv("GMAIL_APP_PASSWORD", "").strip()
        
        download_dir_str = os.getenv("DOWNLOAD_DIR", "downloads").strip()
        self.download_dir = Path(download_dir_str)

        self._loaded = True
        return self.validate()

    def validate(self) -> bool:
        """
        Valida as configurações carregadas.

        Returns:
            True se todas as configurações forem válidas.
        """
        if not self.gmail_email:
            return False
        if not self.gmail_app_password:
            return False
        if "@" not in self.gmail_email:
            return False
        
        self.download_dir.mkdir(parents=True, exist_ok=True)
        return True

    def is_valid(self) -> bool:
        """Verifica se as configurações são válidas."""
        return bool(self.gmail_email and self.gmail_app_password)


_settings_instance: Settings | None = None


def load_settings(env_path: Path | None = None) -> Settings:
    """
    Carrega e retorna as configurações da aplicação.

    Args:
        env_path: Caminho opcional para o arquivo .env.

    Returns:
        Instância de Settings configurada.
    """
    global _settings_instance
    _settings_instance = Settings()
    _settings_instance.load(env_path)
    return _settings_instance


def get_settings() -> Settings:
    """
    Retorna a instância de configurações.

    Returns:
        Instância de Settings.

    Raises:
        RuntimeError: Se as configurações não foram carregadas.
    """
    if _settings_instance is None:
        raise RuntimeError("Configurações não carregadas. Chame load_settings() primeiro.")
    return _settings_instance
