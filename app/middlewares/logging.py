import time

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from datetime import datetime
from jose import jwt

from app.utils.logging import logger
from app.database.connection import db
from app.utils.logger import api_logger
from app.errors.exceptions import exception_handler
from app.common.const import get_settings
from app.utils.utils import cal_time_elapsed_seconds


settings = get_settings()


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        request_datetime = datetime.now()
        try:
            request.state.req_time = request_datetime
            logger.info(f"Request time: {request.state.req_time}")
            request.state.start = time.time()
            request.state.inspect = None
            request.state.user = None
            if settings.USE_TEXTSCOPE_DATABASE:
                request.state.db = next(db.session())
            request.state.email = "none@none.none"
            headers = request.headers
            ip = (
                headers["x-forwarded-for"]
                if "x-forwarded-for" in request.headers.keys()
                else request.client.host
            )
            request.state.ip = ip.split(",")[0] if "," in ip else ip
            if "authorization" in headers.keys():
                token = headers.get("Authorization")
                payload = jwt.decode(
                    token.replace("Bearer ", ""),
                    settings.SECRET_KEY,
                    algorithms=[settings.ALGORITHM],
                )
                request.state.email = payload.get("sub")
            response = await call_next(request)
            api_logger(request=request, response=response)
        except Exception as e:
            error = await exception_handler(e)
            error_dict = dict(
                status=error.status_code,
                msg=error.msg,
                detail=error.detail,
                code=error.code,
            )
            response = JSONResponse(status_code=error.status_code, content=error_dict)
            api_logger(request=request, error=error)
        finally:
            if settings.USE_TEXTSCOPE_DATABASE:
                request.state.db.close()
            response_datetime = datetime.now()
            elapsed = cal_time_elapsed_seconds(request_datetime, response_datetime)
            logger.info(f"Response time: {request.state.req_time}")
            logger.info(f"Elapsed time: {elapsed}")
        return response
