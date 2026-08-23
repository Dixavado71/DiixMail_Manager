"""Cliente IMAP para conexão com o Gmail."""

import imaplib
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class IMAPClient:
    """Cliente IMAP para gerenciar conexão com o Gmail."""

    def __init__(self, email: str, password: str, server: str = "imap.gmail.com", port: int = 993):
        """
        Inicializa o cliente IMAP.

        Args:
            email: Endereço de e-mail do Gmail.
            password: Senha de app do Gmail.
            server: Servidor IMAP.
            port: Porta IMAP.
        """
        self.email = email
        self.password = password
        self.server = server
        self.port = port
        self.connection: Optional[imaplib.IMAP4_SSL] = None
        self.selected_folder: Optional[str] = None
        self.total_messages: int = 0

    def connect(self) -> bool:
        """
        Estabelece conexão com o servidor IMAP.

        Returns:
            True se conectado com sucesso, False caso contrário.
        """
        try:
            logger.info(f"Conectando a {self.server}:{self.port}...")
            self.connection = imaplib.IMAP4_SSL(self.server, self.port)
            
            logger.info("Autenticando...")
            self.connection.login(self.email, self.password)
            
            logger.info("Autenticação bem-sucedida!")
            return True
            
        except imaplib.IMAP4.error as e:
            logger.error(f"Erro de autenticação IMAP: {e}")
            self.connection = None
            return False
        except Exception as e:
            logger.error(f"Erro ao conectar: {e}")
            self.connection = None
            return False

    def disconnect(self) -> None:
        """Encerra a conexão IMAP."""
        if self.connection:
            try:
                self.connection.logout()
                logger.info("Conexão encerrada.")
            except Exception as e:
                logger.warning(f"Erro ao encerrar conexão: {e}")
            finally:
                self.connection = None
                self.selected_folder = None
                self.total_messages = 0

    def reconnect(self) -> bool:
        """
        Reconecta ao servidor IMAP.

        Returns:
            True se reconectado com sucesso.
        """
        self.disconnect()
        return self.connect()

    def is_connected(self) -> bool:
        """Verifica se há uma conexão ativa."""
        if self.connection is None:
            return False
        
        try:
            self.connection.noop()
            return True
        except Exception:
            return False

    def select_folder(self, folder: str = "INBOX", readonly: bool = True) -> tuple[bool, int]:
        """
        Seleciona uma pasta/marcador.

        Args:
            folder: Nome da pasta.
            readonly: Se True, abre em modo somente leitura.

        Returns:
            Tuple (sucesso, número_de_mensagens).
        """
        if not self.is_connected():
            logger.error("Não há conexão IMAP ativa.")
            return False, 0

        try:
            # Tenta selecionar a pasta
            status, data = self.connection.select(folder, readonly=readonly)
            
            if status == "OK":
                self.selected_folder = folder
                # Extrai o número de mensagens
                msg_count = int(data[0]) if data and data[0] else 0
                self.total_messages = msg_count
                logger.info(f"Pasta {folder} selecionada ({msg_count} mensagens)")
                return True, msg_count
            else:
                logger.warning(f"Falha ao selecionar pasta {folder}: {data}")
                return False, 0
                
        except Exception as e:
            logger.error(f"Erro ao selecionar pasta {folder}: {e}")
            return False, 0

    def search(self, criteria: str = "ALL") -> list[int]:
        """
        Pesquisa mensagens na pasta selecionada.

        Args:
            criteria: Critério de busca IMAP.

        Returns:
            Lista de IDs das mensagens encontradas.
        """
        if not self.is_connected():
            logger.error("Não há conexão IMAP ativa.")
            return []

        if not self.selected_folder:
            logger.error("Nenhuma pasta selecionada.")
            return []

        try:
            # Usa unpacking flexível para lidar com diferentes formatos de resposta
            status, *data = self.connection.search(None, criteria)
            
            if status != "OK":
                logger.warning(f"Busca retornou status: {status}")
                return []

            ids = []
            for item in data:
                if item is None:
                    continue
                if isinstance(item, bytes):
                    # Converte bytes para string e divide
                    id_str = item.decode("utf-8", errors="ignore").strip()
                    if id_str:
                        ids.extend([int(x) for x in id_str.split() if x.strip().isdigit()])
                elif isinstance(item, str):
                    if item.strip():
                        ids.extend([int(x) for x in item.split() if x.strip().isdigit()])

            logger.info(f"Busca '{criteria}' retornou {len(ids)} mensagens")
            return sorted(ids, reverse=True)  # Mais recentes primeiro

        except Exception as e:
            logger.error(f"Erro na busca '{criteria}': {e}")
            # Fallback: tenta buscar todas as mensagens diretamente
            try:
                status, data = self.connection.search(None, "1:*")
                if status == "OK" and data and data[0]:
                    id_str = data[0].decode("utf-8", errors="ignore")
                    ids = [int(x) for x in id_str.split() if x.strip().isdigit()]
                    return sorted(ids, reverse=True)
            except Exception:
                pass
            return []

    def fetch(self, message_id: int, parts: str = "(RFC822.HEADER)") -> Optional[bytes]:
        """
        Busca uma mensagem específica.

        Args:
            message_id: ID da mensagem.
            parts: Partes da mensagem a buscar.

        Returns:
            Dados da mensagem ou None se falhar.
        """
        if not self.is_connected():
            logger.error("Não há conexão IMAP ativa.")
            return None

        try:
            status, data = self.connection.fetch(str(message_id), parts)
            
            if status == "OK" and data:
                # Encontra a parte que contém os dados
                for item in data:
                    if isinstance(item, tuple) and len(item) >= 2:
                        return item[1]
                    elif isinstance(item, bytes):
                        return item
                
                # Se data[0] for tuple
                if data and isinstance(data[0], tuple) and len(data[0]) >= 2:
                    return data[0][1]
                    
            logger.warning(f"Fetch retornou status: {status}")
            return None

        except Exception as e:
            logger.error(f"Erro ao buscar mensagem {message_id}: {e}")
            return None

    def fetch_full(self, message_id: int) -> Optional[bytes]:
        """
        Busca a mensagem completa (headers + corpo).

        Args:
            message_id: ID da mensagem.

        Returns:
            Dados completos da mensagem ou None.
        """
        return self.fetch(message_id, "RFC822")

    def mark_as_read(self, message_ids: list[int]) -> bool:
        """
        Marca mensagens como lidas.

        Args:
            message_ids: Lista de IDs das mensagens.

        Returns:
            True se todas foram marcadas com sucesso.
        """
        if not self.is_connected() or not message_ids:
            return False

        try:
            ids_str = ",".join(str(i) for i in message_ids)
            status, _ = self.connection.store(ids_str, "-FLAGS", "\\Seen")
            success = status == "OK"
            if success:
                logger.info(f"{len(message_ids)} mensagens marcadas como lidas")
            return success
        except Exception as e:
            logger.error(f"Erro ao marcar como lidas: {e}")
            return False

    def mark_as_unread(self, message_ids: list[int]) -> bool:
        """
        Marca mensagens como não lidas.

        Args:
            message_ids: Lista de IDs das mensagens.

        Returns:
            True se todas foram marcadas com sucesso.
        """
        if not self.is_connected() or not message_ids:
            return False

        try:
            ids_str = ",".join(str(i) for i in message_ids)
            status, _ = self.connection.store(ids_str, "+FLAGS", "\\Seen")
            success = status == "OK"
            if success:
                logger.info(f"{len(message_ids)} mensagens marcadas como não lidas")
            return success
        except Exception as e:
            logger.error(f"Erro ao marcar como não lidas: {e}")
            return False

    def delete(self, message_ids: list[int]) -> bool:
        """
        Marca mensagens para exclusão.

        Args:
            message_ids: Lista de IDs das mensagens.

        Returns:
            True se todas foram marcadas com sucesso.
        """
        if not self.is_connected() or not message_ids:
            return False

        try:
            ids_str = ",".join(str(i) for i in message_ids)
            status, _ = self.connection.store(ids_str, "+FLAGS", "\\Deleted")
            success = status == "OK"
            if success:
                logger.info(f"{len(message_ids)} mensagens marcadas para exclusão")
            return success
        except Exception as e:
            logger.error(f"Erro ao marcar para exclusão: {e}")
            return False

    def expunge(self) -> bool:
        """
        Remove permanentemente as mensagens marcadas para exclusão.

        Returns:
            True se executado com sucesso.
        """
        if not self.is_connected():
            return False

        try:
            status, _ = self.connection.expunge()
            success = status == "OK"
            if success:
                logger.info("Mensagens excluídas permanentemente")
            return success
        except Exception as e:
            logger.error(f"Erro ao expungir: {e}")
            return False

    def move_to_folder(self, message_ids: list[int], folder: str) -> bool:
        """
        Move mensagens para outra pasta.

        Args:
            message_ids: Lista de IDs das mensagens.
            folder: Pasta de destino.

        Returns:
            True se movido com sucesso.
        """
        if not self.is_connected() or not message_ids:
            return False

        try:
            ids_str = ",".join(str(i) for i in message_ids)
            # Tenta usar COPY seguido de DELETE (método compatível)
            status, _ = self.connection.copy(ids_str, folder)
            if status == "OK":
                # Marca as originais para exclusão
                self.delete(message_ids)
                self.expunge()
                logger.info(f"{len(message_ids)} mensagens movidas para {folder}")
                return True
            return False
        except Exception as e:
            logger.error(f"Erro ao mover mensagens: {e}")
            return False
