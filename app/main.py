import uvicorn
import time

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from os import path
from dataclasses import asdict
from datetime import datetime
from fastapi_profiler.profiler_middleware import PyInstrumentProfilerMiddleware

from routes import auth, index, users, inference
from database.connection import db
from common.config import Config
from utils.logger import api_logger
from utils.token_validator import exception_handler
from common.const import get_settings



# API_KEY_HEADER = APIKeyHeader(name="Authorization", auto_error=False)
base_dir = path.dirname(path.dirname(path.abspath(__file__)))


app = FastAPI()
db.init_app(app, **asdict(Config()))
settings = get_settings()


# app.add_middleware(middleware_class=BaseHTTPMiddleware, dispatch=access_control)
if settings.PROFILING is not None:
    app.add_middleware(PyInstrumentProfilerMiddleware)
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    try: 
        request.state.req_time = datetime.utcnow()
        request.state.start = time.time()
        request.state.inspect = None
        request.state.user = None
        request.state.db = db._session()
        ip = request.headers["x-forwarded-for"]  if "x-forwarded-for" in request.headers.keys() else request.client.host
        request.state.ip = ip.split(",")[0] if "," in ip else ip
        response = await call_next(request)
        await api_logger(request=request, response=response)
    except Exception as e:
        error = await exception_handler(e)
        error_dict = dict(status=error.status_code, msg=error.msg, detail=error.detail, code=error.code)
        response = JSONResponse(status_code=error.status_code, content=error_dict)
        await api_logger(request=request, error=error)
    finally:
        request.state.db.close()
    return response



app.include_router(index.router)
app.include_router(inference.router, tags=["inference"])
app.include_router(users.router, tags=["Users"], prefix="/users")
app.include_router(auth.router, tags=["Authentication"], prefix="/auth")


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

   

# async def create_app():
#     await load_dotenv(env_path)

#     app = FastAPI()
#     db.init_app(app, **asdict(Config()))

#     app.add_middleware(middleware_class=BaseHTTPMiddleware, dispatch=access_control)

#     app.include_router(index.router)
#     app.include_router(inference.router, tags=["inference"])
#     app.include_router(users.router, tags=["Users"], prefix="/users")
#     app.include_router(auth.router, tags=["Authentication"], prefix="/auth")


# app = create_app()