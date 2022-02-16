from httpx import Client

from typing import Dict, Tuple, Optional, List

from app.common import settings

kv_detection_server_url = f"http://{settings.SERVING_IP_ADDR}:{settings.KV_DETECTION_SERVICE_PORT}"
general_detection_server_url = f"http://{settings.SERVING_IP_ADDR}:{settings.GENERAL_DETECTION_SERVICE_PORT}"


def agamotto(
    client: Client,
    inputs: Dict,
    inference_result: Optional[Dict] = None,
    hint: Optional[Dict] = None,
    route_name: Optional[str] = None,
) -> Tuple[int, Dict]:
    # TODO: hint 사용 가능하도록 구성
    inference_inputs = inputs
    if "model_name" in inference_inputs: del inference_inputs["model_name"]
    route_name = "agamotto" if route_name is None else route_name
    detection_response = client.post(
        url=f"{general_detection_server_url}/{route_name}",
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
    doc_type: str,
    hint: Optional[Dict] = None,
    route_name: Optional[str] = None,
) -> Tuple[int, Dict]:
    # TODO: hint 사용 가능하도록 구성
    duriel_inputs = {
        "scores": inference_result.get("scores", []), 
        "boxes": inference_result.get("boxes", []), 
        "classes": inference_result.get("classes", []),
        "texts": inference_result.get("texts", []),
        "image_size": (inference_result.get("image_height"), inference_result.get("image_width")),
        "request_id": inputs.get("request_id"),
        "image_path": inputs.get("image_path"),
        "angle":inputs.get("angle"),
        "page": inputs.get("page"),
        "doc_type": doc_type
    }
    route_name = "duriel" if route_name is None else route_name
    detection_response = client.post(
        f"{kv_detection_server_url}/{route_name}",
        json=duriel_inputs,
        timeout=settings.TIMEOUT_SECOND,
        headers={"User-Agent": "textscope core"},
    )
    detection_result = detection_response.json()
    return dict(status_code=detection_response.status_code, response=detection_result)
