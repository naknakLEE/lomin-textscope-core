import json

from time import time
from fastapi.requests import Request

from typing import Optional
from fastapi import Response
from app.utils.logging import logger
# from app.database.schema import Logs, Usage
from app.common.const import get_settings
from app.errors.exceptions import APIException


settings = get_settings()


def get_status_code(
    response: Optional[Response], error: Optional[APIException]
) -> Optional[int]:
    status_code = None
    if response:
        status_code = response.status_code
    elif error:
        status_code = error.status_code
    return status_code


def api_logger(
    request: Request,
    response: Optional[Response] = None,
    error: Optional[APIException] = None,
) -> None:
    processed_time = time() - request.state.start
    status_code = get_status_code(response, error)
    error_log = None
    try:
        email = request.state.email
    except:
        email = None
    if error:
        logger.exception("Error")
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
    
    log_detail = {}
    if response:
        log_detail = {
            "raw_headers": response.raw_headers,
            "background": response.background,
        }
    user_log = dict(
        client=request.state.ip,
        email=email,
    )
    log_dict = dict(
        url=request.url.hostname + request.url.path,
        method=str(request.method),
        status_code=status_code,
        log_detail=str(log_detail),
        error_detail=json.dumps(error_log),
        client=json.dumps(user_log),
        request_timestamp=str(request.state.start),
        response_timestamp=str(time()),
        processed_time=str(processed_time),
    )

    if settings.USE_TEXTSCOPE_DATABASE and settings.USE_AUTO_LOG:
        if "ocr" in request.url.path.split("/"):
            pass
            # Usage.create(
            #     request.state.db, auto_commit=True, email=email, status_code=status_code
            # )
        if "metrics" not in request.url.path.split("/"):
            pass
            # Logs.create(request.state.db, auto_commit=True, **log_dict)
    if error and error.status_code >= 500:
        logger.error(json.dumps(log_dict, indent=4, sort_keys=True))
        logger.exception("api logger")
    else:
        logger.debug(json.dumps(log_dict, indent=4, sort_keys=True))
