"""Cliente IMAP para conexão com Gmail."""

import imaplib
import email
from typing import Optional
from datetime import datetime

from src.config.settings import Settings


class IMAPClient:
    """Cliente IMAP para gerenciar conexão com Gmail."""

    def __init__(self, settings: Settings):
        """Inicializa o cliente IMAP.

        Args:
            settings: Configurações da aplicação.
        """
        self.settings = settings
        self.connection: Optional[imaplib.IMAP4_SSL] = None
        self.selected_folder: Optional[str] = None
        self.total_messages: int = 0

    def connect(self) -> bool:
        """Estabelece conexão com o servidor IMAP.

        Returns:
            True se conectado com sucesso, False caso contrário.
        """
        try:
            self.connection = imaplib.IMAP4_SSL(
                self.settings.imap_server,
                self.settings.imap_port
            )
            self.connection.login(
                self.settings.gmail_email,
                self.settings.gmail_app_password
            )
            return True
        except imaplib.IMAP4.error as e:
            error_msg = str(e).lower()
            if "authentication" in error_msg or "invalid" in error_msg:
                raise ConnectionError(
                    "Falha na autenticação. Verifique seu e-mail e senha de app."
                ) from e
            raise ConnectionError(f"Erro de conexão IMAP: {e}") from e
        except Exception as e:
            raise ConnectionError(f"Erro ao conectar: {e}") from e

    def disconnect(self) -> None:
        """Fecha a conexão com o servidor."""
        if self.connection:
            try:
                self.connection.logout()
            except Exception:
                pass
            finally:
                self.connection = None
                self.selected_folder = None

    def reconnect(self) -> bool:
        """Tenta reconectar ao servidor.

        Returns:
            True se reconectado com sucesso.
        """
        self.disconnect()
        return self.connect()

    def select_folder(self, folder: str = "INBOX") -> int:
        """Seleciona uma pasta/marcador.

        Args:
            folder: Nome da pasta (padrão: INBOX).

        Returns:
            Número total de mensagens na pasta.
        """
        if not self.connection:
            raise ConnectionError("Não conectado ao servidor")

        try:
            # Tenta selecionar a pasta
            status, data = self.connection.select(folder)
            
            if status != "OK":
                raise ValueError(f"Pasta '{folder}' não encontrada")
            
            self.selected_folder = folder
            
            # Extrai o número de mensagens
            self.total_messages = int(data[0].decode() if data[0] else 0)
            return self.total_messages
            
        except imaplib.IMAP4.error as e:
            raise ValueError(f"Erro ao selecionar pasta '{folder}': {e}") from e

    def search(self, criteria: str = "ALL") -> list[str]:
        """Busca mensagens na pasta selecionada.

        Args:
            criteria: Critério de busca IMAP (padrão: ALL).

        Returns:
            Lista de IDs das mensagens encontradas.
        """
        if not self.connection:
            raise ConnectionError("Não conectado ao servidor")

        try:
            # Usa unpacking flexível para lidar com diferentes respostas
            status, *data = self.connection.search(None, criteria)
            
            if status != "OK":
                return []
            
            # Processa dados retornados
            ids = []
            for item in data:
                if item is None:
                    continue
                if isinstance(item, bytes):
                    ids.extend(item.decode().split())
                elif isinstance(item, str):
                    ids.extend(item.split())
            
            return ids
            
        except imaplib.IMAP4.error as e:
            # Fallback: tenta busca alternativa
            try:
                status, data = self.connection.search(None, "1:*")
                if status == "OK" and data[0]:
                    return data[0].decode().split()
            except Exception:
                pass
            raise ValueError(f"Erro na busca: {e}") from e

    def fetch_headers(self, message_ids: list[str], count: int = 20) -> list[dict]:
        """Busca headers de mensagens específicas.

        Args:
            message_ids: Lista de IDs das mensagens.
            count: Número máximo de mensagens para buscar.

        Returns:
            Lista de dicionários com headers das mensagens.
        """
        if not self.connection:
            raise ConnectionError("Não conectado ao servidor")

        messages = []
        
        # Pega apenas as últimas 'count' mensagens
        ids_to_fetch = message_ids[-count:] if len(message_ids) > count else message_ids
        
        for msg_id in reversed(ids_to_fetch):
            try:
                status, data = self.connection.fetch(msg_id, "(RFC822.HEADER)")
                
                if status != "OK" or not data:
                    continue
                
                # Parse do header
                raw_email = data[0][1]
                msg = email.message_from_bytes(raw_email)
                
                # Extrai informações
                subject = self._decode_header(msg.get("Subject", "Sem assunto"))
                from_addr = self._decode_header(msg.get("From", "Desconhecido"))
                date_str = msg.get("Date", "")
                
                # Formata data
                try:
                    date_obj = email.utils.parsedate_to_datetime(date_str)
                    date_formatted = date_obj.strftime("%d/%m/%Y %H:%M")
                except Exception:
                    date_formatted = date_str[:20] if date_str else "Data inválida"
                
                # Verifica se tem anexos
                has_attachments = self._check_has_attachments(msg)
                
                # Verifica se é lido
                is_read = self._check_is_read(msg_id)
                
                messages.append({
                    "id": msg_id,
                    "subject": subject,
                    "from": from_addr,
                    "date": date_formatted,
                    "has_attachments": has_attachments,
                    "is_read": is_read,
                })
                
            except Exception as e:
                # Log silencioso para não travar o carregamento
                print(f"[DEBUG] Erro ao buscar mensagem {msg_id}: {e}")
                continue
        
        return messages

    def fetch_message(self, message_id: str) -> Optional[dict]:
        """Busca uma mensagem completa.

        Args:
            message_id: ID da mensagem.

        Returns:
            Dicionário com dados completos da mensagem ou None.
        """
        if not self.connection:
            raise ConnectionError("Não conectado ao servidor")

        try:
            status, data = self.connection.fetch(message_id, "(RFC822)")
            
            if status != "OK" or not data:
                return None
            
            raw_email = data[0][1]
            msg = email.message_from_bytes(raw_email)
            
            # Extrai headers
            subject = self._decode_header(msg.get("Subject", "Sem assunto"))
            from_addr = self._decode_header(msg.get("From", "Desconhecido"))
            to_addr = self._decode_header(msg.get("To", ""))
            date_str = msg.get("Date", "")
            
            try:
                date_obj = email.utils.parsedate_to_datetime(date_str)
                date_formatted = date_obj.strftime("%d/%m/%Y %H:%M:%S")
            except Exception:
                date_formatted = date_str
            
            # Extrai corpo
            body_plain, body_html = self._extract_body(msg)
            
            # Extrai anexos
            attachments = self._extract_attachments_info(msg)
            
            return {
                "id": message_id,
                "subject": subject,
                "from": from_addr,
                "to": to_addr,
                "date": date_formatted,
                "body_plain": body_plain,
                "body_html": body_html,
                "attachments": attachments,
            }
            
        except Exception as e:
            print(f"[DEBUG] Erro ao buscar mensagem completa {message_id}: {e}")
            return None

    def mark_as_read(self, message_ids: list[str]) -> bool:
        """Marca mensagens como lidas.

        Args:
            message_ids: Lista de IDs das mensagens.

        Returns:
            True se todas foram marcadas.
        """
        if not self.connection:
            return False

        try:
            ids_str = ",".join(message_ids)
            self.connection.store(ids_str, "+FLAGS", "\\Seen")
            return True
        except Exception:
            return False

    def mark_as_unread(self, message_ids: list[str]) -> bool:
        """Marca mensagens como não lidas.

        Args:
            message_ids: Lista de IDs das mensagens.

        Returns:
            True se todas foram marcadas.
        """
        if not self.connection:
            return False

        try:
            ids_str = ",".join(message_ids)
            self.connection.store(ids_str, "-FLAGS", "\\Seen")
            return True
        except Exception:
            return False

    def delete_messages(self, message_ids: list[str]) -> bool:
        """Marca mensagens para exclusão.

        Args:
            message_ids: Lista de IDs das mensagens.

        Returns:
            True se todas foram marcadas.
        """
        if not self.connection:
            return False

        try:
            ids_str = ",".join(message_ids)
            self.connection.store(ids_str, "+FLAGS", "\\Deleted")
            self.connection.expunge()
            return True
        except Exception:
            return False

    def move_messages(self, message_ids: list[str], destination: str) -> bool:
        """Move mensagens para outra pasta.

        Args:
            message_ids: Lista de IDs das mensagens.
            destination: Pasta de destino.

        Returns:
            True se movidas com sucesso.
        """
        if not self.connection:
            return False

        try:
            # Gmail usa COPY + DELETE para mover
            ids_str = ",".join(message_ids)
            
            # Copia para destino
            self.connection.copy(ids_str, destination)
            
            # Marca como deletadas na origem
            self.connection.store(ids_str, "+FLAGS", "\\Deleted")
            self.connection.expunge()
            
            return True
        except Exception:
            return False

    def get_folders(self) -> list[str]:
        """Lista todas as pastas disponíveis.

        Returns:
            Lista de nomes de pastas.
        """
        if not self.connection:
            return []

        try:
            status, data = self.connection.list()
            
            if status != "OK":
                return ["INBOX"]
            
            folders = []
            for item in data:
                if isinstance(item, bytes):
                    # Parse da resposta LIST
                    parts = item.decode().split('"')
                    if len(parts) >= 3:
                        folder_name = parts[-2]
                        # Remove prefixo INBOX. se existir
                        if folder_name and folder_name != "INBOX":
                            folders.append(folder_name)
                        elif folder_name == "INBOX":
                            folders.insert(0, "INBOX")
            
            return folders if folders else ["INBOX"]
            
        except Exception:
            return ["INBOX"]

    def download_attachment(self, message_id: str, attachment_index: int, 
                           save_path: str) -> bool:
        """Baixa um anexo específico.

        Args:
            message_id: ID da mensagem.
            attachment_index: Índice do anexo (0-based).
            save_path: Caminho para salvar o arquivo.

        Returns:
            True se baixado com sucesso.
        """
        if not self.connection:
            return False

        try:
            status, data = self.connection.fetch(message_id, "(RFC822)")
            
            if status != "OK" or not data:
                return False
            
            msg = email.message_from_bytes(data[0][1])
            
            # Encontra o anexo
            attachments = []
            for part in msg.walk():
                if part.get_content_disposition() == "attachment":
                    attachments.append(part)
            
            if attachment_index >= len(attachments):
                return False
            
            part = attachments[attachment_index]
            filename = part.get_filename()
            
            if not filename:
                return False
            
            # Salva arquivo
            payload = part.get_payload(decode=True)
            if payload:
                with open(save_path, "wb") as f:
                    f.write(payload)
                return True
            
            return False
            
        except Exception as e:
            print(f"[DEBUG] Erro ao baixar anexo: {e}")
            return False

    def _decode_header(self, header: str) -> str:
        """Decodifica header MIME.

        Args:
            header: String do header.

        Returns:
            Header decodificado.
        """
        if not header:
            return ""
        
        decoded_parts = email.header.decode_header(header)
        result = []
        
        for text, encoding in decoded_parts:
            if isinstance(text, bytes):
                try:
                    result.append(text.decode(encoding or "utf-8"))
                except UnicodeDecodeError:
                    try:
                        result.append(text.decode("latin-1"))
                    except Exception:
                        result.append(text.decode("utf-8", errors="replace"))
            else:
                result.append(text)
        
        return "".join(result)

    def _check_has_attachments(self, msg) -> bool:
        """Verifica se mensagem tem anexos."""
        for part in msg.walk():
            if part.get_content_disposition() == "attachment":
                return True
        return False

    def _check_is_read(self, message_id: str) -> bool:
        """Verifica se mensagem foi lida."""
        if not self.connection:
            return False
        
        try:
            status, data = self.connection.fetch(message_id, "(FLAGS)")
            if status == "OK" and data:
                flags = data[0][1].decode()
                return "\\Seen" in flags
        except Exception:
            pass
        return False

    def _extract_body(self, msg) -> tuple[str, str]:
        """Extrai corpo do e-mail.

        Returns:
            Tupla (body_plain, body_html).
        """
        body_plain = ""
        body_html = ""
        
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get_content_disposition() or "")
                
                # Ignora anexos
                if "attachment" in content_disposition:
                    continue
                
                try:
                    payload = part.get_payload(decode=True)
                    if payload:
                        if content_type == "text/plain":
                            body_plain += payload.decode(
                                part.get_content_charset() or "utf-8",
                                errors="replace"
                            )
                        elif content_type == "text/html":
                            body_html += payload.decode(
                                part.get_content_charset() or "utf-8",
                                errors="replace"
                            )
                except Exception:
                    continue
        else:
            try:
                payload = msg.get_payload(decode=True)
                if payload:
                    if msg.get_content_type() == "text/html":
                        body_html = payload.decode(
                            msg.get_content_charset() or "utf-8",
                            errors="replace"
                        )
                    else:
                        body_plain = payload.decode(
                            msg.get_content_charset() or "utf-8",
                            errors="replace"
                        )
            except Exception:
                pass
        
        return body_plain, body_html

    def _extract_attachments_info(self, msg) -> list[dict]:
        """Extrai informações sobre anexos.

        Returns:
            Lista de dicionários com info dos anexos.
        """
        attachments = []
        
        for part in msg.walk():
            if part.get_content_disposition() == "attachment":
                filename = part.get_filename()
                if filename:
                    size = len(part.get_payload(decode=True) or b"")
                    attachments.append({
                        "filename": filename,
                        "size": size,
                        "content_type": part.get_content_type(),
                    })
        
        return attachments
