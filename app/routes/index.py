import aiohttp
import requests
import time
import asyncio
import numpy as np
import base64
import json
import cv2

from fastapi.datastructures import UploadFile
from typing import Any
from datetime import datetime
from fastapi import APIRouter, Depends, File
from fastapi.requests import Request
from sqlalchemy.orm import Session
from fastapi.responses import JSONResponse
from starlette.responses import Response
from inspect import currentframe as frame

from app.database.connection import db
from app.database.schema import Users, Usage, Logs
from app.common.const import get_settings
from app import models


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


# @router.post("/pre_processing")
# async def inference(file: UploadFile = File(...)) -> Any:


#     serving_server_inference_url = (
#         f"http://182.20.0.5:8000/post_processing"
#     )

#     start = time.time()
#     image_data = await file.read()
#     data={'file': image_data}
#     print('\033[94m' + f"{type(image_data)}" + '\033[m')
#     async with aiohttp.ClientSession() as session:
#         async with session.post(
#             serving_server_inference_url, data=data
#         ) as response:
#             result = await response.json()
#             end = time.time()
#             # print('\033[94m' + f"{np.array(result).shape}" + '\033[m')
#             print('\033[94m' + f"total time: {end-start}" + '\033[m')


# @router.post("/post_processing")
# async def inference(file: UploadFile = File(...)) -> Any:

#     image = await file.read()
#     encoded_img = np.frombuffer(image, dtype=np.uint8)
#     img = cv2.imdecode(encoded_img, cv2.IMREAD_COLOR)

#     # print('\033[94m' + f"{img.shape}" + '\033[m')
#     encoded_img = cv2.imencode('.jpg', img)[1].tobytes()
#     return encoded_img
#     # return 1234
#     # serving_server_inference_url = (
#     #     f"http://{settings.SERVING_IP_ADDR}:{settings.SERVING_IP_PORT}/inference"
#     # )

#     # image_data = await file.read()
#     # async with aiohttp.ClientSession() as session:
#     #     async with session.post(
#     #         serving_server_inference_url, data=image_data
#     #     ) as response:
#     #         result = await response.json()
#     #         return models.InferenceResponse(ocrResult=result)
