import requests

from typing import Any
from fastapi import APIRouter
from starlette.responses import Response

from pp_server.app.database.connection import db
from pp_server.app.common.const import get_settings
from pp_server.app import models


settings = get_settings()
router = APIRouter()


@router.get("/status", response_model=models.StatusResponse)
def check_status() -> Any:
    """
    ### 서버 상태 체크
    응답 데이터: Textscope API (is_database_working: $(is_database_working), is_serving_server_working: $(is_serving_server_working))
    -  is_database_working: 데이터베이스 서버와 연결 상태 확인
    -  is_serving_server_working: 모델 서버와 연결 상태 확인
    """

    return Response(f"PP server: on working")
