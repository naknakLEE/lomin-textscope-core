import uvicorn
import os

from fastapi import FastAPI

from kb_wrapper.app.common.const import get_settings
from kb_wrapper.app.middlewares.catch_exception import CatchExceptionMiddleware
from kb_wrapper.app.routes import idcard_ocr


settings = get_settings()


def create_app() -> FastAPI:
    app = FastAPI()
    # db.init_app(app, **asdict(config()))
    # create_db_table()
    app.add_middleware(CatchExceptionMiddleware)
    app.include_router(idcard_ocr.router, tags=["Document ocr"])

    return app


os.environ["API_ENV"] = "production"
app = create_app()

if __name__ == "__main__":
    if settings.DEVELOP:
        uvicorn.run("main:app", host="0.0.0.0", port=8090, reload=True)
    else:
        uvicorn.run(app, host="0.0.0.0", port=8090)
