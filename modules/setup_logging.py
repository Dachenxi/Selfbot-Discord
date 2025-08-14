import os
import logging
from datetime import datetime
from logging.handlers import RotatingFileHandler


os.makedirs("log", exist_ok=True)
log_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
def setup_logging():
    # Create a root logger
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)  # Can be changed to DEBUG as needed

    # Rotating File Handler (limits log file size)
    file_handler = RotatingFileHandler(
        f"log/bot_{log_timestamp}.log",
        maxBytes=10*1024*1024,  # 10 MB per log file
        backupCount=5,  # Keep 5 backup log files
        encoding="utf-8"
    )
    file_handler.setFormatter(logging.Formatter(
        "[%(asctime)s] [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    ))

    # Console Handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(
        "[%(asctime)s] [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    ))

    # Add handlers to the root logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger