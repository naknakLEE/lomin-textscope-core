import requests

from typing import Any
from datetime import datetime
from fastapi import APIRouter, Depends
from fastapi.requests import Request
from sqlalchemy.orm import Session
from fastapi.responses import JSONResponse
from starlette.responses import Response
from inspect import currentframe as frame

from app.database.connection import db
from app.database.schema import Users, Usage, Logs
from app.common.const import get_settings
from app.models import User, UserUpdate



settings = get_settings()
router = APIRouter()


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


# @router.get("/test")
# async def test(request: Request) -> Response:
#     print("state.user", request.state.user)
#     # await index()
#     # Errors.create(next(db.session()), auto_commit=True)
#     # Users.create(session, auto_commit=True, name="test", **FAKE_USER_NFORMATION)
#     try:
#         a = 1/0
#     except Exception as e:
#         request.state.inspect = frame()
#         raise e
#     current_time = datetime.utcnow()
#     return Response(f"Notification API (UTC: {current_time.strftime('%Y.%m.%d %H:%M:%S')})")


@router.get("/status")
def check_status() -> Response:
    """
    서버 상태 체크
    """
    try:
        serving_server_status_check_url = f'http://{settings.SERVING_IP_ADDR}:{settings.SERVING_IP_PORT}/healthz'
        response = requests.get(serving_server_status_check_url)
        assert response.status_code == 200
        is_serving_server_working = 'Connection'
    except Exception:
        is_serving_server_working = 'Exception'

    try:
        session = next(db.session())
        session.execute('SELECT 1')
        is_database_working = 'Connection'
    except Exception:
        is_database_working = 'Exception'
    finally:
        session.close()
    
    status = f"is_database_working: {is_database_working}, is_serving_server_working: {is_serving_server_working}"
    return Response(f"Textscope API ({status})")
