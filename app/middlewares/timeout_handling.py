import time
import asyncio

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from datetime import datetime
from jose import jwt

from app.database.connection import db
from app.utils.logger import api_logger
from app.errors.exceptions import exception_handler
from app.common.const import get_settings
from app.errors import exceptions as ex


settings = get_settings()


timeout = 0.5
loop = asyncio.get_event_loop()
future = asyncio.wait_for(loop.run_in_executor(None, time.sleep, 2), timeout)

class TimeoutMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, 
        request: Request, 
        call_next: RequestResponseEndpoint
    ) -> Response:
        try:
            # return loop.run_until_complete(future)
            return await asyncio.wait_for(call_next(request), 0.1)
            # return await asyncio.wait_for(call_next(request), timeout=0.120)
        except asyncio.TimeoutError:
            raise ex.TimeoutException()
