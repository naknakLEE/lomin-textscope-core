import requests
import aiohttp
import asyncio
import json

from typing import Dict, Any, List
from fastapi import Depends, File, UploadFile, APIRouter
from sqlalchemy.orm import Session
from starlette.responses import Response

from app.database.schema import Usage
from app.database.connection import db
from app.utils.auth import get_current_active_user
from app.common.const import get_settings
from app.errors import exceptions as ex
from app import models


settings = get_settings()
router = APIRouter()


@router.post(
    "",
    dependencies=[Depends(db.session), Depends(get_current_active_user)],
    response_model=models.InferenceResponse,
)
async def inference(file: UploadFile = File(...)) -> Response:
    """
    모델 서버에 inference 요청
    """
    serving_server_inference_url = (
        f"http://{settings.SERVING_IP_ADDR}:{settings.SERVING_IP_PORT}/inference"
    )

    image_data = await file.read()
    async with aiohttp.ClientSession() as session:
        async with session.post(
            serving_server_inference_url, data=image_data
        ) as response:
            result = await response.json()
            return models.InferenceResponse(ocrResult=result)


@router.get("/usage/me", response_model=List[models.Usage])
def read_usage_me_by_email(
    current_user: models.User = Depends(get_current_active_user),
    session: Session = Depends(db.session),
) -> Any:
    """
    현재 유저의 사용량 정보 (날짜, 상태코드 포함) 조회
    """
    usages = Usage.get_usage(session, email=current_user.email)
    return usages


@router.get("/count/me", response_model=models.UsageCount)
def count_usage_me(
    current_user: models.User = Depends(get_current_active_user),
    session: Session = Depends(db.session),
) -> Any:
    """
    현재 유저의 사용량 조회
    """
    usages = Usage.get_usage_count(session, email=current_user.email)
    return cal_usage_count(usages)


def cal_usage_count(usages) -> Dict:
    successed_count = (
        sum(usages["success_response"][0]) if len(usages["success_response"]) else 0
    )
    failed_count = (
        sum(usages["failed_response"][0]) if len(usages["failed_response"]) else 0
    )
    return {
        "total_count": successed_count + failed_count,
        "success_count": successed_count,
        "failed_count": failed_count,
    }
