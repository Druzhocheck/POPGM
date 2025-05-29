import configparser
from typing import Dict, Any
import os

class ConfigManager:

    processes_names = []

    def __init__(self, config_path: str, logger=None):
        """
        Инициализация менеджера конфигурации.
        
        Args:
            config_path: Путь к конфигурационному файлу .ini
            logger: Логгер для записи сообщений
        """
        self.config_path = config_path
        self._config = None
        self.logger = logger
        self.processes_names = []

    def load_config(self):
        if not os.path.isfile(self.config_path) or not os.access(self.config_path, os.R_OK):
            self.logger.error(f"Ошибка чтения файла: {self.config_path}")

        config = configparser.ConfigParser()
        try:
            # read() возвращает список успешно прочитанных файлов
            if not config.read(self.config_path, encoding='utf-8'):
                print("Файл конфигурации пуст или поврежден")
            
            # Дополнительная проверка, что файл не пустой
            if not config.sections():
                print("В файле конифгурации не обнаружены секции")

            else:
                print("Файл конфигурации успешно считан")
                
        except configparser.Error as e:
            print(f"Ошибка чтения файла: {e}")
        except UnicodeDecodeError as e:
            print(f"Ошибка чтения символов файла: {e}")

        result = {}
        processes = {}
        
        for section in config.sections():
            if section.startswith('process:'):
                process_name = section.split(':', 1)[1]
                processes[process_name] = dict(config[section])
                self.processes_names.append(process_name)
            else:
                result[section] = dict(config[section])
        
        if processes:
            result['processes'] = processes
        
        # Конвертируем значения
        self._convert_values(result)
        
        self._config = result
        return result

    def get_config(self) -> Dict[str, Any]:
        """
        Возвращает загруженную конфигурацию.
        
        Returns:
            Текущая конфигурация
            
        Raises:
            RuntimeError: Если конфиг не был загружен
        """
        if self._config is None:
            raise RuntimeError("Конфигурация не загружена. Сначала вызовите load_config()")
        return self._config

    def get_process_config(self, process_name: str) -> Dict[str, Any]:
        """
        Возвращает конфигурацию для конкретного процесса.
        
        Args:
            process_name: Имя процесса (например 'adc')
            
        Returns:
            Словарь с параметрами процесса
            
        Raises:
            KeyError: Если процесс не найден
        """
        if self._config is None:
            raise RuntimeError("Конфигурация не загружена")
        
        if 'processes' not in self._config or process_name not in self._config['processes']:
            raise KeyError(f"Процесс '{process_name}' не найден в конфигурации")
            
        return self._config['processes'][process_name]

    def _convert_values(self, config_dict: Dict[str, Any]) -> None:
        """Рекурсивно конвертирует строковые значения в соответствующие типы"""
        for section in config_dict:
            if isinstance(config_dict[section], dict):
                for key, value in config_dict[section].items():
                    config_dict[section][key] = self._convert_value(value)

    @staticmethod
    def _convert_value(value: str) -> Any:
        """Конвертирует строковое значение из конфига в Python-тип"""
        if isinstance(value, str):
            value = value.strip()
            if value.lower() == 'true':
                return True
            elif value.lower() == 'false':
                return False
            elif value.isdigit():
                return int(value)
            try:
                return float(value)
            except ValueError:
                pass
        return value