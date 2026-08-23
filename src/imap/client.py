"""Cliente IMAP para conexão com o Gmail."""

import imaplib
import ssl
from typing import Optional


class IMAPClient:
    """Classe para gerenciar a conexão IMAP com o Gmail."""

    def __init__(self, server: str, port: int):
        """
        Inicializa o cliente IMAP.

        Args:
            server: Servidor IMAP (ex: imap.gmail.com)
            port: Porta IMAP (ex: 993)
        """
        self.server = server
        self.port = port
        self.connection: Optional[imaplib.IMAP4_SSL] = None
        self.is_connected = False

    def connect(self, email: str, password: str) -> tuple[bool, str]:
        """
        Estabelece conexão com o servidor IMAP e faz login.

        Args:
            email: Endereço de e-mail do Gmail
            password: Senha de app do Gmail

        Returns:
            Tuple[bool, str]: (sucesso, mensagem)
        """
        try:
            # Cria conexão SSL
            context = ssl.create_default_context()
            self.connection = imaplib.IMAP4_SSL(self.server, self.port, ssl_context=context)

            # Faz login
            self.connection.login(email, password)
            self.is_connected = True

            return True, "Conectado com sucesso ao Gmail"

        except imaplib.IMAP4.error as e:
            error_msg = str(e)
            if "Authentication failed" in error_msg or "Invalid credentials" in error_msg:
                return False, "Falha na autenticação. Verifique seu e-mail e senha de app."
            elif "Please log in via your web browser" in error_msg:
                return False, "Acesso bloqueado. Verifique se o acesso IMAP está habilitado no Gmail."
            else:
                return False, f"Erro IMAP: {error_msg}"

        except ssl.SSLError as e:
            return False, f"Erro de conexão SSL: {e}"

        except Exception as e:
            return False, f"Erro inesperado: {e}"

    def disconnect(self) -> None:
        """Fecha a conexão IMAP de forma segura."""
        if self.connection:
            try:
                self.connection.logout()
            except Exception:
                pass  # Ignora erros ao desconectar
            finally:
                self.connection = None
                self.is_connected = False

    def reconnect(self, email: str, password: str) -> tuple[bool, str]:
        """
        Reconecta ao servidor IMAP.

        Args:
            email: Endereço de e-mail do Gmail
            password: Senha de app do Gmail

        Returns:
            Tuple[bool, str]: (sucesso, mensagem)
        """
        self.disconnect()
        return self.connect(email, password)

    def select_folder(self, folder_name: str = "INBOX", read_only: bool = False) -> tuple[bool, str, int]:
        """
        Seleciona uma pasta/marcações para operação.

        Args:
            folder_name: Nome da pasta (padrão: INBOX)
            read_only: Se True, abre em modo somente leitura

        Returns:
            Tuple[bool, str, int]: (sucesso, mensagem, número de mensagens)
        """
        if not self.connection or not self.is_connected:
            return False, "Não conectado ao servidor", 0

        try:
            # Codifica o nome da pasta para UTF-7 (padrão IMAP)
            encoded_folder = folder_name.encode("utf-7").decode("utf-7")

            if read_only:
                status, messages = self.connection.examine(encoded_folder)
            else:
                status, messages = self.connection.select(encoded_folder)

            if status == "OK":
                # Gmail pode retornar diferentes formatos
                # Extrai o número de mensagens de forma robusta
                msg_count = 0
                if messages:
                    for msg in messages:
                        if isinstance(msg, bytes):
                            try:
                                msg_count = int(msg.decode())
                                break
                            except (ValueError, UnicodeDecodeError):
                                continue
                        elif isinstance(msg, str):
                            try:
                                msg_count = int(msg)
                                break
                            except ValueError:
                                continue
                
                return True, f"Pasta '{folder_name}' selecionada", msg_count
            else:
                return False, f"Falha ao selecionar pasta: {folder_name}", 0

        except Exception as e:
            return False, f"Erro ao selecionar pasta: {e}", 0

    def search(self, criteria: str) -> tuple[bool, list[str]]:
        """
        Pesquisa e-mails usando critérios IMAP.

        Args:
            criteria: Critério de busca (ex: 'ALL', 'FROM email', 'SUBJECT texto')

        Returns:
            Tuple[bool, List[str]]: (sucesso, lista de IDs das mensagens)
        """
        if not self.connection or not self.is_connected:
            return False, []

        try:
            # Tenta primeiro com o critério original
            status, *data = self.connection.search(None, criteria)

            if status == "OK":
                # Gmail pode retornar diferentes formatos de resposta
                # Extrai os IDs de mensagem de forma robusta
                message_ids = []
                
                for item in data:
                    if item and isinstance(item, bytes):
                        message_ids.extend(item.split())
                    elif item and isinstance(item, list):
                        for sub_item in item:
                            if isinstance(sub_item, bytes):
                                message_ids.extend(sub_item.split())
                
                if message_ids:
                    return True, [msg_id.decode() if isinstance(msg_id, bytes) else msg_id for msg_id in message_ids]
                
                # Se não encontrou, tenta com critério alternativo para Gmail
                # Gmail as vezes requer "1:*" para buscar todas as mensagens
                status2, *data2 = self.connection.search(None, "1:*")
                if status2 == "OK" and data2:
                    message_ids = []
                    for item in data2:
                        if item and isinstance(item, bytes):
                            message_ids.extend(item.split())
                    
                    if message_ids:
                        return True, [msg_id.decode() if isinstance(msg_id, bytes) else msg_id for msg_id in message_ids]
                
                # Tenta buscar mensagens não lidas como fallback
                status3, *data3 = self.connection.search(None, "UNSEEN")
                if status3 == "OK" and data3:
                    message_ids = []
                    for item in data3:
                        if item and isinstance(item, bytes):
                            message_ids.extend(item.split())
                    
                    if message_ids:
                        return True, [msg_id.decode() if isinstance(msg_id, bytes) else msg_id for msg_id in message_ids]
                    
                return True, []  # Retorna lista vazia mas com sucesso
            
            return False, []

        except Exception as e:
            # Em caso de erro, tenta abordagem alternativa com UID SEARCH
            try:
                status, *data = self.connection.uid('SEARCH', 'CHARSET', 'UTF-8', 'ALL')
                if status == "OK" and data:
                    message_ids = []
                    for item in data:
                        if item and isinstance(item, bytes):
                            message_ids.extend(item.split())
                    
                    if message_ids:
                        return True, [msg_id.decode() if isinstance(msg_id, bytes) else msg_id for msg_id in message_ids]
            except Exception:
                pass
            return False, []

    def fetch(self, message_id: str, parts: str = "(RFC822.HEADER RFC822.TEXT)") -> tuple[bool, bytes]:
        """
        Busca uma mensagem específica.

        Args:
            message_id: ID da mensagem
            parts: Partes da mensagem a buscar

        Returns:
            Tuple[bool, bytes]: (sucesso, dados da mensagem)
        """
        if not self.connection or not self.is_connected:
            return False, b""

        try:
            status, data = self.connection.fetch(message_id, parts)

            if status == "OK":
                return True, data[0][1] if data else b""
            else:
                return False, b""

        except Exception:
            return False, b""

    def delete(self, message_id: str) -> tuple[bool, str]:
        """
        Marca uma mensagem para exclusão.

        Args:
            message_id: ID da mensagem

        Returns:
            Tuple[bool, str]: (sucesso, mensagem)
        """
        if not self.connection or not self.is_connected:
            return False, "Não conectado ao servidor"

        try:
            self.connection.store(message_id, "+FLAGS", "\\Deleted")
            return True, f"Mensagem {message_id} marcada para exclusão"
        except Exception as e:
            return False, f"Erro ao marcar exclusão: {e}"

    def expunge(self) -> tuple[bool, int]:
        """
        Remove permanentemente as mensagens marcadas para exclusão.

        Returns:
            Tuple[bool, int]: (sucesso, número de mensagens removidas)
        """
        if not self.connection or not self.is_connected:
            return False, 0

        try:
            status, data = self.connection.expunge()
            if status == "OK":
                return True, len(data) if data else 0
            return False, 0
        except Exception:
            return False, 0

    def mark_read(self, message_ids: list[str]) -> tuple[bool, str]:
        """
        Marca mensagens como lidas.

        Args:
            message_ids: Lista de IDs das mensagens

        Returns:
            Tuple[bool, str]: (sucesso, mensagem)
        """
        if not self.connection or not self.is_connected:
            return False, "Não conectado ao servidor"

        try:
            for msg_id in message_ids:
                self.connection.store(msg_id, "-FLAGS", "\\Seen")
            return True, f"{len(message_ids)} mensagens marcadas como lidas"
        except Exception as e:
            return False, f"Erro ao marcar como lidas: {e}"

    def mark_unread(self, message_ids: list[str]) -> tuple[bool, str]:
        """
        Marca mensagens como não lidas.

        Args:
            message_ids: Lista de IDs das mensagens

        Returns:
            Tuple[bool, str]: (sucesso, mensagem)
        """
        if not self.connection or not self.is_connected:
            return False, "Não conectado ao servidor"

        try:
            for msg_id in message_ids:
                self.connection.store(msg_id, "+FLAGS", "\\Seen")
            return True, f"{len(message_ids)} mensagens marcadas como não lidas"
        except Exception as e:
            return False, f"Erro ao marcar como não lidas: {e}"

    def move_message(self, message_id: str, destination_folder: str) -> tuple[bool, str]:
        """
        Move uma mensagem para outra pasta.

        Args:
            message_id: ID da mensagem
            destination_folder: Pasta de destino

        Returns:
            Tuple[bool, str]: (sucesso, mensagem)
        """
        if not self.connection or not self.is_connected:
            return False, "Não conectado ao servidor"

        try:
            # Copia para a pasta de destino
            encoded_dest = destination_folder.encode("utf-7").decode("utf-7")
            status, data = self.connection.copy(message_id, encoded_dest)

            if status == "OK":
                # Marca para exclusão na pasta atual
                self.connection.store(message_id, "+FLAGS", "\\Deleted")
                self.connection.expunge()
                return True, f"Mensagem movida para {destination_folder}"
            else:
                return False, f"Falha ao copiar mensagem para {destination_folder}"

        except Exception as e:
            return False, f"Erro ao mover mensagem: {e}"

    def get_connection(self) -> Optional[imaplib.IMAP4_SSL]:
        """Retorna a conexão IMAP atual."""
        return self.connection
