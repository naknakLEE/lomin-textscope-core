from httpx import Client

from typing import Dict, Tuple, Optional

from app.common import settings


kv_detection_server_url = f"http://{settings.MULTIPLE_GPU_LOAD_BALANCING_NGINX_IP_ADDR}:{settings.KV_DETECTION_SERVICE_PORT}"
general_detection_server_url = f"http://{settings.MULTIPLE_GPU_LOAD_BALANCING_NGINX_IP_ADDR}:{settings.GENERAL_DETECTION_SERVICE_PORT}"


def general(
    client: Client,
    inputs: Dict,
    inference_result: Optional[Dict],
    hint: Optional[Dict] = None,
) -> Tuple[int, Dict]:
    # TODO: hint 사용 가능하도록 구성
    inference_inputs = inputs
    del inference_inputs["model_name"]
    route_name = inputs.get("route_name")
    detection_response = client.post(
        f"{general_detection_server_url}/{route_name}",
        json=inference_inputs,
        timeout=settings.TIMEOUT_SECOND,
        headers={"User-Agent": "textscope core"},
    )
    detection_result = detection_response.json()
    return dict(status_code=detection_response.status_code, response=detection_result)


def duriel(
    client: Client,
    inputs: Dict,
    inference_result: Dict,
    hint: Optional[Dict] = None,
) -> Tuple[int, Dict]:
    # TODO: hint 사용 가능하도록 구성
    route_name = inputs.get("route_name")
    inference_inputs = dict(
        scores=inference_result["scores"],
        boxes=inference_result["boxes"],
        texts=inference_result["texts"],
        image_size=(inference_result["image_height"], inference_result["image_width"]),
    )
    detection_response = client.post(
        f"{kv_detection_server_url}/{route_name}",
        json=inference_inputs,
        timeout=settings.TIMEOUT_SECOND,
        headers={"User-Agent": "textscope core"},
    )
    detection_result = detection_response.json()
    return dict(status_code=detection_response.status_code, response=detection_result)
