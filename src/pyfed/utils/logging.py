import logging
import sys
from typing import Optional

def configure_logging(level: Optional[str] = None):
    """
    Configure the logging system for the ActivityPub library.

    Args:
        level (Optional[str]): The logging level. If None, defaults to INFO.
    """
    if level is None:
        level = logging.INFO
    else:
        level = getattr(logging, level.upper())

    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('activitypub_library.log')
        ]
    )

def get_logger(name: str) -> logging.Logger:
    """
    Get a logger with the specified name.

    Args:
        name (str): The name of the logger, typically __name__ of the module.

    Returns:
        logging.Logger: A configured logger instance.
    """
    return logging.getLogger(name)
