from httpx import AsyncClient

from datetime import datetime
from typing import Dict, Tuple, Optional, List
from fastapi import APIRouter, Body
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder

from app.schemas import inference_responses
from app.utils.utils import set_json_response, get_pp_api_name
from app.common.const import get_settings
from app.utils.logging import logger


settings = get_settings()
router = APIRouter()

model_server_url = f"http://{settings.MULTIPLE_GPU_LOAD_BALANCING_NGINX_IP_ADDR}:{settings.MULTIPLE_GPU_LOAD_BALANCING_NGINX_IP_PORT}"
pp_server_url = f"http://{settings.PP_IP_ADDR}:{settings.PP_IP_PORT}"


"""
### 토큰과 파일을 전달받아 모델 서버에 ocr 처리 요청
입력 데이터: 토큰, ocr에 사용할 파일 <br/>
응답 데이터: 상태 코드, 최소 퀄리티 보장 여부, 신뢰도, 문서 타입, ocr결과(문서에 따라 다른 결과 반환)
"""


async def classification_inference(client: AsyncClient, inputs: Dict) -> Tuple[int, Dict]:
    classification_response = await client.post(
        f"{model_server_url}/classification",
        json=inputs,
        timeout=settings.TIMEOUT_SECOND,
        headers = {"User-Agent": "textscope core"}
    )
    classification_result = classification_response.json()
    return (classification_response.status_code, classification_result)


async def detection_inference(
    client: AsyncClient, 
    inputs: Dict, 
    doc_type: str, 
    hint: Optional[Dict] = None
) -> Tuple[int, Dict]:
    # TODO: hint 사용 가능하도록 구성
    detection_response = await client.post(
        f"{model_server_url}/detection",
        json=inputs,
        timeout=settings.TIMEOUT_SECOND,
        headers = {"User-Agent": "textscope core"}
    )
    detection_result = detection_response.json()
    return (detection_response.status_code, detection_result)


async def recognition_inference(
    client: AsyncClient, 
    detection_result: Dict, 
    inputs: Dict
) -> Tuple[int, Dict]:
    recognition_inputs = dict(
        valid_boxes=detection_result.get("boxes", []),
        classes=detection_result.get("classes", []),
        image_path=inputs["image_path"],
        page=inputs.get("page"),
    )
    recognition_response = await client.post(
        f"{model_server_url}/recognition",
        json=recognition_inputs,
        timeout=settings.TIMEOUT_SECOND,
        headers = {"User-Agent": "textscope core"}
    )
    recognition_result = recognition_response.json()
    return (recognition_response.status_code, recognition_result)


# TODO: recify 90 추가 필요
async def ocr_inference_pipeline(
    client: AsyncClient, 
    inputs: Dict, 
    response_log: Dict,
) -> Tuple[int, Dict, Dict]:
    inference_start_time = datetime.now()
    response_log.update(inference_request_start_time=inference_start_time.strftime('%Y-%m-%d %H:%M:%S'))
    
    _, cls_result = await classification_inference(client, inputs)
    response_log.update(cls_result.get("response_log", {}))

    _, det_result = await detection_inference(client,inputs, cls_result.get("doc_type", None))
    response_log.update(det_result.get("response_log", {}))
    
    rec_status_code, rec_result = await recognition_inference(client, det_result, inputs)
    response_log.update(rec_result.get("response_log", {}))
    inference_end_time = datetime.now()
    logger.info(f"Inference time: {str((inference_end_time - inference_start_time).total_seconds())}")
    response_log.update(dict(
        inference_request_end_time=inference_end_time.strftime('%Y-%m-%d %H:%M:%S'),
        inference_request_time=inference_end_time-inference_start_time,
    ))
    converter_status_code, texts = await ocr_convert_preds_to_texts(client, rec_result.get("rec_preds", []))
    response = dict(
        class_score=cls_result.get("score", 0.0),
        scores=det_result.get("scores", []),
        boxes=det_result.get("boxes", []),
        classes=det_result.get("classes", []),
        image_height=det_result.get("image_height"),
        image_width=det_result.get("image_width"),
        doc_type=inputs["doc_type"],
        id_type=det_result["id_type"],
        rec_preds=rec_result.get("rec_preds", []),
        texts=texts,
    )
    return (rec_status_code, response, response_log)


