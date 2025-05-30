import logging
from logging.handlers import TimedRotatingFileHandler, RotatingFileHandler
import os
import re
from typing import Dict, Any

class LoggerManager:
    VALID_LOG_LEVELS = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
    
    def __init__(self, logging_config: Dict[str, Any]):
        self.logging_config = logging_config
        self._logger_instance = logging.getLogger('app_main')
        self._logger_instance.handlers.clear()

        self._setup_log_level()

        if self.logging_config.get('use_console', True):
            self._setup_console_handler()

        self._setup_file_logger()

    def _setup_log_level(self):
        log_level_str = self.logging_config.get('log_level', 'INFO').upper()
        if log_level_str not in self.VALID_LOG_LEVELS:
            logging.warning(f"Неверный уровень логирования в конфиге, используется INFO")
            log_level_str = 'INFO'

        log_level = getattr(logging, log_level_str)
        self._logger_instance.setLevel(log_level)

    def _parse_rotation_time(self, rotation_time: str) -> tuple[str, int]:
        match = re.match(r'^(\d+)([dhm])$', rotation_time.lower())
        if not match:
            self._logger_instance.warning(f"Неверный формат rotation_time: {rotation_time}. Используется значение по умолчанию '7d'")
            return 'midnight', 7

        value, unit = match.groups()
        value = int(value)

        mapping = {
            'd': ('midnight', value),
            'h': ('H', value),
            'm': ('M', value)
        }

        return mapping.get(unit, ('midnight', 7))

    def _setup_console_handler(self):
        console_handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
        console_handler.setFormatter(formatter)
        self._logger_instance.addHandler(console_handler)

    def _setup_file_logger(self):
        try:
            log_dir = self.logging_config.get('log_dir', 'logs')
            os.makedirs(log_dir, exist_ok=True)
            
            log_file = os.path.join(log_dir, self.logging_config.get('log_file', 'app.log'))
            
            max_bytes = self.logging_config.get('max_bytes')
            max_files = self.logging_config.get('max_files')
            
            if max_bytes is not None and max_files is not None:
                file_handler = RotatingFileHandler(
                    log_file,
                    maxBytes=max_bytes,
                    backupCount=max_files
                )
            else:
                rotation_time = self.logging_config.get('rotation_time', '7d')
                when, interval = self._parse_rotation_time(rotation_time)
                backup_count = self.logging_config.get('backup_count', 5)
                
                file_handler = TimedRotatingFileHandler(
                    log_file,
                    when=when,
                    interval=interval,
                    backupCount=backup_count
                )
                
                max_files = self.logging_config.get('max_files')
                if max_files is not None:
                    # Очищаем старые логи при инициализации
                    self._cleanup_old_logs(log_file, max_files)
                    # Устанавливаем собственный rotator
                    def custom_rotator(source, dest):
                        os.rename(source, dest)
                        self._cleanup_old_logs(log_file, max_files)
                    
                    file_handler.rotator = custom_rotator
            
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
            file_handler.setFormatter(formatter)
            self._logger_instance.addHandler(file_handler)
            
            self._logger_instance.info("Файловый логгер успешно настроен")
            
        except Exception as e:
            self._logger_instance.error(
                f"Ошибка настройки файлового логгера: {e}. Используется только консольный вывод"
            )

    def _make_rotator(self, original_rotator, base_filename, max_files):
        def rotator(source, dest):
            # Вызываем оригинальный rotator
            original_rotator(source, dest)
            # Очищаем старые логи после ротации
            self._cleanup_old_logs(base_filename, max_files)
        return rotator

    def _cleanup_old_logs(self, base_filename: str, max_files: int):
        try:
            log_dir = os.path.dirname(base_filename)
            base_name = os.path.basename(base_filename)
            
            log_files = []
            for filename in os.listdir(log_dir):
                if filename.startswith(base_name):
                    log_files.append(filename)
            
            if len(log_files) > max_files:
                log_files.sort()
                files_to_delete = log_files[:-max_files]
                
                for filename in files_to_delete:
                    try:
                        os.remove(os.path.join(log_dir, filename))
                        self._logger_instance.debug(f"Удален старый лог-файл: {filename}")
                    except Exception as e:
                        self._logger_instance.warning(f"Не удалось удалить старый лог-файл {filename}: {e}")
                        
        except Exception as e:
            self._logger_instance.warning(f"Ошибка при очистке старых лог-файлов: {e}")

    @property
    def logger(self):
        return self._logger_instance

    @logger.setter
    def logger(self, value):
        if value is None or not hasattr(value, 'info'):
            logging.basicConfig(level=logging.INFO)
            self._logger_instance = logging.getLogger('fallback_logger')
            self._logger_instance.warning("Передан невалидный логгер, используется fallback")
        else:
            self._logger_instance = value