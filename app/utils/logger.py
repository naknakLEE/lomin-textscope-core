import json

from time import time
from fastapi.requests import Request

from app.utils.logging import logger
from app.database.schema import Logs, Usage
from app.common.const import get_settings


settings = get_settings()


async def api_logger(request: Request, response=None, error=None) -> None:
    processed_time = time() - request.state.start
    status_code = error.status_code if error else response.status_code
    error_log = None
    email = request.state.email
    if error:
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
    log_detail = response.__dict__ if response else None
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
            Usage.create(
                request.state.db, auto_commit=True, email=email, status_code=status_code
            )
        if "metrics" not in request.url.path.split("/"):
            Logs.create(request.state.db, auto_commit=True, **log_dict)
    if error and error.status_code >= 500:
        logger.error(json.dumps(log_dict, indent=4, sort_keys=True))
        logger.exception("api logger")
    else:
        logger.debug(json.dumps(log_dict, indent=4, sort_keys=True))