async def ocr_inference(
    client: AsyncClient, 
    inputs: Dict, 
    response_log: Dict,
) -> Tuple[int, Dict, Dict]:
    inference_start_time = datetime.now()
    model_server_response = await client.post(
        f"{model_server_url}/ocr",
        json=inputs,
        timeout=settings.TIMEOUT_SECOND,
        headers = {"User-Agent": "textscope core"}
    )
    inference_end_time = datetime.now()
    logger.info(f"Inference time: {str((inference_end_time - inference_start_time).total_seconds())}")
    response_log.update(dict(
        inference_request_start_time=inference_start_time.strftime('%Y-%m-%d %H:%M:%S'),
        inference_request_end_time=inference_end_time.strftime('%Y-%m-%d %H:%M:%S'),
        inference_request_time=inference_end_time-inference_start_time,
    ))
    return (model_server_response.status_code, model_server_response.json(), response_log)


async def ocr_post_processing(
    client: AsyncClient, 
    inference_results: Dict, 
    post_processing_type: str, 
    response_log: Dict, 
    request_id: str,
) -> Tuple[int, Dict, Dict]:
    post_processing_start_time = datetime.now()
    response_log.update(post_processing_start_time=post_processing_start_time.strftime('%Y-%m-%d %H:%M:%S'))
    inference_results["img_size"] = inference_results["image_height"], inference_results["image_width"]
    pp_response = await client.post(
        f"{pp_server_url}/post_processing/{post_processing_type}",
        json=inference_results,
        timeout=settings.TIMEOUT_SECOND,
    )
    post_processing_end_time = datetime.now()
    response_log.update(dict(
        post_processing_end_time=post_processing_end_time.strftime('%Y-%m-do%d %H:%M:%S'),
        post_processing_time=post_processing_end_time-post_processing_start_time,
    ))
    return (pp_response.status_code, pp_response.json(), response_log)


async def ocr_convert_preds_to_texts(client: AsyncClient, rec_preds: List, id_type: str = "") -> Tuple[int, Dict]:
    request_data = dict(
        rec_preds=rec_preds,
        id_type="",
    )
    convert_response = await client.post(
        f"{pp_server_url}/convert/recognition_to_text",
        json=jsonable_encoder(request_data),
        timeout=settings.TIMEOUT_SECOND,
    )
    return (convert_response.status_code, convert_response.json())


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
    async with AsyncClient() as client:
        # ocr inference
        if settings.USE_OCR_PIPELINE:
            status_code = 200
            inference_results = dict(
                doc_type='HKL01-CTM-Others'
            )
            response_log = dict()
        else:
            status_code = 200
            inference_results = dict(
                boxes=[
                    [356, 2789, 525, 2938]
                ],
                classes=[
                    "beneficiary_eng_name"
                ],
                scores=[
                    0.3715095520019531
                ],
                texts=[
                    "asdf"
                ],
                id_type='test id type',
                image_height=4032,
                image_width=3024,
                model_name='test model',
                doc_type='test doc type'
            )
            response_log = dict()
        if status_code < 200 or status_code >= 400:
            return set_json_response(code="3000", message="모델 서버 문제 발생")

        # ocr post processing
        if settings.DEVELOP:
            if inputs.get("test_class", None) is not None:
                inference_results["doc_type"] = inputs.get("test_class")
        post_processing_type = get_pp_api_name(inference_results.get("doc_type"))
        if post_processing_type is not None and len(inference_results["rec_preds"]) > 0:
            status_code, post_processing_results, response_log = await ocr_post_processing(
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
        if convert_preds_to_texts is not None:
            status_code, texts = await ocr_convert_preds_to_texts(
                client=client, 
                rec_preds=inference_results.get("rec_preds", []),
            )
            if status_code < 200 or status_code >= 400:
                return set_json_response(code="3000", message="텍스트 변환 과정에서 발생")
            inference_results["texts"] = texts

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
