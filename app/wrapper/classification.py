from httpx import Client

from typing import Dict, Tuple, Optional, List

from app.common import settings


supported_class = ["처방전", "보험금청구서"]
classification_server_url = f"http://{settings.MULTIPLE_GPU_LOAD_BALANCING_NGINX_IP_ADDR}:{settings.CLASSIFICATION_SERVICE_PORT}"


def longinus(
    client: Client,
    inputs: Dict,
    inference_result: Optional[Dict],
    hint: Optional[Dict] = None,
) -> Tuple[int, Dict]:
    inference_inputs = inputs
    route_name = inputs.get("route_name")
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


async def duriel(
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
        image_size=inference_result["image_size"],
    )
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
