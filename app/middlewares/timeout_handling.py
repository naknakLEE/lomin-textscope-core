import time
import asyncio
import signal

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from datetime import datetime
from jose import jwt
from contextlib import contextmanager

from app.database.connection import db
from app.utils.logger import api_logger
from app.errors.exceptions import exception_handler
from app.common.const import get_settings
from app.errors import exceptions as ex


settings = get_settings()


timeout = 1.0
loop = asyncio.get_event_loop()
future = asyncio.wait_for(loop.run_in_executor(None, time.sleep, 2), timeout)


# @contextmanager
# def timeout(time):
#     # Register a function to raise a TimeoutError on the signal.
#     signal.signal(signal.SIGALRM, raise_timeout)
#     # Schedule the signal to be sent after ``time``.
#     signal.alarm(time)

#     try:
#         yield
#     except TimeoutError:
#         pass
#     finally:
#         # Unregister the signal so it won't be triggered
#         # if the timeout is not reached.
#         signal.signal(signal.SIGALRM, signal.SIG_IGN)


# def raise_timeout(signum, frame):
#     raise TimeoutError


class TimeoutMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        try:
            # return loop.run_until_complete(future)
            # with timeout(1):
            #     for i in range(100):
            #         for j in range(100):
            #             for k in range(100):
            #                 ...
            #     return call_next(request)
            return await asyncio.wait_for(call_next(request), timeout)
            # return await asyncio.wait_for(call_next(request), timeout=0.120)
        except asyncio.TimeoutError:
            raise ex.TimeoutException()
