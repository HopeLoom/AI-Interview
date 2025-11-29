import os
import sys
from loguru import logger as base_logger
from typing import Dict, Any

class LoggerManager:
    def __init__(self, base_log_dir: str = "logs"):
        self.base_log_dir = base_log_dir
        self._user_loggers: Dict[str, Any] = {}

        # Reset existing handlers
        base_logger.remove()

        # Add a default console handler for quick debugging
        base_logger.add(
            sys.stderr,
            level="INFO",
            format="{time} | {level} | {extra[user_id]} | {extra[session_id]} | {message}"
        )

    def get_logger_for_user(self, user_id: str, session_id: str):
        key = f"{user_id}:{session_id}"
        if key in self._user_loggers:
            return self._user_loggers[key]

        os.makedirs(f"{self.base_log_dir}/{user_id}", exist_ok=True)

        # Define custom filter for this user's log sink
        def filter_for_user(record):
            #print(f"FILTER DEBUG: {record['message']} | {record['extra']}")
            return (
                record["extra"].get("user_id") == user_id
                and record["extra"].get("session_id") == session_id
            )

        # Add sinks BEFORE binding
        base_logger.add(
            f"{self.base_log_dir}/{user_id}/general_{session_id}.log",
            level="INFO",
            rotation="10 MB",
            retention="7 days",
            enqueue=False,
            filter=filter_for_user,
            format="{time} | {level} | {extra[user_id]} | {extra[session_id]} | {message}",
        )

        base_logger.add(
            f"{self.base_log_dir}/{user_id}/errors_{session_id}.log",
            level="ERROR",
            rotation="5 MB",
            retention="14 days",
            enqueue=False,
            filter=filter_for_user,
            format="{time} | {level} | {extra[user_id]} | {extra[session_id]} | {message}",
        )

        # ✅ Bind AFTER sinks are added
        user_logger = base_logger.bind(user_id=user_id, session_id=session_id)
        self._user_loggers[key] = user_logger

        print(f"[LoggerManager] Created new logger for {key}")
        return user_logger

    def get_main_logger(self):
        return self.get_logger_for_user("main", "main")
    
    def remove_user_logger(self, user_id: str, session_id: str):
        key = f"{user_id}:{session_id}"
        if key in self._user_loggers:
            del self._user_loggers[key]
            print(f"[LoggerManager] Removed logger for {key}")
        else:
            print(f"[LoggerManager] No logger found for {key}")
