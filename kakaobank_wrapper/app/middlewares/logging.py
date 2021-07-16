import json
import time
import httpx
import traceback

from datetime import datetime
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from kakaobank_wrapper.app.utils.logging import logger
from kakaobank_wrapper.app.utils.ocr_response_parser import response_handler
from kakaobank_wrapper.app.database.schema import Logs
from kakaobank_wrapper.app.database.connection import db


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint):
        try:
            request.state.req_time = datetime.utcnow()
            request.state.start = time.time()
            request.state.inspect = None
            request.state.user = None
            request.state.db = next(db.session())
            headers = request.headers
            ip = (
                headers["x-forwarded-for"]
                if "x-forwarded-for" in request.headers.keys()
                else request.client.host
            )
            request.state.ip = ip.split(",")[0] if "," in ip else ip
            response = await call_next(request)
            await api_logger(request=request, response=response)
        except httpx.RequestError as exc:
            logger.error(f"An error occurred while requesting {exc.request.url!r}.")
            logger.exception("What?!")
            response = await response_handler(status=2400)
            # error = await exception_handler(exc)
            await api_logger(request=request, error=exc, response=response)
            response = JSONResponse(status_code=200, content=response)
        except httpx.HTTPStatusError as exc:
            logger.error(
                f"Error response {exc.response.status_code} while requesting {exc.request.url!r}."
            )
            logger.exception("What?!")
            response = await response_handler(status=exc.response.status_code)
            # error = await exception_handler(exc)
            await api_logger(request=request, error=exc, response=response)
            response = JSONResponse(status_code=200, content=response)
        except httpx.HTTPError as exc:
            logger.error(f"HTTP Exception for {exc.request.url} - {exc}")
            logger.exception("What?!")
            response = await response_handler(status=exc.response.status_code)
            # error = await exception_handler(exc)
            await api_logger(request=request, error=exc, response=response)
            response = JSONResponse(status_code=200, content=response)
        except Exception as exc:
            logger.exception("What?!")
            response = await response_handler(status=3400)
            # error = await exception_handler(exc)
            await api_logger(request=request, error=response)
            response = JSONResponse(status_code=200, content=response)
        finally:
            request.state.db.close()

        return response


async def api_logger(request: Request = None, response=None, error=None) -> None:
    processed_time = time.time() - request.state.start
    status_code = 200
    error_log = None
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
            msg=str(error),
            traceback=traceback.format_exc(),
        )
    log_dict = dict(
        url=request.url.hostname + request.url.path,
        method=str(request.method),
        status_code=status_code,
        error_detail=error_log,
        client=request.state.ip,
        request_timestamp=str(request.state.start),
        response_timestamp=str(time.time()),
        processed_time=str(processed_time),
    )
    Logs.create_log(request.state.db, auto_commit=True, **log_dict)
    if error and int(response.get("status")) >= 2000:
        logger.error(json.dumps(log_dict, indent=4, sort_keys=True))
    else:
        logger.info(json.dumps(log_dict, indent=4, sort_keys=True))
