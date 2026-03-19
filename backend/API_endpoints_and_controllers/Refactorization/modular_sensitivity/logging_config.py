import logging
import os
from logging.handlers import RotatingFileHandler

# Create package-level logger
logger = logging.getLogger(__name__)

def setup_logging(logs_dir):
    """Configure logging for the application"""
    # Ensure logs directory exists
    os.makedirs(logs_dir, exist_ok=True)

    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # Create file handler
    file_handler = RotatingFileHandler(
        os.path.join(logs_dir, 'app.log'),
        maxBytes=1024*1024,
        backupCount=5)
    file_handler.setFormatter(formatter)

    # Set up the root logger
    logger.setLevel(logging.DEBUG)
    logger.addHandler(file_handler)

    # Also log to console
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)


def get_module_logger():
    return None