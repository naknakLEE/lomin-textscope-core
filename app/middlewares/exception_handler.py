from fastapi.encoders import jsonable_encoder
from starlette.responses import JSONResponse
from fastapi import Request
from app.errors.exceptions import ResourceDataError, APIException
from app.utils.logging import logger
from app.schemas import error_models as ErrorResponse
import traceback


async def resource_exception_handler(
    request: Request, exc: ResourceDataError
) -> JSONResponse:
    # @TODO: db 혹은 file로 log 남기기
    # Logs.create(request.state.db, auto_commit=True, **log_dict)
    return JSONResponse(status_code=400, content=exc.detail)


async def validation_exception_handler(
    request: Request, exc: RuntimeError
) -> JSONResponse:
    return JSONResponse(
        status_code=400,
        content=jsonable_encoder(
            {
                "status_code": 400,
                "msg": "bad request",
                "detail": "",
                "code": "7400",
                "exc": exc,
            }
        ),
    )

class CoreCustomException(Exception):
    def __init__(self, error_code: int, error_msg:str = None ):
        self.status_code, self.error = ErrorResponse.ErrorCode.get(error_code)
        if error_msg:
            self.error.error_message = self.error.error_message.format(error_msg)
        # 백그라운드 로그용
        logger.error(f"status_code {self.status_code} error_code {self.error.error_code} error_message {self.error.error_message}")

async def core_exception_handler(request: Request, exc: CoreCustomException) -> JSONResponse:
    traceback.print_exc()
    return JSONResponse(status_code=exc.status_code, content=jsonable_encoder({"error":exc.error}))

async def exception_handler(error: Exception) -> APIException:
    if not isinstance(error, APIException):
        error = APIException(exc=error, detail=str(error))
    return error
