from httpx import Client

from typing import Dict, Optional

from app.common import settings


supported_class = ["처방전", "보험금청구서"]
classification_server_url = f"http://{settings.SERVING_IP_ADDR}:{settings.CLASSIFICATION_SERVICE_PORT}"


def longinus(
    client: Client,
    inputs: Dict,
    inference_result: Optional[Dict] = None,
    hint: Optional[Dict] = None,
    route_name: Optional[str] = None,
) -> Dict:
    inference_inputs = inputs
    route_name = "duriel" if route_name is None else route_name
    classification_response = client.post(
        f"{classification_server_url}/{route_name}",
        json=inference_inputs,
        timeout=settings.TIMEOUT_SECOND,
        headers={"User-Agent": "textscope core"},
    )
    classification_result = classification_response.json()
    response = dict(
        status_code=classification_response.status_code,
        response=classification_result,
        is_supported_type=True,
    )
    if classification_result.get("doc_type") not in supported_class:
        response["is_supported_type"] = False
    return response


def duriel(
    client: Client,
    inputs: Dict,
    inference_result: Dict,
    doc_type: str = "du_cls_model",
    hint: Optional[Dict] = None,
    route_name: Optional[str] = None,
) -> Dict:
    # TODO: hint 사용 가능하도록 구성
    duriel_inputs = {
        "scores": inference_result.get("scores", []),
        "boxes": inference_result.get("boxes", []),
        "classes": inference_result.get("classes", []),
        "texts": inference_result.get("texts", []),
        "image_size": (
            inference_result.get("image_height"),
            inference_result.get("image_width"),
        ),
        "request_id": inputs.get("request_id"),
        "image_path": inputs.get("image_path"),
        "image_id": inputs.get("image_id"),
        "angle": inputs.get("angle"),
        "page": inputs.get("page"),
        "doc_type": doc_type,
    }
    route_name = "duriel" if route_name is None else route_name
    classification_response = client.post(
        f"{classification_server_url}/{route_name}",
        json=duriel_inputs,
        timeout=settings.TIMEOUT_SECOND,
        headers={"User-Agent": "textscope core"},
    )
    classification_result = classification_response.json()
    response = dict(
        status_code=classification_response.status_code,
        response=classification_result,
        is_supported_type=True,
    )
    if classification_result.get("doc_type") not in supported_class:
        response["is_supported_type"] = False
    return response
