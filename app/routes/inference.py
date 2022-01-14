from httpx import Client

from typing import Dict
from fastapi import APIRouter, Body, Depends
from pathlib import Path
from datetime import datetime
from sqlalchemy.orm import Session
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder

from app.wrapper import pp, pipeline, settings
from app.schemas import inference_responses
from app.utils.auth import get_current_active_user
from app.utils.utils import set_json_response, get_pp_api_name, print_error_log
from app.common.const import get_settings
from app.utils.logging import logger
from app.database.connection import db
from app.utils.pdf2txt import get_pdf_text_info
from app.utils.visualizer import visualizer
from app.utils.hint import apply_cls_hint


settings = get_settings()
router = APIRouter()

model_server_url = f"http://{settings.SERVING_IP_ADDR}:{settings.SERVING_IP_PORT}"
pp_server_url = f"http://{settings.PP_IP_ADDR}:{settings.PP_IP_PORT}"


"""
### 토큰과 파일을 전달받아 모델 서버에 ocr 처리 요청
입력 데이터: 토큰, ocr에 사용할 파일 <br/>
응답 데이터: 상태 코드, 최소 퀄리티 보장 여부, 신뢰도, 문서 타입, ocr결과(문서에 따라 다른 결과 반환)
"""


@router.post("/ocr", status_code=200, responses=inference_responses)
async def ocr(
    inputs: Dict = Body(...),
    current_user: dict = Depends(get_current_active_user),
    session: Session = Depends(db.session),
) -> Dict:
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
        # inputs["doc_type"] = "법인등기부등본"
        if inputs.get("test_doc_type", None) is not None:
            inputs["doc_type"] = inputs["test_doc_type"]

    # Apply doc type hint
    hint = inputs.get("hint", {})
    if hint is not None and "doc_type" in hint:
        doc_type_hint = hint if isinstance(hint.get("doc_type"), str) else hint.get("doc_type")
        cls_hint_result = apply_cls_hint(doc_type_hint=doc_type_hint)
        response.update(apply_cls_hint_result=cls_hint_result)
        inputs["doc_type"] = cls_hint_result.get("doc_type")

    if inputs.get("use_general_ocr") and Path(inputs.get("image_path", "")).suffix in [".pdf", ".PDF"]:
        parsed_text_info, image_size = get_pdf_text_info(inputs)
        if len(parsed_text_info) > 0:
            visualizer.save_vis_image.remote(result=parsed_text_info, inputs=inputs, anlge=0.0)
            return JSONResponse(content=jsonable_encoder({"inference_results": parsed_text_info, "response_log": {"original_image_size": image_size}}))
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
                route_name=inputs.get("route_name", "ocr"),
            )
        if status_code < 200 or status_code >= 400:
            return set_json_response(code="3000", message="모델 서버 문제 발생")

        # ocr post processing
        if settings.DEVELOP:
            if inputs.get("test_class", None) is not None:
                inference_results["doc_type"] = inputs.get("test_class")
        post_processing_type = get_pp_api_name(inference_results.get("doc_type"))
        if post_processing_type is not None and len(inference_results["rec_preds"]) > 0:
            status_code, post_processing_results, response_log = pp.post_processing(
                client=client, 
                request_id=request_id,
                response_log=response_log, 
                inference_results=inference_results, 
                post_processing_type=post_processing_type, 
            )
            if status_code < 200 or status_code >= 400:
                return set_json_response(code="3000", message="pp 과정에서 문제 발생")
            inference_results["kv"] = post_processing_results["result"]
            inference_results["texts"] = post_processing_results["texts"]

        # convert preds to texts
        if convert_preds_to_texts is not None and "texts" not in inference_results:
            status_code, texts = pp.convert_preds_to_texts(
                client=client, 
                rec_preds=inference_results.get("rec_preds", []),
            )
            if status_code < 200 or status_code >= 400:
                return set_json_response(code="3000", message="텍스트 변환 과정에서 발생")
            inference_results["texts"] = texts

    visualizer.save_vis_image.remote(inference_results, inputs, inference_results.get("angle", 0.0))
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
