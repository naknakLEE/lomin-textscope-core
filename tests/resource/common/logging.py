import sys

from loguru import logger


logger.add(
    sink=sys.stdout,
    format="{time:YYYY-MM-DD at HH:mm:ss} | {level} | {message}"
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
    sys.stderr = StdOutErr(logger.warning)

catch_console_all_log()