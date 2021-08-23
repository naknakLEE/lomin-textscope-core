import requests
import time

from typing import Any
from fastapi import APIRouter
from starlette.responses import Response

from app.database.connection import db
from app.common.const import get_settings
from app.utils.logging import logger
from app import models


settings = get_settings()
router = APIRouter()


@router.get("/status", response_model=models.StatusResponse)
def check_status() -> Any:
    """
    ### 서버 상태 체크
    응답 데이터: Textscope API (is_database_working: $(is_database_working), is_serving_server_working: $(is_serving_server_working))
    -  is_database_working: 데이터베이스 서버와 연결 상태 확인
    -  is_serving_server_working: 모델 서버와 연결 상태 확인
    -  is_pp_server_working: 후처리 서버와 연결 상태 확인
    """
    try:
        is_serving_server_working = "False"
        serving_server_addr = f"http://{settings.SERVING_IP_ADDR}:{settings.SERVING_IP_PORT}"
        serving_server_status_check_url = f"{serving_server_addr}/healthz"
        response = requests.get(serving_server_status_check_url)
        if response.status_code == 200:
            is_serving_server_working = "True"
    except:
        logger.exception("check serving server status")

    try:
        is_pp_server_working = "False"
        pp_server_addr = f"http://{settings.PP_IP_ADDR}:{settings.PP_IP_PORT}"
        pp_server_status_check_url = f"{pp_server_addr}/status"
        response = requests.get(pp_server_status_check_url)
        if response.status_code == 200:
            is_pp_server_working = "True"
    except:
        logger.exception("check pp server status")

    try:
        session = next(db.session())
        session.execute("SELECT 1")
        is_database_working = "True"
    except:
        is_database_working = "False"
    finally:
        session.close()

    status = f"is_database_working: {is_database_working}, is_serving_server_working: {is_serving_server_working}, is_pp_server_working: {is_pp_server_working}"
    return Response(f"Textscope API ({status})")
