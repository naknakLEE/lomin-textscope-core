import uvicorn
import os

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError

from kb_wrapper.app.common.const import get_settings
from kb_wrapper.app.middlewares.logging import LoggingMiddleware
from kb_wrapper.app.routes import idcard_ocr


settings = get_settings()


def create_app() -> FastAPI:
    app = FastAPI()
    # db.init_app(app, **asdict(config()))
    # create_db_table()
    app.add_middleware(LoggingMiddleware)
    app.include_router(idcard_ocr.router, tags=["Document ocr"])

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request, exc):
        return JSONResponse(
            status_code=200,
            content=jsonable_encoder(
                {
                    "status_code": 2000,
                    "error_message": "파라미터가 누락됨",
                }
            ),
        )

    return app


os.environ["API_ENV"] = "production"
app = create_app()

if __name__ == "__main__":
    if settings.DEVELOP:
        uvicorn.run("main:app", host="0.0.0.0", port=8090, reload=True)
    else:
        uvicorn.run(app, host="0.0.0.0", port=8090)
