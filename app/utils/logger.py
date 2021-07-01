import json
import traceback
import os
import logging
from logging.handlers import QueueHandler

print(logging.handlers)

from os import path
from time import time
from typing import Optional
from fastapi.requests import Request
from jose import jwt

# from fastapi.logger import logger
from loguru import logger

from app.database.schema import Logs, Usage
from app.common.const import get_settings
from app.errors import exceptions as ex


settings = get_settings()


# class MyHandler(logging.Handler):
#     def emit(self, record, session: Session = Depends(db.session)):
#         print('\033[96m' + f"\n{record.__dict__}" + '\033[0m')
#         logger.info(json.dumps(record.__dict__))
#         Logs.create(next(db.session()), auto_commit=True, **record.__dict__)


def load_log_file_dir():
    base_dir = path.dirname(path.dirname(path.dirname(path.abspath(__file__))))
    base_dir = settings.BASE_PATH
    log_folder_dir = path.join(base_dir, "logs/fastapi")
    os.makedirs(log_folder_dir, exist_ok=True)
    log_file_dir = path.join(log_folder_dir, "log.log")
    return log_file_dir


def set_logger_config():
    log_file_dir = load_log_file_dir()
    logger.add(log_file_dir, rotation="1 MB")

    # fileHandler = logging.handlers.RotatingFileHandler(log_file_dir, maxBytes=settings.FILE_MAX_BYTE, backupCount=settings.BACKUP_COUNT)
    # logger.setLevel(getattr(logging, settings.LOG_LEVEL))
    # logger.addHandler(fileHandler)


set_logger_config()


async def api_logger(request: Request = None, response=None, error=None) -> None:
    processed_time = time() - request.state.start
    status_code = error.status_code if error else response.status_code
    error_log = None
    email = request.state.email
    # body = await request.body()
    if error:
        # print('\033[96m' + f"\n{request.state.inspect}" + '\033[0m')
        if request.state.inspect:
            frame = request.state.inspect
            error_file = frame.f_code.co_filename
            error_func = frame.f_code.co_name
            error_line = frame.f_lineno
        else:
            error_func = error_file = error_line = "UNKNOWN"

        error_log = dict(
            errorFunc=error_func,
            location="{} line in {}".format(str(error_line), error_file),
            raised=str(error.__class__.__name__),
            msg=str(error.exc),
            # traceback=traceback.format_exc()
        )
    # log_detail = response.__dict__ if response else None
    user_log = dict(
        # user=user.id if user and user.id else None,
        client=request.state.ip,
        email=email,
    )

    log_dict = dict(
        url=request.url.hostname + request.url.path,
        method=str(request.method),
        status_code=status_code,
        # log_detail=str(log_detail),
        error_detail=error_log,
        client=user_log,
        request_timestamp=str(request.state.start),
        response_timestamp=str(time()),
        processed_time=str(processed_time),
    )
    # if body:
    #     log_dict["body"] = body
    # print('\033[96m' + f"\n{log_dict}" + '\033[0m')
    # request.state.db.add(Logs(**log_dict))
    # request.state.db.flush()
    # request.state.db.commit()
    # Logs.querycreate(request.state.db, auto_commit=True, **log_dict)

    if email is not None and request.url.path == "/inference":
        Usage.create_usage(
            request.state.db, auto_commit=True, email=email, status_code=status_code
        )
    if error and error.status_code >= 500:
        logger.error(json.dumps(log_dict, indent=4, sort_keys=True))
        logger.error(traceback.format_exc())
    else:
        logger.info(json.dumps(log_dict, indent=4, sort_keys=True))
        logger.info(traceback.format_exc())


# https://hwangheek.github.io/2019/python-logging/
# import logging

# logger = logging.getLogger(__name__)
# logger.setLevel(logging.DEBUG) # 모든 레벨의 로그를 Handler들에게 전달해야함

# formatter = logging.Formatter('%(asctime)s:%(module)s:%(levelname)s:%(message)s', '%Y-%m-%d %H:%M:%S')

# # INFO 레벨 이상의 로그를 콘솔에 출력하는 Handler
# console_handler = logging.StreamHandler()
# console_handler.setLevel(logging.INFO)
# console_handler.setFormatter(formatter)
# logger.addHandler(console_handler)

# # DEBUG 레벨 이상의 로그를 `debug.log`에 출력하는 Handler
# file_debug_handler = logging.FileHandler('debug.log')
# file_debug_handler.setLevel(logging.DEBUG)
# file_debug_handler.setFormatter(formatter)
# logger.addHandler(file_debug_handler)

# # ERROR 레벨 이상의 로그를 `error.log`에 출력하는 Handler
# file_error_handler = logging.FileHandler('error.log')
# file_error_handler.setLevel(logging.ERROR)
# file_error_handler.setFormatter(formatter)
# logger.addHandler(file_error_handler)


# response body 응답 추가
# class async_iterator_wrapper:
#     def __init__(self, obj):
#         self._it = iter(obj)
#     def __aiter__(self):
#         return self
#     async def __anext__(self):
#         try:
#             value = next(self._it)
#         except StopIteration:
#             raise StopAsyncIteration
#         return value

# resp_body = [section async for section in response.__dict__['body_iterator']]
# # Repairing FastAPI response
# response.__setattr__('body_iterator', async_iterator_wrapper(resp_body))
# print('\033[96m' + f"\n{resp_body}" + '\033[0m')
