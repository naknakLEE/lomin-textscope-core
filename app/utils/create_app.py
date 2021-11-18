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

from app.routes import (
    auth,
    index,
    users,
    inference,
    admin,
    dataset
)
from app.database.connection import db
from app.common.config import config
from app.common.const import get_settings
from app.database.schema import create_db_table
from app.middlewares.logging import LoggingMiddleware
from app.middlewares.timeout_handling import TimeoutMiddleware
from app.middlewares.exception_handler import validation_exception_handler
from app.errors import exceptions as ex


settings = get_settings()


def app_generator() -> FastAPI:
    app = FastAPI()

    db.init_app(app, **asdict(config()))
    create_db_table()

    if settings.PROFILING_TOOL == "pyinstrument":
        from fastapi_profiler.profiler_middleware import PyInstrumentProfilerMiddleware

        app.add_middleware(
            PyInstrumentProfilerMiddleware, unicode=True, color=True, show_all=True
        )
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

    app.add_exception_handler(RuntimeError, validation_exception_handler)

    app.add_middleware(TimeoutMiddleware)
    app.add_middleware(LoggingMiddleware)
    app.add_middleware(PrometheusMiddleware)

    app.add_route("/metrics", metrics_route)

    app.include_router(index.router, prefix="/v1")
    app.include_router(inference.router, tags=["inference"], prefix="/v1/inference")
    app.include_router(users.router, tags=["Users"], prefix="/v1/users")
    app.include_router(auth.router, tags=["Authentication"], prefix="/v1/auth")
    app.include_router(admin.router, tags=["Admin"], prefix="/v1/admin")
    app.include_router(dataset.router, tags=["Training dataset"], prefix="/dataset/training")

    return app
