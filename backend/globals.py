from logger_config import LoggerManager

from core.config.config_manager import get_config

logger_manager = LoggerManager(base_log_dir="data/logs/")
main_logger = logger_manager.get_main_logger()
config = get_config()
