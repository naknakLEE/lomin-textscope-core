import uvicorn
import os

from fastapi import FastAPI, HTTPException
from loguru import logger
from requests.sessions import Request
from starlette.responses import JSONResponse

from kakaobank_wrapper.app.routes import document_ocr
from kakaobank_wrapper.app.common.const import get_settings
from kakaobank_wrapper.app.middlewares.catch_exception import CatchExceptionMiddleware
from kakaobank_wrapper.app.middlewares.custom_exception import CustomHTTPException

# from kakaobank_wrapper.app.errors.exceptions import HTTPException
from fastapi.responses import PlainTextResponse


settings = get_settings()


def create_app() -> FastAPI:
    app = FastAPI()
    # db.init_app(app, **asdict(config()))
    # create_db_table()
    app.add_middleware(CatchExceptionMiddleware)
    app.add_exception_handler(HTTPException, CustomHTTPException)
    app.include_router(document_ocr.router, tags=["Document ocr"], prefix="/api/v1")

    return app


os.environ["API_ENV"] = "production"
app = create_app()


@app.get("/testapi/v1")
async def GetTestException():
    raise HTTPException(status_code="200", detail={})


if __name__ == "__main__":
    if settings.DEVELOP:
        uvicorn.run("main:app", host="0.0.0.0", port=8090, reload=True)
    else:
        uvicorn.run(app, host="0.0.0.0", port=8090)
