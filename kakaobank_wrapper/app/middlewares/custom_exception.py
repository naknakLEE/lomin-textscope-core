from fastapi.encoders import jsonable_encoder
from starlette.responses import JSONResponse
from fastapi import Request


async def CustomHTTPException(request: Request, exc: RuntimeError) -> JSONResponse:
    return JSONResponse(status_code=200, content=exc.detail)
