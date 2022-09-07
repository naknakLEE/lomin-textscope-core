import time

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from fastapi import Request, Response
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from starlette.types import Scope, Message
from datetime import datetime
from jose import jwt
from app.errors.exceptions import APIException

from app.utils.logging import logger
from app.database.connection import db
from app.utils.logger import api_logger
from app.middlewares.exception_handler import exception_handler
from app.common.const import get_settings
from app.utils.utils import cal_time_elapsed_seconds
from app.schemas import error_models as ErrorResponse


settings = get_settings()


class RequestWithBody(Request):
    def __init__(self, scope: Scope, body: bytes) -> None:
        super().__init__(scope, self._receive)
        self._body = body
        self._body_returned = False

    async def _receive(self) -> Message:
        if self._body_returned:
            return {"type": "http.disconnect"}
        else:
            self._body_returned = True
            return {"type": "http.request", "body": self._body, "more_body": False}

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
            json_body = {}
            if request.headers.get("content-type") == "application/json":
                json_body = await request.json()
            body = await request.body()
            form = await request.form()
            logger.info(f"{request.method} {request.url.path} Request Info \n\
            Request header{request.headers} ")
            request = RequestWithBody(request.scope, body)
            if settings.USE_TEXTSCOPE_DATABASE:
                request.state.db = next(db.session())
            headers = request.headers
            ip = (
                headers["x-forwarded-for"]
                if "x-forwarded-for" in request.headers.keys()
                else request.client.host
            )
            ip = ip if ip is not None else "127.0.0.1"
            request.state.ip = ip.split(",")[0] if "," in ip else ip
            if "authorization" in headers.keys():
                token = headers.get("Authorization")
                payload = jwt.decode(
                    token.replace("Bearer ", ""),
                    settings.SECRET_KEY,
                    algorithms=[settings.ALGORITHM],
                )
                request.state.email = payload.get("sub")
            logger.info("finsh middleware.. start request")
            response = await call_next(request)
            api_logger(request=request, response=response)
        except jwt.ExpiredSignatureError as e:
            error = await exception_handler(e)
            error_dict = parse_error_dict(error)
            status_code, error_model = ErrorResponse.ErrorCode.get(2402)
            response = JSONResponse(status_code=status_code, content=jsonable_encoder({"error": error_model}))
            api_logger(request=request, error=error)
        except jwt.JWTError as e:
            error = await exception_handler(e)
            error_dict = parse_error_dict(error)
            status_code, error_model = ErrorResponse.ErrorCode.get(2403)
            response = JSONResponse(status_code=status_code, content=jsonable_encoder({"error": error_model}))
            api_logger(request=request, error=error)
        except Exception as e:
            error = await exception_handler(e)
            error_dict = parse_error_dict(error)
            response = JSONResponse(status_code=error.status_code, content=error_dict)
            api_logger(request=request, error=error)
        finally:
            if settings.USE_TEXTSCOPE_DATABASE:
                request.state.db.close()
            response_datetime = datetime.now()
            elapsed = cal_time_elapsed_seconds(request_datetime, response_datetime)
            logger.info(f"Response time: {response_datetime}")
            logger.info(f"Elapsed time: {elapsed}")
        return response


def parse_error_dict(exection: APIException):
    return dict(
        status=exection.status_code,
        msg=exection.msg,
        detail=exection.detail,
        code=exection.code,
        error=dict(
            error_code=exection.code,
            error_message=str(exection.detail) + ", " + str(exection.msg)
        )
    )