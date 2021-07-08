import uvicorn
import sys
import os
import asyncio

from fastapi.encoders import jsonable_encoder
from starlette.responses import JSONResponse
from fastapi import FastAPI, Request, Depends
from fastapi import Depends, File, UploadFile, APIRouter
from fastapi.security import OAuth2PasswordBearer
from fastapi.exceptions import RequestValidationError
from dataclasses import asdict
from prometheusrock import PrometheusMiddleware, metrics_route

from app.routes import auth, index, users, inference, admin
from app.database.connection import db
from app.common.config import config
from app.common.const import get_settings
from app.database.schema import create_db_table
from app.middlewares.logging import LoggingMiddleware
from app.middlewares.timeout_handling import TimeoutMiddleware
from app.errors import exceptions as ex


os.environ["API_ENV"] = "production"
settings = get_settings()


def create_app() -> FastAPI:
    app = FastAPI()

    db.init_app(app, **asdict(config()))
    create_db_table()

    if settings.PROFILING_TOOL == "pyinstrument":
        from fastapi_profiler.profiler_middleware import PyInstrumentProfilerMiddleware

        app.add_middleware(PyInstrumentProfilerMiddleware, unicode=True, color=True, show_all=True)
    elif settings.PROFILING_TOOL == "cProfile":
        from fastapi_cprofile.profiler import CProfileMiddleware

        app.add_middleware(
            CProfileMiddleware,
            enable=True,
            server_app=app,
            print_each_request=True,
            filename="/tmp/output.pstats",
            strip_dirs=False,
            sort_by="cumulative",
        )
    else:
        pass

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request, exc):
        return JSONResponse(
            status_code=400,
            content=jsonable_encoder(
                {
                    "status_code": 400,
                    "msg": "bad request",
                    "detail": "",
                    "code": "7400",
                    "exc": exc,
                }
            ),
        )

    app.add_middleware(TimeoutMiddleware)
    app.add_middleware(LoggingMiddleware)
    app.add_middleware(PrometheusMiddleware)

    app.add_route("/metrics", metrics_route)

    app.include_router(index.router, prefix="/v1")
    app.include_router(inference.router, tags=["inference"], prefix="/v1/inference")
    app.include_router(users.router, tags=["Users"], prefix="/v1/users")
    app.include_router(auth.router, tags=["Authentication"], prefix="/v1/auth")
    app.include_router(admin.router, tags=["Admin"], prefix="/v1/admin")

    return app


app = create_app()


if __name__ == "__main__":
    if settings.DEVELOP:
        uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
    else:
        uvicorn.run(app, host="0.0.0.0", port=8000)
