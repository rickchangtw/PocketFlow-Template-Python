import logging
import logging.handlers
import os
from pathlib import Path

from src.core.config import settings

def setup_logging():
    """Setup logging configuration"""
    # Create logs directory if it doesn't exist
    log_dir = Path(settings.LOG_FILE).parent
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Create formatters
    formatter = logging.Formatter(settings.LOG_FORMAT)
    
    # Create handlers
    file_handler = logging.handlers.RotatingFileHandler(
        settings.LOG_FILE,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setFormatter(formatter)
    
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    
    # Setup root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(settings.LOG_LEVEL)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    # Setup specific loggers
    loggers = [
        "uvicorn",
        "uvicorn.access",
        "uvicorn.error",
        "fastapi",
        "src"
    ]
    
    for logger_name in loggers:
        logger = logging.getLogger(logger_name)
        logger.setLevel(settings.LOG_LEVEL)
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
    
    return root_logger

# Create logger instance
logger = setup_logging()
