import requests
import aiohttp
import asyncio
import json

from datetime import datetime
from typing import Dict, Any, List, Optional
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


inference_responses = {
    200: {
        "description": "Item requested by ID",
        "content": {
            "application/json": {
                "example": {
                    "status": "1200",
                    "minQlt": "00",
                    "reliability": "0.367125",
                    "docuType": "00",
                    "ocrResult": {
                        "tenantName": "홍길동",
                        "tenantID": "200123-1234567",
                        "memberNum": "5",
                        "memberList": {
                            "memberName": "심청이",
                            "memberID": "510123-2234567",
                            "memberRelation": "배우자",
                            "status": "00",
                        },
                        "releaseData": "2021-02-10",
                    },
                }
            }
        },
    }
}


@router.post(
    "",
    dependencies=[Depends(db.session), Depends(get_current_active_user)],
    response_model=models.InferenceResponse,
    responses=inference_responses,
)
async def inference(file: UploadFile = File(...)) -> Any:
    """
    ### 토큰과 파일을 전달받아 모델 서버에 ocr 처리 요청
    입력 데이터: 토큰, ocr에 사용할 파일 <br/>
    응답 데이터: 상태 코드, 최소 퀄리티 보장 여부, 신뢰도, 문서 타입, ocr결과(문서에 따라 다른 결과 반환)
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
