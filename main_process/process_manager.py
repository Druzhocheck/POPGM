import subprocess
import os
import shlex
from typing import Dict, Optional, Tuple, List, Any
from main_process.cfg import ConfigManager

class ProcessManager:
    def __init__(self, logger=None, config_manager=None):
        self.processes: Dict[str, subprocess.Popen] = {}
        self.logger = logger or self._create_fallback_logger()
        self.config_manager = config_manager
        self.all_processes = self._get_all_configured_processes()
        
    def _create_fallback_logger(self):
        """Создает fallback логгер, если основной не передан"""
        import logging
        logging.basicConfig(level=logging.INFO)
        return logging.getLogger('ProcessManagerFallback')
    
    def _get_all_configured_processes(self) -> List[str]:
        """Возвращает список всех процессов, указанных в конфигурации"""
        if self.config_manager is None:
            return []
        return self.config_manager.processes_names
    
    def start_configured_processes(self) -> None:
        """Запускает все процессы, у которых enable=true в конфигурации"""
        if not self.all_processes:
            self.logger.warning("В конфигурации не найдено ни одного процесса")
            return
            
        for process_name in self.all_processes:
            process_config = self.config_manager.get_process_config(process_name)
            if process_config and process_config.get("enable", "false").lower() == "true":
                self.start_process(process_name)
            else:
                self.logger.info(f"Процесс '{process_name}' отключен в конфигурации (enable=false)")

    def handle_command(self, command: str) -> Tuple[bool, str]:
        """
        Обрабатывает входящую команду и возвращает результат выполнения.
        
        Args:
            command: строка команды (например "start adc", "stop fft", "status processes",
                     "start hello --message ONE --time 2 --file data.txt --directory ./processes")
            
        Returns:
            Кортеж (успех, сообщение)
        """
        try:
            parts = shlex.split(command.strip())
            if not parts:
                return False, "Пустая команда"
            
            cmd = parts[0].lower()
            
            if cmd == "start" and len(parts) > 1:
                process_name = parts[1]
                # Извлекаем пользовательские параметры (все что после имени процесса)
                user_args = self._parse_user_args(parts[2:]) if len(parts) > 2 else {}
                return self._handle_start(process_name, user_args)
            elif cmd == "stop" and len(parts) > 1:
                return self._handle_stop(parts[1])
            elif cmd == "status":
                if len(parts) > 1 and parts[1].lower() == "processes":
                    return self._handle_status_all()
                elif len(parts) > 1:
                    return self._handle_status(parts[1])
                else:
                    return False, "Не указан процесс для статуса"
            elif cmd == "shutdown":
                return self._handle_shutdown()
            else:
                return False, f"Неизвестная команда: {cmd}"
        except Exception as e:
            self.logger.error(f"Ошибка обработки команды '{command}': {e}", exc_info=True)
            return False, f"Ошибка выполнения команды: {str(e)}"

    def _parse_user_args(self, args: List[str]) -> Dict[str, str]:
        """Парсит пользовательские аргументы в формате --key value в словарь"""
        user_args = {}
        i = 0
        while i < len(args):
            arg = args[i]
            if arg.startswith("--"):
                key = arg[2:]
                if i + 1 < len(args) and not args[i+1].startswith("--"):
                    user_args[key] = args[i+1]
                    i += 2
                else:
                    user_args[key] = ""  # Флаг без значения
                    i += 1
            else:
                i += 1
        return user_args

    def _handle_start(self, process_name: str, user_args: Dict[str, str] = None) -> Tuple[bool, str]:
        """Обработка команды start с пользовательскими параметрами"""
        if process_name not in self.all_processes:
            return False, f"Процесс '{process_name}' не найден в конфигурации"
            
        if process_name in self.processes:
            status = self.get_process_status(process_name)
            return False, f"Процесс '{process_name}' уже запущен (статус: {status})"
            
        success = self.start_process(process_name, user_args or {})
        if success:
            return True, f"Процесс '{process_name}' успешно запущен"
        else:
            return False, f"Не удалось запустить процесс '{process_name}'"

    def _handle_stop(self, process_name: str) -> Tuple[bool, str]:
        """Обработка команды stop"""
        if process_name not in self.all_processes:
            return False, f"Процесс '{process_name}' не найден в конфигурации"
            
        if process_name not in self.processes:
            return False, f"Процесс '{process_name}' не запущен"
            
        success = self.stop_process(process_name)
        if success:
            return True, f"Процесс '{process_name}' успешно остановлен"
        else:
            return False, f"Не удалось остановить процесс '{process_name}'"

    def _handle_status(self, process_name: str) -> Tuple[bool, str]:
        """Обработка команды status для одного процесса"""
        if process_name not in self.all_processes:
            return False, f"Процесс '{process_name}' не найден в конфигурации"
            
        status = self.get_process_status(process_name)
        return True, f"Статус процесса '{process_name}': {status}"

    def _handle_status_all(self) -> Tuple[bool, str]:
        """Обработка команды status processes"""
        statuses = self.list_all_processes_statuses()
        if not statuses:
            return True, "Нет процессов в конфигурации"
            
        status_lines = [f"{name}: {status}" for name, status in statuses.items()]
        return True, "Статусы всех процессов:\n" + "\n".join(status_lines)

    def _handle_shutdown(self) -> Tuple[bool, str]:
        """Обработка команды shutdown"""
        count = len(self.processes)
        self.stop_all_processes()
        return True, f"Система выключена. Остановлено процессов: {count}"

    def start_process(self, name: str, user_args: Dict[str, str] = None) -> bool:
        """
        Запускает процесс с заданным именем, объединяя параметры из конфигурации
        и пользовательские параметры (пользовательские имеют приоритет).
        
        Args:
            name: имя процесса
            user_args: словарь пользовательских параметров (например {'message': 'ONE', 'time': '2'})
        """
        try:
            script_path = f"processes/{name}.py"
            if not os.path.exists(script_path):
                self.logger.error(f"Файл процесса не найден: {script_path}")
                return False
                
            if name in self.processes:
                self.logger.warning(f"Попытка запуска уже запущенного процесса '{name}'")
                return False
            
            # Получаем конфигурацию процесса
            process_config = self.config_manager.get_process_config(name) or {}
            
            # Удаляем параметр enable из конфигурации
            process_config.pop('enable', None)
            
            # Объединяем параметры (пользовательские имеют приоритет)
            combined_args = {**process_config, **(user_args or {})}
            
            # Формируем команду для запуска
            command = ["python", script_path]
            
            # Добавляем параметры в командную строку
            for param, value in combined_args.items():
                command.extend([f"--{param}", str(value)])
            
            self.logger.debug(f"Запускаем процесс командой: {' '.join(command)}")
            
            process = subprocess.Popen(command)
            self.processes[name] = process
            self.logger.info(f"Процесс '{name}' запущен (PID: {process.pid}) с параметрами: {combined_args}")
            return True
            
        except Exception as e:
            self.logger.error(f"Ошибка при запуске процесса '{name}': {e}", exc_info=True)
            return False

    def stop_process(self, name: str, timeout: float = 5.0) -> bool:
        """Останавливает процесс по имени, используя мягкое завершение (SIGTERM)."""
        if name not in self.processes:
            self.logger.warning(f"Попытка остановки несуществующего процесса '{name}'")
            return False
        
        process = self.processes[name]
        try:
            process.terminate()
            process.wait(timeout=timeout)
            del self.processes[name]
            self.logger.info(f"Процесс '{name}' (PID: {process.pid}) остановлен")
            return True
            
        except subprocess.TimeoutExpired:
            self.logger.warning(f"Процесс '{name}' не завершился вовремя, принудительное завершение (SIGKILL)")
            process.kill()
            del self.processes[name]
            return True
            
        except Exception as e:
            self.logger.error(f"Ошибка при остановке процесса '{name}': {e}", exc_info=True)
            return False

    def stop_all_processes(self) -> None:
        """Останавливает все запущенные процессы."""
        for name in list(self.processes.keys()):
            self.stop_process(name)

    def get_process_status(self, name: str) -> str:
        """Возвращает статус процесса (Running, Stopped, None или Not Configured)."""
        if name not in self.all_processes:
            return "Not Configured"
            
        if name not in self.processes:
            process_config = self.config_manager.get_process_config(name)
            if process_config and process_config.get("enable", "false").lower() == "true":
                if os.path.exists(f"processes/{name}.py"):
                    return "Stopped"
                else:
                    return "None"
            else:
                return "Disabled"
                
        process = self.processes[name]
        return "Running" if process.poll() is None else "Stopped"

    def list_processes(self) -> Dict[str, str]:
        """Возвращает словарь запущенных процессов и их статусов."""
        return {name: "Running" if process.poll() is None else "Stopped" 
                for name, process in self.processes.items()}
    
    def list_all_processes_statuses(self) -> Dict[str, str]:
        """Возвращает словарь всех процессов из конфигурации и их статусов."""
        return {name: self.get_process_status(name) for name in self.all_processes}
