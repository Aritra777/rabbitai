"""Logging configuration for RabbitAI"""

import logging
import sys
from pathlib import Path
from datetime import datetime
from logging.handlers import RotatingFileHandler


class RabbitAILogger:
    """Logger for RabbitAI with file and console output"""

    def __init__(self, name: str = "rabbitai"):
        self.name = name
        self.logger = None
        self._setup_logger()

    def _setup_logger(self):
        """Setup logger with file and console handlers"""
        # Create logger
        self.logger = logging.getLogger(self.name)
        self.logger.setLevel(logging.DEBUG)

        # Prevent duplicate handlers
        if self.logger.handlers:
            return

        # Create logs directory
        log_dir = Path.home() / ".rabbitai" / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)

        # Create log file with timestamp
        log_file = log_dir / f"rabbitai_{datetime.now().strftime('%Y%m%d')}.log"

        # File handler - DEBUG level (rotating, max 10MB, keep 5 backups)
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)

        # Console handler - ERROR level only (to not clutter terminal)
        console_handler = logging.StreamHandler(sys.stderr)
        console_handler.setLevel(logging.ERROR)
        console_formatter = logging.Formatter(
            '%(levelname)s: %(message)s'
        )
        console_handler.setFormatter(console_formatter)

        # Add handlers
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

    def get_logger(self):
        """Get the configured logger instance"""
        return self.logger

    @staticmethod
    def get_log_dir() -> Path:
        """Get the logs directory path"""
        return Path.home() / ".rabbitai" / "logs"

    @staticmethod
    def get_latest_log_file() -> Path:
        """Get the path to today's log file"""
        log_dir = Path.home() / ".rabbitai" / "logs"
        return log_dir / f"rabbitai_{datetime.now().strftime('%Y%m%d')}.log"


# Global logger instance
_logger_instance = None


def get_logger(name: str = "rabbitai") -> logging.Logger:
    """
    Get or create global logger instance.

    Args:
        name: Logger name (default: rabbitai)

    Returns:
        Configured logger instance
    """
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = RabbitAILogger(name)
    return _logger_instance.get_logger()


def log_info(message: str):
    """Log info message"""
    get_logger().info(message)


def log_debug(message: str):
    """Log debug message"""
    get_logger().debug(message)


def log_warning(message: str):
    """Log warning message"""
    get_logger().warning(message)


def log_error(message: str, exc_info=False):
    """Log error message"""
    get_logger().error(message, exc_info=exc_info)


def log_exception(message: str):
    """Log exception with traceback"""
    get_logger().exception(message)
