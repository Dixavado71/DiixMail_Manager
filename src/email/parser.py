"""Parser de e-mails para extração de conteúdo."""

import re
from html import unescape
from typing import Optional


class EmailParser:
    """Classe utilitária para parsear e processar conteúdo de e-mails."""

    @staticmethod
    def html_to_text(html: str) -> str:
        """
        Converte HTML simples para texto plano.

        Nota: Esta é uma conversão básica e segura, sem executar JavaScript.

        Args:
            html: Conteúdo HTML

        Returns:
            str: Conteúdo em texto plano
        """
        if not html:
            return ""

        text = html

        # Remove scripts e styles (segurança)
        text = re.sub(r"<script[^>]*>.*?</script>", "", text, flags=re.IGNORECASE | re.DOTALL)
        text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.IGNORECASE | re.DOTALL)

        # Remove comentários HTML
        text = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)

        # Substitui tags de bloco por quebras de linha
        block_tags = ["<p>", "<div>", "<br>", "<br/>", "<br />", "</p>", "</div>"]
        for tag in block_tags:
            text = text.replace(tag, "\n")

        # Remove todas as outras tags HTML
        text = re.sub(r"<[^>]+>", "", text)

        # Decodifica entidades HTML
        text = unescape(text)

        # Normaliza espaços em branco
        text = re.sub(r"\s+", " ", text)

        # Remove espaços extras no início/fim de cada linha
        lines = [line.strip() for line in text.split("\n")]
        text = "\n".join(lines)

        # Remove linhas vazias consecutivas
        text = re.sub(r"\n\s*\n", "\n\n", text)

        return text.strip()

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """
        Sanitiza um nome de arquivo para evitar problemas no sistema.

        Args:
            filename: Nome original do arquivo

        Returns:
            str: Nome sanitizado
        """
        if not filename:
            return "anexo_sem_nome"

        # Remove caracteres inválidos para nomes de arquivo
        invalid_chars = r'[<>:"/\\|？*]'
        filename = re.sub(invalid_chars, "_", filename)

        # Remove espaços no início/fim
        filename = filename.strip()

        # Limita tamanho máximo (255 caracteres é o limite comum)
        if len(filename) > 255:
            name, ext = filename.rsplit(".", 1) if "." in filename else (filename, "")
            max_name_len = 255 - len(ext) - 1 if ext else 250
            filename = f"{name[:max_name_len]}.{ext}" if ext else filename[:max_name_len]

        return filename or "anexo_sem_nome"

    @staticmethod
    def format_size(size_bytes: int) -> str:
        """
        Formata um tamanho em bytes para uma string legível.

        Args:
            size_bytes: Tamanho em bytes

        Returns:
            str: Tamanho formatado (ex: "1.5 MB")
        """
        if size_bytes < 0:
            return "0 B"

        units = ["B", "KB", "MB", "GB", "TB"]
        unit_index = 0
        size = float(size_bytes)

        while size >= 1024 and unit_index < len(units) - 1:
            size /= 1024
            unit_index += 1

        if unit_index == 0:
            return f"{int(size)} {units[unit_index]}"
        else:
            return f"{size:.1f} {units[unit_index]}"

    @staticmethod
    def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
        """
        Trunca um texto se exceder um comprimento máximo.

        Args:
            text: Texto a truncar
            max_length: Comprimento máximo
            suffix: Sufixo a adicionar se truncado

        Returns:
            str: Texto truncado ou original
        """
        if not text or len(text) <= max_length:
            return text or ""

        return text[:max_length - len(suffix)] + suffix

    @staticmethod
    def extract_email_addresses(text: str) -> list[str]:
        """
        Extrai endereços de e-mail de um texto.

        Args:
            text: Texto contendo e-mails

        Returns:
            List[str]: Lista de e-mails encontrados
        """
        pattern = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
        return re.findall(pattern, text)

    @staticmethod
    def is_valid_email(email: str) -> bool:
        """
        Verifica se uma string é um e-mail válido.

        Args:
            email: String a verificar

        Returns:
            bool: True se for um e-mail válido
        """
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        return bool(re.match(pattern, email))

    @staticmethod
    def clean_subject(subject: str) -> str:
        """
        Limpa um assunto de e-mail removendo prefixos comuns.

        Args:
            subject: Assunto original

        Returns:
            str: Assunto limpo
        """
        if not subject:
            return ""

        # Remove prefixos comuns de reply/forward
        prefixes = [
            r"^(Re:|RE:|R:)\s*",
            r"^(Fwd:|Fw:|FW:|Forwarded:)\s*",
            r"^(Encaminhamento:|Enc:)\s*",
            r"^(Resposta:|Resp:)\s*",
        ]

        cleaned = subject
        for prefix in prefixes:
            cleaned = re.sub(prefix, "", cleaned, flags=re.IGNORECASE)

        return cleaned.strip()

    @staticmethod
    def get_content_preview(content: str, max_lines: int = 10, max_chars: int = 500) -> str:
        """
        Obtém uma prévia do conteúdo de um e-mail.

        Args:
            content: Conteúdo completo
            max_lines: Número máximo de linhas
            max_chars: Número máximo de caracteres

        Returns:
            str: Prévia do conteúdo
        """
        if not content:
            return ""

        lines = content.split("\n")

        # Limita número de linhas
        if len(lines) > max_lines:
            lines = lines[:max_lines]
            lines.append("...")

        preview = "\n".join(lines)

        # Limita número de caracteres
        if len(preview) > max_chars:
            preview = preview[:max_chars - 3] + "..."

        return preview
