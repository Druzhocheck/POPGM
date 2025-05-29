import logging
from logging.handlers import TimedRotatingFileHandler
import os
from typing import Dict, Any
import re

class LoggerManager:
    VALID_LOG_LEVELS = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
    
    def __init__(self, logging_config: Dict[str, Any]):
        self.logging_config = logging_config
        self.logger = logging.getLogger('app_main')
        self.logger.handlers.clear()  # Очистка старых хэндлеров, если были

        # Сначала настраиваем логгер
        log_level = getattr(logging, self.logging_config.get('log_level', 'INFO').upper())
        self.logger.setLevel(log_level)

        # Теперь добавляем обработчики
        if self.logging_config.get('use_console', True):
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
            console_handler.setLevel(log_level)  # ограничиваем уровень
            self.logger.addHandler(console_handler)

        self._setup_file_logger()

    def _setup_log_level(self):
        """Устанавливает уровень логирования из конфига."""
        log_level_str = self.logging_config.get('log_level', 'INFO').upper()
        
        if log_level_str not in self.VALID_LOG_LEVELS:
            log_level_str = 'INFO'
            self.logger.warning(f"Неверный уровень логирования в конфиге, используется INFO")
        
        log_level = getattr(logging, log_level_str)
        self.logger.setLevel(log_level)

    def _parse_rotation_time(self, rotation_time: str) -> tuple[str, int]:
        """Парсит строку времени ротации."""
        match = re.match(r'^(\d+)([dhm])$', rotation_time.lower())
        if not match:
            self.logger.warning(
                f"Неверный формат rotation_time: {rotation_time}. Используется значение по умолчанию '7d'"
            )
            return 'midnight', 7
            
        value = int(match.group(1))
        unit = match.group(2)
        
        if unit == 'd':
            return 'midnight', value
        elif unit == 'h':
            return 'H', value
        elif unit == 'm':
            return 'M', value
        else:
            self.logger.warning(
                f"Неизвестная единица времени: {unit}. Используется значение по умолчанию '7d'"
            )
            return 'midnight', 7

    def _setup_console_handler(self):
        """Настраивает консольный обработчик для вывода ошибок."""
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        ))
        # Устанавливаем тот же уровень, что и для логгера
        console_handler.setLevel(self.logger.level)
        self.logger.addHandler(console_handler)

    def _setup_file_logger(self):
        """Настройка файлового логгера с ротацией."""
        try:
            log_dir = self.logging_config.get('log_dir', 'logs')
            os.makedirs(log_dir, exist_ok=True)
            
            log_file = os.path.join(log_dir, self.logging_config.get('log_file', 'app.log'))
            
            # Парсим время ротации
            rotation_time = self.logging_config.get('rotation_time', '7d')
            when, interval = self._parse_rotation_time(rotation_time)
            
            # Настраиваем ротацию логов
            file_handler = TimedRotatingFileHandler(
                log_file,
                when=when,
                interval=interval,
                backupCount=self.logging_config.get('backup_count', 5)
            )
            file_handler.setFormatter(logging.Formatter(
                '%(asctime)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            ))
            # Устанавливаем тот же уровень, что и для логгера
            file_handler.setLevel(self.logger.level)
            self.logger.addHandler(file_handler)
            
            self.logger.info("Файловый логгер успешно настроен")
            
        except Exception as e:
            self.logger.error(
                f"Ошибка настройки файлового логгера: {e}. Используется только консольный вывод"
            )

    @property
    def logger(self):
        """Геттер для логгера."""
        return self._logger

    @logger.setter
    def logger(self, value):
        """Сеттер для логгера с проверкой."""
        if value is None or not hasattr(value, 'info'):
            logging.basicConfig(level=logging.INFO)
            self._logger = logging.getLogger('fallback_logger')
            self._logger.warning("Передан невалидный логгер, используется fallback")
        else:
            self._logger = value