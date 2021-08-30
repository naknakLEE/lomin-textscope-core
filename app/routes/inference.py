import httpx

from typing import Any, Dict
from fastapi import Depends, File, UploadFile, APIRouter, Form, Request
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder

from app.database.connection import db
from app.utils.auth import get_current_active_user
from app.common.const import get_settings
from app.utils.logging import logger
from app.schemas import inference_responses
from app import models


settings = get_settings()
router = APIRouter()


model_server_url = f"http://{settings.SERVING_IP_ADDR}:{settings.SERVING_IP_ADDR}"
if settings.CUSTOMER == "kakaobank":
    model_server_url = f"http://{settings.MULTIPLE_GPU_LOAD_BALANCING_NGINX_IP_ADDR}:{settings.MULTIPLE_GPU_LOAD_BALANCING_NGINX_IP_PORT}"
pp_server_url = f"http://{settings.PP_IP_ADDR}:{settings.PP_IP_PORT}"


# response_model=models.InferenceResponse,
# dependencies=[Depends(db.session), Depends(get_current_active_user)],
"""
### 토큰과 파일을 전달받아 모델 서버에 ocr 처리 요청
입력 데이터: 토큰, ocr에 사용할 파일 <br/>
응답 데이터: 상태 코드, 최소 퀄리티 보장 여부, 신뢰도, 문서 타입, ocr결과(문서에 따라 다른 결과 반환)
"""


@router.post("/ocr", status_code=200, responses=inference_responses)
async def ocr(request: Request) -> Dict:
    """
    ### 토큰과 파일을 전달받아 모델 서버에 ocr 처리 요청
    입력 데이터: 토큰, ocr에 사용할 파일 <br/>
    응답 데이터: 상태 코드, 최소 퀄리티 보장 여부, 신뢰도, 문서 타입, ocr결과(문서에 따라 다른 결과 반환)
    """
    serving_server_inference_url = f"http://{settings.SERVING_IP_ADDR}:{settings.SERVING_IP_PORT}"
    inputs = await request.json()
    post_processing = inputs.get("post_processing", None)
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{serving_server_inference_url}/ocr",
            json=inputs,
            timeout=settings.TIMEOUT_SECOND,
        )
        if response.status_code < 200 or response.status_code >= 400:
            return JSONResponse(
                content=jsonable_encoder(dict(code="3000", ocr_result={}, message="모델 서버 문제 발생"))
            )
        inference_results = response.json()
        if post_processing is not None:
            response = await client.post(
                f"{pp_server_url}/post_processing/{post_processing}",
                json=inference_results,
                timeout=settings.TIMEOUT_SECOND,
            )
            if response.status_code < 200 or response.status_code >= 400:
                return JSONResponse(
                    content=jsonable_encoder(
                        dict(code="3000", ocr_result={}, message="후처리 서버 문제 발생")
                    )
                )
            post_processing_results = response.json()
            inference_results["kv"] = post_processing_results["result"]
        logger.debug(f"inference_results: {inference_results}")
    return JSONResponse(content=jsonable_encoder(dict(code="1000", ocr_result=inference_results)))


@router.post("/pipeline")
async def inference(
    edmsId: str,
    lnbzDocClcd: str,
    lnbzMgmtNo: str,
    pwdNo: str,
    image: UploadFile = File(...),
) -> Any:
    image_bytes = await image.read()
    files = {"image": ("document_img.jpg", image_bytes)}
    document_type = settings.DOCUMENT_TYPE_SET[lnbzDocClcd]

    response = dict(
        code="3400",
        minQlt="00",
        reliability="",
        lnbzDocClcd="",
        ocrResult="",
        texts=[],
    )
    async with httpx.AsyncClient() as client:
        logger.debug(model_server_url)
        import time

        inference_start_time = time.time()
        document_ocr_model_response = await client.post(
            f"{model_server_url}/document_ocr",
            files=files,
            timeout=settings.TIMEOUT_SECOND,
        )
        logger.info(f"Ocr time: {time.time() - inference_start_time}")
        if (
            document_ocr_model_response.status_code < 200
            or document_ocr_model_response.status_code >= 400
        ):
            return response
        document_ocr_result = document_ocr_model_response.json()

        post_processing_start_time = time.time()
        document_ocr_pp_response = await client.post(
            f"{pp_server_url}/post_processing/{document_type}",
            json=document_ocr_result,
            timeout=settings.TIMEOUT_SECOND,
        )
        logger.info(f"Post processing time: {time.time() - post_processing_start_time}")
        result = document_ocr_pp_response.json()

    response["texts"] = result["texts"]
    if result["result"] is not None:
        response["code"] = "1200"
        response["minQlt"] = "01"
        response["reliability"] = "1.0"
        response["lnbzDocClcd"] = lnbzDocClcd
        response["ocrResult"] = result["result"]["values"]
    return JSONResponse(content=jsonable_encoder(response))
