import logging
import os
from logging.handlers import RotatingFileHandler

def setup_logger(name="youtube_agent", log_file="logs/agent.log", level=logging.INFO):
    """Function to setup as many loggers as you want"""
    
    # Create logs directory if it doesn't exist
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # File handler with rotation (forcing utf-8 to avoid Windows charmap errors with Telugu)
    file_handler = RotatingFileHandler(log_file, maxBytes=5*1024*1024, backupCount=5, encoding='utf-8')
    file_handler.setFormatter(formatter)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Prevent adding handlers multiple times if logger is called again
    if not logger.handlers:
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

    return logger

# Default logger instance
logger = setup_logger()
