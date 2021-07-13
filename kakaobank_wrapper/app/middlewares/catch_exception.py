import httpx
import traceback
import sys

from loguru import logger
from fastapi import Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from kakaobank_wrapper.app.utils.ocr_response_parser import response_handler


class CatchExceptionMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint):
        try:
            return await call_next(request)
        except httpx.RequestError as exc:
            logger.debug(f"An error occurred while requesting {exc.request.url!r}.")
            response = await response_handler(status=2400)
            return JSONResponse(status_code=200, content=jsonable_encoder(response))
        except httpx.HTTPStatusError as exc:
            logger.debug(
                f"Error response {exc.response.status_code} while requesting {exc.request.url!r}."
            )
            if exc.response.status_code <= 1000:
                ...
            response = await response_handler(status=exc.response.status_code)
            return JSONResponse(status_code=200, content=jsonable_encoder(response))
        except httpx.HTTPError as exc:
            logger.debug(f"HTTP Exception for {exc.request.url} - {exc}")
            response = await response_handler(status=exc.response.status_code)
            return JSONResponse(status_code=200, content=jsonable_encoder(response))
        except Exception as e:
            logger.debug(f"Unexpected error: {sys.exc_info()}")
            logger.debug(traceback.print_exc())
            response = await response_handler(status=3400)
            return JSONResponse(status_code=200, content=jsonable_encoder(response))
