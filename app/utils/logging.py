import os
import sys

from loguru import logger
from app.common.const import get_settings

settings = get_settings()

log_dir_path = settings.TEXTSCOPE_LOG_DIR_PATH
os.makedirs(log_dir_path, exist_ok=True)

log_path = os.path.join(log_dir_path, "server.log")

logger.remove()
logger.add(sys.stderr, level=settings.LOG_LEVEL)

logger.add(
    log_path,
    format="{time:YYYY-MM-DD at HH:mm:ss} | {level} | {message}",
    rotation=settings.LOG_ROTATION,
    retention=settings.LOG_RETENTION,
    encoding=settings.ENCODING,
    level=settings.LOG_LEVEL,
    backtrace=settings.BACKTRACE,
    diagnose=settings.DIAGNOSE,
    enqueue=settings.ENQUEUE,
    colorize=settings.COLORIZE,
)

# Error로그 따로 저장 
error_log_path = os.path.join(log_dir_path, "server_error.log")
logger.add(
    error_log_path,
    format="{time:YYYY-MM-DD at HH:mm:ss} | {level} | {message}",
    rotation=settings.LOG_ROTATION,
    retention=settings.LOG_RETENTION,
    encoding=settings.ENCODING,
    level="ERROR",
    backtrace=settings.BACKTRACE,
    diagnose=settings.DIAGNOSE,
    enqueue=settings.ENQUEUE,
    colorize=settings.COLORIZE,
)

# handler = logging.handlers.SysLogHandler(address=("localhost", settings.KAKAO_WRAPPER_IP_PORT))
# logger.add(handler)
