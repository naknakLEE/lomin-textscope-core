import httpx

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from fastapi import Request, Response
from fastapi.responses import JSONResponse

from kb_wrapper.app.utils.ocr_response_parser import response_handler


class CatchExceptionMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint):
        try:
            return await call_next(request)
        except httpx.RequestError as exc:
            print(f"An error occurred while requesting {exc.request.url!r}.")
            response = response_handler(status=2400)
            return JSONResponse(status_code=200, content=response)
        except httpx.HTTPStatusError as exc:
            print(
                f"Error response {exc.response.status_code} while requesting {exc.request.url!r}."
            )
            response = response_handler(status=exc.response.status_code)
            return JSONResponse(status_code=200, content=response)
        except httpx.HTTPError as exc:
            print(f"HTTP Exception for {exc.request.url} - {exc}")
        # except Exception as error:
        #     print('\033[95m' + f"{error}" + '\033[95m')
        #     response = response_handler(status=9400)
        #     return JSONResponse(status_code=200, content=response)
