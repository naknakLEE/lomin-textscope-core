import json

from httpx import Client

from typing import Dict, Tuple, List, Optional
from operator import attrgetter
from datetime import datetime

from app import wrapper
from app.common import settings
from app.utils.logging import logger

model_server_url = f"http://{settings.SERVING_IP_ADDR}:{settings.SERVING_IP_PORT}"
# TODO: move to json file
inference_pipeline_list = {
    "heungkuk": {
        "general_detection": {
            "model_name": "agamotto",
            "route_name": "agamotto",
            "module_name": "detection",
        },
        "kv_detection": {
            "model_name": None,
            "route_name": "duriel",
            "module_name": "detection",
        },
        "classification": {
            "model_name": "duriel",
            "route_name": "duriel",
            "module_name": "classification",
        },
        "recognition": {
            "model_name": "tiamo",
            "route_name": "tiamo",
            "module_name": "recognition",
        },
        "sequence": {
            "kv": ["general_detection", "recognition", "classification", "kv_detection"]
        },
    },
    "lomin": {
        "general_detection": {
            "model_name": "detection",
            "route_name": "detection",
            "module_name": "detection",
        },
        "classification": {
            "model_name": "classification",
            "route_name": "classification",
            "module_name": "classification",
        },
        "recognition": {
            "model_name": "recognition",
            "route_name": "recognition",
            "module_name": "recognition",
        },
        "sequence": {"kv": ["classification", "general_detection", "recognition"]},
    },
    "kbcard": {
        "general_detection": {
            "model_name": "general",
            "route_name": "detection",
            "module_name": "detection",
        },
        "classification": {
            "model_name": "longinus",
            "route_name": "classification",
            "module_name": "classification",
        },
        "recognition": {
            "model_name": "tiamo",
            "route_name": "recognition",
            "module_name": "recognition",
        },
        "sequence": {"kv": ["classification", "general_detection", "recognition"]},
    },
}
model_mapping_table = {"보험금청구서": "agammoto", "처방전": "duriel"}
route_mapping_table = {"보험금청구서": "agammoto", "처방전": "duriel"}


inference_pipeline = inference_pipeline_list.get(settings.CUSTOMER)


# TODO: move to utils
def get_name_list(items: Dict, key: str, separator: str = ",") -> List:
    return list(map(lambda x: x.strip(), items.get(key).split(separator)))


def set_predictions(
    detection_result: Dict,
    recogniton_result: Dict,
) -> Dict:
    classes = detection_result.get("classes", [])
    scores = detection_result.get("scores", [])
    boxes = detection_result.get("boxes", [])
    texts = (
        detection_result.get("texts", [])
        if "texts" in detection_result
        else recogniton_result.get("texts", [])
    )
    predictions = list()
    for class_, score_, box_, text_ in zip(classes, scores, boxes, texts):
        prediction = {
            "class": class_,
            "score": score_,
            "box": box_,
            "text": text_,
        }
        predictions.append(prediction)
    return predictions


# TODO: move to utils
def set_ocr_response(inputs: Dict, sequence_list: str, result_set: Dict) -> Dict:
    detection_method = "general_detection"
    if "kv_detection" in sequence_list:
        detection_method = "kv_detection"
    classification_result = result_set.get("classification")
    detection_result = result_set.get(detection_method)
    recogniton_result = result_set.get("recognition")
    predicsions = set_predictions(
        detection_result=detection_result,
        recogniton_result=recogniton_result,
    )
    return dict(
        predicsions=predicsions,
        class_score=classification_result.get("score", 0.0),
        image_height=detection_result.get("image_height"),
        image_width=detection_result.get("image_width"),
        id_type=detection_result["id_type"],
        rec_preds=recogniton_result.get("rec_preds", []),
        doc_type=classification_result.get("doc_type"),
    )


# TODO: raise not e~xist method name in pipeline
def get_model_info(method_name: str, result_set: str) -> Tuple[str, str, str]:
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
def multiple(
    client: Client,
    inputs: Dict,
    sequence_type: str,
    response_log: Dict,
    hint: Optional[Dict] = None,
) -> Tuple[int, Dict, Dict]:
    ocr_pipeline_start_time = datetime.now()
    response_log["ocr_pipeline_start_time"] = ocr_pipeline_start_time.strftime("%Y-%m-%d %H:%M:%S")
    sequence_list = inference_pipeline.get("sequence")
    result_set = dict()
    latest_result = dict()
    for method_name in sequence_list.get(sequence_type):
        inference_start_time = datetime.now()
        response_log[f"{method_name}_start_time"] = inference_start_time.strftime("%Y-%m-%d %H:%M:%S")
        model_info = get_model_info(method_name, result_set)
        inputs["model_name"], inputs["route_name"], module_name = model_info
        func_name = inputs["model_name"]

        call_func = attrgetter(f"{module_name}.{func_name}")(wrapper)
        result = call_func(client, inputs, latest_result, hint)
        latest_result = result_set[method_name] = result.get("response")

        inference_end_time = datetime.now()
        response_log[f"{method_name}_end_time"] = inference_end_time.strftime("%Y-%m-%d %H:%M:%S")
        response_log[f"{method_name}_inference_time"] = (inference_end_time - inference_start_time).total_seconds()

        if method_name == "classification" and result.get("is_supported_type") == True:
            break
    ocr_pipeline_end_time = datetime.now()
    response_log["ocr_pipeline_end_time"] = ocr_pipeline_end_time.strftime("%Y-%m-%d %H:%M:%S")
    response_log["ocr_pipeline_total_time"] = (ocr_pipeline_end_time - ocr_pipeline_start_time).total_seconds()
    logger.info("inference log: {}", json.dumps(response_log, indent=4, sort_keys=True))

    response = set_ocr_response(
        inputs=inputs,
        sequence_list=sequence_list,
        result_set=result_set,
    )
    return (result.get("status_code"), response, response_log)


def single(
    client: Client,
    inputs: Dict,
    response_log: Dict,
    route_name: str = "ocr",
    hint: Optional[Dict] = None,
) -> Tuple[int, Dict, Dict]:
    inference_start_time = datetime.now()
    ocr_response = client.post(
        f"{model_server_url}/{route_name}",
        json=inputs,
        timeout=settings.TIMEOUT_SECOND,
        headers={"User-Agent": "textscope core"},
    )
    inference_end_time = datetime.now()
    logger.info(
        f"Inference time: {str((inference_end_time - inference_start_time).total_seconds())}"
    )
    response_log.update(
        dict(
            inference_request_start_time=inference_start_time.strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
            inference_request_end_time=inference_end_time.strftime("%Y-%m-%d %H:%M:%S"),
            inference_request_time=inference_end_time - inference_start_time,
        )
    )
    return (ocr_response.status_code, ocr_response.json(), response_log)
