import uvicorn
import os

from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from requests.sessions import Request
from starlette.responses import JSONResponse

from kakaobank_wrapper.app.utils.logging import logger
from kakaobank_wrapper.app.routes import document_ocr
from kakaobank_wrapper.app.common.const import get_settings
from kakaobank_wrapper.app.middlewares.logging import LoggingMiddleware
from kakaobank_wrapper.app.middlewares.custom_exception import (
    http_exception_handler,
    validation_exception_handler,
)

# from kakaobank_wrapper.app.errors.exceptions import HTTPException
from fastapi.responses import PlainTextResponse


settings = get_settings()


def create_app() -> FastAPI:
    app = FastAPI()
    # db.init_app(app, **asdict(config()))
    # create_db_table()
    app.add_middleware(LoggingMiddleware)
    # app.add_middleware(LoggingMiddleware)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.include_router(document_ocr.router, tags=["Document ocr"], prefix="/api/v1")

    return app


os.environ["API_ENV"] = "production"
app = create_app()


if __name__ == "__main__":
    if settings.DEVELOP:
        uvicorn.run("main:app", host="0.0.0.0", port=8090, reload=True)
    else:
        uvicorn.run(app, host="0.0.0.0", port=8090)
