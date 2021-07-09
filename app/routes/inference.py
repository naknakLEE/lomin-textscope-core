import aiohttp
import httpx

from typing import Dict, Any, List, Optional
from fastapi import Depends, File, UploadFile, APIRouter, Form
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from loguru import logger

from app.database.connection import db
from app.utils.auth import get_current_active_user
from app.common.const import get_settings
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
        async with session.post(serving_server_inference_url, data=image_data) as response:
            result = await response.json()
            return models.InferenceResponse(ocrResult=result)


@router.post(
    "/tiff/idcard",
    dependencies=[Depends(db.session)],
    responses=inference_responses,
)
async def tiff_idcard_inference(
    image_path: str = Form(...),
    request_id: str = Form(...),
    doc_type: str = Form(...),
    page: str = Form(...),
) -> Any:
    """
    ### 토큰과 파일을 전달받아 모델 서버에 ocr 처리 요청
    입력 데이터: 토큰, ocr에 사용할 파일 <br/>
    응답 데이터: 상태 코드, 최소 퀄리티 보장 여부, 신뢰도, 문서 타입, ocr결과(문서에 따라 다른 결과 반환)
    """
    serving_server_inference_url = f"http://{settings.SERVING_IP_ADDR}:{settings.SERVING_IP_PORT}"

    data = {
        "image_path": image_path,
        "request_id": request_id,
        "doc_type": doc_type,
        "page": page,
    }
    json_data = jsonable_encoder(data)
    async with aiohttp.ClientSession() as session:
        request_api = "tiff_inference_all"
        if json_data["page"] != "None":
            # below return line enable if not set "tiff_inference"
            request_api = "tiff_inference"
        async with session.post(
            f"{serving_server_inference_url}/{request_api}", json=json_data
        ) as response:
            results = await response.json()
            return {"code": "1000", "ocr_result": results}


@router.post("/pipeline")
async def inference(
    edmisId: str, lnbzDocClcd: str, lnbzMgntNo: str, pwdNo: str, image: UploadFile = File(...)
) -> Any:
    image_bytes = await image.read()
    files = {"image": ("document_img.jpg", image_bytes)}
    document_type = settings.DOCUMENT_TYPE_SET[lnbzDocClcd]

    async with httpx.AsyncClient() as client:
        document_ocr_model_response = await client.post(
            f"{MODEL_SERVER_URL}/document_ocr", files=files, timeout=300.0
        )
        document_ocr_result = document_ocr_model_response.json()

        document_ocr_pp_response = await client.post(
            f"{PP_SERVER_URL}/post_processing/{document_type}",
            json=document_ocr_result,
            timeout=30.0,
        )
        result = document_ocr_pp_response.json()["texts"]["values"]

    json_compatible_files = jsonable_encoder(
        {
            "code": "1200",
            "description": "",
            "minQlt": "01",
            "reliability": "1.0",
            "docuType": lnbzDocClcd,
            "ocrResult": result,
        }
    )
    return JSONResponse(content=json_compatible_files)
