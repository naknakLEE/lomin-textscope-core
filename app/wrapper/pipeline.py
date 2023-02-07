from httpx import Client

from typing import Dict, Tuple
from datetime import datetime

from app.models import DocTypeHint
from app.common import settings
from app.utils.hint import apply_cls_hint
from app.utils.logging import logger


model_server_url = f"http://{settings.SERVING_EP_ADDR}:{settings.SERVING_IP_PORT}"
inference_mapping_table = settings.INFERENCE_MAPPING_TABLE

# TODO: pipeline 상에서 각 모델의 inference 끝났을 때 결과를 출력하도록 구성
async def single(
    client: Client,
    inputs: Dict,
    response_log: Dict,
    route_name: str = "gocr",
) -> Tuple[int, Dict, Dict]:
    """doc type hint를 적용하고 inference 요청"""
    # Apply doc type hint
    hint = inputs.get("hint")
    if hint is not None and hint.get("doc_type") is not None:
        doc_type_hint = hint.get("doc_type", {})
        doc_type_hint = DocTypeHint(**doc_type_hint)
        cls_hint_result = apply_cls_hint(doc_type_hint=doc_type_hint)
        response_log.update(apply_cls_hint_result=cls_hint_result)
        inputs["doc_type"] = cls_hint_result.get("doc_type")
    \
    inference_start_time = datetime.now()
    response_log["inference_start_time"] = inference_start_time.strftime(
        "%Y-%m-%d %H:%M:%S.%f"
    )[:-3]

    input_doc_type = inputs["doc_type"]

    if input_doc_type:
        route_name = [k for k, v in inference_mapping_table.items() if input_doc_type in v][-1]
        
    ocr_response = await client.post(
        f"{model_server_url}/{route_name}",
        json=inputs,
        timeout=settings.TIMEOUT_SECOND,
        headers={"User-Agent": "textscope core"},
    )
    inference_end_time = datetime.now()
    response_log.update(
        {
            "inference_end_time": inference_end_time.strftime("%Y-%m-%d %H:%M:%S.%f")[
                :-3
            ],
            "inference_total_time": (
                inference_end_time - inference_start_time
            ).total_seconds(),
        }
    )
    logger.info(
        f"Inference time: {str((inference_end_time - inference_end_time).total_seconds())}"
    )
    return (ocr_response.status_code, ocr_response.json(), response_log)
