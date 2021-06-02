import uvicorn
import sys

from prometheusrock import PrometheusMiddleware, metrics_route
from fastapi import FastAPI
from fastapi_profiler.profiler_middleware import PyInstrumentProfilerMiddleware
from fastapi_cprofile.profiler import CProfileMiddleware
from dataclasses import asdict

sys.path.append("/workspace")
from app.routes import auth, index, users, inference
from app.database.connection import db
from app.common.config import Config
from app.common.const import get_settings
from app.database.schema import create_db_table
from app.middlewares.logging import AddLoggingMiddleware


def create_app():
    app = FastAPI()
    db.init_app(app, **asdict(Config()))

    settings = get_settings()
    create_db_table()


    if settings.PROFILING_TOOL == "pyinstrument":
        app.add_middleware(PyInstrumentProfilerMiddleware, unicode=True, color=True, show_all=True)
    elif settings.PROFILING_TOOL == "cProfile":
        app.add_middleware(CProfileMiddleware, enable=True, server_app=app, print_each_request=True, filename='/tmp/output.pstats', strip_dirs=False, sort_by='cumulative')
    else:
        pass

    app.add_middleware(AddLoggingMiddleware)
    app.add_middleware(PrometheusMiddleware)
    app.add_route("/metrics", metrics_route)

    app.include_router(index.router)
    app.include_router(inference.router, tags=["inference"])
    app.include_router(users.router, tags=["Users"], prefix="/users")
    app.include_router(auth.router, tags=["Authentication"], prefix="/auth")
    return app

app = create_app()

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
