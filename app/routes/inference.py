import re
from httpx import Client

from datetime import datetime
from typing import Dict
from fastapi import APIRouter, Body
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder

from app.schemas import inference_responses
from app.utils.utils import (
    set_json_response,
    get_pp_api_name,
    set_ocr_response
)
from app.utils.logging import logger
from app.wrapper import pp, pipeline, settings


router = APIRouter()


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
    start_time = datetime.now()
    request_id = inputs.get("request_id")
    convert_preds_to_texts = inputs.get("convert_preds_to_texts", None)
    post_processing_results = dict()
    response_log = dict()
    response = dict()
    if settings.DEVELOP:
        if inputs.get("test_doc_type", None) is not None:
            inputs["doc_type"] = inputs["test_doc_type"]
    with Client() as client:
        # ocr inference
        if settings.USE_OCR_PIPELINE:
            # TODO: sequence_type을 wrapper에서 받도록 수정
            # TODO: python 3.6 버전에서 async profiling 사용에 제한이 있어 sync로 변경했는데 추후 async 사용해 micro bacing 사용하기 위해서는 다시 변경 필요
            status_code, inference_results, response_log = pipeline.multiple(
                client=client, 
                inputs=inputs,
                sequence_type="kv",
                response_log=response_log,
            )
            response_log = dict()
        else:
            status_code, inference_results, response_log = pipeline.single(
                client=client, 
                inputs=inputs,
                response_log=response_log,
                route_name="heungkuk_life_pipeline",
            )
        
        if status_code < 200 or status_code >= 400:
            return set_json_response(code="3000", message="모델 서버 문제 발생")

        logger.info(f'inf results : {inference_results}')

        kv_inference_results = inference_results.get('kv_detection_result')
        general_detection_result = inference_results.get('general_detection_result')
        classification_result = inference_results.get('classification_result')
        recognition_result = inference_results.get('recognition_result')
        
        pp_inference_results = dict(
            boxes=kv_inference_results.get('boxes'),
            scores=kv_inference_results.get('scores'),
            classes=kv_inference_results.get("classes"),
            texts=kv_inference_results.get("texts"),
            id_type=inference_results.get("id_type"),
            doc_type=inference_results.get("doc_type"),
            image_height=inference_results.get("image_height"),
            image_width=inference_results.get("image_width")
        )

        # ocr post processing
        if settings.DEVELOP:
            if inputs.get("test_class", None) is not None:
                inference_results["doc_type"] = inputs.get("test_class")
        post_processing_type = get_pp_api_name(inference_results.get("doc_type"))
        logger.info(f'pp type: {post_processing_type}')
        if post_processing_type is not None and len(recognition_result["rec_preds"]) > 0:
            status_code, post_processing_results, response_log = pp.post_processing(
                client=client, 
                request_id=request_id,
                response_log=response_log, 
                inference_results=pp_inference_results, 
                post_processing_type=post_processing_type, 
            )
            if status_code < 200 or status_code >= 400:
                return set_json_response(code="3000", message="pp 과정에서 문제 발생")
            kv_inference_results["kv"] = post_processing_results["result"]
            kv_inference_results["texts"] = post_processing_results["texts"]

        # convert preds to texts
        if convert_preds_to_texts is not None and "texts" not in kv_inference_results:
            status_code, texts = pp.convert_preds_to_texts(
                client=client, 
                rec_preds=inference_results.get("rec_preds", []),
            )
            if status_code < 200 or status_code >= 400:
                return set_json_response(code="3000", message="텍스트 변환 과정에서 발생")
            kv_inference_results["texts"] = texts

        logger.info(f'kvresults: {kv_inference_results}')

        inference_results = set_ocr_response(
            general_detection_result=general_detection_result,
            kv_detection_result=kv_inference_results.get("kv", {}),
            recognition_result=recognition_result,
            classification_result=classification_result
        )

    response_log.update(inference_results.get("response_log", {}))
    response.update(response_log=response_log)
    response.update(inference_results=inference_results)
    logger.debug(f"{request_id} inference results: {inference_results}")
    if post_processing_results.get("result", None) is not None or post_processing_type is None:
        response.update(code="1200")
        response.update(minQlt="00")
    logger.info(
        f"OCR api total time: \t{datetime.now() - start_time}"
    )
    return JSONResponse(content=jsonable_encoder(response))
