"""
Centralized logging configuration for the semantic image search project.
"""

import logging
from logging.handlers import RotatingFileHandler
from . import config

# Ensure the logs directory exists
config.LOGS_DIR.mkdir(parents=True, exist_ok=True)

def get_logger(module_name: str) -> logging.Logger:
    """
    Get a configured logger for the given module.
    Writes to both console and a rotating log file.
    
    Args:
        module_name: Usually __name__ of the calling module
        
    Returns:
        A configured logging.Logger object
    """
    logger = logging.getLogger(module_name)
    
    # If the logger already has handlers, it means it was previously configured
    # We return it as is to avoid duplicate log entries.
    if logger.hasHandlers():
        return logger

    logger.setLevel(logging.INFO)

    # Common format for both console and file
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # 1. Console Handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    
    # 2. File Handler (Rotating log file: max 5MB, keep 3 backups)
    file_handler = RotatingFileHandler(
        config.LOG_FILE,
        maxBytes=5 * 1024 * 1024,  # 5 MB
        backupCount=3,
        encoding="utf-8"
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    
    # Add handlers to the logger
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    # Prevent logs from propagating to the root logger to avoid double-printing
    logger.propagate = False
    
    return logger
