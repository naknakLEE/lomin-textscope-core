from loguru import logger
from fastapi.encoders import jsonable_encoder
from starlette.responses import JSONResponse
from fastapi import Request
from kakaobank_wrapper.app.errors import exceptions as ex


async def http_exception_handler(request: Request, exc: RuntimeError) -> JSONResponse:
    return JSONResponse(status_code=200, content=exc.detail)


async def validation_exception_handler(request: Request, exc: RuntimeError) -> JSONResponse:
    loc = ", ".join(exc.errors()[0].get("loc"))
    result = vars(ex.parameterException(minQlt="00", description=f"{loc} is required"))
    return JSONResponse(
        status_code=200,
        content=jsonable_encoder(result),
    )
