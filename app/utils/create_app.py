from fastapi import FastAPI
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.openapi.docs import (
    get_redoc_html,
    get_swagger_ui_html,
    get_swagger_ui_oauth2_redirect_html,
)
from dataclasses import asdict

from prometheusrock import PrometheusMiddleware, metrics_route
from rich import pretty
from rich.traceback import install
install(show_locals=True)
pretty.install()

from app.routes import auth, index, inference, dataset, prediction, dao, status, ldap, websocket, users, test, rpa, drm, base, front
from app.routes import document, model, inspect
from app.database.connection import db
from app.common.config import config
from app.common.const import get_settings

from app.errors.exceptions import ResourceDataError
from app.database.schema import (
    create_db_table,
    create_extension,
    create_db_users,
    insert_initial_data
)
from app.middlewares.logging import LoggingMiddleware
from app.middlewares.timeout_handling import TimeoutMiddleware
from app.middlewares.exception_handler import (
    validation_exception_handler,
    resource_exception_handler,
    core_exception_handler,
    CoreCustomException
)


settings = get_settings()


def app_generator() -> FastAPI:
    app = FastAPI(docs_url=None, redoc_url=None)

    ################ swagger redoc offline ################
    app.mount("/static", StaticFiles(directory="static"), name="static")
    @app.get("/docs", include_in_schema=False)
    async def custom_swagger_ui_html():
        return get_swagger_ui_html(
            openapi_url=app.openapi_url,
            title=app.title + " - Swagger UI",
            oauth2_redirect_url=app.swagger_ui_oauth2_redirect_url,
            swagger_js_url="/static/swagger-ui-bundle.js",
            swagger_css_url="/static/swagger-ui.css",
        )
    @app.get(app.swagger_ui_oauth2_redirect_url, include_in_schema=False)
    async def swagger_ui_redirect():
        return get_swagger_ui_oauth2_redirect_html()


    @app.get("/redoc", include_in_schema=False)
    async def redoc_html():
        return get_redoc_html(
            openapi_url=app.openapi_url,
            title=app.title + " - ReDoc",
            redoc_js_url="/static/redoc.standalone.js",
        )
    ################ swagger redoc offline ################


    if settings.USE_TEXTSCOPE_DATABASE:
        db.init_app(app, **asdict(config()))
        if settings.INITIAL_DB:
            create_db_table()
            create_extension()
            create_db_users()
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
    app.add_exception_handler(CoreCustomException, core_exception_handler)

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
    app.include_router(websocket.router, tags=["WebSocket"], prefix="/ws")
    app.include_router(model.router, tags=["Model"], prefix="/v1/model")

    
    app.include_router(document.router, tags=["Kei Document Info"], prefix="/v1/docx/info", include_in_schema=True)
    app.include_router(inspect.router, tags=["Kei Inpsect Info"], prefix="/v1/docx/inspect", include_in_schema=True)
    
    app.include_router(users.router, tags=["Company User Info"], prefix="/v1/user", include_in_schema=True)
    
    app.include_router(test.router, tags=["Kei Connection Test Api"], prefix="/test", include_in_schema=True)
    app.include_router(rpa.router, tags=["Kei Robotic Process Automation"], prefix="/v1/rpa", include_in_schema=True)
    app.include_router(drm.router, tags=["Kei DRM"], prefix="/v1/drm", include_in_schema=True)
    app.include_router(base.router, tags=["nak2210 API"], prefix="/api/v1", include_in_schema=True)

    app.include_router(front.router, tags=["nak2210 DashBoard API"], prefix="", include_in_schema=True)

    return app
