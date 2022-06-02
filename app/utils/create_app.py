from fastapi import FastAPI
from dataclasses import asdict
from prometheusrock import PrometheusMiddleware, metrics_route
from rich import pretty
from rich.traceback import install
install(show_locals=True)
pretty.install()

from app.routes import auth, index, inference, dataset, prediction, dao, status, ldap
from app.database.connection import db
from app.common.config import config
from app.common.const import get_settings

from app.errors.exceptions import ResourceDataError
from app.database.schema import create_db_table, insert_initial_data
from app.middlewares.logging import LoggingMiddleware
from app.middlewares.timeout_handling import TimeoutMiddleware
from app.middlewares.exception_handler import (
    validation_exception_handler,
    resource_exception_handler,
)


settings = get_settings()


def app_generator() -> FastAPI:
    app = FastAPI()

    if settings.USE_TEXTSCOPE_DATABASE:
        db.init_app(app, **asdict(config()))
        if settings.INITIAL_DB:
            create_db_table()
            insert_initial_data()

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

    app.add_exception_handler(RuntimeError, validation_exception_handler)
    app.add_exception_handler(ResourceDataError, resource_exception_handler)

    app.add_middleware(TimeoutMiddleware)
    app.add_middleware(LoggingMiddleware)
    app.add_middleware(PrometheusMiddleware)

    app.add_route("/metrics", metrics_route)

    app.include_router(index.router, prefix="/v1")
    app.include_router(status.router, tags=["Status"])
    app.include_router(ldap.router, tags=["Ldap"], prefix="/v1/ldap")
    app.include_router(inference.router, tags=["Inference"], prefix="/v1/inference")
    app.include_router(auth.router, tags=["Authentication"], prefix="/v1/auth")
    app.include_router(
        dataset.router, tags=["Training dataset"], prefix="/dataset/training"
    )
    app.include_router(
        prediction.router, tags=["Prediction Result"], prefix="/prediction"
    )
    app.include_router(dao.router, tags=["Dao"], prefix="/dao")
    
    return app
