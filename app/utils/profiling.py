import time
import cProfile
import pstats
import cv2

from fastapi.testclient import TestClient
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from dataclasses import asdict
from datetime import datetime
from pyinstrument import Profiler
from pyinstrument_flame import FlameGraphRenderer
from starlette.middleware.base import RequestResponseEndpoint

from app.routes import auth, index, users, inference
from app.database.connection import db
from app.common.config import Config
from app.utils.logger import api_logger
from app.common.const import get_settings
from app.database.schema import create_db_table
from app.errors.exceptions import exception_handler


app = FastAPI()
db.init_app(app, **asdict(Config()))

settings = get_settings()
fake_user_info = settings.FAKE_USER_INFORMATION
create_db_table()


@app.middleware("http")
async def add_process_time_header(
    request: Request, call_next: RequestResponseEndpoint
) -> None:
    try:
        request.state.req_time = datetime.utcnow()
        request.state.start = time.time()
        request.state.inspect = None
        request.state.user = None
        request.state.db = db._session()
        ip = (
            request.headers["x-forwarded-for"]
            if "x-forwarded-for" in request.headers.keys()
            else request.client.host
        )
        request.state.ip = ip.split(",")[0] if "," in ip else ip
        response = await call_next(request)
        await api_logger(request=request, response=response)
    except Exception as e:
        error = await exception_handler(e)
        error_dict = dict(
            status=error.status_code,
            msg=error.msg,
            detail=error.detail,
            code=error.code,
        )
        response = JSONResponse(status_code=error.status_code, content=error_dict)
        await api_logger(request=request, error=error)
    finally:
        request.state.db.close()
    return response


app.include_router(index.router)
app.include_router(inference.router, tags=["inference"])
app.include_router(users.router, tags=["Users"], prefix="/users")
app.include_router(auth.router, tags=["Authentication"], prefix="/auth")


client = TestClient(app)


image_dir = "test.jpg"
token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyIiwiZXhwIjoxNjIyMTg3MjQxfQ.XvKljVY9zmor3DB8snNOCSFYRvarFoe0cQyFvbqUD9U"

img = cv2.imread(image_dir)
_, img_encoded = cv2.imencode(".jpg", img)


def test_main() -> None:
    login_data = {
        "username": fake_user_info["username"],
        "password": fake_user_info["password"],
    }
    headers = {
        "accept": "application/json",
        "Content-Type": "application/x-www-form-urlencoded",
    }
    response = client.post("/auth/token", headers=headers, data=login_data)
    token = response.json()["access_token"]
    response = client.post(
        f"/inference?token={token}",
        headers={
            "accept": "application/json",
        },
        files={"file": img_encoded.tobytes()},
    )
    print(response.json())


settings.PROFILING_TOOL = "pyinstrument"
if settings.PROFILING_TOOL == "pyinstrument":
    profiler = Profiler()
    profiler.start()
    test_main()
    profiler.stop()
    if settings.PYINSTRUMENT_RENDERER == "flame_chart":
        renderer = FlameGraphRenderer(title="Task profile", flamechart=True)
        svg = profiler.output(renderer)
        html_file = open("pytinstrument_result_flame_chart_svg.html", "w")
        html_file.write(svg)
    elif settings.PYINSTRUMENT_RENDERER == "html":
        html_file = open("pytinstrument_result.html", "w")
        html_file.write(profiler.output_html())
        html_file.close()
elif settings.PROFILING_TOOL == "cProfile":
    profiler = cProfile.Profile()
    profiler.enable()
    test_main()
    stats = pstats.Stats(profiler).sort_stats("tottime")
    stats.strip_dirs()
    stats.print_stats()
