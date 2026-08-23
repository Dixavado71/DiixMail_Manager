"""Parser para processamento de e-mails."""

import re
from html import unescape


class EmailParser:
    """Utilitários para parse de e-mails."""

    @staticmethod
    def html_to_text(html: str) -> str:
        """Converte HTML para texto simples.

        Args:
            html: Conteúdo HTML.

        Returns:
            Conteúdo em texto simples.
        """
        if not html:
            return ""

        # Remove scripts e styles
        html = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL | re.IGNORECASE)
        html = re.sub(r"<style[^>]*>.*?</style>", "", html, flags=re.DOTALL | re.IGNORECASE)

        # Substitui tags comuns
        html = re.sub(r"<br\s*/?>", "\n", html, flags=re.IGNORECASE)
        html = re.sub(r"</p>", "\n\n", html, flags=re.IGNORECASE)
        html = re.sub(r"</div>", "\n", html, flags=re.IGNORECASE)
        html = re.sub(r"</h[1-6]>", "\n\n", html, flags=re.IGNORECASE)

        # Remove todas as outras tags
        html = re.sub(r"<[^>]+>", "", html)

        # Decodifica entidades HTML
        text = unescape(html)

        # Limpa espaços extras
        text = re.sub(r"\n\s*\n", "\n\n", text)
        text = text.strip()

        return text

    @staticmethod
    def format_size(size_bytes: int) -> str:
        """Formata tamanho de arquivo.

        Args:
            size_bytes: Tamanho em bytes.

        Returns:
            String formatada (KB, MB, etc).
        """
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
        else:
            return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Limpa nome de arquivo para salvar.

        Args:
            filename: Nome original.

        Returns:
            Nome seguro para filesystem.
        """
        # Remove caracteres inválidos
        filename = re.sub(r'[<>:"/\\|?*]', "_", filename)
        
        # Remove espaços no início/fim
        filename = filename.strip()
        
        # Limita tamanho
        if len(filename) > 200:
            name, ext = filename.rsplit(".", 1) if "." in filename else (filename, "")
            filename = f"{name[:195]}.{ext}" if ext else filename[:200]
        
        return filename or "arquivo_sem_nome"
