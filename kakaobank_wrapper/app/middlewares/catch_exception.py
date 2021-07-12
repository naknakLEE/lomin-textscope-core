import httpx
import traceback
import sys

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from loguru import logger

from kakaobank_wrapper.app.utils.ocr_response_parser import response_handler


class CatchExceptionMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint):
        try:
            response = await call_next(request)
            logger.debug(response["body_iterator"])
            return response
        except httpx.RequestError as exc:
            logger.debug(f"An error occurred while requesting {exc.request.url!r}.")
            response = response_handler(status=2400)
            return JSONResponse(status_code=200, content=response)
        except httpx.HTTPStatusError as exc:
            logger.debug(
                f"Error response {exc.response.status_code} while requesting {exc.request.url!r}."
            )
            if exc.response.status_code <= 1000:
                ...
            response = response_handler(status=exc.response.status_code)
            return JSONResponse(status_code=200, content=response)
        except httpx.HTTPError as exc:
            logger.debug(f"HTTP Exception for {exc.request.url} - {exc}")
            response = response_handler(status=exc.response.status_code)
            return JSONResponse(status_code=200, content=response)
        except:
            logger.debug(f"Unexpected error: {sys.exc_info()}")
            logger.debug(traceback.print_exc())
            response = response_handler(status=3400)
            return JSONResponse(status_code=200, content=response)
