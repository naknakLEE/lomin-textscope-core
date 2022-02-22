import os
import logging

from loguru import logger
from rich.logging import RichHandler

from app.common.const import get_settings

settings = get_settings()

log_dir_path = settings.TEXTSCOPE_LOG_DIR_PATH
os.makedirs(log_dir_path, exist_ok=True)
log_path = os.path.join(log_dir_path, "server.log")

simple_formatter = "[%(name)s] %(message)s"
complex_formatter = "%(asctime)s %(levelname)s [%(name)s] [%(filename)s:%(lineno)d] - %(message)s"

fileHandler = logging.handlers.RotatingFileHandler(
	log_path,
    mode='a',
    maxBytes=settings.FILE_MAX_BYTE,
    backupCount=settings.BACKUP_COUNT,
    encoding=settings.ENCODING, 
    delay=True
)
logging.basicConfig(
    level=settings.LOG_LEVEL,
    format=complex_formatter if settings.FORMAT == "complex" else simple_formatter,
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True, tracebacks_show_locals=True)]
)

logger = logging.getLogger('wrapper-textscope')
logger.addHandler(fileHandler)
