from fastapi.encoders import jsonable_encoder
from starlette.responses import JSONResponse
from fastapi import Request


async def validation_exception_handler(request: Request, exc: RuntimeError) -> JSONResponse:
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
