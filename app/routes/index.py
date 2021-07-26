import requests
import time

from fastapi.responses import StreamingResponse
from fastapi.datastructures import UploadFile
from fastapi import Body
from typing import Any
from datetime import datetime
from fastapi import APIRouter, Depends, File, FastAPI
from fastapi.testclient import TestClient
from fastapi.requests import Request
from sqlalchemy.orm import Session
from starlette.responses import Response, JSONResponse
from fastapi.encoders import jsonable_encoder
from inspect import currentframe as frame

from app.database.connection import db
from app.database.schema import Users, Usage, Logs
from app.common.const import get_settings
from app import models


settings = get_settings()
router = APIRouter()
app = FastAPI()
client = TestClient(app)


# @router.get("/")
# async def index(session: Session = Depends(db.session)) -> Response:
#     # Users.remove(session, "tongo@example.com")
#     Users.create(session, auto_commit=True, **settings.FAKE_USER_INFORMATION)
#     # Users.remove(session, "gule@example.com")

#     # # user = Users.get_by_email(session, email="user@example.com")
#     # # print('\033[96m' + f"\n{user.__dict__}" + '\033[0m')
#     # # print("")

#     # # users = Users.get_multi(session, skip=0, limit=10)
#     # # for user in users:
#     # #     print('\033[96m' + f"{user.__dict__}" + '\033[0m')
#     # current_user = User(**settings.FAKE_USER_INFORMATION)
#     # user_in = UserUpdate(**settings.FAKE_USER_INFORMATION2)
#     # user = Users.update(session, db_obj=current_user, obj_in=user_in)
#     # print('\033[96m' + f"{user.__dict__}" + '\033[0m')

#     # print('\033[96m' + f"{user}" + '\033[0m')

#     curren_time = datetime.utcnow()
#     return Response(f"Textscope API (UTC: {curren_time.strftime('%Y.%m.%d %H:%M:%S')})")


async def sleep_func():
    time.sleep(5)
    return 342


# @router.get("/test")
# async def test(request: Request) -> Response:
#     # print("state.user", request.state.user)
#     # await index()
#     # Errors.create(next(db.session()), auto_commit=True)
#     # Users.create(session, auto_commit=True, name="test", **FAKE_USER_NFORMATION)
#     # await sleep_func()
#     # task = asyncio.create_task(sleep_func())
#     # await task
#     # sleep_func()
#     # try:
#     #     a = 1/0
#     # except Exception as e:
#     #     request.state.inspect = frame()
#     #     raise e
#     current_time = datetime.utcnow()
#     return Response(f"Notification API (UTC: {current_time.strftime('%Y.%m.%d %H:%M:%S')})")


@router.get("/status", response_model=models.StatusResponse)
def check_status() -> Any:
    """
    ### 서버 상태 체크
    응답 데이터: Textscope API (is_database_working: $(is_database_working), is_serving_server_working: $(is_serving_server_working))
    -  is_database_working: 데이터베이스 서버와 연결 상태 확인
    -  is_serving_server_working: 모델 서버와 연결 상태 확인
    """
    try:
        serving_server_status_check_url = (
            f"http://{settings.SERVING_IP_ADDR}:{settings.SERVING_IP_PORT}/healthz"
        )
        response = requests.get(serving_server_status_check_url)
        assert response.status_code == 200
        is_serving_server_working = "True"
    except Exception:
        is_serving_server_working = "False"

    try:
        session = next(db.session())
        session.execute("SELECT 1")
        is_database_working = "True"
    except Exception:
        is_database_working = "False"
    finally:
        session.close()

    status = f"is_database_working: {is_database_working}, is_serving_server_working: {is_serving_server_working}"
    return Response(f"Textscope API ({status})")


@router.get("/start_stage")
def check_status() -> Any:
    # client.get("/stage_one")
    return stage_one()


# @router.get("/stage_one")
def stage_one() -> Any:
    # client.get("/stage_two")
    return stage_two()


# @router.get("/stage_two")
def stage_two() -> Any:
    # client.get("/stage_three")
    return stage_three()


# @router.get("/stage_three")
def stage_three() -> Any:
    json_compatible_item_data = jsonable_encoder("All stage completed")
    return JSONResponse(content=json_compatible_item_data)
