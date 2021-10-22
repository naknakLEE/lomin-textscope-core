import httpx
import time
import json
import numpy as np

from datetime import datetime
from typing import Any, Dict
from fastapi import Depends, File, UploadFile, APIRouter, Form, Request, Body
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder

from app import models
from app.schemas import inference_responses
from app.utils.auth import get_current_active_user
from app.utils.utils import set_json_response, get_pp_api_name
from app.common.const import get_settings
from app.utils.logging import logger
from app.database.connection import db


settings = get_settings()
router = APIRouter()

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
async def ocr(inputs: Dict = Body(...)) -> Dict:
    """
    ### 토큰과 파일을 전달받아 모델 서버에 ocr 처리 요청
    입력 데이터: 토큰, ocr에 사용할 파일 <br/>
    응답 데이터: 상태 코드, 최소 퀄리티 보장 여부, 신뢰도, 문서 타입, ocr결과(문서에 따라 다른 결과 반환)
    """
    # inputs = await request.json()
    request_id = inputs.get("request_id")
    convert_preds_to_texts = inputs.get("convert_preds_to_texts", None)
    post_processing_results = dict()
    response_log = dict()
    response = dict(
        code="3400",
        minQlt="01",
        reliability="",
        kv="",
        texts=[],
    )
    async with httpx.AsyncClient() as client:
        # ocr inference
        inference_start_time = datetime.now()
        model_server_response = await client.post(
            f"{model_server_url}/ocr",
            json=inputs,
            timeout=settings.TIMEOUT_SECOND,
        )
        inference_end_time = datetime.now()
        logger.info(f"Inference time: {str((inference_end_time - inference_start_time).total_seconds())}")
        response_log.update(dict(
            inference_request_start_time=inference_start_time.strftime('%Y-%m-%d %H:%M:%S'),
            inference_request_end_time=inference_end_time.strftime('%Y-%m-%d %H:%M:%S'),
        ))
        if model_server_response.status_code < 200 or model_server_response.status_code >= 400:
            logger.debug(f"{request_id} response text: {model_server_response.text}")
            return set_json_response(code="3000", message="모델 서버 문제 발생")
        inference_results = model_server_response.json()
    

        # ocr pp
        if settings.DEVELOP:
            # inference_results["doc_type"] = "Z1_1_거래통장_가상계좌발급확인서"
            pass
        post_processing_start_time = datetime.now()
        post_processing_type = get_pp_api_name(inference_results.get("doc_type", None))
        logger.info(f"{request_id} post processing: {post_processing_type}")
        if post_processing_type is not None and len(inference_results["rec_preds"]) > 0:
            inference_results["img_size"] = inference_results["image_height"], inference_results["image_width"]
            pp_server_response = await client.post(
                f"{pp_server_url}/post_processing/{post_processing_type}",
                json=inference_results,
                timeout=settings.TIMEOUT_SECOND,
            )
            post_processing_end_time = datetime.now()
            response_log.update(dict(
                post_processing_start_time=post_processing_start_time.strftime('%Y-%m-%d %H:%M:%S'),
                post_processing_end_time=post_processing_end_time.strftime('%Y-%m-do%d %H:%M:%S'),
            ))
            logger.info(f"Post processing time: {post_processing_end_time - post_processing_start_time}")
            logger.debug(f"{request_id} response: {type(pp_server_response.text)}")
            if pp_server_response.status_code < 200 or pp_server_response.status_code >= 400:
                return set_json_response(code="3000", message="pp 과정에서 문제 발생")
            post_processing_results = pp_server_response.json()
            inference_results["kv"] = post_processing_results["result"]
            inference_results["texts"] = post_processing_results["texts"]

        # convert preds to texts
        if convert_preds_to_texts is not None:
            request_data = dict(
                rec_preds=inference_results.get("rec_preds", []),
                id_type=inference_results.get("id_type", ""),
            )
            pp_server_response = await client.post(
                f"{pp_server_url}/convert/recognition_to_text",
                json=jsonable_encoder(request_data),
                timeout=settings.TIMEOUT_SECOND,
            )
            if pp_server_response.status_code < 200 or pp_server_response.status_code >= 400:
                return set_json_response(code="3000", message="텍스트 변환 과정에서 발생")
            get_tests_results = pp_server_response.json()
            inference_results["texts"] = get_tests_results

    response_log.update(inference_results.get("response_log", {}))
    response.update(response_log=response_log)
    response.update(inference_results=inference_results)
    logger.debug(f"{request_id} inference results: {inference_results}")
    if post_processing_results.get("result", None) is not None:
        response.update(code="1200")
        response.update(minQlt="00")
    return JSONResponse(content=jsonable_encoder(response))
