import os
import sys
from loguru import logger
from common.const import get_settings

cfgs = get_settings()

# class LogFilter:
#     def __init__(self, level):
#         self.level = level
    
#     def __call__(self, record):
#         levelno = logger.level(self.level).no
#         return record['level'].no >= levelno
    

# # https://github.com/Delgan/loguru
log_dir_path = cfgs.LOG_DIR_PATH
# log_level = cfgs.LOG_LEVEL
# log_level_env = os.getenv('LOG_LEVEL')
# if log_level_env:
#     log_level = log_level_env

# log_filter = LogFilter(log_level)


os.makedirs(log_dir_path, exist_ok=True)
log_path = os.path.join(log_dir_path, "server.log")
# logger.remove()
logger.add(
    log_path,
    rotation=cfgs.LOG_ROTATION,
    retention=cfgs.LOG_RETENTION,
    format="{time:YYYY-MM-DD HH:mm:ss.SSS} {level} {message}",
    # filter=log_filter,
    encoding="utf-8",
    level=cfgs.LOG_LEVEL
)

# logger.remove()
# logger.add(
#     sys.stderr,
#     format="{time:YYYY-MM-DD HH:mm:ss.SSS} {level} {message}",
#     level=cfgs.LOG_LEVEL
# )