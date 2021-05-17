import json
import logging
import traceback
import os

from datetime import timedelta, datetime
from time import time
from fastapi.requests import Request
from fastapi.logger import logger
from os import path

from database.schema import Errors
from database.connection import db



base_dir = path.dirname(path.dirname(path.dirname(path.abspath(__file__))))
log_folder_dir = path.join(base_dir, "log")
os.makedirs(log_folder_dir, exist_ok=True)
log_file_dir = path.join(log_folder_dir, "log.log")
fileMaxByte = 1024 * 1024
fileHandler = logging.handlers.RotatingFileHandler(log_file_dir, maxBytes=fileMaxByte, backupCount=1000)
logger.setLevel(logging.DEBUG)
logger.addHandler(fileHandler)


async def api_logger(request: Request, response=None, error=None):
    time_format = "%Y/%m/%d %H:%M:%S"
    t = time() - request.state.start
    status_code = error.status_code if error else response.status_code
    error_log = None
    user = request.state.user
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
            msg=str(error.ex),
        )
    email = user.email if user and user.email else None
    user_log = dict(
        client=request.state.ip,
        user=user.id if user and user.id else None,
        email=email
    )


    log_dict = dict(
        url=request.url.hostname + request.url.path,
        method=str(request.method),
        status_code=status_code,
        error_detail=error_log,
        client=str(user_log),
        processed_time=str(round(t * 1000, 5)) + "ms",
        datetime_kr=(datetime.utcnow() + timedelta(hours=9)).strftime(time_format),
    )
    # if body:
    #     log_dict["body"] = body
    print('\033[96m' + f"\n{log_dict}" + '\033[0m')
    # Errors.create(next(db.session()), auto_commit=True, **log_dict)
    if error and error.status_code >= 500:
        logger.error(json.dumps(log_dict))
        logger.error({"traceback": f"{traceback.print_exc()}"})
    else:
        logger.info(json.dumps(log_dict))
        logger.info({"traceback": f"{traceback.print_exc()}"})