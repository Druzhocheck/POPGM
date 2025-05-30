from main_process.network_module import NetworkModule
from main_process.cfg import ConfigManager
from main_process.process_manager import ProcessManager
from main_process.logger import LoggerManager
import logging

def create_command_handler(process_manager):
    """Создает обработчик команд для ProcessManager."""
    def handler(command):
        try:
            # Обрабатываем команду через ProcessManager
            return process_manager.handle_command(command)
        except Exception as e:
            return False, f"Ошибка обработки команды: {str(e)}"
    return handler

if __name__ == "__main__":
    # Инициализация конфигурации
    config_manager = ConfigManager('cfg.ini')
    config = config_manager.load_config()
    # Инициализация логгера
    logger_manager = LoggerManager(config["logging"])
    logger = logger_manager.logger
    
    # Если логгер не инициализирован, то задаем дефолтные настройки
    if logger is None:
        logging.basicConfig(level=logging.INFO)
        logger = logging.getLogger('fallback_logger')
        logger.error("Не удалось инициализировать основной логгер, используется fallback")
    
    # Инициализация ProcessManager с конфигурацией
    process_manager = ProcessManager(logger=logger, config_manager=config_manager)
    
    # Создаем обработчик команд
    command_handler = create_command_handler(process_manager)
    
    # Инициализация NetworkModule с обработчиком команд
    server = NetworkModule(
        host=config.get('network', {}).get('host', '0.0.0.0'),
        port=config.get('network', {}).get('port', 30000),
        logger=logger,
        command_handler=command_handler
    )
    
    try:
        logger.info("Запуск системы...")
        # Автозапуск процессов из конфига (теперь это делается внутри ProcessManager)
        process_manager.start_configured_processes()
        
        logger.info("Текущие процессы: %s", process_manager.list_all_processes_statuses())
        
        # Запуск сервера
        server.start()
        logger.info("UDP-сервер запущен")
        
        # Основной цикл
        while True:
            pass
            
    except KeyboardInterrupt:
        logger.info("Получен сигнал KeyboardInterrupt, остановка системы...")
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}", exc_info=True)
    finally:
        # Остановка всех процессов и сервера
        process_manager.stop_all_processes()
        server.stop()
        logger.info("Система остановлена")