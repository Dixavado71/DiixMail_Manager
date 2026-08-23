"""Gerenciamento de mensagens de e-mail."""

from email import message_from_bytes
from email.header import decode_header, make_header
from email.utils import parsedate_to_datetime, parseaddr
from datetime import datetime
from typing import Optional

from .client import IMAPClient


class MessageManager:
    """Classe para gerenciar operações com mensagens de e-mail."""

    def __init__(self, imap_client: IMAPClient):
        """
        Inicializa o gerenciador de mensagens.

        Args:
            imap_client: Instância do cliente IMAP
        """
        self.imap_client = imap_client

    def get_message_headers(self, message_id: str) -> Optional[dict]:
        """
        Obtém apenas os cabeçalhos de uma mensagem (metadados).

        Args:
            message_id: ID da mensagem

        Returns:
            dict ou None: Metadados da mensagem ou None se falhar
        """
        success, data = self.imap_client.fetch(message_id, "(RFC822.HEADER)")

        if not success or not data:
            # Tenta abordagem alternativa com UID FETCH
            try:
                conn = self.imap_client.get_connection()
                if conn and self.imap_client.is_connected:
                    status, msg_data = conn.uid('FETCH', message_id, '(RFC822.HEADER)')
                    if status == 'OK' and msg_data:
                        data = msg_data[0][1]
                    else:
                        return None
            except Exception:
                return None

        try:
            msg = message_from_bytes(data)

            # Extrai remetente
            from_raw = msg.get("From", "Desconhecido")
            from_name, from_email = parseaddr(from_raw)

            # Extrai destinatário
            to_raw = msg.get("To", "")
            to_name, to_email = parseaddr(to_raw)

            # Extrai assunto
            subject_raw = msg.get("Subject", "Sem assunto")
            subject = str(make_header(decode_header(subject_raw)))

            # Extrai data
            date_raw = msg.get("Date", "")
            date_obj = None
            date_str = "Data desconhecida"

            if date_raw:
                try:
                    date_obj = parsedate_to_datetime(date_raw)
                    date_str = date_obj.strftime("%d/%m/%Y %H:%M")
                except Exception:
                    date_str = date_raw[:25] if len(date_raw) > 25 else date_raw

            # Verifica status (lido/não lido) - verifica flags do Gmail
            flags_raw = msg.get("X-Gmail-Labels", "")
            is_read = "\\Seen" in str(data) or "Seen" in flags_raw or "\\Seen" in flags_raw

            # Conta anexos
            attachment_count = self._count_attachments(msg)

            return {
                "id": message_id,
                "from_name": from_name or from_email or "Desconhecido",
                "from_email": from_email or "unknown@example.com",
                "to_name": to_name or to_email,
                "to_email": to_email,
                "subject": subject or "Sem assunto",
                "date_str": date_str,
                "date_obj": date_obj,
                "is_read": is_read,
                "attachment_count": attachment_count,
                "flags": flags_raw,
            }

        except Exception as e:
            print(f"[DEBUG] Erro ao processar mensagem {message_id}: {e}")
            return None

    def get_full_message(self, message_id: str) -> Optional[dict]:
        """
        Obtém uma mensagem completa com conteúdo.

        Args:
            message_id: ID da mensagem

        Returns:
            dict ou None: Mensagem completa ou None se falhar
        """
        success, data = self.imap_client.fetch(message_id, "(RFC822)")

        if not success or not data:
            return None

        try:
            msg = message_from_bytes(data)
            headers = self.get_message_headers(message_id)

            if not headers:
                return None

            # Extrai conteúdo do e-mail
            body_plain = ""
            body_html = ""

            if msg.is_multipart():
                for part in msg.walk():
                    content_type = part.get_content_type()
                    content_disposition = str(part.get_content_disposition())

                    # Ignora anexos
                    if "attachment" in content_disposition:
                        continue

                    try:
                        payload = part.get_payload(decode=True)
                        if payload:
                            if content_type == "text/plain":
                                charset = part.get_content_charset() or "utf-8"
                                body_plain += payload.decode(charset, errors="ignore")
                            elif content_type == "text/html":
                                charset = part.get_content_charset() or "utf-8"
                                body_html += payload.decode(charset, errors="ignore")
                    except Exception:
                        continue
            else:
                # Mensagem não multipart
                try:
                    payload = msg.get_payload(decode=True)
                    if payload:
                        charset = msg.get_content_charset() or "utf-8"
                        body_plain = payload.decode(charset, errors="ignore")
                except Exception:
                    body_plain = str(msg.get_payload())

            # Extrai lista de anexos
            attachments = self._get_attachments_list(msg)

            return {
                **headers,
                "body_plain": body_plain,
                "body_html": body_html,
                "attachments": attachments,
                "raw_message": data,
            }

        except Exception:
            return None

    def _count_attachments(self, msg) -> int:
        """
        Conta o número de anexos em uma mensagem.

        Args:
            msg: Objeto Message

        Returns:
            int: Número de anexos
        """
        count = 0

        if msg.is_multipart():
            for part in msg.walk():
                content_disposition = str(part.get_content_disposition())
                if "attachment" in content_disposition:
                    count += 1
        else:
            content_disposition = str(msg.get_content_disposition())
            if "attachment" in content_disposition:
                count = 1

        return count

    def _get_attachments_list(self, msg) -> list[dict]:
        """
        Obtém lista de anexos com informações.

        Args:
            msg: Objeto Message

        Returns:
            List[dict]: Lista de dicionários com informações dos anexos
        """
        attachments = []

        if msg.is_multipart():
            for idx, part in enumerate(msg.walk()):
                content_disposition = str(part.get_content_disposition())

                if "attachment" in content_disposition:
                    filename = part.get_filename()

                    if not filename:
                        # Tenta obter nome alternativo
                        filename = part.get_param("name", header="content-disposition")

                    if not filename:
                        filename = f"anexo_{idx + 1}"

                    # Decodifica nome do arquivo se necessário
                    if filename:
                        try:
                            decoded = decode_header(filename)
                            filename = str(make_header(decoded))
                        except Exception:
                            pass

                    # Obtém tamanho aproximado
                    payload = part.get_payload(decode=True)
                    size = len(payload) if payload else 0

                    # Obtém tipo de conteúdo
                    content_type = part.get_content_type()

                    attachments.append({
                        "index": len(attachments),
                        "filename": filename,
                        "size": size,
                        "content_type": content_type,
                        "payload": payload,
                    })

        return attachments

    def get_messages_summary(self, message_ids: list[str], limit: int = 50) -> list[dict]:
        """
        Obtém resumo de múltiplas mensagens (apenas metadados).

        Args:
            message_ids: Lista de IDs das mensagens
            limit: Limite máximo de mensagens a retornar

        Returns:
            List[dict]: Lista de resumos de mensagens
        """
        summaries = []

        # Ordena IDs em ordem decrescente (mais recentes primeiro)
        sorted_ids = sorted(message_ids, key=int, reverse=True)

        for msg_id in sorted_ids[:limit]:
            summary = self.get_message_headers(msg_id)
            if summary:
                summaries.append(summary)

        return summaries

    def delete_messages(self, message_ids: list[str]) -> tuple[bool, int, list[str]]:
        """
        Marca múltiplas mensagens para exclusão.

        Args:
            message_ids: Lista de IDs das mensagens

        Returns:
            Tuple[bool, int, List[str]]: (sucesso, quantidade excluída, erros)
        """
        errors = []
        deleted_count = 0

        for msg_id in message_ids:
            success, _ = self.imap_client.delete(msg_id)
            if success:
                deleted_count += 1
            else:
                errors.append(msg_id)

        # Executa expunge para remover permanentemente
        if deleted_count > 0:
            self.imap_client.expunge()

        return len(errors) == 0, deleted_count, errors

    def mark_messages_read(self, message_ids: list[str]) -> tuple[bool, str]:
        """
        Marca múltiplas mensagens como lidas.

        Args:
            message_ids: Lista de IDs das mensagens

        Returns:
            Tuple[bool, str]: (sucesso, mensagem)
        """
        return self.imap_client.mark_read(message_ids)

    def mark_messages_unread(self, message_ids: list[str]) -> tuple[bool, str]:
        """
        Marca múltiplas mensagens como não lidas.

        Args:
            message_ids: Lista de IDs das mensagens

        Returns:
            Tuple[bool, str]: (sucesso, mensagem)
        """
        return self.imap_client.mark_unread(message_ids)

    def move_messages(self, message_ids: list[str], destination_folder: str) -> tuple[bool, int, list[str]]:
        """
        Move múltiplas mensagens para outra pasta.

        Args:
            message_ids: Lista de IDs das mensagens
            destination_folder: Pasta de destino

        Returns:
            Tuple[bool, int, List[str]]: (sucesso, quantidade movida, erros)
        """
        errors = []
        moved_count = 0

        for msg_id in message_ids:
            success, _ = self.imap_client.move_message(msg_id, destination_folder)
            if success:
                moved_count += 1
            else:
                errors.append(msg_id)

        return len(errors) == 0, moved_count, errors
