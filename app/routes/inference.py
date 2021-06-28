import aiohttp
import asyncio
import json
import requests
import httpx
import cv2

from datetime import datetime
from typing import Dict, Any, List, Optional
from fastapi import Depends, File, UploadFile, APIRouter
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session
from starlette.responses import Response

from app.database.schema import Usage
from app.database.connection import db
from app.utils.auth import get_current_active_user
from app.common.const import get_settings
from app.errors import exceptions as ex
from app.schemas import inference_responses
from app import models


settings = get_settings()
router = APIRouter()

MODEL_SERVER_URL = f"http://{settings.SERVING_IP_ADDR}:{settings.SERVING_IP_PORT}"
PP_SERVER_URL = f"http://{settings.PP_IP_ADDR}:{settings.PP_IP_PORT}"


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


API_ADDR = "v1/inference/pipeline"
URL = f"http://{settings.WEB_IP_ADDR}:{settings.WEB_IP_PORT}/{API_ADDR}"

image_dir = "./others/assets/000000000000000IMG_4825.jpg"
img = cv2.imread(image_dir)
_, img_encoded = cv2.imencode(".jpg", img)
img_bytes = img_encoded.tobytes()

files = {"image": ("test.jpg", img_bytes)}


async def request(client):
    response = await client.post(URL, files=files, timeout=30.0)
    return response.text


async def task():
    async with httpx.AsyncClient() as client:
        tasks = [request(client) for _ in range(10)]
        result = await asyncio.gather(*tasks)
        print("\033[95m" + f"{result}" + "\033[m")


@router.get("/async_test")
async def async_test():
    await task()


@router.get("/get_asyncio_sleep")
async def achyncio_sleep():
    await asyncio.sleep(3)
    return "Complete"


@router.post("/pipeline")
async def inference(image: UploadFile = File(...)) -> Any:
    image_bytes = await image.read()
    files = {"image": ("document_img.jpg", image_bytes)}

    async with httpx.AsyncClient() as client:
        document_ocr_model_response = await client.post(
            f"{MODEL_SERVER_URL}/document_ocr", files=files, timeout=30.0
        )
        document_ocr_result = document_ocr_model_response.json()[0]

        document_ocr_pp_response = await client.post(
            f"{PP_SERVER_URL}/post_processing/document_ocr",
            json=document_ocr_result,
            timeout=30.0,
        )
        result = document_ocr_pp_response.json()

    return result
