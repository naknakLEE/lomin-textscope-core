from httpx import AsyncClient

from typing import Dict, Tuple, List, Optional
from operator import attrgetter
from datetime import datetime

from app import wrapper
from app.common import settings
from app.wrapper import model_server_url
from app.utils.logging import logger


"""
### 토큰과 파일을 전달받아 모델 서버에 ocr 처리 요청
입력 데이터: 토큰, ocr에 사용할 파일 <br/>
응답 데이터: 상태 코드, 최소 퀄리티 보장 여부, 신뢰도, 문서 타입, ocr결과(문서에 따라 다른 결과 반환)
"""

# TODO: move to json file
inference_pipeline_list = {    
    "heungkuk": {
        "general_detection": {
            "model_name": "agamotto",
            "route_name": "agamotto",
            "module_name": "detection"
        },
        "kv_detection": {
            "model_name": None,
            "route_name": "duriel",
            "module_name": "detection"
        },
        "classification": {
            "model_name": "duriel",
            "route_name": "duriel",
            "module_name": "classification"
        },
        "recognition": {
            "model_name": "tiamo",
            "route_name": "tiamo",
            "module_name": "recognition"
        },
        "sequence": {
            "kv": ["general_detection", "recognition", "classification", "kv_detection"]
        }
        
    },
    "lomin": {
        "general_detection": {
            "model_name": "detection",
            "route_name": "detection",
            "module_name": "detection"
        },
        "classification": {
            "model_name": "classification",
            "route_name": "classification",
            "module_name": "classification"
        },
        "recognition": {
            "model_name": "recognition",
            "route_name": "recognition",
            "module_name": "recognition"
        },
        "sequence": {
            "kv": ["classification", "general_detection", "recognition"]
        }
    },
    "kbcard": {
        "general_detection": {
            "model_name": "general",
            "route_name": "detection",
            "module_name": "detection"
        },
        "classification": {
            "model_name": "longinus",
            "route_name": "classification",
            "module_name": "classification"
        },
        "recognition": {
            "model_name": "tiamo",
            "route_name": "recognition",
            "module_name": "recognition"
        },
        "sequence": {
            "kv": ["classification", "general_detection", "recognition"]
        }
    }

}
model_mapping_table = {
    "보험금청구서": "agammoto",
    "처방전": "duriel"
}
route_mapping_table = {
    "보험금청구서": "agammoto",
    "처방전": "duriel"
}


inference_pipeline = inference_pipeline_list.get(settings.CUSTOMER)


# TODO: move to utils
def get_name_list(items: Dict, key: str, separator: str = ",") -> List:
    return list(map(
            lambda x: x.strip(), items.get(key).split(separator)
        ))


# TODO: move to utils
def set_ocr_response(
    inputs: Dict, 
    sequence_list: str,
    result_set: Dict
) -> Dict:
    detection_method = "general_detection"
    if "kv_detection" in sequence_list:
        detection_method = "kv_detection"
    classification_result = result_set.get("classification")
    detection_result = result_set.get(detection_method)
    recogniton_result = result_set.get("recognition")
    return dict(
        class_score=classification_result.get("score", 0.0),
        classes=classification_result.get("classes", []),
        scores=detection_result.get("scores", []),
        boxes=detection_result.get("boxes", []),
        image_height=detection_result.get("image_height"),
        image_width=detection_result.get("image_width"),
        id_type=detection_result["id_type"],
        rec_preds=recogniton_result.get("rec_preds", []),
        texts=recogniton_result.get("texts", []),
        doc_type=inputs.get("doc_type"),
    )


def get_model_info(method_name: str, result_set: str) -> Tuple[str, str, str]:
    # TODO: raise not exist method name in pipeline
    model_info = inference_pipeline.get(method_name)
    model_name = model_info.get("model_name", None)
    route_name = model_info.get("route_name", None)
    module_name = model_info.get("module_name", None)
    if route_name is None or method_name is None:
        doc_class = result_set.get("classification").get("doc_class")
        if route_name is None:
            route_name = route_mapping_table.get(doc_class)
        if method_name is None: 
            model_name = model_mapping_table.get(doc_class)
    return (model_name, route_name, module_name)


# TODO: recify 90 추가
# TODO: hint 사용
async def multiple_model_inference(
    client: AsyncClient, 
    inputs: Dict, 
    sequence_type: str,
    response_log: Dict,
    hint: Optional[Dict] = None,
) -> Tuple[int, Dict, Dict]:
    response_log["ocr_pipeline_start_time"] = datetime.now()
    result_set = dict()
    latest_result = dict()
    sequence_list = inference_pipeline.get("sequence")
    for method_name in sequence_list.get(sequence_type):
        start_time = datetime.now()
        response_log[f"{method_name}_start_time"] = start_time
        model_info = get_model_info(method_name, result_set)
        inputs["model_name"], inputs["route_name"], module_name = model_info
        func_name = inputs["model_name"]
        call_func = attrgetter(f"{module_name}.{func_name}")(wrapper)
        result = await call_func(client, inputs, latest_result, response_log, hint)
        latest_result = result_set[method_name] = result.get("response")
        if method_name == "classification" and result.get("is_supported_type") == True:
            break
        if "response_log" in result:
            response_log.update(result.get("response_log"))
        end_time = datetime.now()
        response_log[f"{method_name}_end_time"] = end_time
        response_log[f"{method_name}_inference_time"] = end_time - start_time
    response_log["ocr_pipeline_end_time"] = datetime.now()
    response = set_ocr_response(
        inputs=inputs,
        sequence_list=sequence_list,
        result_set=result_set,
    ) 
    return (result.get("status_code"), response, response_log)


async def single_model_inference(
    client: AsyncClient, 
    inputs: Dict,
    response_log: Dict,
    route_name: str = "ocr",
    hint: Optional[Dict] = None,
) -> Tuple[int, Dict, Dict]:
    inference_start_time = datetime.now()
    ocr_response = await client.post(
        f"{model_server_url}/{route_name}",
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
    return (ocr_response.status_code, ocr_response.json(), response_log)