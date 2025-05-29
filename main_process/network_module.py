import socket
import threading
import logging
from typing import Callable, Optional

class NetworkModule:
    def __init__(self, host='0.0.0.0', port=30000, logger=None, command_handler: Optional[Callable] = None):
        self.host = host
        self.port = port
        self.socket = None
        self.running = False
        self.logger = logger or logging.getLogger('network_module')
        self.command_handler = command_handler
        
        # Fallback если логгер не передан
        if not hasattr(self.logger, 'info'):
            logging.basicConfig(level=logging.INFO)
            self.logger = logging.getLogger('network_module_fallback')

    def start(self):
        """Запускает сервер для прослушивания UDP-порта."""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.socket.bind((self.host, self.port))
            self.running = True
            self.logger.info(f"UDP-сервер запущен и слушает порт {self.port}")

            # Запускаем поток для приема сообщений
            receive_thread = threading.Thread(target=self._receive_messages)
            receive_thread.daemon = True
            receive_thread.start()
        except Exception as e:
            self.logger.error(f"Ошибка при запуске сервера: {e}")
            raise

    def stop(self):
        """Останавливает сервер."""
        self.running = False
        if self.socket:
            self.socket.close()
        self.logger.info("UDP-сервер остановлен")

    def _receive_messages(self):
        """Принимает сообщения от клиентов и передает их обработчику команд."""
        while self.running:
            try:
                data, client_address = self.socket.recvfrom(1024)
                if not data:
                    continue
                
                message = data.decode('utf-8').strip()
                self.logger.info(f"Получено от {client_address}: {message}")
                
                # Если есть обработчик команд, передаем ему сообщение
                if self.command_handler:
                    response = self.command_handler(message)
                    if response:
                        self._send_response(client_address, response)
                        
            except (socket.error, OSError) as e:
                if not self.running:
                    break
                self.logger.error(f"Ошибка при приеме сообщения: {e}")

    def _send_response(self, client_address, response):
        """Отправляет ответ клиенту."""
        try:
            if isinstance(response, tuple):
                success, message = response
                response_str = f"{'SUCCESS' if success else 'ERROR'}: {message}"
            else:
                response_str = str(response)
                
            self.socket.sendto(response_str.encode('utf-8'), client_address)
        except (socket.error, OSError) as e:
            self.logger.error(f"Ошибка при отправке ответа клиенту {client_address}: {e}")

    def send_to_client(self, client_address, message):
        """Отправляет сообщение конкретному клиенту."""
        if self.running:
            try:
                self.socket.sendto(message.encode('utf-8'), client_address)
            except (socket.error, OSError) as e:
                self.logger.error(f"Ошибка при отправке сообщения клиенту {client_address}: {e}")