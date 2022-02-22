import os
import logging

from loguru import logger
from rich.logging import RichHandler

from app.common.const import get_settings


settings = get_settings()

log_dir_path = settings.TEXTSCOPE_LOG_DIR_PATH
os.makedirs(log_dir_path, exist_ok=True)
log_path = os.path.join(log_dir_path, "server.log")

fileHandler = logging.handlers.RotatingFileHandler(
	log_path,
    mode='a',
    maxBytes=10000000,
    backupCount=10,
    encoding=settings.ENCODING, 
    delay=True
)
logging.basicConfig(
    level="NOTSET",
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True, tracebacks_show_locals=True, tracebacks_width=1000)]
)
logger = logging.getLogger('wrapper-textscope')
logger.addHandler(fileHandler)
