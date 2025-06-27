import logging
import os

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = os.getenv("LOG_FILE", "backend.log")

logger = logging.getLogger("backend")
logger.setLevel(LOG_LEVEL)

formatter = logging.Formatter('[%(asctime)s] %(levelname)s %(name)s: %(message)s')

file_handler = logging.FileHandler(LOG_FILE)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

# Contoh penggunaan:
# from monitoring.logger import logger
# logger.info("Log info")
# logger.error("Log error") 