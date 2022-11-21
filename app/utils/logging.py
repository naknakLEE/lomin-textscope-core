import os
import sys

from fastapi.logger import logger as logging
from loguru import logger
from app.common.const import get_settings
settings = get_settings()

log_dir_path = settings.TEXTSCOPE_LOG_DIR_PATH
os.makedirs(log_dir_path, exist_ok=True)
log_path = os.path.join(log_dir_path, "server.log")

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

# handler = logging.handlers.SysLogHandler(address=("localhost", settings.KAKAO_WRAPPER_IP_PORT))
# logger.add(handler)
class StdOutErr(object):
    def __init__(self,logger_object):
        self.logger_object = logger_object

    def write(self,string):
        self.logger_object(string)

    def flush(self):
        pass
    def isatty(self):
        pass

def catch_console_all_log():
    sys.stdout = StdOutErr(logger.info)
    sys.stderr = StdOutErr(logger.error)

catch_console_all_log()