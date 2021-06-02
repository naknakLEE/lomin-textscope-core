import time
import sys

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from datetime import datetime


sys.path.append("/workspace")
from app.database.connection import db
from app.utils.logger import api_logger
from app.errors.exceptions import exception_handler


class AddLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        try:
            request.state.req_time = datetime.utcnow()
            request.state.start = time.time()
            request.state.inspect = None
            request.state.user = None
            request.state.db = db._session()
            ip = request.headers["x-forwarded-for"] if "x-forwarded-for" in request.headers.keys() else request.client.host
            request.state.ip = ip.split(",")[0] if "," in ip else ip
            response = await call_next(request)
            await api_logger(request=request, response=response)
        except Exception as e:
            error = await exception_handler(e)
            error_dict = dict(status=error.status_code, msg=error.msg, detail=error.detail, code=error.code)
            response = JSONResponse(status_code=error.status_code, content=error_dict)
            await api_logger(request=request, error=error)
        finally:
            request.state.db.close()
        return response
