from fastapi.encoders import jsonable_encoder
from starlette.responses import JSONResponse
from fastapi import Request
from app.errors.exceptions import ResourceDataError


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
