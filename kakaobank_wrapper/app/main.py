import uvicorn
import os

from fastapi import FastAPI

from kakaobank_wrapper.app.middlewares.catch_exception import CatchExceptionMiddleware
from kakaobank_wrapper.app.routes import document_ocr


def create_app() -> FastAPI:
    app = FastAPI()
    # db.init_app(app, **asdict(config()))
    # create_db_table()
    app.add_middleware(CatchExceptionMiddleware)
    app.include_router(document_ocr.router, tags=["Document ocr"], prefix="/api/v1")

    return app


os.environ["API_ENV"] = "production"
app = create_app()

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8090, reload=True)
    # uvicorn.run(app, host="0.0.0.0", port=8090)
