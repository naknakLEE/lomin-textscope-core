import uvicorn
import sys
import os
import asyncio

from fastapi import FastAPI, Request, Depends
from fastapi import Depends, File, UploadFile, APIRouter

# from fastapi.security import OAuth2PasswordBearer
# from dataclasses import asdict
# from prometheusrock import PrometheusMiddleware, metrics_route

sys.path.append("/workspace")
from pp_server.app.routes import document

# from app.common.const import get_settings
# from app.database.connection import db
# from app.common.config import config
# from app.database.schema import create_db_table
# from app.middlewares.logging import LoggingMiddleware
# from app.middlewares.timeout_handling import TimeoutMiddleware
# from app.errors import exceptions as ex


# settings = get_settings()


def create_app() -> FastAPI:
    app = FastAPI()

    # async def get_all():
    #     return await redis_cache.keys("*")

    # @app.on_event("startup")
    # async def starup_event():
    #     await redis_cache.init_cache()

    # @app.on_event("shutdown")
    # async def shutdown_event():
    #     redis_cache.close()
    #     await redis_cache.wait_closed()

    # @app.get("/")
    # async def redis_keys():
    #     return await get_all()

    # db.init_app(app, **asdict(config()))
    # create_db_table()

    # if settings.PROFILING_TOOL == "pyinstrument":
    #     from fastapi_profiler.profiler_middleware import PyInstrumentProfilerMiddleware

    #     app.add_middleware(
    #         PyInstrumentProfilerMiddleware, unicode=True, color=True, show_all=True
    #     )
    # elif settings.PROFILING_TOOL == "cProfile":
    #     from fastapi_cprofile.profiler import CProfileMiddleware

    #     app.add_middleware(
    #         CProfileMiddleware,
    #         enable=True,
    #         server_app=app,
    #         print_each_request=True,
    #         filename="/tmp/output.pstats",
    #         strip_dirs=False,
    #         sort_by="cumulative",
    #     )
    # else:
    #     pass
    # app.add_middleware(TimeoutMiddleware)
    # app.add_middleware(LoggingMiddleware)
    # app.add_middleware(PrometheusMiddleware)

    # app.add_route("/metrics", metrics_route)

    # app.include_router(index.router, tags=["Index"], prefix="/index")
    # app.include_router(inference.router, tags=["Inference"], prefix="/inference")
    app.include_router(document.router, tags=["Document"], prefix="/post_processing")

    return app


# os.environ["API_ENV"] = "production"
app = create_app()

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=True)
