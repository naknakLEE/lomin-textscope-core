import time

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from fastapi import Request, Response
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from datetime import datetime
from jose import jwt
from app.errors.exceptions import APIException

from app.utils.logging import logger
from app.database.connection import db
from app.utils.logger import api_logger
from app.middlewares.exception_handler import exception_handler
from app.common.const import get_settings
from app.utils.utils import cal_time_elapsed_seconds, get_ts_uuid
from app.schemas import error_models as ErrorResponse
from app.utils.auth import jwt_decode
from app.database.schema import LogAPI


settings = get_settings()


class LoggingMiddleware(BaseHTTPMiddleware):

    INSERT_LOG_INFO_API: list = [
        "POST_/api/v1/inference/ocr",
        "PUT_/api/v1/pdf"
    ]

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        request_datetime = datetime.now()

        api_is_success = False
        try:
            request.state.req_time = request_datetime
            request.state.start = time.time()
            request.state.inspect = None
            request.state.user = None
            request.state.db = next(db.session())            
            if(f"{request.method}_{request.url.path}" in self.INSERT_LOG_INFO_API):
                api_id = get_ts_uuid('log_api')
                request.state.api_id = api_id
            headers = request.headers
            ip = (
                headers["x-forwarded-for"]
                if "x-forwarded-for" in request.headers.keys()
                else request.client.host
            )
            ip = ip if ip is not None else "127.0.0.1"
            request.state.ip = ip.split(",")[0] if "," in ip else ip
            
            # 국가기록원 방어코드(2022-11-28 Issue)
            request.state.ip = '127.0.0.1'

            if "authorization" in headers.keys():
                token = headers.get("Authorization")
                token_data = jwt_decode(token.replace("Bearer ", ""))
                
                if request.state.ip != token_data.loc:
                    raise jwt.ExpiredSignatureError
                
                request.state.email = token_data.email
            response = await call_next(request)
            api_logger(request=request, response=response)
            api_is_success = True
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
            # if settings.USE_TEXTSCOPE_DATABASE:
            #     request.state.db.close()

            if(f"{request.method}_{request.url.path}" in self.INSERT_LOG_INFO_API):
                elapsed_datetime = cal_time_elapsed_seconds(request.state.req_time, datetime.now())
                api_log_dict = dict({
                    'api_id': api_id,
                    'api_end_point': request.url.path,
                    'api_method': request.method,
                    'api_status_code': response.status_code,
                    'api_is_success': api_is_success,
                    'api_response_time': elapsed_datetime  
                })
                LogAPI.create(
                    session=request.state.db,
                    **api_log_dict
                )                 
                 
            request.state.db.close()            
            response_datetime = datetime.now()
            elapsed = cal_time_elapsed_seconds(request_datetime, response_datetime)
            logger.info(f"Req: {request_datetime}, Res: {response_datetime}, - {elapsed}s")
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