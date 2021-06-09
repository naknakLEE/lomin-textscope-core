import uvicorn
import sys
import os

from fastapi import FastAPI
from dataclasses import asdict
from prometheusrock import PrometheusMiddleware, metrics_route

sys.path.append("/workspace")
from app.routes import auth, index, users, inference, admin
from app.database.connection import db
from app.common.config import Config
from app.common.const import get_settings
from app.database.schema import create_db_table
from app.middlewares.logging import LoggingMiddleware


settings = get_settings()


def create_app() -> FastAPI:
    app = FastAPI()
    db.init_app(app, **asdict(Config()))

    create_db_table()

    if settings.PROFILING_TOOL == "pyinstrument":
        from fastapi_profiler.profiler_middleware import PyInstrumentProfilerMiddleware
        app.add_middleware(PyInstrumentProfilerMiddleware, unicode=True, color=True, show_all=True)
    elif settings.PROFILING_TOOL == "cProfile":
        from fastapi_cprofile.profiler import CProfileMiddleware
        app.add_middleware(CProfileMiddleware, enable=True, server_app=app, print_each_request=True, filename='/tmp/output.pstats', strip_dirs=False, sort_by='cumulative')
    else:
        pass
    app.add_middleware(LoggingMiddleware)
    app.add_middleware(PrometheusMiddleware)

    app.add_route("/metrics", metrics_route)

    app.include_router(index.router)
    app.include_router(inference.router, tags=["inference"], prefix="/inference")
    app.include_router(users.router, tags=["Users"], prefix="/users")
    app.include_router(auth.router, tags=["Authentication"], prefix="/auth")
    app.include_router(admin.router, tags=["Admin"], prefix="/admin")
    return app

app = create_app()

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
